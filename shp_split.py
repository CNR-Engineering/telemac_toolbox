#!/usr/bin/python3
"""
@brief:
FIXME
"""

import fiona
from shapely.geometry import LineString, mapping
import shapely.affinity as aff
import sys

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueWrite_i2s
from geom.base import get_attr_value, resampling


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entrée shp")
parser.add_argument("outname", help="fichier de sortie shp")
args = parser.parse_args()


schema = {'geometry': 'LineString', 'properties': {'rien': 'float'}}
with fiona.open(args.inname, 'r') as filein:
    with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
        def write_linestring(linestring):
            elem = {}
            elem['geometry'] = mapping(linestring)
            elem['properties'] = {'rien': 0.0}
            layer.write(elem)

        for i, obj in enumerate(filein):
            print(i)
            obj_type = obj['geometry']['type']

            coord = obj['geometry']['coordinates']
            if obj_type == 'MultiLineString':
                for subcoord in coord:
                    write_linestring(LineString(subcoord))
            elif obj_type == 'LineString':
                write_linestring(LineString(coord))
