#!/usr/bin/python3
"""
@brief:
Recherche des micros Ã©lÃ©ments
"""

import sys

from common.arg_command_line import myargparse
import math
from slf import Serafin, common_data


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname", help="Serafin input filename")
parser.add_argument("min_area", type=float, help="taille minimum cible")
args = parser.parse_args()

common_data.verbose = args.verbose

with Serafin.Read(args.inname) as resin:
    resin.readHeader()
    resin.get_time()

    for i in range(resin.nelem):
        i_elem = i+1  # 1-indexed (like BlueKenue)
        nodes = resin.triangle_nodes(i_elem)

        pt1 = resin.get_coord(nodes[0])
        pt2 = resin.get_coord(nodes[1])
        pt3 = resin.get_coord(nodes[2])

        def dist(c1, c2):
            """c1 and c2 a tuple of 2D-coord"""
            return math.sqrt( (c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 )

        # Formule de Héron
        a = dist(pt1, pt2)
        b = dist(pt2, pt3)
        c = dist(pt3, pt1)

        p = (a + b + c)/2
        surface = math.sqrt(p*(p-a)*(p-b)*(p-c))

        if surface < args.min_area:
            print("Surface élément #{} (noeuds = {}) de {} m2".format(i_elem, nodes, surface))
