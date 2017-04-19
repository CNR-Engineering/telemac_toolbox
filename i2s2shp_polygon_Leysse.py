#!/usr/bin/python3
"""
@brief:
Convertir (et translater) un ensemble de polylignes fermées i2s en shp

@features:
* "value" est stocké en valeur attributaire et le nom de l'attribut est alors à renseigner
* translation possible

@warnings:
Le fichier de sortie est remplacé s'il existe déjà

@info:
L'information attributaire de "value" est stockée en tant que flottant
"""
#FIXME:
#merge with i2s2shp and detect with first element if Polygon or LineString... (or do this in the class BlueKenue...?

import fiona
import shapely.affinity as aff
from shapely.geometry import mapping, Polygon

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entree i2s (format BlueKenue)")
parser.add_argument("outname", help="fichier de sortie shp")
parser.add_argument("--colname", help="column name", default='value')
parser.add_argument("--shift", type=float, nargs=2, help="decalage en X et Y (en metre)")
parser.add_argument("--append", nargs='+', help="liste des fichiers (du  même type que inname) à ajouter", default=[])
args = parser.parse_args()

innames = [args.inname] + args.append
first = True
for inname in innames:
    with BlueKenueRead_i2s(inname) as in_i2s:
        in_i2s.read_header()

        schema = {'geometry': 'Polygon', 'properties': {args.colname: 'float'}}
        mode = 'w' if first else 'a'
        count = 0
        with fiona.open(args.outname, mode, 'ESRI Shapefile', schema) as layer:
            for value, linestring in in_i2s.iter_on_polylines():
                if args.shift is not None:
                    linestring = aff.translate(linestring, xoff=args.shift[0], yoff=args.shift[1])
                nb_pt = len(linestring.coords)

                if nb_pt>3:
                    if linestring.is_ring:
                        linestring = Polygon(linestring.coords[:-1])
                   
                        elem = {}
                        elem['geometry'] = mapping(linestring)
                        elem['properties'] = {args.colname: value}
                        layer.write(elem)
                    else:
                        count += 1
                        print("Ligne non fermée {}".format(count))
                else:
                    print("Ignore {} coordonnées".format(nb_pt))
    first = False
