#!/usr/bin/python3
"""
@brief:
Export 2D frames as multiple shp files with a serie of variables

@features:
* select variables
* select frames by a time list (exact value are required)
"""

import fiona
import csv
from glob import glob
import numpy as np
import sys

from common.arg_command_line import myargparse
from slf import Serafin, common_data


# if False:
#     parser = myargparse(description=__doc__, add_args=['verbose'])
#     parser.add_argument("slf_list", help="list of T2D result files")
#     parser.add_argument("outcsv", help="fichier csv de sortie")
#     parser.add_argument("var", help="variable 2D (un identifiant parmi : U, V, H, S, B, ...)")
#     parser.add_argument("--time", nargs='+', type=float, help="time (in seconds)")
#     parser.add_argument("--sep", help="séparateur de colonnes", default=';')
#     args = parser.parse_args()
# else:
class args:
    pass

args.slf_list = glob("*/r2d.slf")
args.outcsv = "test_S.csv"
args.var = 'S'
args.time = [0]
args.verbose = True
args.sep = ";"


common_data.verbose = args.verbose

nodes = [1, 10, 100]  # liste de noeuds (numerotation à partir de 1 comme BlueKenue)

with open(args.outcsv, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=args.sep)
    csvwriter.writerow(['file', 'time'] + nodes)

    for slf_file in args.slf_list:
        print(">>>>> FICHIER RESULTAT T2D : {} <<<<<".format(slf_file))
        with Serafin.Read(slf_file) as resin:
            resin.readHeader()

            if resin.type != '2D':
                sys.exit("The current script is working only with 2D meshes !")

            resin.get_time()

            for time in args.time:
                try:
                    print(resin.time.index(time))
                except ValueError:
                    print("/!\ Le temps {} n'est pas dans le fichier.".format(time))
                    sys.exit("Temps possibles : {}".format(resin.time))

                data = resin.read_var_in_frame(time, args.var)[[n+1 for n in nodes]]

                csvwriter.writerow([slf_file, time] + list(data))
