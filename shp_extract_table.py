#!/usr/bin/python3
"""
@brief:
Extraire la table attributaire en tant que csv
"""
#TODO: ajouter les coordonnées si c'est un semis de points (et le nombre de points si c'est une polyligne???)

import csv
import fiona
import sys

from common.arg_command_line import myargparse


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entrée shp")
parser.add_argument("outname", help="fichier de sortie csv")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants", default=4)
parser.add_argument("--sep", help="séparateur de colonnes", default=';')
args = parser.parse_args()

with fiona.open(args.inname, 'r') as filein:
    with open(args.outname, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=args.sep)

        first = True
        for elem in filein:
            attrs = elem['properties']

            if first:
                fields = [key for key, value in attrs.items()]
                print("Colonnes = {}".format(fields))
                csvwriter.writerow(fields)

            values = [value for key, value in attrs.items()]
            # Round is floatting attributes
            if args.digits is not None:
                values = [round(x, args.digits) if isinstance(x, float) else x for x in values]
            csvwriter.writerow(values)

            first = False
