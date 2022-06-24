import os.path

from .convert import Openair, seq_name
from .helpers import level, load, merge_loa

LOA_NAMES = ["DAVENTRY BOX", "NUCLEAR EXEMPTIONS"]
RAT_NAMES = []

HEADER = """
Version [Preliminary]
WWGC 2022
"""

def filter_func(volume, feature):
    if level(volume['lower']) >= 10000:
        return False

    if "NOTAM" in feature.get('rules', []):
        return False

    return feature.get('localtype', "") not in [
            'GLIDER', 'GVS', 'HIRTA', 'ILS', 'LASER', 'NOATZ', 'UL']

def type_func(volume, feature):
    if feature.get('localtype') == "MATZ":
        return "G"
    elif feature['type'] == "ATZ":
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
