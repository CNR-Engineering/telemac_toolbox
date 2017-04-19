#!/usr/bin/python3
"""
@brief:
Order elements by a single field

TODO:
* mutliple fields
* exception KeyError sur les fields
"""

from collections import OrderedDict
import fiona
import sys

from common.arg_command_line import myargparse


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entree shp")
parser.add_argument("outname", help="fichier de sortie shp")
parser.add_argument("field", help="attribut pour trier")
parser.add_argument("--reverse", help="inverser l'ordre de tri (par défaut: croissant)", action='store_true')
args = parser.parse_args()


elems = []
with fiona.open(args.inname, 'r') as filein:
    # with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
    first_elem = filein[0]
    first_type = first_elem['geometry']['type']
    nb_elem = len(filein)

    print("Type des données : {}".format(first_type))
    print("Nombres d'élements : {}".format(nb_elem))

    for i, elem in enumerate(filein):
        print("{}: {}={}".format(i, args.field, elem['properties'][args.field]))
        if elem['geometry']['type'] != first_type:
            sys.exit("ERREUR: L'objet {} n'est pas de type {}".format(i, first_type))
        elems.append(elem)

sorted_elems = sorted(elems, key=lambda x: x['properties'][args.field], reverse=args.reverse)

geom_type = first_type
if len(first_elem['geometry']['coordinates'][0]):
    geom_type = '3D ' + geom_type

# Copy types of fields
properties = OrderedDict()
for key, value in first_elem['properties'].items():
    properties[key] = type(value).__name__

schema = {'geometry': geom_type, 'properties': properties}

print("Ecriture des éléments triés")
with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
    for i, elem in enumerate(sorted_elems):
        print("{}: {}={}".format(i, args.field, elem['properties'][args.field]))
        layer.write(elem)
