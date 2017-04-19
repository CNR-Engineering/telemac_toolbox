#!/usr/bin/python3
"""
@brief:
Convertir (et translater) un ensemble de polylignes ouvertes i2s en shp

@features:
* "value" est stocké en valeur attributaire et le nom de l'attribut est alors à renseigner
* translation possible

@warnings:
Le fichier de sortie est remplacé s'il existe déjà

@info:
L'information attributaire de "value" est stockée en tant que flottant
"""
#FIXME:
# * add force option
# * ok si polyligne ferme???

import fiona
import shapely.affinity as aff
from shapely.geometry import mapping

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entree i2s (format BlueKenue)")
parser.add_argument("outname", help="fichier de sortie shp")
parser.add_argument("--colname", help="column name", default='value')
parser.add_argument("--shift", type=float, nargs=2, help="decalage en X et Y (en metre)")
args = parser.parse_args()

with BlueKenueRead_i2s(args.inname) as in_i2s:
    in_i2s.read_header()
    schema = {'geometry': 'LineString', 'properties': {args.colname: 'float'}}
    with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
        for value, linestring in in_i2s.iter_on_polylines():
            if args.shift is not None:
                linestring = aff.translate(linestring, xoff=args.shift[0], yoff=args.shift[1])

            elem = {}
            elem['geometry'] = mapping(linestring)
            elem['properties'] = {args.colname: value}
            layer.write(elem)
