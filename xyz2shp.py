#!/usr/bin/python3
"""
@brief:
Convertir (et translater) un semis de points au format xyz en shp
"""
#FIXME: problème de BlueKenue aussi pour '3D Point'???

import fiona
import shapely.affinity as aff
from shapely.geometry import mapping

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_xyz


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entree xyz (format BlueKenue)")
parser.add_argument("outname", help="fichier de sortie shp")
parser.add_argument("--shift", type=float, nargs=2, help="decalage en X et Y (en metre)")
parser.add_argument("--append", nargs='+', help="liste des fichiers (du  même type que inname) à ajouter", default=[])
args = parser.parse_args()

innames = [args.inname] + args.append

schema = {'geometry': '3D Point', 'properties': {'Z': 'float'}}  #FIXME: schema selon si Z ou non
with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
    for inname in innames:
        with BlueKenueRead_xyz(inname) as in_xyz:
            in_xyz.read_header()
            print("En-tête lue avec succès")
            for i, point in enumerate(in_xyz.iter_on_points()):
                if args.shift is not None:
                    point = aff.translate(point, xoff=args.shift[0], yoff=args.shift[1])
                elem = {}
                elem['geometry'] = mapping(point)
                elem['properties'] = {'Z': point.z}
                layer.write(elem)
