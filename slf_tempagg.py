#!/usr/bin/python3
"""
@brief:
Extract temporal min/max/mean for each node and each variable

@warnings:
for the mean, a constant time step is compulsary!

@info:
Un seul enregistrement est exporté (avec le temps remis à zéro)
"""
#FIXME: remove computation of UV @see slf_anal
#TODO: add progressif max

import copy
import numpy as np

from common.arg_command_line import myargparse
from slf import common_data, Serafin


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname", help="Serafin input filename")
parser.add_argument("outname", help="Serafin output filename")
parser.add_argument("fun", help="function among max, min and mean")
parser.add_argument("--velMag", help="compute velocity 2D (or 3D) magnitude of a simple difference for U, V (and W)", action="store_true")
args = parser.parse_args()

common_data.verbose = args.verbose
OUTPUT_TIME = 0.0

if   args.fun == 'max':  np_fun = np.maximum
elif args.fun == 'min':  np_fun = np.minimum
elif args.fun == 'mean': np_fun = np.add  # divide the final sum by the frame number
else: sys.exit("Unknown function {} !".format(args.fun))

with Serafin.Read(args.inname) as resin:
    resin.readHeader()
    resin.get_time()

    with Serafin.Write(args.outname, args.force) as resout:
        resout.copy_header(resin)

        varID_list = copy.copy(resin.varID)
        if args.velMag:
            varID_list.remove('U')
            varID_list.remove('V')
            varID_list.append('UV')
            normalVarID = varID_list[:-1]  # ignore UV to read Serafin files
            resout.assignVarIDs(varID_list)
        else:
            normalVarID = resout.varID

        resout.write_header()

        values = np.array([], dtype='float64')

        for i, time in enumerate(resin.time):
            common_data.log("Compute {} for time {}".format(args.fun, time))

            # Compute simple differences for each variables
            curVal = resin.read_vars_in_frame(time, normalVarID)

            if args.velMag:
                # Compute velocity magnitude difference
                U = resin.read_var_in_frame(time, 'U')
                V = resin.read_var_in_frame(time, 'V')
                if resin.type == '2D':
                    V2D = np.sqrt(np.power(U, 2) + np.power(V, 2))
                    curVal = np.vstack((curVal, V2D))
                elif resin.type == '3D':
                    raise Exception("TODO: 3D velocity")

            if i == 0: values = curVal
            else: values = np_fun(curVal, values)

        if args.fun == 'mean': values = values/len(resin.time)

        # Write a single frame with t=0s
        resout.write_entire_frame(OUTPUT_TIME, values)
