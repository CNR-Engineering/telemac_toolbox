#!/usr/bin/python3
"""
@brief:
Calcule la différence entre inname1 et inname2 pour chaque variable et enregitrement communs

@prerequisites:
Les maillages sont identiques (tableaux x, y, ikle, ipobo)
"""
#FIXME: remove velMag

import argparse
import numpy as np
import sys

from common.arg_command_line import myargparse
from slf import Serafin, common_data


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname1", help="reference Serafin input filename")
parser.add_argument("inname2", help="Serafin input filename to subtract")
parser.add_argument("outname", help="Serafin output filename")
parser.add_argument("--velMag", help="compute velocity 2D (or 3D) difference instead of a simple difference for U, V (and W)", action="store_true")
args = parser.parse_args()

common_data.verbose = args.verbose

with Serafin.Read(args.inname1) as res1, Serafin.Read(args.inname2) as res2:
    res1.readHeader()
    res2.readHeader()

    res1.get_time()
    res2.get_time()

    # Check coherence between input files
    if not res1.sameMesh(res2):
        sys.exit("mesh {} and {} are different".format(inname1, inname2))

    with Serafin.Write(args.outname, args.force) as resout:
        resout.copy_header(res1)

        # Find common variables
        varID_list = res1.commonVarID(res2)
        if args.velMag:
            try:
                varID_list.remove('U')
                varID_list.remove('V')
                varID_list.append('UV')
            except ValueError:
                sys.exit("ERROR: a velocity variable (U, V or UV) could not be found in file")
        resout.assignVarIDs(varID_list)

        # Find common time
        resout.time = res1.commonTime(res2)
        resout.write_header()

        if args.velMag: normalVarID = resout.varID[:-1]  # ignore UV to read serafin files
        else: normalVarID = resout.varID

        for time in resout.time:
            # Compute simple differences for each variables
            var1 = res1.read_vars_in_frame(time, normalVarID)
            var2 = res2.read_vars_in_frame(time, normalVarID)
            values = var1-var2

            if args.velMag:
                # Compute velocity magnitude difference
                U1 = res1.read_var_in_frame(time, 'U')
                V1 = res1.read_var_in_frame(time, 'V')
                U2 = res2.read_var_in_frame(time, 'U')
                V2 = res2.read_var_in_frame(time, 'V')
                if res1.type is '2D':
                    V2D1 = np.sqrt(np.power(U1, 2) + np.power(V1, 2))
                    V2D2 = np.sqrt(np.power(U2, 2) + np.power(V2, 2))
                    values = np.vstack((values, V2D1-V2D2))
                elif res1.type is '3D':
                    W1 = res1.read_var_in_frame(time, 'W')
                    W2 = res2.read_var_in_frame(time, 'W')
                    V3D1 = np.sqrt(np.power(U1, 2) + np.power(V1, 2) + np.power(W1, 2))
                    V3D2 = np.sqrt(np.power(U2, 2) + np.power(V2, 2) + np.power(W2, 2))
                    values = np.vstack((values, V3D1-V3D2))

            resout.write_entire_frame(time, values)

        common_data.log("{} frames were ignored from res1".format(len(res1.time)-len(resout.time)))
        common_data.log("{} frames were ignored from res2".format(len(res2.time)-len(resout.time)))
