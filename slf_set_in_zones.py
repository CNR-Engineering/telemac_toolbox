#!/usr/bin/python3
"""
@brief:
Modifier les variables d'un résultat 2D dans les zones définies par des polylignes

@info:
Toutes les variables sont modifiées
Les polygones peuvent se chevaucher mais le dernier polylgone lu écrasera les valeurs précédentes

@prerequisites:
* La valeur des polygones est utilisée comme valeur de remplacement
"""

import numpy as np
import sys
import shapely.affinity as aff
import shapely.geometry as geo

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s
from slf import Serafin, common_data


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname", help="Serafin input filename")
parser.add_argument("outname", help="Serafin output filename")
parser.add_argument("i2s_name", help="BlueKenue 2D polyline file (i2s format)")
parser.add_argument("--var", nargs='+', help="liste des variables 2D")
args = parser.parse_args()
# class args:
#     pass
# args.inname = "../r2d.slf"
# args.outname = "arf.slf"
# args.i2s_name = 'toto.i2s'
# args.var = ['S', 'H']
# args.force = True
# args.verbose = True


common_data.verbose = args.verbose

class Mask:
    """
    Mask: definir une zone pour laquelle, les noeuds inclus dedans sont traités différement

    Attributs:
    * value = valeur
    TODO
    """

    def __init__(self, value, geom, nodes_included):
        self.value = value
        self.geom = geom
        self.nodes_included = nodes_included


with Serafin.Read(args.inname) as resin:
    resin.readHeader()

    if resin.type != '2D':
        sys.exit("The current script is working only with 2D meshes !")

    resin.get_time()

    # Define zones from polylines
    print("~> Lecture des polylignes et recherche des noeuds inclus dedans")
    masks = []
    with BlueKenueRead_i2s(args.i2s_name) as in_i2s:
        in_i2s.read_header()
        for i, (value, polyline) in enumerate(in_i2s.iter_on_polylines()):
            if not polyline.is_valid:
                sys.exit("ERROR: polyline {} is not valid (probably because it intersects itself) !".format(i))
            if not polyline.is_ring:
                sys.exit("ERROR: polyline {} is not closed".format(i))

            polygon = geo.Polygon(polyline)  # only Polygon has `contains` method

            # Construction du tableau de maskage (avec des booléens)
            nodes_included = np.zeros(resin.nnode2d, dtype=bool)
            for j in range(resin.nnode):  # iterate over all nodes
                node = j + 1
                (x, y) = resin.get_coord(node)
                pt = geo.Point(x,y)
                if polygon.contains(pt):
                    nodes_included[j] = True

            nb_nodes_included = int(np.sum(nodes_included))
            print("Polyligne {} (avec {} points et une valeur à {}) contient {} noeuds".format(i, len(polyline.coords), value, nb_nodes_included))

            mask = Mask(value, polyline, nodes_included)
            masks.append(mask)

    if args.var is not None:
        var2D_list = args.var
    else:
        var2D_list = resin.varID

    var2D_pos = [resin.varID.index(x) for x in var2D_list]
    print(var2D_pos)

    with Serafin.Write(args.outname, args.force) as resout:
        resout.copy_header(resin)
        resout.write_header()

        for time in resin.time:
            var = resin.read_vars_in_frame(time, resout.varID)

            # Application aux zones
            for pos in var2D_pos:
                for mask in masks:
                    var[pos,:][mask.nodes_included] = mask.value

            resout.write_entire_frame(time, var)

