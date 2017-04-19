#!/usr/bin/python3
"""
@brief:
Convertir (et translater) un ensemble de polylignes fermées??? au format shp en sx

@features:
* choix du nombre de chiffres significatifs à écrire
* translation possible
"""
# TODO: sansZ => affecte 0 de partout?
# Si Polygon alors ne le ferme pas...

import fiona
import shapely.affinity as aff
from shapely.geometry import LineString, Polygon, LinearRing
import sys

from common.arg_command_line import myargparse
from geom.dataset import Write_SX


parser = myargparse(description=__doc__, add_args=['force'])
parser.add_argument("inname", help="fichier d'entrée shp")
parser.add_argument("outname", help="fichier de sortie sx")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants")
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
args = parser.parse_args()

# Ouverture du fichier shape
with fiona.open(args.inname, 'r') as filein:
    with Write_SX(args.outname, args.force, args.digits) as out_sx:
        out_sx.write_header()

        for i, obj in enumerate(filein):
            obj_type = obj['geometry']['type']
            if obj_type == 'LineString':
                linestring = LineString(obj['geometry']['coordinates'])

            elif obj_type == 'Polygon':
                # Export as a LineString without duplicated point
                coord = obj['geometry']['coordinates']

                if len(coord) == 1:
                    # Coordinates are already inside a list
                    coord = coord[0]

                if coord[0] == coord[-1]:
                    # Remove last duplicated point
                    del coord[-1]

                linestring = LineString(coord)
            else:
                # LinearRing considered as Polygon???
                sys.exit("ERREUR: L'objet {} n'est pas convertible".format(obj_type))

            if args.shift is not None:
                linestring = aff.translate(linestring, xoff=args.shift[0], yoff=args.shift[1])

            out_sx.write_polyline(linestring, id=i)
