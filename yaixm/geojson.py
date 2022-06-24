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

from pygeodesy.ellipsoidalVincenty import LatLon

from .helpers import parse_latlon, level

def do_line(line):
    return [parse_latlon(p)[::-1] for p in line]

def do_circle(circle, resolution):
    centre = LatLon(*parse_latlon(circle['centre']))
    delta = 90 / resolution

    # Get radius, in metres
    radius_str = circle['radius']
    radius = float(radius_str.split()[0]) * 1852

    # Calculate points on circumference
    points = []
    for i in range(resolution * 4):
        bearing = i * delta
        dest = centre.destination(radius, bearing)
        points.append((dest.lon, dest.lat))

    return points

def do_arc(arc, from_lonlat, resolution):
    centre = LatLon(*parse_latlon(arc['centre']))
    from_point = LatLon(from_lonlat[1], from_lonlat[0])
    to_point = LatLon(*parse_latlon(arc['to']))

    # Get radius, in metres
    radius = centre.distanceTo(from_point)

    # Get from and to bearings
    bearing_from = centre.bearingTo(from_point)
    bearing_to = centre.bearingTo(to_point)

    # Calculate arc length, in degrees
    arc_len = (bearing_to - bearing_from) % 360
    if arc['dir'] == "ccw":
        arc_len = 360 - arc_len

    # Piecewise approximation of arc
    points = []
    num_incs = round(arc_len / (90 / resolution))
    if num_incs > 0:
        delta = arc_len / num_incs
        if arc['dir'] == "ccw":
            delta = -delta

        for i in range(1, num_incs):
            bearing = bearing_from + i * delta
            dest = centre.destination(radius, bearing)
            points.append((dest.lon, dest.lat))

    # Add to point
    points.append((to_point.lon, to_point.lat))

    return points

def geojson(airspace, resolution=15):
    geo_features = []
    for feature in airspace:
        for volume in feature['geometry']:
            # Create new GeoJSON feature
            geo_feature = {'type': "Feature"}

            # Add properties
            name =  volume.get('name') or feature.get('name')
            if 'seqno' in volume:
                name = "{} {}".format(name, volume['seqno'])
            properties = {
                'name': name,
                'lower': volume['lower'],
                'upper': volume['upper'],
                'type' : feature['type'],
                'normlower': level(volume['lower'])
            }

            cls = volume.get('class') or feature.get('class')
            if cls:
                properties['class'] = cls

            if feature.get('localtype'):
                properties['localtype'] = feature.get('localtype')

            rules = feature.get('rules', [])[:]
            rules.extend(volume.get('rules', []))
            if rules:
                properties['rules'] = rules

            geo_feature['properties'] = properties

            # Add polygon geometry
            points = []
            for segment in volume['boundary']:
                if 'line' in segment:
                    points.extend(do_line(segment['line']))
                elif 'arc' in segment:
                    points.extend(do_arc(segment['arc'], points[-1],
                                         resolution))
                elif 'circle' in segment:
                    points = do_circle(segment['circle'], resolution)

            # Close the polygon
            if points[0] != points[-1]:
                points.append(points[0])

            # Add feature to feature list
            geo_feature['geometry'] = {
                'type': "Polygon",
                'coordinates': [points]
            }
            geo_features.append(geo_feature)

    collection = {
        'type': "FeatureCollection",
        'name': "UKAIR",
        'features': geo_features
    }

    return collection
