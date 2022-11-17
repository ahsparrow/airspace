from lark import Lark, Transformer

grammer = '''
    ?start: feature_list
    feature_list: feature+

    feature: airtype airname freq? geometry_list
    geometry_list: geometry+
    geometry: lower upper boundary

    airtype: "AC" _WS_INLINE+ AIRTYPE _NEWLINE
    airname: "AN" _WS_INLINE+ NAME_STRING _NEWLINE
    lower: "AL" _WS_INLINE + (ALT | FL | SFC) _NEWLINE
    upper: "AH" _WS_INLINE+ (ALT | FL) _NEWLINE
    freq: "AF" _WS_INLINE+ FREQ _NEWLINE

    boundary: (line | circle | arc)+

    line: point+
    circle: centre radius
    arc: dir centre limits

    ?point: "DP" _WS_INLINE+ lat_lon _NEWLINE

    centre: "V" _WS_INLINE+ "X=" lat_lon _NEWLINE
    radius: "DC" _WS_INLINE+ RADIUS _NEWLINE

    dir: "V" _WS_INLINE+ "D=" DIRECTION _NEWLINE
    limits: "DB" _WS_INLINE+ lat_lon "," _WS_INLINE+ lat_lon _NEWLINE

    ?lat_lon: LAT_LON

    AIRTYPE: LETTER+

    NAME_STRING: LETTER (NAME_CHAR | " ")* NAME_CHAR 
    NAME_CHAR: (LETTER | DIGIT | "(" | ")" | "/" | "-" | ".")

    ALT: DIGIT+ "ALT"
    FL: "FL" DIGIT+
    SFC: "SFC"

    FREQ: DIGIT~3 "." DIGIT~3
    %ignore FREQ

    RADIUS: NUMBER
    DIRECTION: ("+" | "-")

    LAT_LON: LAT WS_INLINE+ LON
    LAT: DIGIT~2 ":" DIGIT~2 ":" DIGIT~2 WS_INLINE+ LAT_HEMI
    LON: DIGIT~3 ":" DIGIT~2 ":" DIGIT~2 WS_INLINE+ LON_HEMI
    LAT_HEMI: ("N" | "S")
    LON_HEMI: ("E" | "W")

    _NEWLINE: NEWLINE
    _WS_INLINE: WS_INLINE

    COMMENT: /\*[^\\n]*/ NEWLINE
    %ignore COMMENT

    %import common.DIGIT
    %import common.LETTER
    %import common.NEWLINE
    %import common.NUMBER
    %import common.WS_INLINE
'''

class OpenairTransformer(Transformer):
    def LAT_LON(self, latlon):
        t = latlon.replace(':', '').replace(' ', '')
        return t[:7] + " " + t[7:]

    def DIRECTION(self, dirn):
        return "cw" if dirn == '+' else 'ccw'

    def RADIUS(self, r):
        return r + " nm"

    def SFC(self, sfc):
        return sfc.value

    def FL(self, fl):
        return fl.value

    def ALT(self, alt):
        return alt[:-3] + " ft"

    def NAME_STRING(self, str):
        return str.value

    def AIRTYPE(self, str):
        return str.value

    def limits(self, data):
        return 'to', data[1]

    def dir(self, data):
        return 'dir', data[0]

    def radius(self, tree):
        return ('radius', tree[0])

    def centre(self, tree):
        return 'centre', tree[0]

    def arc(self, tree):
        return 'arc', dict(tree)

    def circle(self, tree):
        return 'circle', dict(tree)

    def line(self, tree):
        return 'line', tree

    def boundary(self, tree):
        return 'boundary', [dict([x]) for x in tree]

    def upper(self, data):
        return 'upper', data[0]

    def lower(self, data):
        return 'lower', data[0]

    def airname(self, data):
        return 'name', data[0]

    def airtype(self, data):
        return 'type', data[0]

    def freq(self, data):
        return "freq", data[0]

    geometry = dict
    def geometry_list(self, tree):
        return 'geometry', tree

    feature = dict
    feature_list = list

def parse(data):
    parser = Lark(grammer)
    tree = parser.parse(data)

    out = OpenairTransformer().transform(tree)
    return out
