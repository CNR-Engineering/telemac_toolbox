#!/usr/bin/python3
"""
@brief:
Analyse un ensemble de polylignes et exporte un semis de points (sans Z) correspondant à des points consécutifs des lignes qui sont trop proches
"""

import fiona
from shapely.geometry import Point, mapping
import sys

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueWrite_i2s


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entrée shp")
parser.add_argument("outname", help="fichier de sortie shp")
parser.add_argument("distmin", type=float, help="distance minimale entre deux points consécutifs (en mètre)")
args = parser.parse_args()

schema = {'geometry': 'Point', 'properties': {'dist': 'float'}}
with fiona.open(args.inname, 'r') as filein:
    with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
        for i, obj in enumerate(filein):
            print(i)
            obj_type = obj['geometry']['type']
            coords = obj['geometry']['coordinates']

            prev_point = None
            for coord in coords:
                point = Point(coord)

                if prev_point is not None:
                    dist = point.distance(prev_point)
                    if dist < args.distmin:
                        elem = {}
                        elem['geometry'] = mapping(point)
                        elem['properties'] = {'dist': dist}
                        layer.write(elem)

                prev_point = point
