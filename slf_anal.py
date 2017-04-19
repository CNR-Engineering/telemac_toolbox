#!/usr/bin/python3
"""
@brief:
Extraire une partie d'un slf

@features:
* échantionnage et intervalle temporels
* suppression de variables en précisant soit les variables à conserver, soit les variables à supprimer (le choix est exclusif)
* _ajout de variables suivantes (EN COURS DE REALISATION)_
** S = B+H
** H = S-B
** M = sqrt(U²+V²)
** US = f(W,H,M)
** TAU = rho*US²
"""

import sys

from common.arg_command_line import myargparse
from slf import Serafin, common_data


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname", help="Serafin input filename")
parser.add_argument("outname", help="Serafin output filename")
parser.add_argument("--var2del", nargs='+', help="variable(s) to delete", default=[])
parser.add_argument("--var2keep", nargs='+', help="variable(s) to keep", default=[])
parser.add_argument("--ech", type=int, help="frequency sampling of inname", default=1)
parser.add_argument("--start", type=float, help="minimum time", default=-float('inf'))
parser.add_argument("--end", type=float, help="maximum time", default=float('inf'))
parser.add_argument("--shift", type=float, nargs=2, help="translation (x_distance, y_distance)")
args = parser.parse_args()

common_data.verbose = args.verbose

with Serafin.Read(args.inname) as resin:
    resin.readHeader()
    resin.get_time()

    with Serafin.Write(args.outname, args.force) as resout:
        resout.copy_header(resin)

        if args.shift is not None:
            resout.mesh_shift(args.shift)
        # Remove or assign variables from the user defined list
        if args.var2keep == []:
            resout.removeVarIDs(args.var2del)
        elif args.var2del == []:
            resout.assignVarIDs(args.var2keep)
        else:
            sys.exit("ERROR: Only del and keep are a correct type")

        common_data.log("Variables to export: {}".format(resout.varID))
        resout.write_header()

        resout.time = []
        for i, time in enumerate(resin.time):
            if args.start <= time <= args.end:
                if i % args.ech is 0:
                    resout.time.append(time)
                    var = resin.read_vars_in_frame(time, resout.varID)
                    resout.write_entire_frame(time, var)

        common_data.log("Write {} frames from the {} initial frames of input".format(len(resout.time), len(resin.time)))
