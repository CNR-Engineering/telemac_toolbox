#!/usr/bin/python3
"""
@brief:
Convertir (et translater) un ensemble de polylignes ouvertes shp en i2s, en attribuant la valeur selon une colonne d'un tableau csv

@features:
* choix du nombre de chiffres significatifs à écrire
* translation possible
* valeur prise dans le tableau de correspondance CSV et selon l'attribut de la table du shp

@warnings:
La colonne de la table attributaire doit être un flottant ou un entier?? (et non du texte par exemple)
"""
#FIXME: échantionner après la translation (gagner en précision)

import fiona
import pandas as pd
from shapely.geometry import LineString
import shapely.affinity as aff
import sys

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueWrite_i2s
from geom.base import get_attr_value, resampling

parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entrée shp")
parser.add_argument("outname", help="fichier de sortie i2s (format BlueKenue)")
parser.add_argument("csv_corresp", help="fichier de correspondance des valeurs (colonnes lues = [attr, 'value'])")
parser.add_argument("attr", help="nom de la colonne de la table attributaire")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants")
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
parser.add_argument("--force", "-f", help="Ecrase le fichier de sortie s'il existe", action='store_true')
args = parser.parse_args()

csv_data = pd.read_csv(args.csv_corresp)
csv_data.index = csv_data[args.attr]

with fiona.open(args.inname, 'r') as filein:
    with BlueKenueWrite_i2s(args.outname, args.force, args.digits) as out_i2s:
        out_i2s.auto_keywords()
        out_i2s.write_header()

        def write_single_polyline(coord, value):
            """Ecrire une seule polyligne à partir d'une liste de coordonnées"""
            linestring = LineString(coord)
            if args.shift is not None:
                linestring = aff.translate(linestring, xoff=args.shift[0], yoff=args.shift[1])
            out_i2s.write_polyline(linestring, value)

        for i, obj in enumerate(filein):
            obj_type = obj['geometry']['type']
            coord = obj['geometry']['coordinates']

            if obj_type == 'Polygon':
                if len(coord) == 1:  #FIXME: astuce. Toujours le cas??
                    coord = coord[0]
                else:
                    sys.exit("Le bricolage est bizarre, il y a {} coord. BRICOLAGE A SUPPRIMER ET CORRIGER PLUTOT LES FICHIERS SHP".format(len(coord)))

            # Récupération l'attribut value
            attr_key = get_attr_value(obj, args.attr)
            try:
                value = csv_data.loc[attr_key, 'value']
            except KeyError:
                sys.exit("The attribute '{}' is not a row name in file '{}' or 'value' is not a column name".format(attr_key, args.csv_corresp))
            print("- ajout zone #{} de type {} et de valeur {}".format(i, attr_key, value))

            # Export des données
            if obj_type == 'MultiLineString' or obj_type == 'MultiPolygon':
                print("Un objet MutliLineString est converti en {} objets LineString".format(len(coord)))
                for sub_coord in coord:
                    if obj_type == 'MultiPolygon':
                        # if len(coord) == 1:  #FIXME: astuce. Toujours le cas??
                        sub_coord = sub_coord[0]

                    write_single_polyline(sub_coord, value)

            elif obj_type == 'LineString' or obj_type == 'Polygon':
                write_single_polyline(coord, value)

            else:
                sys.exit("ERREUR: L'objet n'est pas une polyligne, mais vaut {}".format(obj_type))
