#!/usr/bin/python3
"""
@brief:
* Interpolate values at given points in a 2D unstructured mesh (with triangular elements)
* VOIR slf_int2d_v2 pour en csv différent et surtout plus rapide

@warnings:
* target point is outside the model => value of the nearest node is taken
* target point is exactly at a node location => node value is taken (no interpolation is required)
* target point is at the boundary of two elements => interpolation

@features:
* Deux exports possibles (le choix est fait en spécifiant l'extension du fichier de sortie `OUTPATTERN`) :
** export en _csv_ en un seul fichier contenant les colonnes ['id', 'X', 'Y', 'time'] et une colonne par variable à traiter
** export en _xlsx_ avec une variable par onglet et un point par colonne

@info:
* Format du fichier CSV d'entrée :
** 3 columns (id, x, y) with colon (';') separator
** header is compulsory but order of column may vary
** id must be unique and is a string or an integer
"""

import copy
import csv
import numpy as np
import os
import pandas as pd
import sys
import xlwt

from common.arg_command_line import myargparse
from slf import common_data, Serafin

parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
#FIXME: force is not used...
parser.add_argument("resname", help="Serafin input filename")
parser.add_argument("csv_filename", help="filename with a set of points (columns: id,x,y)")
parser.add_argument("--var", nargs='+', help="list of 2D or 3D variables (see table)")
parser.add_argument("-o", "--outpattern", help="CSV output filename pattern (without variable suffix and extension)")
parser.add_argument("--sep", help="CSV separator", default=';')
parser.add_argument('--digits', type=int, help="significant digit for exported values", default=4)
args = parser.parse_args()

common_data.verbose = args.verbose

varID_list = args.var

if args.outpattern is None:  # use resname basename (ie filename without extension)
    args.outpattern = os.path.splitext(args.resname)[0]

irow = 0
with Serafin.Read(args.resname) as res:
    res.readHeader()
    res.get_time()

    # Read points coord and id from CSV file
    #FIXME: do it for xyz file
    points = pd.read_csv(args.csv_filename, sep=args.sep, header=0)
    points.index = points['id']  # column hardcoded
    common_data.log("{} points found in {}".format(len(points.index), args.csv_filename))
    ponderations = res.compute_ponderations(points)

    values_empty = pd.DataFrame(points)

    # Add empty column values
    for varID in varID_list:
        values_empty[varID] = np.nan

    # Read results
    if varID_list is None: varID_list = res.varID
    first = True
    for time in res.time:
        var = res.read_vars_in_frame(time, varID_list)

        # values = Serafin.interpolate_from_ponderations(var, ponderations, points, varID_list, add_columns={'time': time}, digits=None)

        # for ponderation in ponderations:
        values = copy.copy(values_empty)
        values['time'] = time

        for ptID, ponderation in ponderations:
            row_values = np.zeros(var.shape[0])  # len(varID_list)
            for node, coeff in ponderation.items():
                row_values = row_values + var[:,node-1]*coeff
            values.loc[ptID,varID_list] = row_values

        if args.outpattern.endswith('.xls'):
            # Export as xls
            if first:
                book = xlwt.Workbook(encoding="utf-8")
                sheets = {}
                for varID in varID_list:
                    sheets[varID] = book.add_sheet(varID)
                    #sheets[varID].write(irow, 0, 'time') #FIXME: buggy because not a numpy value
                    for i, ptID in enumerate(points.index):
                        sheets[varID].write(irow, i+1, ptID)
                irow += 1
                first = False

            for varID in varID_list:
                sheets[varID].write(irow, 0, time)
                for i, ptID in enumerate(points.index):
                    sheets[varID].write(irow, i+1, values[varID][ptID])
            irow += 1

        elif args.outpattern.endswith('.csv'):
            # Export as csv
            if first:
                mode = 'w'
                header = True
                first = False
            else:
                mode = 'a'
                header = False
            values.to_csv(args.outpattern, sep=args.sep, index=True, mode=mode, header=header)

        else:
            # Not implemented
            sys.exit('Extension of {} is unknown (expected xls or csv)'.format(args.outpattern))

if args.outpattern.endswith('.xls'):
    book.save(args.outpattern)
    print("Writing {}".format(args.outpattern))
