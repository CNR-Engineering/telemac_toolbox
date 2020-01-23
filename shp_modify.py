#!/usr/bin/python3
"""
@brief:
Order elements (by a single field) and/or shift X,Y geometry
"""
from collections import OrderedDict
import fiona
import shapely.affinity as aff
from shapely.geometry import mapping, shape
import sys

from common.arg_command_line import myargparse


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entree shp")
parser.add_argument("outname", help="fichier de sortie shp")
parser.add_argument("--attr_to_order", help="attribut pour trier")
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
parser.add_argument("--reverse", help="inverser l'ordre de tri (par défaut: croissant)", action='store_true')
args = parser.parse_args()


elems = []
with fiona.open(args.inname, 'r') as filein:
    first_elem = filein[0]
    first_type = first_elem['geometry']['type']
    nb_elem = len(filein)

    print("Type des données : {}".format(first_type))
    print("Nombres d'élements : {}".format(nb_elem))

    for i, elem in enumerate(filein):
        if args.attr_to_order:
            print("{}: {}={}".format(i, args.attr_to_order, elem['properties'][args.attr_to_order]))
        if elem['geometry']['type'] != first_type:
            sys.exit("ERREUR: L'objet {} n'est pas de type {}".format(i, first_type))
        elems.append(elem)

if args.attr_to_order:
    elems = sorted(elems, key=lambda x: x['properties'][args.attr_to_order], reverse=args.reverse)


geom_type = first_type
if len(first_elem['geometry']['coordinates'][0]):
    geom_type = '3D ' + geom_type

# Copy types of fields
properties = OrderedDict()
for key, value in first_elem['properties'].items():
    properties[key] = type(value).__name__

schema = {'geometry': geom_type, 'properties': properties}
print("Ecriture des éléments triés avec ce schéma:")
print(schema)
with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
    for i, elem in enumerate(elems):

        if args.shift is not None:
            obj = shape(elem['geometry'])
            obj = aff.translate(obj, xoff=args.shift[0], yoff=args.shift[1])
            elem['geometry'] = mapping(obj)

        if args.attr_to_order:
            print("{}: {}={}".format(i, args.attr_to_order, elem['properties'][args.attr_to_order]))
        layer.write(elem)
