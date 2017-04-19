#!/usr/bin/python3
"""
@brief:
Convertir un fichier shp en un un fichier csv
X, Y, ...fields...
"""
#TODO: avec et sans Z?

import csv
import fiona
import sys
from shapely.geometry import Point, MultiPoint
import shapely.affinity as aff

from common.arg_command_line import myargparse


parser = myargparse(description=__doc__, add_args=['force'])
parser.add_argument("inname", help="fichier d'entrée shp (semis de points avec ou sans Z)")
parser.add_argument("outname", help="fichier de sortie csv (X, Y, Z, ...fields...)")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants", default=4)
parser.add_argument("--sep", help="séparateur de colonnes", default=';')
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètres)")
args = parser.parse_args()


with fiona.open(args.inname, 'r') as filein:
    with open(args.outname, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=args.sep)

        def write_single_point(coords, properties):
            """Write a single point (dict from fiona)"""
            global first

            geom_point = Point(coords)

            if args.shift is not None:
                geom_point = aff.translate(geom_point, xoff=args.shift[0], yoff=args.shift[1])
            if first:
                # Write header
                fields = ['X', 'Y']
                if geom_point.has_z:
                    fields.append('Z')
                fields = fields + [key for key, value in properties.items()]
                csvwriter.writerow(fields)
                first = False
            csvwriter.writerow([round(x, args.digits) for x in geom_point.coords[0]] + [value for key, value in properties.items()])

        first = True
        for point in filein:
            geom = point['geometry']
            properties = point['properties']

            if geom is None:
                sys.exit("Object is a None type")

            else:
                type = geom['type']
                coords = geom['coordinates']

                if type == 'Point':
                    write_single_point(coords, properties)

                elif type == 'MultiPoint':
                    for coord in coords:
                        write_single_point(coords, properties)

                else:
                    sys.exit("ERREUR: L'objet '{}' n'est un semis de point".format(type))

