# Copyright 2017 Alan Sparrow
#
# This file is part of YAIXM
#
# YAIXM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YAIXM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YAIXM.  If not, see <http://www.gnu.org/licenses/>.

import json
import sys

from .convert import Openair, Tnp, seq_name, make_openair_type
from .helpers import load, validate, merge_loa

def check(args):
    # Load airspace
    airspace = load(args.airspace_file)

    # Validate and write any errors to stderr
    e = validate(airspace)
    if e:
        print(e.message, file=sys.stderr)
        sys.exit(1)

def openair(args):
    # Load airspace
    airspace = load(args.airspace_file)

    # Convert to openair
    if args.comp:
        convert = Openair(name_func=seq_name, type_func=make_openair_type(comp=True))
    else:
        convert = Openair()
    oa = convert.convert(airspace['airspace'])

    # Don't accept anything other than ASCII
    output_oa = oa.encode("ascii").decode("ascii")

    args.openair_file.write(output_oa)

def tnp(args):
    # Load airspace
    airspace = load(args.airspace_file)

    # Convert to openair
    convert = Tnp()
    oa = convert.convert(airspace['airspace'])

    # Don't accept anything other than ASCII
    output_oa = oa.encode("ascii").decode("ascii")

    args.tnp_file.write(output_oa)

def json(args):
    data = load(args.yaml_file)
    json.dump(data, args.json_file, sort_keys=args.sort, indent=args.indent)

    if args.json_file is sys.stdout:
        print()

def merge(args):
    yaixm = load(args.input_file)
    airspace = yaixm['airspace']
    loa = yaixm['loa']

    loa_names = [x.strip() for x in args.merge.split(",")]

    if loa_names[0]:
        loa = [x for x in loa if x['name'] in loa_names]

    merged = {'airspace': merge_loa(airspace, loa)}

    json.dump(merged, args.output_file, sort_keys=True, indent=4)

def geojson(args):
    # Do the import here to avoid hard dependency on pygeodesy
    try:
        from .geojson import geojson as convert_geojson
    except ModuleNotFoundError:
        print("ERROR: GeoJSON requires the PyGeodesy package")
        sys.exit(1)

    # Load airspace
    airspace = load(args.airspace_file)

    # Convert to GeoJSON
    gjson = convert_geojson(airspace['airspace'], resolution=args.resolution)

    json.dump(gjson, args.geojson_file, sort_keys=True, indent=4)
