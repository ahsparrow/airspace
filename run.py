#!/usr/bin/env python
import argparse
import sys

import yaixm.cli
import yaixm.util_cli

def cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='commands', dest='cmd',
                                       required=True)

    # check sub-command
    sub_parser = subparsers.add_parser('check', help='check against schema')
    sub_parser.add_argument("airspace_file", nargs="?",
                            help="YAML airspace file",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.set_defaults(func=yaixm.cli.check)

    # check-service sub-command
    sub_parser = subparsers.add_parser('check-service',
            help='check services exist in airspace file')
    sub_parser.add_argument("service_file", type=argparse.FileType("r"),
                            help="Service file")
    sub_parser.add_argument("airspace_file", type=argparse.FileType("r"),
                            help="Airspace file")
    sub_parser.set_defaults(func=yaixm.util_cli.check_service)

    # geojson sub-command
    sub_parser = subparsers.add_parser('geojson', help='convert to GeoJSON')
    sub_parser.add_argument("airspace_file", nargs="?",
                            help="airspace file (YAIXM or Openair)",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.add_argument("geojson_file", nargs="?",
                            help="GeoJSON output file, stdout if not specified",
                            type=argparse.FileType("w"),
                            default=sys.stdout)
    sub_parser.add_argument("-r", "--resolution", type=int, default=15,
                            help="Angular resolution, per 90 degrees")
    sub_parser.set_defaults(func=yaixm.cli.geojson)

    # ils sub-command
    sub_parser = subparsers.add_parser('ils', help='calculate ILS coordinates')
    sub_parser.add_argument("lat", help="Centre latitude, DMS e.g. 512345N")
    sub_parser.add_argument("lon", help="Centre longitude, DMS e.g. 0012345W")
    sub_parser.add_argument("bearing", type=float, help="Runway bearing, degrees")
    sub_parser.add_argument("radius", type=float, nargs="?", default=2,
                            help="ATZ radius, in nm (default 2)")
    sub_parser.set_defaults(func=yaixm.util_cli.calc_ils)

    # json sub-command
    sub_parser = subparsers.add_parser('json', help='convert to JSON')
    sub_parser.add_argument("yaml_file", nargs="?",
                            help="YAML input file, stdin if not specified",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.add_argument("json_file", nargs="?",
                            help="JSON output file, stdout if not specified",
                            type=argparse.FileType("w"), default=sys.stdout)
    sub_parser.add_argument("-i", "--indent", type=int, help="indent level",
                            default=None)
    sub_parser.add_argument("-s", "--sort", help="sort keys", action="store_true")
    sub_parser.set_defaults(func=yaixm.cli.jsonify)

    # merge sub-command
    sub_parser = subparsers.add_parser('merge', help='merge LOAs')
    sub_parser.add_argument("input_file", nargs="?",
                            help="YAML input file, stdin if not specified",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.add_argument("output_file", nargs="?",
                            help="Merged JSON output file, stdout if not specified",
                            type=argparse.FileType("w"), default=sys.stdout)
    sub_parser.add_argument("-m", "--merge", default="",
                            help="Comma separated list of LOAs to merge")
    sub_parser.set_defaults(func=yaixm.cli.merge)

    # obstacle sub-command
    sub_parser = subparsers.add_parser('obstacle', help='convert obstacles')
    sub_parser.add_argument("obstacle_xls", help="ENR obstacle XLS data")
    sub_parser.add_argument("names", help="CSV file with id, name",
                            type=argparse.FileType("r"))
    sub_parser.add_argument("yaml_file", nargs="?",
                            help="YAML output file, stdout if not specified",
                            type=argparse.FileType("w"), default=sys.stdout)
    sub_parser.set_defaults(func=yaixm.util_cli.convert_obstacle)

    # navplot sub-command
    sub_parser = subparsers.add_parser('navplot', help='make NavPlot airspace')
    sub_parser.add_argument("yaixm_file", type=argparse.FileType("r"),
                            help="Airspace input file")
    sub_parser.add_argument("navplot_file", type=argparse.FileType("w"),
                            help="NavPlot output file")
    sub_parser.set_defaults(func=yaixm.cli.navplot)

    # openair sub-command
    sub_parser = subparsers.add_parser('openair', help='convert to OpenAir')
    sub_parser.add_argument("airspace_file", nargs="?",
                            help="YAML airspace file",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.add_argument("openair_file", nargs="?",
                            help="Openair output file, stdout if not specified",
                            type=argparse.FileType("w", encoding="ascii"),
                            default=sys.stdout)
    sub_parser.add_argument("--comp",
                            help="Competition airspace", action="store_true")
    sub_parser.set_defaults(func=yaixm.cli.openair)

    # point sub-command
    sub_parser = subparsers.add_parser('point', help='calculate offset point')
    sub_parser.add_argument("lat", help="Centre latitude, DMS e.g. 512345N")
    sub_parser.add_argument("lon", help="Centre longitude, DMS e.g. 0012345W")
    sub_parser.add_argument("bearing", type=float, help="Degrees (true)")
    sub_parser.add_argument("distance", type=float, help="Distance (nm)")
    sub_parser.set_defaults(func=yaixm.util_cli.calc_point)

    # release sub-command
    sub_parser = subparsers.add_parser('release', help='make ASSelect airspace')
    sub_parser.add_argument("yaixm_dir",
                            help="YAML input directory")
    sub_parser.add_argument("yaixm_file", type=argparse.FileType("w"),
                            help="JSON output file")
    sub_parser.add_argument("openair_file", type=argparse.FileType("w"),
                            help="OpenAir output file")
    sub_parser.add_argument("--indent", "-i", type=int, default=None,
                            help="JSON file indentation level (default none)")
    sub_parser.add_argument("--note", "-n", help="Release note file",
                            type=argparse.FileType("r"), default=None)
    group = sub_parser.add_mutually_exclusive_group()
    group.add_argument("--prev", "-p", action="store_const", default=0,
                       dest="offset", const=-28, help="Use previous AIRAC date")
    group.add_argument("--next", action="store_const", default=0,
                       dest="offset", const=28, help="Use next AIRAC date")
    sub_parser.set_defaults(func=yaixm.util_cli.release)

    # stub sub-command
    sub_parser = subparsers.add_parser('stub', help='calculate MATZ stub coordinates')
    sub_parser.add_argument("lat", help="Centre latitude, DMS e.g. 512345N")
    sub_parser.add_argument("lon", help="Centre longitude, DMS e.g. 0012345W")
    sub_parser.add_argument("bearing", type=float, help="R/W bearing, degrees (true)")
    sub_parser.add_argument("length", type=float, nargs="?", default=5,
                            help="Stub length (nm)")
    sub_parser.add_argument("width", type=float, nargs="?", default=4,
                            help="Stub width (nm)")
    sub_parser.add_argument("radius", type=float, nargs="?", default=5,
                            help="Circle radius (nm)")
    sub_parser.set_defaults(func=yaixm.util_cli.calc_stub)

    # tnp sub-command
    sub_parser = subparsers.add_parser('tnp', help='convert to TNP')
    sub_parser.add_argument("airspace_file", nargs="?",
                            help="YAML airspace file",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.add_argument("tnp_file", nargs="?",
                            help="TNP output file, stdout if not specified",
                            type=argparse.FileType("w", encoding="ascii"),
                            default=sys.stdout)
    sub_parser.set_defaults(func=yaixm.cli.tnp)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    cli()
