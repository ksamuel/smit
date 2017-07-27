
import asyncio
import inspect

from contextlib import closing
import xml.etree.ElementTree as ET

import devpy.develop as log

from haversine import haversine

from website.models import Settings


NH_LOGIN_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" ?>
<ivf:MSG_IVEF xmlns:ivf="http://www.iala-to-be-confirmed.org/XMLSchema/IVEF/0.2.4">
    <ivf:Header MsgRefId="" Version="0.2.4"/>
    <ivf:Body>
        <ivf:LoginRequest Encryption="1" Name="{login}" Password="{password}"/>
    </ivf:Body>
</ivf:MSG_IVEF>
"""

XML_OPENING_TAG = '<?xml version="1.0'
XML_CLOSING_TAG = '</ns:MSG_IVEF>'
XML_NS = {
    "ns": 'http://www.iala-to-be-confirmed.org/XMLSchema/IVEF/0.2.4'
}


async def crawl_xml(
    xml_callback=print,
    tick=10 * 60,  # 10 minutes
    max_timeout=10
):

    if not callable(xml_callback):
        raise ValueError('xml_callback must be callable')

    if not inspect.iscoroutinefunction(xml_callback):
        xml_callback = asyncio.coroutine(xml_callback)

    timeout = 1
    while True:

        try:

            try:
                nh_settings = Settings.objects.get(active=True)
            except (Settings.DoesNotExist, Settings.MultipleObjectsReturned):
                log.error('Unable to load NH settings')
                await asyncio.sleep(1)
                continue

            host = nh_settings.nh_ip_address
            port = nh_settings.nh_port
            login = nh_settings.nh_username
            pwd = nh_settings.nh_password
            tick = nh_settings.nh_refresh_rate

            log.info(f"Connection to {host}:{port}...")

            reader, writer = await asyncio.open_connection(host, port)

            with closing(writer):

                login_payload = NH_LOGIN_TEMPLATE.format(
                    login=login,
                    password=pwd
                )

                writer.write(login_payload.encode('utf8'))

                timeout = 1
                while True:

                    buffer = ""
                    while True:
                        log.info('Download a piece of xml.')
                        data = await reader.read(100000)
                        buffer += data.decode('utf8', errors="replace")

                        if len(buffer) > 10000000:
                            log.error('Buffer is too big. Flushing')
                            buffer = ""
                            continue

                        start = buffer.find(XML_OPENING_TAG)
                        end = buffer.find(XML_CLOSING_TAG)

                        if (start != -1 and end != -1):
                            log.info('Passing xml to callback.')
                            xml = buffer[start:end + len(XML_CLOSING_TAG)]
                            await xml_callback(xml)
                            break

                    nh_settings.refresh_from_db()
                    await asyncio.sleep(nh_settings.nh_refresh_rate)
                    log.info(f'Next download in {tick}s.')
        except Exception as e:
            raise e

        await asyncio.sleep(timeout)
        timeout *= 2

        if timeout > max_timeout:
            timeout = max_timeout


async def process_xml(xml):
    distances = {}
    try:
        nh_settings = Settings.objects.get(active=True)
    except (Settings.DoesNotExist, Settings.MultipleObjectsReturned):
        log.error('Unable to load NH settings')
        return {}
    try:
        root = ET.fromstring(xml)
        for tag in root.findall('.//ns:ObjectData', XML_NS):
            try:
                id_tag = list(tag.findall('.//ns:Identifier', XML_NS))[0]
            except IndexError:
                continue
            try:
                call_sign = id_tag.get('Callsign').strip()
            except AttributeError:
                log.error('No call sign for a vessel in this xml')
                continue
            try:
                pos_tag = list(tag.findall('.//ns:Pos', XML_NS))[0]
            except IndexError:
                continue
            try:
                lat = float(pos_tag.get('Lat'))
                long = float(pos_tag.get('Long'))
            except (TypeError, ValueError):
                continue

            distances[call_sign] = round(haversine(
                (nh_settings.red_dot_lat, nh_settings.red_dot_long),
                (lat, long)
            ), 2)

        log.info(f'New distances to red dot: {distances!r}')
        return distances

    except Exception as e:
        log.exception("Unable to read xml stream.")
