import logging
import argparse
import sys

from nmea_converter_proxy.cmd import (run_cmd, init_cmd, fake_concentrator_cmd,
                                      log_file_cmd, fake_aanderaa_cmd,
                                      fake_optiplex_cmd, fake_generic_sensor)
from nmea_converter_proxy.conf import LoggerConfig, LOG_FILE

logger_config = LoggerConfig('nmea_converter_proxy', LOG_FILE, logging.DEBUG)

parser = argparse.ArgumentParser(prog="python -m nmea_converter_proxy",
                                 description='Convert and proxy messages to an NMEA concentrator.')
parser.add_argument('--debug', action="store_true")

subparsers = parser.add_subparsers()

run = subparsers.add_parser('run')
run.add_argument('config_file', metavar="CONFIG_FILE", help='.ini configuration file')
run.set_defaults(func=run_cmd)

run = subparsers.add_parser('init')
run.set_defaults(func=init_cmd)

log_file = subparsers.add_parser('log')
log_file.set_defaults(func=log_file_cmd)

fake_concentrator = subparsers.add_parser('fakeconcentrator')
fake_concentrator.set_defaults(func=fake_concentrator_cmd)
fake_concentrator.add_argument('--port', default=8500, nargs='?')

fake_aanderaa = subparsers.add_parser('fakeaanderaa')
fake_aanderaa.set_defaults(func=fake_aanderaa_cmd)
fake_aanderaa.add_argument('data_file', metavar="DATA_FILE", nargs='?',
                           help='File containing fake data to send')
fake_aanderaa.add_argument('--port', default=8502, nargs='?')

fake_optiplex = subparsers.add_parser('fakeoptiplex')
fake_optiplex.set_defaults(func=fake_optiplex_cmd)
fake_optiplex.add_argument('data_file', metavar="DATA_FILE", nargs='?',
                           help='File containing fake data to send')
fake_optiplex.add_argument('--port', default=8501, nargs='?')

fake_optiplex = subparsers.add_parser('fakegenericsensor')
fake_optiplex.set_defaults(func=fake_generic_sensor)
fake_optiplex.add_argument('--port', default=8503, nargs='?')

args = parser.parse_args()
logger_config.debug_mode(args.debug)
if not hasattr(args, 'func'):
    parser.print_usage()
else:
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit('Program interrupted manually')
