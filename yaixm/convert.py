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

from .helpers import parse_latlon, level, minmax_lat, dms

OBSTACLE_TYPES = {
   'BLDG': "BUILDING",
   'BRDG': "BRIDGE",
   'CHIM': "CHIMNEY",
   'COOL': "COOLING TOWER",
   'CRN': "CRANE",
   'FLR': "GAS FLARE",
   'MET': "MET MAST",
   'MINE': "MINE",
   'MISC': "OBSTACLE",
   'MONT': "MONUMENT",
   'OBST': "OBSTACLE",
   'OIL': "OIL REFINERY",
   'PLT': "BUILDING",
   'POW': "CHURCH",
   'PYL': "PYLON",
   'RTM': "RADIO MAST",
   'TURB-ON': "WIND TURBINE",
   'WASTE': "WASTE PIPE"
}

# Format distance as nm or km
def format_distance(distance):
    dist, unit = distance.split()
    if unit == "km":
        dist = "%.3f" % (float(dist) / 1.852)
    return dist

# Filter factory
def make_filter(noatz=True, microlight=True, hgl=True,
                gliding_site=True, north=59, south=49, max_level=None,
                exclude=None):
    def airfilter(volume, feature):
        as_name = feature['name']
        as_type = feature['type']
        as_localtype = feature.get('localtype')
        rules = feature.get('rules', []) + volume.get('rules', [])

        # Exclude if all properties match
        if exclude:
            for e in exclude:
                if all([e[k] == feature.get(k) for k in e]):
                    return False

        # Non-ATZ airfields
        if not noatz and as_localtype == "NOATZ":
            return False

        # Microlight strips
        if not microlight and as_localtype == "UL":
            return False

        # HIRTA, GVS and LASER
        if not hgl and as_localtype in ["HIRTA", "GVS", "LASER"]:
            return False

        # Gliding sites
        if not gliding_site and as_type == "OTHER" and as_localtype == "GLIDER" and "LOA" not in rules:
            return False

        # Max level
        if max_level and level(volume['lower']) >= max_level:
            return False

        # Min/max latitude
        min_lat, max_lat = minmax_lat(volume)
        if (min_lat > north) or (max_lat < south):
            return False

        return True

    return airfilter

# Default filter includes everything
default_filter = make_filter()

# Mame function
def name_func(volume, feature, add_seqno=False):
    if 'name' in volume:
        name = volume['name']
    else:
        name = feature['name']
        rules = feature.get('rules', []) + volume.get('rules', [])

        if 'localtype' in feature:
            localtype = feature['localtype']
            if localtype in ["NOATZ", "UL"]:
                name += " A/F"
            elif localtype in ["MATZ", "DZ", "GVS", "HIRTA", "ILS", "LASER"]:
                name += " " + localtype

        elif feature['type'] in ["ATZ"]:
            name += " " + feature['type']

        elif "RAZ" in rules:
            name += " " + "RAZ"

        if add_seqno:
            if len(feature.get('geometry', [])) > 1:
                seqno = volume.get('seqno')
                if not seqno:
                    seqno = chr(ord('A') + feature['geometry'].index(volume))

                name += "-{}".format(seqno)

        qualifiers = [q for q in ["SI", "NOTAM"] if q in rules]
        if qualifiers:
            name += " ({})".format("/".join(qualifiers))

    freq = volume.get('frequency') or feature.get('frequency')
    if freq:
        name += " {:.3f}".format(freq)

    return name

def seq_name(volume, feature):
    return name_func(volume, feature, True)

def noseq_name(volume, feature):
    return name_func(volume, feature, False)

