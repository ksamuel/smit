
import asyncio

from django.core.management.base import BaseCommand

from vessels.crawler.nh_client import crawl_xml, process_xml


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'


    def handle(self, *args, **options):

        loop = asyncio.get_event_loop()
        coro = crawl_xml(xml_callback=process_xml)
        loop.run_until_complete(coro)
        loop.close()
