#!/usr/bin/env python

import argparse
import sys

import yaixm.cli

def cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands', required=True)

    # check sub-command
    sub_parser = subparsers.add_parser('check', help='check against schema')
    sub_parser.add_argument("airspace_file", nargs="?",
                            help="YAML airspace file",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.set_defaults(func=yaixm.cli.check)

    # geojson sub-command
    sub_parser = subparsers.add_parser('geojson', help='convert to GeoJSON')
    sub_parser.add_argument("airspace_file", nargs="?",
                            help="YAML airspace file",
                            type=argparse.FileType("r"), default=sys.stdin)
    sub_parser.add_argument("geojson_file", nargs="?",
                            help="GeoJSON output file, stdout if not specified",
                            type=argparse.FileType("w"),
                            default=sys.stdout)
    sub_parser.add_argument("-r", "--resolution", type=int, default=15,
                            help="Angular resolution, per 90 degrees")
    sub_parser.set_defaults(func=yaixm.cli.geojson)

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
    sub_parser.set_defaults(func=yaixm.cli.json)

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