# Openair type function. Possible types are:
#    A - G (class)
#    P (prohibited)
#    Q (danger)
#    R (restricted)
#    CTR (control area)
#    RMZ (radio mandatory zone)
#    TMZ (transponder mandatory zone)
#    W (wave)
#    MATZ (military ATZ)
#    OTHER
def make_openair_type(atz="CTR", ils="G", glider="G", noatz="G", ul="G", comp=False):
    def openair_type(volume, feature):
        as_type = feature['type']
        localtype = feature.get('localtype')
        rules = feature.get('rules', []) + volume.get('rules', [])

        if "NOTAM" in rules:
            out_type = "G"
        elif as_type == "ATZ":
            out_type = atz
        elif as_type == "D":
            if comp and "SI" in rules:
                out_type = "P"
            else:
                out_type = "Q"
        elif as_type == "D_OTHER":
            if localtype == "GLIDER":
                # Wave box
                out_type = "W"
            elif comp and localtype == "DZ" and "INTENSE" in rules:
                # Intense DZ's for competition airspace
                out_type = "P"
            else:
                # Danger area (Drop zone, HIRTA, etc.)
                out_type = "Q"
        elif as_type == "OTHER":
            if localtype == "GLIDER":
                if 'LOA' in rules:
                    out_type = "W"
                else:
                    # Gliding sites - use configuraable type
                    out_type = glider
            elif localtype == "ILS":
                out_type = ils
            elif localtype == "MATZ":
                out_type = "MATZ"
            elif localtype == "NOATZ":
                out_type = noatz
            elif localtype == "RAT":
                out_type = "P"
            elif localtype == "TMZ":
                out_type = "TMZ"
            elif localtype == "UL":
                out_type = ul
            elif localtype == "RMZ":
                out_type = "RMZ"
            else:
                out_type = "G"
        elif as_type == "P":
            out_type = "P"
        elif as_type == "R":
            out_type = "R"
        elif "TMZ" in rules:
            out_type = "TMZ"
        elif "RMZ" in rules:
            out_type = "RMZ"
        else:
            # Fallback is airspace class, or OTHER if no class
            out_type = volume.get('class') or feature.get('class') or "G"

        return out_type

    return openair_type

default_openair_type = make_openair_type()

# TNP class function
def make_tnp_class(atz=None, ils=None, glider="G", noatz="G", ul="G"):
    def tnp_class(volume, feature):
        as_type = feature['type']
        localtype = feature.get('localtype')
        rules = feature.get('rules', []) + volume.get('rules', [])

        if "NOTAM" in rules:
            return "G"
        elif as_type == "ATZ":
            return atz
        elif as_type == "OTHER":
            if localtype == "GLIDER":
                # Gliding site
                return glider
            elif localtype == "ILS":
                return ils
            elif localtype == "NOATZ":
                return noatz
            elif localtype == "UL":
                return ul
            else:
                # Default is no class
                return None
        else:
            return volume.get('class') or feature.get('class') or None

    return tnp_class

default_tnp_class = make_tnp_class()

# TNP type function. Possible types are:
#    AWY
#    CTA/CTR
#    DANGER
#    GSEC
#    MATZ
#    OTHER
#    PROHIBITED
#    RESTRICTED
#    RMZ
#    TMZ
def make_tnp_type(ils="OTHER", glider="OTHER"):
    def tnp_type(volume, feature):
        as_type = feature['type']
        localtype = feature.get('localtype')
        rules = feature.get('rules', []) + volume.get('rules', [])

        if "RMZ" in rules:
            out_type = "RMZ"
        elif "TMZ" in rules:
            out_type = "TMZ"
        elif as_type == "AWY":
            out_type = "AIRWAYS"
        elif as_type in ["ATZ", "CTA", "CTR", "TMA"]:
            out_type = "CTA/CTR"
        elif as_type == "D":
            out_type = "DANGER"
        elif as_type == "D_OTHER":
            if localtype == "GLIDER":
                out_type = "GSEC"
            else:
                out_type = "DANGER"
        elif as_type == "OTHER":
            if localtype == "GLIDER":
                out_type = glider
            elif localtype == "ILS":
                out_type = ils
            elif localtype == "MATZ":
                out_type = "MATZ"
            elif localtype == "RAT":
                out_type = "PROHIBITED"
            elif localtype == "RMZ":
                out_type = "RMZ"
            elif localtype == "TMZ":
                out_type = "TMZ"
            else:
                out_type = "OTHER"
        elif as_type == "P":
            out_type = "PROHIBITED"
        elif as_type == "R":
            out_type = "RESTRICTED"
        else:
            out_type = "OTHER"

        return out_type

    return tnp_type

