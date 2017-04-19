#!/usr/bin/python3
"""
Pour récuperer le plantage d'Arcgis... en test pour Leysse amont
"""

from shapely.geometry import Point

import fiona
from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i3s
import shapely.affinity as aff
from shapely.geometry import mapping


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier i3s")
parser.add_argument("outname", help="fichier shp (Polylignes Z)")
parser.add_argument("--shift", type=float, nargs=2, help="decalage en X et Y (en metre)")
args = parser.parse_args()

schema = {'geometry': '3D LineString', 'properties': {'value': 'float'}}

with BlueKenueRead_i3s(args.inname) as in_i3s:
    in_i3s.read_header()

    # with fiona.open(args.outname, 'w', 'ESRI Shapefile', schema) as layer:
    for i, (value, linestring) in enumerate(in_i3s.iter_on_polylines()):
        # if args.shift is not None:
        #     linestring = aff.translate(linestring, xoff=args.shift[0], yoff=args.shift[1])
        print(linestring)
            # elem = {}
            # elem['geometry'] = mapping(linestring)
            # elem['properties'] = {'value': value}
            # layer.write(elem)

