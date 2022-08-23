from copy import deepcopy
import os.path

from .convert import Openair, seq_name, noseq_name
from .helpers import level, load, merge_loa

LOA_NAMES = ["DAVENTRY BOX", "NUCLEAR EXEMPTIONS"]
RAT_NAMES = ["SYERSTON (24 AUG)",
             "WATTISHAM (25 AUG)",
             "SYWELL A (24 AUG)",
             "SYWELL B (24 AUG)"]
NOTAM_OVERRIDE = "OLD WARDEN"
DISABLED_AIRSPACE = ["R219 SANDRINGHAM HOUSE"]

HEADER = """
Version: 5
19/8/22

Add
    SYWELL A (24 AUG)
    SYWELL B (24 AUG)

Remove temporary restricted airspace:
    WELLINGBOROUGH (20 AUG)

WWGC 2022

Airspace type "P" - Penalty areas.
Airspace type "R" - ATZs, see local rules.
"""

ADVISORY_HEADER = """
Version: 1
13/7/22

WWGC 2022

NON-PENALTY (advisory) airspace
"""

def filter_func(volume, feature):
    if feature['name'] in DISABLED_AIRSPACE:
        return False

    if level(volume['lower']) >= 10000:
        return False

    if "NOTAM" in feature.get('rules', []):
        if feature['name'] not in NOTAM_OVERRIDE:
            return False

    return feature.get('localtype', "") not in [
            'GLIDER', 'GVS', 'HIRTA', 'ILS', 'LASER', 'NOATZ', 'UL', 'MATZ']

def advisory_filter_func(volume, feature):
    if feature['name'] in DISABLED_AIRSPACE:
        return False

    if level(volume['lower']) >= 10000:
        return False

    if "NOTAM" in feature.get('rules', []):
        if feature['name'] not in NOTAM_OVERRIDE:
            return False

    return feature['type'] == "OTHER" and feature['localtype'] in ["MATZ"]

def type_func(volume, feature):
    if feature['type'] == "ATZ":
        return "R"
    else:
        return "P"

# Generate WWGC airspace
def wwgc(args):
    if args.info:
        wwgc_advisory(args)
        return

    # Aggregate YAIXM files
    yaixm = {}
    for f in ["airspace", "loa", "rat", "service"]:
        yaixm.update(load(open(os.path.join(args.yaixm_dir, f + ".yaml"))))

    # Merge LoA
    loa = [loa for loa in yaixm['loa'] if loa['name'] in LOA_NAMES]
    airspace = merge_loa(yaixm['airspace'], loa)

    # RA(T)s
    rats = [rat for rat in yaixm['rat'] if rat['name'] in RAT_NAMES]
    airspace.extend(rats)

    # ATZ frequencies
    services = {}
    for service in yaixm['service']:
        for control in service['controls']:
            services[control] = service['frequency']

    for feature in airspace:
        if feature['type'] == "ATZ":
            feature['frequency'] = services[feature['id']]

    converter = Openair(filter_func=filter_func, name_func=seq_name,
                        type_func=type_func, header=HEADER)
    oa = converter.convert(airspace)

    # Don't accept anything other than ASCII
    output_oa = oa.encode("ascii").decode("ascii")

    args.openair_file.write(output_oa)
    args.openair_file.write("\n")

# Generate WWGC advisory airspace
def wwgc_advisory(args):
    # YAIXM files
    yaixm = {}
    for f in ["airspace", "service"]:
        yaixm.update(load(open(os.path.join(args.yaixm_dir, f + ".yaml"))))

    airspace = deepcopy(yaixm['airspace'])

    # ATZ frequencies
    services = {}
    for service in yaixm['service']:
        for control in service['controls']:
            services[control] = service['frequency']

    for feature in airspace:
        if feature['type'] == "OTHER" and feature['localtype'] == "GLIDER":
            freq = services.get(feature.get('id'))
            if freq:
                feature['frequency'] = freq

    converter = Openair(filter_func=advisory_filter_func, name_func=noseq_name,
                        type_func=lambda f, v: "G", header=ADVISORY_HEADER)
    oa = converter.convert(airspace)

    # Don't accept anything other than ASCII
    output_oa = oa.encode("ascii").decode("ascii")

    args.openair_file.write(output_oa)
    args.openair_file.write("\n")
