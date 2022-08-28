## Airspace data for the United Kingdom

Airspace data in YAIXM format.

The data is split into five files:

1. airspace.yaml - Airspace data from the UK Aeronautical Information Package

2. loa.yaml - BGA Letters of Agreement (see https://members.gliding.co.uk/library/loas)

3. obstacle.yaml - Obstacle data from the data file listed in section ENR 5.4
   of the UK AIP.

4. rat.yaml - RA(T) data from mauve AICs

5. service.yaml - Radio frequencies

## YAIXM

YAIXM is a simplified version of the FAA/EUROCONTOL Aeronautical
Information Exchange Model (AIXM) using YAML.

AIXM was chosen as the underlying model because it provides a ready made
mapping of the AIP to computer readable data. The AIP itself is (or,
possibly, will be) built on AIXM data, though unfortunately this data
isn't publicly available.

YAML is a data serialisation format specifically designed to be human
readable and writable. This is important - YAIXM data is entered manually
from the AIP.

YAIXM data can be parsed directly (YAML libraries are available for all
common computer languages) or converted to JSON before parsing.

### Schema

YAML doesn't have a schema language. However YAIXM data can
be mapped directly to/from JSON, so [JSON Schema](http://json-schema.org/)
can be used instead. The JSON schema (written in YAML!) can be found at
yaixm/data/schema.yaml

### Utilities

Use the run.py script for various utilities, `./run.py -h` to get a list

To validate a YAIXM file against the schema:

    ./run.py check airspace.yaml

To generate a ASSelect airspace files

    ./run.py release --note airspace/release.txt airspace yaixm.json openair.txt

### Contributing

I'm Alan Sparrow

YAIXM is on [GitHub](https://github.com/ahsparrow/airspace).

Please get in touch, via GitHub or otherwise. If you've got something
to contribute it would be very welcome.
