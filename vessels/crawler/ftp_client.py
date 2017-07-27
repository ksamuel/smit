
import io
import csv
import asyncio
import inspect
import hashlib
import logging

import aioftp

import pendulum

from vessels.models import Vessel, VesselActivity
from website.models import Settings

import devpy.develop as log


logger = logging.getLogger("aioftp.client")
logger.propagate = False


class DictReaderStrip(csv.DictReader):
    """ Custom CSV parser stripping whitespaces from header """

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            csv.DictReader.fieldnames.fget(self)
            if self._fieldnames is not None:
                self._fieldnames = [name.strip() for name in self._fieldnames]
        return self._fieldnames


async def crawl_csv(
    host,
    port,
    login,
    pwd,
    path,
    csv_callback=print,
    tick=10 * 60,  # 10 minutes
    max_timeout=10
):

    if not callable(csv_callback):
        raise ValueError('csv_callback must be callable')

    if not inspect.iscoroutinefunction(csv_callback):
        csv_callback = asyncio.coroutine(csv_callback)

    timeout = 1
    while True:

        try:

            try:
                ftp_settings = Settings.objects.get(active=True)
            except (Settings.DoesNotExist, Settings.MultipleObjectsReturned):
                log.error('Unable to load ftp settings')
                await asyncio.sleep(1)
                continue

            host = ftp_settings.sirene_ftp_ip_address
            port = ftp_settings.sirene_ftp_port
            login = ftp_settings.sirene_ftp_username
            pwd = ftp_settings.sirene_ftp_password
            tick = ftp_settings.sirene_ftp_refresh_rate
            path = ftp_settings.sirene_csv_file_path

            log.info(f"Connection to {host}:{port}...")

            async with aioftp.ClientSession(host, port, login, pwd) as client:

                timeout = 1
                while True:

                    if not await client.exists(path):
                        log.error(
                            f"'{path}' can't be "
                            f"found on FTP {host}:{port}"
                        )
                    else:
                        log.info('Downloading csv.')
                        async with client.download_stream(path) as stream:
                            log.info('Passing csv to callback.')
                            await csv_callback(stream)
                            log.info('Callback ok.')

                    log.info(f'Next download in {tick}s.')
                    ftp_settings.refresh_from_db()
                    await asyncio.sleep(ftp_settings.sirene_ftp_refresh_rate)

        except AttributeError as e:

            if "'Client' object has no attribute 'stream'" in str(e):
                log.warning(
                    f"Unable to connect to FTP {host}:{port}\n"
                    f"Retrying in {timeout}s"
                )
            else:
                raise

        except aioftp.errors.StatusCodeError as e:
            if '530' in e.received_codes:
                log.error(
                    f"The login or password has been "
                    f'rejected by {host}:{port}'
                )
            else:

                log.warning(
                    f"Connection to {host}:{port} failed with: '{e}'\n"
                    f"Retrying in {timeout}s"
                )

        except ConnectionResetError:

                log.warning(
                    f"Connection to {host}:{port} lost\n"
                    f"Retrying in {timeout}s"
                )

        await asyncio.sleep(timeout)
        timeout *= 2

        if timeout > max_timeout:
            timeout = max_timeout


def get_text_field(row, name):
    value = row.get(name)
    if value is not None:
        value = value.strip()
    if value == 'AUCUN':
        return None
    return value


def get_num_field(row, name, cast=float, default=None):
    try:
        return float(row.get(name).strip())
    except (ValueError, AttributeError):
        return default