default_tnp_type = make_tnp_type()

# Base class for TNP and OpenAir converters
class Converter():
    def format_latlon(self, latlon):
        lat, lon = parse_latlon(latlon)
        return self.__class__.latlon_fmt.format(dms(lat), dms(lon))

    def do_line(self, line):
        output = []
        for point in line:
            output.extend(self.do_point(point))

        return output

    def do_boundary(self, boundary):
        output = []
        for segment in boundary:
            segtype = list(segment.keys())[0]
            if segtype == 'circle':
                output.extend(self.do_circle(segment['circle']))
            elif segtype == 'line':
                output.extend(self.do_line(segment['line']))
                point = segment['line'][-1]
            elif segtype == 'arc':
                output.extend(self.do_arc(segment['arc'], point))
                point = segment['arc']['to']

        # Close the polygon
        if 'line' in boundary[0]:
            if 'line' in boundary[-1]:
                output.extend(self.do_point(boundary[0]['line'][0]))
            elif 'arc' in boundary[-1]:
              if boundary[0]['line'][0] != boundary[-1]['arc']['to']:
                  output.extend(self.do_point(boundary[0]['line'][0]))

        return output

    def start(self):
        hdr = []
        if self.header:
            hdr = ["{} {}".format(self.comment_char, line).strip()
                   for line in self.header.splitlines()]
        return hdr

    def end(self):
        return []

    def convert(self, airspace, obstacles=None):
        output = self.start()
        for feature in airspace:
            for volume in feature['geometry']:
                if self.filter_func(volume, feature):
                    x = self.do_volume(volume, feature)
                    output.extend(x)

        if obstacles:
            for obstacle in obstacles:
                # Create dummy feature/volume
                name = obstacle.get('name') or \
                       OBSTACLE_TYPES.get(obstacle['type'], "OBSTACLE")
                feature = {
                    'name': name,
                    'type': "OTHER"
                }
                volume = {
                    'upper': obstacle['elevation'],
                    'lower': "SFC",
                    'boundary': [{'circle': {'centre': obstacle['position'],
                                             'radius': "0.5 nm"}}]
                }

                if self.filter_func(volume, feature):
                    x = self.do_volume(volume, feature)
                    output.extend(x)

        output.extend(self.end())

        return "\n".join(output)

