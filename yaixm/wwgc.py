import os.path

from .convert import Openair, seq_name
from .helpers import level, load, merge_loa

LOA_NAMES = ["DAVENTRY BOX", "NUCLEAR EXEMPTIONS"]
RAT_NAMES = []
NOTAM_OVERRIDE = "OLD WARDEN"
DISABLED_AIRSPACE = ["R219 SANDRINGHAM HOUSE"]

HEADER = """
Version: 1
6/7/22

WWGC 2022

Airspace type "P" - Penalty areas.
Airspace type "R" - ATZs, see local rules.
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

def type_func(volume, feature):
    if feature['type'] == "ATZ":
        return "R"
    else:
        return "P"

# Generate WWGC airspace
def wwgc(args):
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
