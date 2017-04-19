#!/usr/bin/python3
"""
@brief:
Modifier la bathymétrie par des zones définies par des polylignes

@info:
* value in i3s file is not used

@features:
* interpolate intermediate point if bottom is below a threshold...

@prerequisites:
* file is a mesh 2D
* variable 'B' (BOTTOM) is required
"""

import numpy as np
import sys
import shapely.affinity as aff
import shapely.geometry as geo

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i3s
from slf import Serafin, common_data


def bottom(inname, outname, i3s_name, overwrite, threshold):
    # global prev_line, zones, np_coord, Xt, Z, ref_rows, polyline
    with Serafin.Read(inname) as resin:
        resin.readHeader()

        if resin.type != '2D':
            sys.exit("The current script is working only with 2D meshes !")

        resin.get_time()

        # Define zones from polylines
        polylines = []
        with BlueKenueRead_i3s(i3s_name) as in_i3s:
            in_i3s.read_header()
            for i, (value, polyline) in enumerate(in_i3s.iter_on_polylines()):
                if not polyline.is_valid:
                    sys.exit("ERROR: polyline {} is not valid (probably because it intersects itself) !".format(i))

                # Linear interpolation along the line for values below the threshold
                if threshold is not None:
                    np_coord = np.array(polyline.coords)
                    Xt = np.sqrt(np.power(np.ediff1d(np_coord[:,0], to_begin=0.), 2) +
                                 np.power(np.ediff1d(np_coord[:,1], to_begin=0.), 2))
                    Xt = Xt.cumsum()
                    ref_rows = np_coord[:,2] > args.threshold
                    np_coord[:,2] = np.interp(Xt, Xt[ref_rows], np_coord[ref_rows,2])
                    polyline = geo.LineString(np_coord)
                polylines.append(polyline)

        prev_line = None
        zones = []

        for i, polyline in enumerate(polylines):
            if prev_line is not None:
                # print(prev_line, polyline)
                outline_pts = list(prev_line.coords) + list(reversed(polyline.coords))
                outline_zone = geo.Polygon(outline_pts)
                if not outline_zone.is_valid:
                    sys.exit("ERROR: Zone {} is invalid. Check polyline direction consistancy !".format(i))
                zones.append(outline_zone)
            prev_line = polyline

        with Serafin.Write(outname, overwrite) as resout:
            resout.copy_header(resin)
            resout.write_header()
            posB = resin.varID.index('B')

            for time in resin.time:
                var = resin.read_vars_in_frame(time, resout.varID)

                # Replace bottom locally
                nmodif = 0
                for i in range(resin.nnode):  # iterate over all nodes
                    node = i + 1
                    (x, y) = resin.get_coord(node)
                    pt = geo.Point(x,y)

                    for j, zone in enumerate(zones):
                        if zone.contains(pt):
                            # Current point is inside zone number j
                            #   and is between polylines a and b
                            print("node {} is in zone n°{}".format(node, j))
                            a = polylines[j+1]
                            b = polylines[j]
                            za = a.interpolate(a.project(pt)).z
                            zb = b.interpolate(b.project(pt)).z
                            da = pt.distance(a)
                            db = pt.distance(b)

                            # Replace value by a linear interpolation
                            var[posB,node-1] = (db*za + da*zb)/(da + db)

                            nmodif += 1
                            break

                resout.write_entire_frame(time, var)
                print("{} nodes were overwritten".format(nmodif))

if __name__ == '__main__':
    parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
    parser.add_argument("inname", help="Serafin input filename")
    parser.add_argument("outname", help="Serafin output filename")
    parser.add_argument("i3s_name", help="i3s BlueKenue 3D polyline file")
    parser.add_argument("--threshold", type=float, help="value to interpolate")
    args = parser.parse_args()
    # class args:
    #     pass
    # args.inname = "J:/DI-Affaires-2014/I.00850.001 - Remise navigabilité BC/9 - Volet Hydraulique/EDD ecluse/6_Travail/Modele_T2D/mesh.slf"
    # args.outname = "J:/DI-Affaires-2014/I.00850.001 - Remise navigabilité BC/9 - Volet Hydraulique/EDD ecluse/6_Travail/Modele_T2D/mesh2.slf"
    # args.i3s_name = "J:/DI-Affaires-2014/I.00850.001 - Remise navigabilité BC/9 - Volet Hydraulique/EDD ecluse/6_Travail/Modele_T2D/extraction_manuelle_TOPO_LZII_bathy_order.i3s"
    # args.verbose = True
    # args.force = True
    # args.threshold = 0.1

    common_data.verbose = args.verbose

    bottom(args.inname, args.outname, args.i3s_name, args.force, args.threshold)
