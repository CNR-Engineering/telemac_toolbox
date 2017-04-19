#!/usr/bin/python3
"""
@brief:
Vérifier que les extrêmes des variables d'unu résultat 2D
"""

import numpy as np
import os

from common.arg_command_line import myargparse
from slf import common_data, Serafin

parser = myargparse(description=__doc__, add_args=['verbose'])
parser.add_argument("resname", help="Serafin input filename")
args = parser.parse_args()

common_data.verbose = args.verbose

with open('arf.csv', 'w') as fileout:
    with Serafin.Read(args.resname) as res:
        res.readHeader()
        res.get_time()

        fileout.write(';'.join(['time', 'H_min', 'Vmax'])+'\n')
        for time in res.time:
            H = res.read_var_in_frame(time, 'H')
            M = res.read_var_in_frame(time, 'M')
            fileout.write(';'.join(str(x) for x in [time, H.min(), M.max()])+'\n')
            fileout.flush()
