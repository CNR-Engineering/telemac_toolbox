#!/usr/bin/python3
"""
@brief:
FIXME
"""

import fiona
from shapely.geometry import Point, mapping
import shapely.affinity as aff
import sys

from common.arg_command_line import myargparse

parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entree shp")
parser.add_argument("outname", help="fichier de sortie shp")
args = parser.parse_args()



schema = {'geometry': '3D Point', 'properties': {'Z': 'float'}}
with fiona.open(args.inname, 'r') as filein:
    with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
        for point in filein:
            if point['geometry']['type'] != 'Point':
                sys.exit("ERREUR: L'objet {} n'est pas un semis de point".format(type))
            lCoordXY_point = point['geometry']['coordinates']
            print(lCoordXY_point)
            fZ_table = point['properties']['Z']
            print(fZ_table)
            point_Z = Point([lCoordXY_point[0], lCoordXY_point[1], fZ_table]) 
            elem = {}
            elem['geometry'] = mapping(point_Z)
            elem['properties'] = {'Z': fZ_table}
            layer.write(elem)


                
