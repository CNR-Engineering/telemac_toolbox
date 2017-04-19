#!/usr/bin/python3
"""
@brief:
Export 2D frames as multiple shp files with a serie of variables

@features:
* select variables
* select frames by a time list (exact value are required)
"""

from collections import OrderedDict
import fiona
import numpy as np
import os
import pandas as pd
import shapely.geometry as geo
import sys

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s
from slf import Serafin, common_data


if True:
    parser = myargparse(description=__doc__, add_args=['verbose'])
    parser.add_argument("slf_name", help="Serafin input filename")
    parser.add_argument("preffixname", help="csv output filename")
    parser.add_argument("--var", nargs='+', help="liste des variables 2D")
    parser.add_argument("--time", nargs='+', type=float, help="time (in seconds)")
    parser.add_argument("--i2s_name", help="i2s input file")
    parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
    args = parser.parse_args()
else:
    class args:
        pass
    args.slf_name = "r2d.slf"
    args.preffixname = "r2d_extraction"
    args.var = ['H', 'U', 'V', 'M']  # ['H']
    args.time = [0]
    args.i2s_name = None #"zone-titi.i2s"
    args.shift = [976000, 6550000]
    args.verbose = True

RHO_EAU = 1000.  # kg/m3
add_angle = True

common_data.verbose = args.verbose
# cur_path = os.getcwd()
# (export_folder, export_preffix) = os.path.split(args.preffixname)
export_preffix = args.preffixname

with Serafin.Read(args.slf_name) as resin:
    resin.readHeader()

    if resin.type != '2D':
        sys.exit("The current script is working only with 2D meshes !")

    if args.i2s_name:
        print("Lecture du fichier {}".format(args.i2s_name))
        with BlueKenueRead_i2s(args.i2s_name) as in_i2s:
            in_i2s.read_header()
            for i, (value, polyline) in enumerate(in_i2s.iter_on_polylines()):
                # Gestion des erreurs
                if i!=0:
                    raise NotImplementedError("Une seule polyligne est attendue")
                if not polyline.is_valid:
                    sys.exit("ERROR: polyline {} is not valid (probably because it intersects itself) !".format(i))
                if not polyline.is_ring:
                    sys.exit("ERROR: polyline {} is not closed".format(i))

                polygon = geo.Polygon(polyline)  # only Polygon has `contains` method

                # Construction du tableau de maskage (avec des booléens)
                nodes_included = np.zeros(resin.nnode2d, dtype=bool)
                for j in range(resin.nnode):  # iterate over all nodes
                    node = j + 1
                    (x, y) = resin.get_coord(node)
                    pt = geo.Point(x,y)
                    if polygon.contains(pt):
                        nodes_included[j] = True

                nb_nodes_included = int(np.sum(nodes_included))
                print("Polyligne {} (avec {} points et une valeur à {}) contient {} noeuds".format(i, len(polyline.coords), value, nb_nodes_included))
    else:
        nodes_included = np.ones(resin.nnode2d, dtype=bool)

    resin.get_time()

    if args.var:
        vars = args.var
    else:
        vars = resin.varID

    # Translation
    if args.shift:  #FIXME: shift method for Serafin class?
        resin.x += args.shift[0]
        resin.y += args.shift[1]

    # DataFrame model to export
    df_data = pd.DataFrame(np.column_stack((resin.x, resin.y)), columns=['x','y'])
    for col in vars:
        df_data[col] = np.nan
    df_data.index += 1  # to have 1-indexed rows, ie node numbering like BlueKenue
    df_data = df_data[nodes_included]  # filtered by the zone

    for time in args.time:
        ignore = False
        try:
            print(resin.time.index(time))
        except ValueError:
            print("/!\ Le temps {} n'est pas dans le fichier.".format(time))
            print("Temps possibles : {}".format(resin.time))
            ignore = True

        if not ignore:
            var = resin.read_vars_in_frame(time, vars)
            if args.i2s_name:
                var = var[:,nodes_included]

            # Export CSV
            df_data[vars] = var.T
            # outname = args.preffixname + '_' + str(time) + '.csv'
            # df_data.to_csv(outname, sep=';', index_label="node") #float_format=None

            # Ajout de UV_angle
            if add_angle:
                df_data['UV_angle'] = np.degrees(np.arctan2(df_data['V'], df_data['U']))

            # Export shp
            var2export = vars
            if add_angle:
                var2export.append('UV_angle')
            dict_vars = OrderedDict([('node', 'int')] + [(col, 'float') for col in var2export])

            schema = {'geometry': 'Point', 'properties': dict_vars}
            # if export_folder != "":
                # os.chdir(export_folder)
            outname = export_preffix + '_' + str(time) + '.shp'
            # print(os.getcwd())
            # print(outname)
            with fiona.open(outname, 'w', 'ESRI Shapefile', schema) as layer:
                for node, row in df_data.iterrows():
                    pt = geo.Point(row['x'], row['y'])

                    elem = {}
                    elem['geometry'] = geo.mapping(pt)
                    elem['properties'] = {'node': int(node)}
                    for col in var2export:
                        elem['properties'][col] = row[col]
                    layer.write(elem)
