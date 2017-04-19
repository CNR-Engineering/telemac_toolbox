#!/usr/bin/python3
"""
@brief:
Modifier le maillage horizontal avec des transformations géométriques

@features:
# translation
# rotation (angle en degrée dans le sens anti-horaire)
# homothétie
#* |ratio|>1 : agrandissement
#* |ratio|<1 : réduction
#* ratio=-1 : symétrie centrale
#* (ratio=1 : identité)

@warnings:
* l'ordre des transformations est fixée (@see features) et ne dépend pas de l'ordre des arguments
* les transformations sont valables uniquement en planimétrie
"""
#TODO: détecter si shift et homothety ont 3 coordonnées pour modifier le fond aussi

import sys

from common.arg_command_line import myargparse
from slf import Serafin, common_data


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname", help="fichier slf d'entrée")
parser.add_argument("outname", help="fichier slf de sortie")
parser.add_argument("--shift", type=float, nargs=2, help="translation (x_distance, y_distance)")
parser.add_argument("--rotate", type=float, nargs=3, help="rotation (x_center, y_center, angle_deg)")
parser.add_argument("--homothety", type=float, nargs=3, help="homothétie (x_center, y_center, ratio)")
args = parser.parse_args()

common_data.verbose = args.verbose

with Serafin.Read(args.inname) as resin:
    resin.readHeader()
    resin.get_time()

    with Serafin.Write(args.outname, args.force) as resout:
        resout.copy_header(resin)

        # Compute mesh transformation(s)
        if args.shift is not None:
            resout.mesh_shift(args.shift)
        if args.rotate is not None:
            resout.mesh_rotate(args.rotate[0:2], args.rotate[2])
        if args.homothety is not None:
            resout.mesh_homothety(args.homothety[0:2], args.homothety[2])

        resout.write_header()

        # Write all frames
        for time in resin.time:
            var = resin.read_vars_in_frame(time, resout.varID)
            resout.write_entire_frame(time, var)
