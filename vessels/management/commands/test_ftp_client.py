
import asyncio

from django.core.management.base import BaseCommand

from vessels.crawler.ftp_client import crawl_csv, save_csv


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='localhost', type=str)
        parser.add_argument('--port', default='2121', type=str)
        parser.add_argument('--login', default='user', type=str)
        parser.add_argument('--password', default='password', type=str)
        parser.add_argument('--csv-file', default='fixture.csv', type=str)
        parser.add_argument('--tick', default=1, type=int)

    def handle(self, *args, **options):

        loop = asyncio.get_event_loop()
        coro = crawl_csv(
            host=options['host'],
            port=options['port'],
            login=options['login'],
            pwd=options['password'],
            path=options['csv_file'],
            csv_callback=save_csv,
            tick=options['tick']
        )
        loop.run_until_complete(coro)
        loop.close()