# Openair converter
class Openair(Converter):
    latlon_fmt =  "{0[d]:02d}:{0[m]:02d}:{0[s]:02d} {0[ns]} "\
                  "{1[d]:03d}:{1[m]:02d}:{1[s]:02d} {1[ew]}"

    def __init__(self, filter_func=default_filter, name_func=noseq_name,
                 type_func=default_openair_type, header=None):
        self.filter_func = filter_func
        self.name_func = name_func
        self.type_func = type_func
        self.header = header
        self.comment_char ="*"

    def do_name(self, name):
        return ["AN %s" % name]

    def do_frequency(self, volume, feature):
        freq = volume.get('frequency') or feature.get('frequency')
        return [f"AF {freq:.3f}"] if freq else []

    def do_type(self, as_type):
        return ["AC %s" % as_type]

    # Upper and lower levels
    def do_levels(self, volume):
        def level_str(level):
          if level == "SFC":
              return "SFC"
          elif level.endswith('ft'):
              return level[:-3] + "ALT"
          else:
              return level

        return ["AL %s" % level_str(volume['lower']),
                "AH %s" % level_str(volume['upper'])]

    # Centre of arc or circle
    def centre(self, latlon):
        return "V X=%s" % self.format_latlon(latlon)

    # Airspace circle boundary
    def do_circle(self, circle):
        radius = format_distance(circle['radius'])
        return [self.centre(circle['centre']), "DC %s" % radius]

    # Airspace boundary point
    def do_point(self, point):
        return ["DP %s" % self.format_latlon(point)]

    # Airspace arc direction
    def dir(self, dir):
        if dir == "cw":
            return "V D=+"
        else:
            return "V D=-"

    # Airspace arc from/to points
    def fromto(self, from_point, to_point):
        return "DB %s, %s" % (self.format_latlon(from_point),
                              self.format_latlon(to_point))

    # Airspace arc
    def do_arc(self, arc, from_point):
        return [self.dir(arc['dir']),
                self.centre(arc['centre']),
                self.fromto(from_point, arc['to'])]

    def do_volume(self, volume, feature):
        return (["*"] +
                self.do_type(self.type_func(volume, feature)) +
                self.do_name(self.name_func(volume, feature)) +
                self.do_frequency(volume, feature) +
                self.do_levels(volume) +
                self.do_boundary(volume['boundary']))

# TNP converter
# IMPORTANT - this implemention starts each airspace block with TITLE,
# followed by CLASS/TYPE. This may not compatible with some programs.
class Tnp(Converter):
    latlon_fmt = "{0[ns]}{0[d]:02d}{0[m]:02d}{0[s]:02d} "\
                 "{1[ew]}{1[d]:03d}{1[m]:02d}{1[s]:02d}"

    def __init__(self, filter_func=default_filter, name_func=noseq_name,
                 class_func=default_tnp_class, type_func=default_tnp_type,
                 header=None):
        self.filter_func = filter_func
        self.name_func = name_func
        self.class_func = class_func
        self.type_func = type_func
        self.header = header
        self.comment_char = "#"

    def end(self):
        return ['#', 'END']

    def do_name(self, name):
        return ["TITLE=%s" % name]

    def do_class(self, as_class):
        return ["CLASS=%s" % (as_class or "")]

    def do_type(self, as_type):
        return ["TYPE=%s" % as_type]

    def do_levels(self, volume):
        def level_str(level):
          if level == "SFC":
              return "SFC"
          elif level.endswith('ft'):
              return level[:-3] + "ALT"
          else:
              return level

        return ["BASE=%s" % level_str(volume['lower']),
                "TOPS=%s" % level_str(volume['upper'])]

    def do_point(self, point):
        return ["POINT=%s" % self.format_latlon(point)]

    def do_circle(self, circle):
        radius = format_distance(circle['radius'])
        centre = self.format_latlon(circle['centre'])
        return ["CIRCLE RADIUS=%s CENTRE=%s" % (radius, centre)]

    def do_arc(self, arc, from_point):
        dir = "CLOCKWISE" if arc['dir'] == 'cw' else "ANTI-CLOCKWISE"
        radius = format_distance(arc['radius'])
        centre = self.format_latlon(arc['centre'])
        to = self.format_latlon(arc['to'])
        return ["%s RADIUS=%s CENTRE=%s TO=%s" % (dir, radius, centre, to)]

    def do_volume(self, volume, feature):
        tnp = ["#"] +\
              self.do_name(self.name_func(volume,feature)) +\
              self.do_type(self.type_func(volume, feature)) +\
              self.do_class(self.class_func(volume, feature)) +\
              self.do_levels(volume) +\
              self.do_boundary(volume['boundary'])

        # If class is defined then order is type/class, otherwise class/type.
        # So XCSoar type is airspace class if defined or airspace type if not.
        if tnp[3] == "CLASS=":
            tnp[2], tnp[3] = tnp[3], tnp[2]

        return tnp
