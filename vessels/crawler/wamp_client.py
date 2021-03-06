import os
import sys
import asyncio

from pathlib import Path

import pendulum

sys.path.append(str(Path(__file__).absolute().parent.parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
from django.core.wsgi import get_wsgi_application  # noqa
application = get_wsgi_application()

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner # noqa

import devpy.develop as log

# Boost the log max file size to 1Gb
log.handlers[0].maxBytes *= 1000

from vessels.models import VesselActivity # noqa
from vessels.crawler.ftp_client import crawl_csv, save_csv # noqa
from vessels.crawler.nh_client import process_xml, crawl_xml # noqa


class WampClient(ApplicationSession):

    async def onJoin(self, details):

        loop = asyncio.get_event_loop()

        async def update_activity_status(id, status):
            """ Update ship status for the given activity """

            def _(id, value):
                log.info(f'Update activity "{id}" status to "{status}"')
                activity = VesselActivity.objects.get(id=id)
                activity.status = status or None
                activity.save()
                return activity.to_dict(
                    timezone="Europe/Paris", include_vessel=True
                )

            activity = await loop.run_in_executor(None, _, id, status)
            activity['timestamp'] = pendulum.utcnow().timestamp()

            log.info(f'Update status info for activity {activity!r}')

            self.publish('smit.activity.update', activity)
            return activity
        self.register(update_activity_status, 'smit.activity.update.status')

        async def update_vessel_helico(id, helico):
            """ Update helicopter approval for the vessel of this activity """

            def _(id, value):

                activity = VesselActivity.objects.get(id=id)
                vessel = activity.vessel

                log.info(f'Update vessel "{vessel.id}" helico to "{helico}"')

                vessel.helico = helico or None
                vessel.save()
                return activity.to_dict(
                    timezone="Europe/Paris", include_vessel=True
                )

            activity = await loop.run_in_executor(None, _, id, helico)
            activity['timestamp'] = pendulum.utcnow().timestamp()

            log.info(f'Update helico info for activity {activity!r}')

            self.publish('smit.activity.update', activity)
            return activity
        self.register(update_vessel_helico, 'smit.vessel.update.helico')

        async def update_vessel_helico_obs(id, obs):
            """ Update helicopter obs for the vessel of this activity """

            def _(id, value):

                activity = VesselActivity.objects.get(id=id)
                vessel = activity.vessel

                log.info(f'Update vessel "{vessel.id}" helico to "{obs}"')

                vessel.helico_observation = obs or None
                vessel.save()
                return activity.to_dict(
                    timezone="Europe/Paris", include_vessel=True
                )

            activity = await loop.run_in_executor(None, _, id, obs)
            activity['timestamp'] = pendulum.utcnow().timestamp()

            log.info(f'Update helico obs for activity {activity!r}')

            self.publish('smit.activity.update', activity)
            return activity
        self.register(update_vessel_helico_obs, 'smit.vessel.update.helico_obs')


        async def publish_csv_update(stream):
            activities = await save_csv(stream)
            self.publish('smit.sirene.csv.update', activities)

        coro = crawl_csv(
            host="localhost",
            login="user",
            pwd="password",
            port=2121,
            path="fixture.csv",
            csv_callback=publish_csv_update,
            tick=3
        )

        asyncio.ensure_future(coro)

        async def publish_xml_update(stream):
            distances = await process_xml(stream)
            self.publish('smit.nh.xml.update', distances)

        asyncio.ensure_future(crawl_xml(xml_callback=publish_xml_update))


if __name__ == '__main__':
    runner = ApplicationRunner("ws://127.0.0.1:3333/ws", "realm1")
    runner.run(WampClient)
