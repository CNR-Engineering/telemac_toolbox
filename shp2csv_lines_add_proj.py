#!/usr/bin/python3
"""
@brief:
Convertir un fichier shp (de type LINESTRING) en un fichier CSV
X, Y, ...fields...

/!\ Not tested on a 3D file!
"""
import csv
import fiona
import sys
from shapely.geometry import Point, LineString, MultiLineString
import shapely.affinity as aff

from common.arg_command_line import myargparse


parser = myargparse(description=__doc__, add_args=['force'])
parser.add_argument("inname", help="fichier d'entrée shp (avec des lignes)")
parser.add_argument("outname", help="fichier de sortie csv (X, Y, ...fields...)")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants", default=4)
parser.add_argument("--sep", help="séparateur de colonnes", default=';')
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
parser.add_argument("--add_proj", help="fichier shp avec une polyligne")
args = parser.parse_args()


FIELD = 'Absc_proj'

if args.add_proj is not None:
    with fiona.open(args.add_proj, 'r') as filein:
        for i, elem in enumerate(filein):
            profil_long = LineString(elem['geometry']['coordinates'])

            if i != 0:
                raise NotImplementedError("Une seule polyligne pour add_proj est attendue !")


with fiona.open(args.inname, 'r') as filein:
    with open(args.outname, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=args.sep)

        def write_single_point(coords, properties):
            """Write a single point (dict from fiona)"""
            global first

            geom_point = Point(coords)

            if args.add_proj is not None:
                absc_proj = profil_long.project(geom_point)
                if absc_proj <= 0 or absc_proj >= profil_long.length:
                    absc_proj = -1.  # HARDCODED default value (NaN?)
            if first:
                # Write header
                fields = ['X', 'Y']
                if len(coords) == 3:
                    fields.append('Z')
                fields = fields + [key for key, value in properties.items()]
                if args.add_proj is not None:
                    fields.append(FIELD)
                csvwriter.writerow(fields)
                first = False

            if args.shift is not None:
                geom_point = aff.translate(geom_point, xoff=args.shift[0], yoff=args.shift[1])

            row = [round(x, args.digits) for x in list(geom_point.coords)[0]] + [value for key, value in properties.items()]
            if args.add_proj is not None:
                row.append(absc_proj)

            csvwriter.writerow(row)

        first = True
        for point in filein:
            geom = point['geometry']
            properties = point['properties']

            if geom is None:
                sys.exit("Object is a None type")

            else:
                type = geom['type']
                coords = geom['coordinates']

                if type == 'LineString':
                    for coord in coords:
                        write_single_point(coord, properties)

                elif type == 'MultiLineString':
                    raise NotImplementedError

                else:
                    sys.exit("ERREUR: L'objet '{}' n'est une ligne".format(type))
