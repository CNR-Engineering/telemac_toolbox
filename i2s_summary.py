#!/usr/bin/python3
"""
@brief:
Analyser un ensemble de polylignes au format i2s

@features:
A préciser
"""
#FIXME doc

import math
from shapely.geometry import Point

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier i2s")
args = parser.parse_args()

npoly = 0
npt = 0
nsimple = 0
nclose = 0
polylines = []

with BlueKenueRead_i2s(args.inname) as in_i2s:
    in_i2s.read_header()

    # Read polyline by polyline, display infos and save objects in polylines
    for i, (value, polyline) in enumerate(in_i2s.iter_on_polylines()):
        npoly += 1

        # Type
        if polyline.has_z:
            type = 'avec Z'
        else:
            type = 'sans Z'
        print("\n-> Polyligne {} ({})".format(i+1, type))

        print("valeur = {}".format(value))

        # Number of vertices
        cur_npt = len(polyline.coords)  #FIXME: optimal?
        print("nombre de points = {}".format(cur_npt))
        npt = npt + cur_npt
        print("longueur = {}".format(polyline.length))

        if polyline.is_closed: nclose += 1
        print("fermé = {}".format(polyline.is_closed))  # Similar to is_ring?

        if polyline.is_simple: nsimple += 1
        print("s'intersecte pas = {}".format(polyline.is_simple))

        polylines.append(polyline)

        # Consecutive distance
        min_const_dist = float('inf')
        min_const_id = (None, None)
        coords = polyline.coords
        min_const_dist = polyline.length
        for i in range(1, len(coords)):
            dist = math.sqrt((coords[i][0]-coords[i-1][0])**2 + (coords[i][1]-coords[i-1][1])**2)
            if dist < min_const_dist:
                min_const_dist = dist
                min_const_id = (i-1, i)
        print("Distance mini entre points consecutifs = {} entre les points {} et {}".format(min_const_dist, min_const_id[0], min_const_id[1]))

    # Distance between polylines
    print("\n-> Calcul des distances minimales entre polylignes")
    min_dist = float('inf')
    min_id = (None, None)
    for i, p1 in enumerate(polylines[:-1]):  # omit last polyline
        id1 = i + 1
        for j, p2 in enumerate(polylines[i+1:]):  # avoid duplication of calculation
            id2 = id1 + j + 1
            dist = p1.distance(p2)
            if dist < min_dist:
                min_dist = dist
                min_id = (id1, id2)
            print("distance({}, {}) = {}".format(id1, id2, dist))
    print("Distance minimale = {} entre les polylignes {} et {}".format(min_dist, min_id[0], min_id[1]))

print('\n')
print("===== Summary =====")
print("{} polylignes analysés avec un total de {} points".format(npoly, npt))  # FIXME: i not properly defined
print("{} polyligne(s) s'intersectant avec lui-même".format(npoly - nsimple))
print("{} polyligne(s) fermé(s)".format(nclose))
