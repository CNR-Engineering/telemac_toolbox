#!/usr/bin/python3
"""
@brief:
Interpolate values at given points in a 2D unstructured mesh (with triangular elements)

@warnings:
* target point is outside the model => value of the nearest node is taken
* target point is exactly at a node location => node value is taken (no interpolation is required)
* target point is at the boundary of two elements => interpolation

@info:
* csv_convention for the point set:
** 3 columns (id, x, y) with colon (',') separator
** header is compulsory but order of column may vary
** id must be unique and is a string or an integer
* outCSV : CSV with columns : time, id, x, y and varID_list
"""

import csv
import numpy as np
import pandas as pd
import os
import sys

from common.arg_command_line import myargparse
from slf import common_data, Serafin


def int2d(resname, xyzname, varID_list, outCSV, overwrite=False, sep=',', digits=4):
    with Serafin.Read(resname) as res:
        res.readHeader()
        res.get_time()

        # Read points coord and id from CSV file
        points = pd.read_csv(xyzname, sep=sep, header=0, index_col=0)
        common_data.log("{} points found in {}".format(len(points.index), xyzname))

        # Compute ponderation for each target points
        res.compute_element_barycenters()
        ponderation = {}
        for ptID, coord in points.iterrows():
            common_data.log("Search position of point {}".format(ptID))
            ponderation[ptID] = res.ponderation_in_element(coord['x'], coord['y'])
        common_data.log("Ponderation coefficients: {}".format(ponderation))

        # Read results
        first = True
        for time in res.time:
            var = res.read_vars_in_frame(time, varID_list)
            df_var = pd.DataFrame(index=None, columns=None, dtype='float64')

            for ptID in points.index:
                result = np.zeros((res.nplan, len(varID_list)))
                for node, coeff in ponderation[ptID].items():
                    nodes = [(node-1) + x*res.nnode2d for x in range(res.nplan)]  # 3D nodes -1
                    result = result + coeff*(var[:,nodes].transpose())
                df_append = pd.DataFrame(result, columns=varID_list, dtype='float64')

                # Add columns
                df_append['time'] = str(time)
                df_append['iplan'] = list([str(x + 1) for x in df_append.index]) # Bricolage pour retrouver le numero du plan et passer en str pour eviter le float
                df_append['id'] = ptID
                df_append['x'] = list(str(x) for x in points['x'][df_append['id']]) # list pour effacer index
                df_append['y'] = list(str(x) for x in points['y'][df_append['id']]) # list pour effacer index
                df_var = df_var.append(df_append)

            if first:
                mode = 'w' if overwrite else 'x'
                df_var.to_csv(outCSV, mode=mode, sep=sep, index=False, float_format='%1.'+str(digits-1)+'e')
                first = False
            else:
                df_var.to_csv(outCSV, mode='a', sep=sep, index=False, float_format='%1.'+str(digits-1)+'e', header=None)

if __name__ == "__main__":
    parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
    parser.add_argument("resname", help="Serafin input filename")
    parser.add_argument("csv_filename", help="filename with a set of points (columns: id,x,y)")
    parser.add_argument("outCSV", help="CSV output filename")
    parser.add_argument("--var", nargs='+', help="list of 2D or 3D variables (see table)")
    parser.add_argument("--sep", help="CSV separator", default=',')
    parser.add_argument('--digits', type=int, help="significant digit for exported values", default=4)
    args = parser.parse_args()

    common_data.verbose = args.verbose

    int2d(args.resname, args.csv_filename, args.var, args.outCSV, args.force, args.sep, args.digits)
