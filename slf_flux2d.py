#!/usr/bin/python3
"""
@brief:
Calculer le débit traversant une série de section renseignée dans un fichier i2s

@warnings:
* chaque section est definie par 2 points et ne doit pas couper un contour extérieur (intersecter une pile de pont par exemple)

@info:
* le fichier i2s contient plusieurs sections (au moins une) et 2 points par ligne
* outfile : CSV with time in line and points id as column
* convention de signe: flux > 0 si l'écoulement se fait de l'amont vers l'aval entre les rives gauches et droites
"""

import argparse
import csv
import copy
import math
import numpy as np
import pandas as pd
from shapely.geometry import LineString

from geom.dataset import BlueKenueRead_i2s, BlueKenueWrite_i2s
from slf import common_data, Serafin


def int2d(resname, i2s_inname, outname=None, outname_short=None, overwrite=False, sep=',', digits=4):
    # global poly, final, res, df_all_points, df_points, values, df_poly, ipoly, row_values, df_append, S, Hmax, df_append_wet, Hmoy, values_short, Zmoy

    # df_poly: ['dx', 'dy'] (index = id_poly)
    # df_points: ['id_poly', 'id_pt', 'x', 'y', 'dx', 'dist']
    # df_all_points: list de df_points
    varID_list=['H', 'U', 'V']

    with Serafin.Read(resname) as res:
        res.readHeader()
        res.get_time()

        # ~> Compute mesh triangulation and sample segments
        res.compute_element_barycenters()
        res.compute_triangulation()

        # Build final and points
        final = []
        df_poly = pd.DataFrame()
        df_all_points = []

        # Read input polylines file
        with BlueKenueRead_i2s(i2s_inname) as in_i2s:
            in_i2s.read_header()

            with BlueKenueWrite_i2s('check.i2s', True) as out_i2s:  #FIXME: AVOID check.i2s
                # Prepare output i2s file
                out_i2s.copy_header(in_i2s)
                out_i2s.auto_keywords()
                out_i2s.write_header()

                # Loop on input polylines
                for ipoly, (value, poly) in enumerate(in_i2s.iter_on_polylines()):
                    print("Lecture polyligne {} de valeur {}".format(ipoly, value))
                    [(xa, ya), (xb, yb)] = list(poly.coords)
                    long = math.sqrt((xb - xa)**2 + (yb - ya)**2)
                    df_poly = df_poly.append(pd.DataFrame({'dx': [(xb-xa)/long], 'dy': [(yb-ya)/long], 'value': [value]}), ignore_index=True)
                    final.append([])
                    polyline = []
                    df_points = pd.DataFrame(columns=['id_poly', 'id_pt', 'x', 'y'])
                    for i, ((x,y), ponderation) in enumerate(res.iter_intersect_segment(xa, ya, xb, yb)):
                        final[ipoly].append(((x,y), ponderation))
                        df_points.loc[i] = [ipoly, i, x, y]
                        polyline.append((x, y))

                    # Compute cumulative distance (of the current polyline)
                    df_points['dx'] = np.sqrt(np.power(np.roll(df_points['x'], 1) - df_points['x'], 2) +
                                              np.power(np.roll(df_points['y'], 1) - df_points['y'], 2))
                    df_points['dx'].iloc[0] = 0.0
                    df_points['dist'] = df_points['dx'].cumsum()  # cumulative sum
                    df_all_points.append(df_points)

                    # Write output poyline (with added points)
                    out_i2s.write_polyline(LineString(polyline), value)

        mode = 'w' if overwrite else 'x'
        with open(outname_short, mode, newline='') as csvfile:
            fieldnames = ['time']
            for x in range(ipoly + 1):
                fieldnames.append(str(x))
            csvwriter = csv.writer(csvfile, delimiter=',')
            csvwriter.writerow(fieldnames)

            # ~> Read and interpolate results
            varID2write = copy.copy(varID_list)
            varID2write.append('Un')

            first = True
            for time in res.time:
                print("Temps {}".format(time))
                var = res.read_vars_in_frame(time, varID_list)

                # Initialiaze values
                values = pd.DataFrame()

                # Initialiaze values_short
                values_short = df_poly.copy()

                values_Q = [str(time)]

                for ipoly, ponderations in enumerate(final):
                    # ~> Interpolate
                    df_append = df_all_points[ipoly].copy()
                    # Add columns
                    #df_append['time'] = time
                    for varID in varID2write:
                        df_append[varID] = np.nan
                    for i, ((x,y), ponderation) in enumerate(ponderations):
                        row_values = np.zeros(len(varID_list))
                        for node, coeff in ponderation.items():
                            row_values = row_values + coeff*var[:,node-1]
                        df_append.loc[i,varID_list] = row_values

                    # Deduce Un (dot product)
                    df_append['Un'] = (df_append['V'] * df_poly.loc[df_append['id_poly'],'dx'].reset_index(drop=True) -
                                       df_append['U'] * df_poly.loc[df_append['id_poly'],'dy'].reset_index(drop=True))
                    df_append['Un'] = -1*df_append['Un'] # FIXME: bidouille debit positif
                    values = values.append(df_append)

                    # Compute discharge
                    df_append['integ'] = (2*df_append['H']*df_append['Un'] +
                                          2*np.roll(df_append['H'], 1)*np.roll(df_append['Un'], 1) +
                                          df_append['H']*np.roll(df_append['Un'], 1) +
                                          df_append['Un']*np.roll(df_append['H'], 1))
                    Q = (df_append['integ']*df_append['dx']/6).sum()

                    values_Q.append(round(Q, digits))

                # Export in CSV file
                if first:
                    mode = 'w'
                    header = True
                    first = False
                else:
                    mode = 'a'
                    header = False

                del values_short['dx']
                del values_short['dy']

                csvwriter.writerow(values_Q)

                #values.to_csv(outname, sep=sep, index=False, mode=mode, header=header, float_format='%.3f')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=__doc__)
    parser.add_argument("resname", help="Serafin input filename")
    parser.add_argument("i2s_inname", help="i2s filename (2 points per line)")
    #parser.add_argument("outname", help="CSV output filename")
    parser.add_argument("outname_short", help="CSV short output filename")
    parser.add_argument("--sep", help="CSV separator", default=',')
    parser.add_argument('--digits', type=int, help="significant digit for exported values", default=4)
    parser.add_argument("-f", "--force", help="force output overwrite", action="store_true")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    common_data.verbose = args.verbose

    int2d(args.resname, args.i2s_inname, None, args.outname_short, args.force, args.sep, args.digits)

