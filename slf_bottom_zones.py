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

/!\ NECESSITE pyteltools !
"""

import numpy as np
import sys
import shapely.geometry as geo

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i3s
from pyteltools.slf import Serafin


class Zone:
    def __init__(self, polyline_1, polyline_2):
        self.polyline_1 = polyline_1
        self.polyline_2 = polyline_2
        self.polygon = None
        self._build_polygon()

    def _build_polygon(self):
        outline_pts = list(self.polyline_1.coords) + list(reversed(self.polyline_2.coords))
        self.polygon = geo.Polygon(outline_pts)
        if not self.polygon.is_valid:
            sys.exit("ERROR: Zone is invalid. Check polyline direction consistancy!")

    def contains(self, point):
        return self.polygon.contains(point)

    def interpolate(self, point):
        a = self.polyline_1
        b = self.polyline_2
        za = a.interpolate(a.project(point)).z
        zb = b.interpolate(b.project(point)).z
        da = point.distance(a)
        db = point.distance(b)
        return (db*za + da*zb)/(da + db)

    @staticmethod
    def get_zones_from_i3s_file(i3s_name, threshold):
        polylines = []
        with BlueKenueRead_i3s(i3s_name) as in_i3s:
            in_i3s.read_header()
            for i, (value, polyline) in enumerate(in_i3s.iter_on_polylines()):
                if not polyline.is_valid:
                    sys.exit("ERROR: polyline {} is not valid (probably because it intersects itself)!".format(i))

                # Linear interpolation along the line for values below the threshold
                if threshold is not None:
                    np_coord = np.array(polyline.coords)
                    Xt = np.sqrt(np.power(np.ediff1d(np_coord[:, 0], to_begin=0.), 2) +
                                 np.power(np.ediff1d(np_coord[:, 1], to_begin=0.), 2))
                    Xt = Xt.cumsum()
                    ref_rows = np_coord[:, 2] > args.threshold
                    np_coord[:, 2] = np.interp(Xt, Xt[ref_rows], np_coord[ref_rows, 2])
                    polyline = geo.LineString(np_coord)
                polylines.append(polyline)

        zones = []
        for prev_line, next_line in zip(polylines[:-1], polylines[1:]):
            zones.append(Zone(prev_line, next_line))
        return zones


def bottom(inname, outname, i3s_names, overwrite, threshold):
    # global prev_line, zones, np_coord, Xt, Z, ref_rows, polyline
    with Serafin.Read(inname, 'fr') as resin:
        resin.read_header()

        if not resin.header.is_2d:
            sys.exit("The current script is working only with 2D meshes !")

        resin.get_time()

        # Define zones from polylines
        zones = []
        for i3s_name in i3s_names:
            zones += Zone.get_zones_from_i3s_file(i3s_name, threshold)

        with Serafin.Write(outname, 'fr', overwrite) as resout:
            output_header = resin.header
            resout.write_header(output_header)
            posB = output_header.var_IDs.index('B')

            for time_index, time in enumerate(resin.time):
                var = np.empty((output_header.nb_var, output_header.nb_nodes), dtype=output_header.np_float_type)
                for i, var_ID in enumerate(output_header.var_IDs):
                    var[i, :] = resin.read_var_in_frame(time_index, var_ID)

                # Replace bottom locally
                nmodif = 0
                for i in range(output_header.nb_nodes):  # iterate over all nodes
                    x, y = output_header.x[i], output_header.y[i]
                    pt = geo.Point(x, y)

                    for j, zone in enumerate(zones):
                        if zone.contains(pt):
                            # Current point is inside zone number j
                            #   and is between polylines a and b
                            print("node {} is in zone n°{}".format(i + 1, j))

                            # Replace value by a linear interpolation
                            z_int = zone.interpolate(pt)
                            print(z_int)
                            var[posB, i] = min(var[posB, i], z_int)

                            nmodif += 1
                            break

                resout.write_entire_frame(output_header, time, var)
                print("{} nodes were overwritten".format(nmodif))

if __name__ == '__main__':
    parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
    parser.add_argument("inname", help="Serafin input filename")
    parser.add_argument("outname", help="Serafin output filename")
    parser.add_argument("i3s_names", help="i3s BlueKenue 3D polyline file", nargs='+')
    parser.add_argument("--threshold", type=float, help="value to interpolate")
    args = parser.parse_args()

    bottom(args.inname, args.outname, args.i3s_names, args.force, args.threshold)