async def save_csv(
    stream,
    encoding='utf8',
    new_activity_delay=5 * 3600,
    timezone='Europe/Paris'
):
    now = pendulum.utcnow().timestamp()
    vessel_activities = []
    loop = asyncio.get_event_loop()
    try:

        text = await stream.read(10_000_000)
        text = text.decode(encoding=encoding, errors='replace')

        # Check if we have several vessels with the same name
        duplicate_names = {}
        for row in DictReaderStrip(io.StringIO(text)):
            name = get_text_field(row, 'NOMNAVIRE')
            duplicate_names[name] = duplicate_names.get(name, 0) + 1

        duplicate_names = {
            name: count
            for name, count in duplicate_names.items()
            if count > 1
        }

        all_call_signs = set()
        for i, row in enumerate(DictReaderStrip(io.StringIO(text))):

            vessel_activity_dict = {'timestamp': now}

            # Example of row:
            # OrderedDict([
            #   ('MOUVEMENT', 'E'),
            #   ('NUMERODEMANDE', '198678'),
            #   ('NOMNAVIRE', 'BUTES'),
            #   ('LONGUEUR', '87.84'),
            #   ('TIRANTEAU', '3.3'),
            #   ('POSTEAQUAI', ''),
            #   ('PROVENANCE', 'Warrenpoint'),
            #   ('DESTINATION', 'Sevilla'),
            #   ('DATEDEBUTMVTPREVUE', '27/05/2016 00:01'),
            #   ('NUMEROSOFI', '194323'),
            #   ('NAVIREDANGEREUX', '0'),
            #   ('CALLSIGN', 'A8UR6'),
            #   ('TYPEVTS', '4'),
            #   ('NUMEROLLOYD', '9409637'),
            #   ('BONPOURMOUVEMENT', '0'),
            #   ('OBSERVATIONS', '')
            #   ])

            call_sign = get_text_field(row, 'CALLSIGN')

            # duplicate call sign. There is nothing we can do but
            # ignore it
            if call_sign and call_sign in all_call_signs:
                log.error(f'Duplicate call sign {call_sign}')
                continue

            all_call_signs.add(call_sign)

            draft = get_num_field(row, 'TIRANTEAU')
            length = get_num_field(row, 'LONGUEUR')
            name = get_text_field(row, 'NOMNAVIRE')

            # no name and no call sign: nothing we can do
            if not call_sign and not name:
                continue

            def get_vessel(call_sign, name, draft, length, duplicates):
                """ Try to get a matching vessel """

                # get the vessel by the unique name
                if call_sign:
                    try:
                        vessel = Vessel.objects.get(call_sign=call_sign)
                        log.info(f'Known vessel: {vessel}')
                        return vessel
                    except Vessel.DoesNotExist:
                        vessel = Vessel.objects.create(
                            draft=draft,
                            length=length,
                            name=name,
                            call_sign=call_sign
                        )
                        log.info(f'New vessel: {vessel}')
                        return vessel

                # failling that, try to get the boat by the name.
                if name not in duplicates:

                    # from the boat table
                    try:
                        return Vessel.objects.get(name=name)
                    except Vessel.DoesNotExist:
                        log.info(f'New vessel: {vessel}')
                        return Vessel.objects.create(
                            draft=draft,
                            length=length,
                            name=name,
                            all_sign=call_sign
                        )
                    # or in case there are several known vessels with that
                    # name, from the most recent unique activity with this
                    # boat
                    except Vessel.MultipleObjectsReturned:
                        activity = VesselActivity.get_recent_activity_for(
                            name=name
                        )
                        if activity:
                            log.info(f'Known vessel: {activity.vessel}')
                            return activity.vessel

                return None

            vessel = await loop.run_in_executor(
                None,
                get_vessel,
                call_sign,
                name,
                draft,
                length,
                duplicate_names
            )

            if not vessel:
                log.error(f'Anonymous vessel record: {row}')

            # If we can find a vessel, we update its values
            else:

                before = repr(vessel)

                if draft and vessel.draft != draft:
                    vessel.draft = draft
                if length and vessel.length != length:
                    vessel.length = length
                if name and vessel.name != name:
                    vessel.name = name

                after = repr(vessel)

                if before != after:
                    await loop.run_in_executor(None, vessel.save)
                    log.info(f'Vessel data has changed to: {vessel!r}')

            # the serialized vessel activity is either from db
            # or, lacking from a known vessel, constructed from the
            # date from the csv
            vessel_activity = None
            if vessel:
                vessel_activity_dict['anonymous'] = False
                vessel_activity_dict.update(vessel.to_dict())
                vessel_activity = await loop.run_in_executor(
                    None,
                    vessel.get_latest_activity,
                    new_activity_delay
                )
            else:
                vessel_activity_dict['anonymous'] = True
                vessel_activity_dict['name'] = name
                vessel_activity_dict['length'] = length
                vessel_activity_dict['draft'] = draft
                vessel_activity_dict['call_sign'] = call_sign

            if not vessel_activity:
                vessel_activity = VesselActivity(vessel=vessel)

            activity_type = get_text_field(row, 'MOUVEMENT')
            vessel_activity.type = ({
                'S': 'departing',
                'E': 'incomming',
                'D': 'shifting'
            }).get(activity_type)

            vessel_activity.good_to_go = bool(get_num_field(
                row,
                'NOMBREDETUGS',
                cast=int,
                default=0)
            )

            incoming_from = get_text_field(row, 'PROVENANCE')
            vessel_activity.incoming_from = incoming_from

            leaving_to = get_text_field(row, 'DESTINATION')
            vessel_activity.leaving_to = leaving_to

            berth = get_text_field(row, 'POSTEAQUAI')
            vessel_activity.berth = berth

            services = get_text_field(row, 'DEBUTDESOPERATIONSCOMMERCIALES')
            vessel_activity.services = services or None

            vessel_activity.tugs = get_num_field(row, 'NOMBREDETUGS', int)

            try:
                date = get_text_field(row, 'DATEDEBUTMVTPREVUE') or ''
                sirene_time_estimate = pendulum.parse(
                    date,
                    tz=timezone
                )
            except (ValueError, AttributeError):
                sirene_time_estimate = None
            vessel_activity.sirene_time_estimate = sirene_time_estimate

            obs = get_text_field(row, 'OBSERVATIONS')
            vessel_activity.sirene_observation = obs

            vessel_activity.dangerous_materials = get_num_field(
                row,
                'NAVIREDANGEREUX',
                int
            )

            # we only create a vessel activity if we have a named vessel
            # since we could not get it back later anyway with it
            if vessel:
                vessel_activity.save()

            # serialized vessel activity data is completed with previous
            # data from db and the one found in the csv plus a few
            # adjustment for the front end
            vessel_activity_dict.update(vessel_activity.to_dict(timezone))

            if vessel_activity_dict['anonymous']:
                # generate a fake unique id for this name
                duplicate_index = duplicate_names.setdefault(name, 0) - 1
                unique_name = f"{name}/{duplicate_index}".encode('utf8')
                fake_id = hashlib.sha256(unique_name).hexdigest()
                duplicate_names[name] -= 1
                vessel_activity_dict['id'] = fake_id

            vessel_activities.append(vessel_activity_dict)
    except Exception as e:
        log.exception("Unable to read csv file.")

    # clear all activities older than 6 months
    def clear_old_activities():
        six_month_ago = pendulum.utcnow().add(months=-6)
        res = VesselActivity.objects.filter(modified__lt=six_month_ago).delete()
        log.info(f'Deleted old activities: {res}')
    await loop.run_in_executor(None, clear_old_activities)

    return vessel_activities
