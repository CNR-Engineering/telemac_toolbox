#!/usr/bin/python3
"""
@brief:
Convertir un fichier shp en un semis de points xyz (format BlueKenue)

@features:
* possibilité de translater les points
* formats d'entrée possibles :
** polylignes (avec Z)
** semis de points (avec Z)
"""
#TODO: etudier le cas sans Z
#FIXME: optimiser conversion en point et point par point pour MultiPoint

import fiona
import sys
from shapely.geometry import Point, MultiPoint
import shapely.affinity as aff

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueWrite_xyz


parser = myargparse(description=__doc__, add_args=['force'])
parser.add_argument("inname", help="fichier d'entrée shp (semis de points avec ou sans Z)")
parser.add_argument("outname", help="fichier de sortie xyz (format BlueKenue)")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants")
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
args = parser.parse_args()

with fiona.open(args.inname, 'r') as filein:
    with BlueKenueWrite_xyz(args.outname, args.force, args.digits) as out_xyz:
        out_xyz.auto_keywords()
        out_xyz.write_header()

        def write_single_point(geom_point):
            """Write a single point (class Point)"""
            if args.shift is not None:
                geom_point = aff.translate(geom_point, xoff=args.shift[0], yoff=args.shift[1])
            out_xyz.write_point(geom_point)

        for point in filein:
            geom = point['geometry']

            if geom is None:
                print("None type")

            else:
                type = point['geometry']['type']
                coords = point['geometry']['coordinates']

                if type == 'Point':
                    geom_point = Point(coords)
                    write_single_point(geom_point)

                elif type == 'MultiPoint':
                    for coord in coords:
                        geom_point = Point(coord)
                        write_single_point(geom_point)

                else:
                    sys.exit("ERREUR: L'objet '{}' n'est un semis de point".format(type))

