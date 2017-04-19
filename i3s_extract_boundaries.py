#!/usr/bin/python3
"""
@brief:
Extraires les limites latérales à partir d'une successsion de profils en travers

@warnings:
Les profils doivent être décrit de manière similaire (toujours d'une rive à l'autre)
"""

from shapely.geometry import Point, LineString

import csv
from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i3s, BlueKenueWrite_i3s


FIELDNAMES = ['PROFIL', 'X', 'Y', 'Z']

parser = myargparse(description=__doc__, add_args=['force'])
parser.add_argument("inname", help="fichier i3s d'entrée")
parser.add_argument("outname", help="fichier i3s de sortie")
args = parser.parse_args()

with BlueKenueRead_i3s(args.inname) as in_i3s:
    in_i3s.read_header()
    first_lim = []
    last_lim = []

    for value, polyline in in_i3s.iter_on_polylines():
        first_lim.append(polyline.coords[0])
        last_lim.append(polyline.coords[-1])

    with BlueKenueWrite_i3s(args.outname, args.force) as out_i3s:
        out_i3s.auto_keywords()
        out_i3s.write_header()
        out_i3s.write_polyline(LineString(first_lim))
        out_i3s.write_polyline(LineString(last_lim))
