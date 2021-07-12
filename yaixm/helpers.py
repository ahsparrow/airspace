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

from copy import deepcopy
import json as _json
import logging
import math
import re
from string import ascii_uppercase

import jsonschema
import pkg_resources
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Load timestamps as strings
def timestamp_constructor(loader, node):
    return loader.construct_scalar(node)

Loader.add_constructor("tag:yaml.org,2002:timestamp", timestamp_constructor)

# Property order for pretty printing (follows order in AIP)
PPRINT_PROP_LIST = [
    "name", "type", "localtype",

    "release", "airspace", "loa", "obstacle", "rat",

    "areas",

    "add", "replace",

    "id", "seqno", "upper", "lower", "class", "rules", "boundary",

    "controltype", "geometry",

    "circle", "arc", "line",
    "dir", "radius", "centre", "to",

    "commit", "airac_date", "timestamp", "schema_version",

    "position", "elevation",

    "notes",
]

# Latitude/longitude regex
# Pattern is: [D]DDMMSS[.s[s[s]]]H
DMS_PATTERN = "(?P<d>[0-9]{2}|[01][0-9]{2})(?P<m>[0-5][0-9])(?P<s>[0-5][0-9](\.[0-9]{1,3})?)(?P<h>[NESW])"
DMS_RE = re.compile(DMS_PATTERN)

# Conversion factor
NM_TO_DEGREES = 1 / 60

# Load data from either YAML or JSON
def load(stream, json=False):
    if json:
        if hasattr(stream, 'read'):
            data = _json.load(stream)
        else:
            data = _json.loads(stream)
    else:
        data = yaml.load(stream, Loader=Loader)

    return data

# Check airspace against schema
def validate(yaixm):
    schema = load(pkg_resources.resource_string(__name__, "data/schema.yaml"))

    try:
        jsonschema.validate(yaixm, schema,
                            format_checker=jsonschema.FormatChecker())
    except jsonschema.exceptions.ValidationError as e:
        return e

    return None

# Representer to list properties in fixed order
def ordered_map_representer(dumper, data):
    return dumper.represent_mapping(
            'tag:yaml.org,2002:map',
            sorted(data.items(), key=lambda t: PPRINT_PROP_LIST.index(t[0])))

# Get volume and associated feature for given volume ID
def find_volume(airspace, vid):
    for feature in airspace:
        for volume in feature['geometry']:
            if volume.get('id') == vid:
                return volume, feature

    return None, None

# Merge LoAs into a copy of airspace and return merged copy
def merge_loa(airspace, loas):
    merge_airspace = deepcopy(airspace)
    merge_loas = deepcopy(loas)

    replace_vols = []

    # Add new features
    for loa in merge_loas:
        for area in loa['areas']:
            # Add LOA rule to new features
            for feature in area['add']:
                rules = feature.get('rules', [])
                rules.append("LOA")
                feature['rules'] = rules

            # Add new LoA airspace features
            merge_airspace.extend(area['add'])

            # Store replacement volumes
            replace_vols.extend(area.get('replace', []))

    # Replacement volumes
    for replace in replace_vols:
        if len(replace['geometry']) == 0:
            continue

        # Find volume to be replaced
        volume, feature = find_volume(merge_airspace, replace['id'])
        if feature is None:
            continue

        # Update seqno, e.g. 12 -> 12A, 12B, etc
        seqno = volume.get('seqno')
        if seqno:
            if len(replace['geometry']) > 1:
                for n, g in enumerate(replace['geometry']):
                    g['seqno'] = "%s%s" % (str(seqno), ascii_uppercase[n])
            else:
                replace['geometry'][0]['seqno'] = seqno

        # Delete old volume
        feature['geometry'].remove(volume)

        # Append new volumes (maybe null array)
        feature['geometry'].extend(replace['geometry'])

        # Remove feature if no geometry remaining
        if not feature['geometry']:
            merge_airspace.remove(feature)

    return merge_airspace

# Merge radio frequencies into airsace
def merge_service(airspace, service):
    merge_airspace = deepcopy(airspace)

    for feature in merge_airspace:
        freq = service.get(feature.get('id'))
        if freq:
            feature['frequency'] = freq

        for volume in feature['geometry']:
            freq = service.get(volume.get('id'))
            if freq:
                volume['frequency'] = freq

    return merge_airspace

# Convert latitude or longitude string to floating point degrees
def parse_deg(deg_str):
    m = DMS_RE.match(deg_str)
    if m is None:
        return None

    deg = int(m.group('d')) + int(m.group('m')) / 60 + float(m.group('s')) / 3600
    if m.group('h') in "SW":
        deg = -deg
    return deg

# Convert latlon string to pair of floats
def parse_latlon(latlon_str):
    lat, lon = [parse_deg(d) for d in latlon_str.split()]
    return lat, lon

# Get (approximate) minimum and maximum latitude for volume
def minmax_lat(volume):
    lat_arr = []
    for bdry in volume['boundary']:
        if 'circle' in bdry:
            radius = float(bdry['circle']['radius'].split()[0])
            clat, clon = parse_latlon(bdry['circle']['centre'])
            lat_arr.append(clat + radius * NM_TO_DEGREES)
            lat_arr.append(clat - radius * NM_TO_DEGREES)
        elif 'arc' in bdry:
            radius = float(bdry['arc']['radius'].split()[0])
            clat, clon = parse_latlon(bdry['arc']['centre'])
            lat_arr.append(clat + radius * NM_TO_DEGREES)
            lat_arr.append(clat - radius * NM_TO_DEGREES)
        elif 'line' in bdry:
            lat_arr.extend([parse_latlon(b)[0] for b in bdry['line']])

    return min(lat_arr), max(lat_arr)

# Return "normalised" level from SFC, altitude or flight level
def level(value):
    if value.startswith("FL"):
        return int(value[2:]) * 100
    elif value.endswith("ft"):
        return int(value.split()[0])
    else:
        return 0

# Return DMS values for floating point degrees
def dms(deg):
    if deg < 0:
        ns = "S"
        ew = "W"
        deg = -deg
    else:
        ns = "N"
        ew = "E"

    secs = round(deg * 3600)
    mins, secs = divmod(secs, 60)
    degs, mins = divmod(mins, 60)
    return {'d': degs, 'm': mins, 's': secs, 'ns': ns, 'ew': ew}
