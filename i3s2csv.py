#!/usr/bin/python3
"""
@brief:
Convertir un fichier i3s en fichier csv

@info:
Colonnes exportés : ['x', 'y', 'z', 'id', 'id_pt', 'id_line', 'value']

@warnings:
La valeur doit être unique par polyligne sinon on perd l'information...
"""
#FIXME: myargparse + force

from shapely.geometry import Point

import csv
from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i3s
from math import sqrt

FIELDNAMES = ['x', 'y', 'z', 'id', 'id_pt', 'id_line', 'value', 'dist']

parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier i3s")
parser.add_argument("outname", help="fichier csv")
parser.add_argument("--sep", help="séparateur de colonnes", default=';')
args = parser.parse_args()

with BlueKenueRead_i3s(args.inname) as in_i3s:
    in_i3s.read_header()

    mode = 'w'
    with open(args.outname, mode, newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';')
        csvwriter.writerow(FIELDNAMES)

        id = 0
        for i, (value, polyline) in enumerate(in_i3s.iter_on_polylines()):
            dist = 0
            print("Traitement ligne {} de valeur {}".format(i, value))
            for j, point in enumerate(polyline.coords):
                (x, y, z) = point

                if j!= 0:  # Not first point
                    dist += sqrt((x - x_prev)**2 + (y - y_prev)**2)

                csvwriter.writerow(list(point) + [id, j, i, value, dist])

                id += 1
                x_prev = x
                y_prev = y
