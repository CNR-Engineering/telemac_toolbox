#!/usr/bin/python3
"""
@brief:
Convertir un fichier i2s en fichier csv

@info:
Colonnes exportés : ['x', 'y', 'id', 'id_pt', 'id_line', 'value']
"""
#FIXME: myargparse + force

from shapely.geometry import Point

import csv
from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s


FIELDNAMES = ['x', 'y', 'id', 'id_pt', 'id_line', 'value']

parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier i2s")
parser.add_argument("outname", help="fichier csv")
parser.add_argument("--sep", help="séparateur de colonnes", default=';')
args = parser.parse_args()

with BlueKenueRead_i2s(args.inname) as in_i2s:
    in_i2s.read_header()

    mode = 'w'
    with open(args.outname, mode, newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=args.sep)
        csvwriter.writerow(FIELDNAMES)

        id = 0
        for i, (value, polyline) in enumerate(in_i2s.iter_on_polylines()):
            print("Traitement ligne {} de valeur {}".format(i, value))
            for j, point in enumerate(polyline.coords):
                csvwriter.writerow(list(point) + [id, j, i, value])
                id += 1
