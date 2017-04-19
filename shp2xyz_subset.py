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
from shapely.geometry import Point, MultiPoint, Polygon, MultiPolygon
import shapely.affinity as aff

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueWrite_xyz


parser = myargparse(description=__doc__, add_args=['force'])
parser.add_argument("inname", help="fichier d'entrée shp (semis de points avec ou sans Z)")
parser.add_argument("outname", help="fichier de sortie xyz (format BlueKenue)")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants")
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
parser.add_argument("--include", help="fichier de polygones dont les emprises sont à conserver")
parser.add_argument("--exclude", help="fichier de polygones dont les emprises sont à exclure (exclude est prioritaire sur include)")
parser.add_argument("--buffer", type=float, help="buffer distance (>0 pour agrandir les polygones)")
# parser.add_argument("--exclude", help="exclure des zones dans les polygones")
args = parser.parse_args()


polygones2include = []
if args.include is not None:
    with fiona.open(args.include, 'r') as filein:
        for polygon_dict in filein:
            type = polygon_dict['geometry']['type']
            if type != 'Polygon':
                print("Les zones à exclure doivent être des polygones")
                sys.exit("{} != {}".format(type, 'Polygon'))
            coord = polygon_dict['geometry']['coordinates'][0]
            polygon = Polygon(coord)
            polygones2include.append(polygon)
    collec_polygones2include = MultiPolygon(polygones2include)

polygones2exclude = []
if args.exclude is not None:
    with fiona.open(args.exclude, 'r') as filein:
        for polygon_dict in filein:
            type = polygon_dict['geometry']['type']
            if type != 'Polygon':
                print("Les zones à exclure doivent être des polygones")
                sys.exit("{} != {}".format(type, 'Polygon'))
            coord = polygon_dict['geometry']['coordinates'][0]
            polygon = Polygon(coord)
            polygones2exclude.append(polygon)
    collec_polygones2exclude = MultiPolygon(polygones2exclude)


if args.buffer is not None:
    if args.include is not None:
        collec_polygones2include = collec_polygones2include.buffer(args.buffer)
    if args.exclude is not None:
        collec_polygones2exclude = collec_polygones2exclude.buffer(args.buffer)

nb_writed_pts = 0

with fiona.open(args.inname, 'r') as filein:
    with BlueKenueWrite_xyz(args.outname, args.force, args.digits) as out_xyz:
        out_xyz.auto_keywords()
        out_xyz.write_header()

        def write_single_point(geom_point):
            """Write a single point (class Point)"""
            global nb_writed_pts

            to_write = True

            if args.include is not None:
                if not collec_polygones2include.contains(geom_point):
                    to_write = False
            if args.exclude is not None:
                if collec_polygones2exclude.contains(geom_point):
                    to_write = False

            if to_write:
                nb_writed_pts += 1
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


print("Nombre des points exportés : {}".format(nb_writed_pts))
