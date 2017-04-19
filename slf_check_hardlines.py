#!/usr/bin/python3
"""
@brief:
Vérifier que les points sont assez proches des noeuds du maillage (permet de vérifier les maillages issus de BlueKenue)

@features:
* les points de la ligne dure (hardline) sont parcourus et si aucun noeud du maillage se situe à proximité (distance seuil à définir), le noeud le plus proche est affiché (c'est vers ce noeud que se situe le problème, la ligne dure n'a pas été respectée)
* la distance seuil est paramétrable avec l'option `--dist`
"""

import sys
import math

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s
from slf import Serafin, common_data


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("resname", help="Serafin input filename")
parser.add_argument("i2s_name", help="i2s input filename")
parser.add_argument("--dist", type=float, help="distance minimale", default=0.01)
args = parser.parse_args()

common_data.verbose = args.verbose

with Serafin.Read(args.resname) as resin:
    resin.readHeader()
    resin.get_time()

    with BlueKenueRead_i2s(args.i2s_name) as in_i2s:
        in_i2s.read_header()
        for i, (value, linestring) in enumerate(in_i2s.iter_on_polylines()):
            for point in linestring.coords:
                node = resin.nearest_node(point[0], point[1])
                (x_node, y_node) = resin.get_coord(node)
                dist = math.sqrt((point[0] - x_node)**2 + (point[1] - y_node)**2)

                if dist > args.dist:
                    print("Polyligne {} (coord ({},{})) : noeud {} à {} m".format(i, point[0], point[1], node, dist))
