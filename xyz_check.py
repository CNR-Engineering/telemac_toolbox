#!/usr/bin/python3
"""
@brief:
Analyser un semis de points au format xyz

@features:
* min/max/moyenne des coordonnées x et y
"""
#TODO: calcul des distances min
#FIXME: cleaner to use Multipoint.bound of shapely...

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_xyz


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier xyz")
args = parser.parse_args()

# Min/max
min_x = float('inf')
min_y = float('inf')
min_z = float('inf')
max_x = -float('inf')
max_y = -float('inf')
max_z = -float('inf')

# Sum
sum_x = 0
sum_y = 0
sum_z = 0

# Number of points
i = 0

with BlueKenueRead_xyz(args.inname) as in_xyz:
    in_xyz.read_header()

    for i, point in enumerate(in_xyz.iter_on_points()):
        min_x = min(min_x, point.x)
        min_y = min(min_y, point.y)
        min_z = min(min_z, point.z)

        max_x = max(max_x, point.x)
        max_y = max(max_y, point.y)
        max_z = max(max_z, point.z)

        sum_x += point.x
        sum_y += point.y
        sum_z += point.z

        # Compute distance
        #FIXME: to be optimized...
        # with BlueKenueRead_xyz(args.inname) as in_xyz2:
        #     in_xyz2.read_header()

        #     for j, point2 in enumerate(in_xyz2.iter_on_points()):
        #         print(i, j)

npts = i + 1

print("===== Summary =====")
print()

print("{} points".format(npts))
print()

mean_x = sum_x/npts
mean_y = sum_y/npts
mean_z = sum_z/npts
print("Coordonnées min/max/moyenne :")
print("min(x) = {}".format(min_x))
print("max(x) = {}".format(max_x))
print("mean(x) = {}".format(mean_x))
print()
print("min(y) = {}".format(min_y))
print("max(y) = {}".format(max_y))
print("mean(y) = {}".format(mean_y))
print()
print("min(z) = {}".format(min_z))
print("max(z) = {}".format(max_z))
print("mean(z) = {}".format(mean_z))
print()

bary = (mean_x, mean_y, mean_z)
print("Barycentre des points : {}".format(bary))
print()

