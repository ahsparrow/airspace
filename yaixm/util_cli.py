# Copyright 2017 Alan Sparrow
#
# This file is part of YAIXM utils
#
# YAIXM utils is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YAIXM utils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YAIXM utils.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import datetime
import json
import math
import os.path
import re
import subprocess
import sys
import tempfile

from pygeodesy.ellipsoidalVincenty import LatLon
import yaixm
import yaml

from .convert import Openair, make_openair_type, make_filter
from .helpers import merge_loa, merge_service
from .obstacle import make_obstacles

HEADER = """UK Airspace
Alan Sparrow (airspace@asselect.uk)

To the extent possible under law Alan Sparrow has waived all
copyright and related or neighbouring rights to this file. The data
is sourced from the UK Aeronautical Information Package (AIP)\n\n"""

# Convert obstacle data XLS spreadsheet from AIS to YAXIM format
def convert_obstacle(args):
    # Using temporary working directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Convert xls to xlsx
        subprocess.run(["libreoffice",
             "--convert-to", "xlsx",
             "--outdir", tmp_dir,
             args.obstacle_xls], errors=True)

        base_xls = os.path.basename(args.obstacle_xls)
        base_xlsx = os.path.splitext(base_xls)[0] + ".xlsx"
        xlsx_name = os.path.join(tmp_dir, base_xlsx)

        # Convert xlsx to CSV
        csv_name = os.path.join(tmp_dir, "obstacle.csv")
        subprocess.run(["xlsx2csv",
                        "--sheetname" , "All", xlsx_name, csv_name],
                       errors=True)

        obstacles = make_obstacles(open(csv_name), args.names)

    # Write to YAML file
    yaml.add_representer(dict, yaixm.ordered_map_representer)
    yaml.dump({'obstacle': obstacles},
              args.yaml_file, default_flow_style=False)

# Get next AIRAC effective date after today
def get_airac_date(offset=0):
    # AIRAC cycle is fixed four week schedule
    airac_date = datetime.date(2017, 11, 9)
    today = datetime.date.today()
    while airac_date < today:
        airac_date += datetime.timedelta(days=28)

    if offset != 0:
        airac_date += datetime.timedelta(days=offset)

    return airac_date.isoformat() + "T00:00:00Z"

# Convert collection of YAIXM files containing airspace, LOAs and
# obstacles to JSON file with release header and to default Openair file
def release(args):
    # Aggregate YAIXM files
    out = {}
    for f in ["airspace", "loa", "obstacle", "rat", "service"]:
        out.update(yaixm.load(open(os.path.join(args.yaixm_dir, f + ".yaml"))))

    # Append release header
    header = {
        'schema_version': 1,
        'airac_date': get_airac_date(args.offset),
        'timestamp': datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    }

    # Add notes
    if args.note:
        header['note'] = args.note.read()
    out.update({'release': header})

    # Get Git commit
    try:
        # Get head revision
        head = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"],
                              cwd=args.yaixm_dir, check=True,
                              stdout=subprocess.PIPE)

        # Check for pending commits
        diff = subprocess.run(["git", "diff-index", "--quiet", "HEAD", "--"],
                              cwd=args.yaixm_dir)
        if diff.returncode:
            commit = "changed"
        else:
            commit = head.stdout.decode("ascii").strip()

    except subprocess.CalledProcessError:
        commit = "unknown"

    header['commit'] = commit

    # Validate final output
    error = yaixm.validate(out)
    if error:
        print(error)
        sys.exit(-1)

    json.dump(out, args.yaixm_file, sort_keys=True, indent=args.indent)

    # Default Openair file
    hdr = HEADER
    hdr += f"AIRAC: {header['airac_date'][:10]}\n"
    hdr += "asselect.uk: Default airspace file\n"
    hdr += f"Commit: {commit}\n"
    hdr += "\n"
    if args.note:
        hdr += header['note']

    loas = [loa for loa in out['loa'] if loa['name'] == "CAMBRIDGE RAZ"]
    airspace = merge_loa(out['airspace'], loas)

    services = {}
    for service in out['service']:
        for control in service['controls']:
            services[control] = service['frequency']
    airspace = merge_service(airspace, services)

    type_func = make_openair_type(atz="CTR", ils="G", glider="W", noatz="G",
                                  ul="G", comp=False)

    exclude = [{'name': a['name'], 'type': "D_OTHER"} for a in out['airspace']
            if "TRA" in a.get('rules', []) or "NOSSR" in a.get('rules', [])]
    filter_func = make_filter(microlight=False, hgl=False, exclude=exclude)

    convert = Openair(type_func=type_func, filter_func=filter_func, header=hdr)
    oa = convert.convert(airspace)

    # Don't accept anything other than ASCII
    output_oa = oa.encode("ascii").decode("ascii")

    # Convert to DOS format
    dos_oa = output_oa.replace("\n", "\r\n") + "\r\n"

    args.openair_file.write(dos_oa)

def calc_ils(args):
    lon = yaixm.parse_deg(args.lon)
    lat = yaixm.parse_deg(args.lat)
    centre = LatLon(lat, lon)

    bearing = args.bearing + 180
    radius = args.radius * 1852

    distances = [radius, 8 * 1852, 8 * 1852, radius]
    bearings = [bearing -3, bearing -3, bearing + 3, bearing + 3]

    for d, b in zip(distances, bearings):
        p = centre.destination(d, b)
        print("- %s" % p.toStr(form="sec", prec=0, sep=" "))

def calc_point(args):
    lon = yaixm.parse_deg(args.lon)
    lat = yaixm.parse_deg(args.lat)
    origin = LatLon(lat, lon)

    dist = args.distance * 1852

    p = origin.destination(dist, args.bearing)
    print(p.toStr(form="sec", prec=0, sep=" "))

def calc_stub(args):
    lon = yaixm.parse_deg(args.lon)
    lat = yaixm.parse_deg(args.lat)
    centre = LatLon(lat, lon)

    length = args.length * 1852
    width = args.width * 1852
    radius = args.radius * 1852

    # Inner stub
    theta = math.asin(width / (2 * radius))

    bearing = args.bearing + 180 - math.degrees(theta)
    p1 = centre.destination(radius, bearing)

    bearing = args.bearing + 180 + math.degrees(theta)
    p2 = centre.destination(radius, bearing)

    print("Inner:")
    print(p1.toStr(form="sec", prec=0, sep=" "))
    print(p2.toStr(form="sec", prec=0, sep=" "))

    # Outer stub
    dist = math.sqrt((radius + length) ** 2 + (width / 2) **2)
    theta = math.atan(width / (2 * (radius + length)))

    bearing = args.bearing + 180 + math.degrees(theta)
    p1 = centre.destination(dist, bearing)

    bearing = args.bearing + 180 - math.degrees(theta)
    p2 = centre.destination(dist, bearing)

    print("\nOuter:")
    print(p1.toStr(form="sec", prec=0, sep=" "))
    print(p2.toStr(form="sec", prec=0, sep=" "))

# Check services exist in airspace file
def check_service(args):
    service = yaml.safe_load(args.service_file)
    airspace = yaml.safe_load(args.airspace_file)

    airspace = airspace['airspace']
    service = service['service']

    ids = [feature['id'] for feature in airspace if feature.get('id')]
    for s in service:
        for c in s['controls']:
            if c not in ids:
                print("Missing:", c)
