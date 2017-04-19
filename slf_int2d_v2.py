#!/usr/bin/python3
"""
@brief:
Idem slf_int2d avec quelques fonctionnalités qui diffèrent et une exécution plus rapide

@features:
Export 
"""

import csv
import numpy as np
import os
import pandas as pd
import sys

from common.arg_command_line import myargparse
from slf import common_data, Serafin


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("resname", help="Serafin input filename")
parser.add_argument("csv_filename", help="filename with a set of points (columns: id,x,y)")
parser.add_argument("--var", nargs='+', help="list of 2D or 3D variables (see table)")
parser.add_argument("-o", "--outpattern", help="CSV output filename pattern (without variable suffix and extension)")
parser.add_argument("--sep", help="CSV separator", default=',')
parser.add_argument('--digits', type=int, help="significant digit for exported values", default=4)
args = parser.parse_args()

common_data.verbose = args.verbose

varID_list = args.var

if args.outpattern is None:  # use resname basename (ie filename without extension)
    args.outpattern = os.path.splitext(args.resname)[0]

with Serafin.Read(args.resname) as res:
    res.readHeader()
    res.get_time()

    # Read points coord and id from CSV file
    points = pd.read_csv(args.csv_filename, sep=args.sep, header=0)
    points.index = points['id']  # column hardcoded
    common_data.log("{} points found in {}".format(len(points.index), args.csv_filename))

    ponderations = res.compute_ponderations(points)

    # Read results
    if varID_list is None: varID_list = res.varID
    for i, varID in enumerate(varID_list):
        # Write in outCSV
        outCSV = args.outpattern + '_' + varID + '.csv'
        mode = 'w' if args.force else 'x'
        with open(outCSV, mode, newline='') as fp:
            a = csv.writer(fp, delimiter=',')
            header = ['time'] + list(points.index)
            a.writerow(header)
            float_fmt = '{:1.'+str(args.digits-1)+'e}'

            for time in res.time:
                var = res.read_var_in_frame(time, varID)

                # Compute linear interpolation in a triangle
                values = [0] * len(points.index)
                for i, (ptID, ponderation) in enumerate(ponderations):
                    for node, coeff in ponderation.items():
                        values[i] = values[i] + coeff*var[node-1]
                a.writerow([time] + [float_fmt.format(x) for x in values])
