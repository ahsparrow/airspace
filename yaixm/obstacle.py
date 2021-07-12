import argparse
import csv
import math
import sys

from yaixm import parse_latlon, dms

def read_names(csv_file):
    reader = csv.reader(csv_file)

    names = {}
    for x in reader:
        if len(x) == 2:
            names[x[0].strip()] = x[1].strip()

    return names

def read_obstacles(csv_file):
    reader = csv.DictReader(csv_file)

    obstacles = []
    for obs in reader:
        id = [x for x in obs['Designation/Identification'].split()
              if x.startswith('UK')][0]

        typ = obs['Obstacle Type'].split()[0]

        if obs['Elevation'] == "Unknown":
            continue

        elevation = obs['Elevation'].split()[0] + " ft"

        lat, lon = parse_latlon(obs['Obstacle Position'])
        lat_str = "{0[d]:02d}{0[m]:02d}{0[s]:02d}{0[ns]}".format(dms(lat))
        lon_str = "{0[d]:03d}{0[m]:02d}{0[s]:02d}{0[ew]}".format(dms(lon))

        obstacles.append({'id': id,
                          'type': typ,
                          'elevation': elevation,
                          'position': lat_str + " " + lon_str})

    return obstacles

def make_obstacles(csv_file, titles_file):
    obstacles = read_obstacles(csv_file)
    names = read_names(titles_file)

    # Add named obstacles
    out = []
    for obstacle in obstacles:
        if obstacle['id'] in names:
            obstacle['name'] = names[obstacle['id']]
            out.append(obstacle)

    return out
