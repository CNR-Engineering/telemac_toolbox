#!/usr/bin/python3
"""
@brief:
Convertir (et translater) un ensemble de polylignes ouvertes shp en i2s

@features:
* choix du nombre de chiffres significatifs à écrire (option `--digits`)
* translation possible (option `--shift`)
* La valeur de chaque polyligne est adaptable (option `--value`) :
    1. si l'option value est un flottant alors les valeurs sont toutes égales à cette constante
    2. si l'option value est égale à `iter` alors la valeur correspond à la position/numérotation de la polyligne
    3. sinon la valeur est prise dans l'attribut portant le nom de l'option
* Chaque polyligne peut être échantionnée selon une distance maximale avec l'option `--ech`
"""
#FIXME: échantionner après la translation (gagner en précision)

import fiona
from shapely.geometry import LineString
import shapely.affinity as aff
import sys

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueWrite_i2s
from geom.base import get_attr_value, resampling


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entrée shp")
parser.add_argument("outname", help="fichier de sortie i2s (format BlueKenue)")
parser.add_argument("--value", help="colonne de la table attributaire (voir l'aide)", default=0)
parser.add_argument("--ech", help="colonne de la table attributaire (voir l'aide)")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants")
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
parser.add_argument("--force", "-f", help="Ecrase le fichier de sortie s'il existe", action='store_true')
args = parser.parse_args()

try:
    float(args.value)
    value_type = 'int'
except ValueError:
    value_type = args.value
ech_int = False
if args.ech is not None:
    try:
        float(args.ech)
        ech_int = True
    except ValueError:
        pass

count = 0
with fiona.open(args.inname, 'r') as filein:
    with BlueKenueWrite_i2s(args.outname, args.force, args.digits) as out_i2s:
        out_i2s.auto_keywords()
        out_i2s.write_header()

        def write_single_polyline(coord, value, dist):
            global count
            """Ecrire une seule polyligne à partir d'une liste de coordonnées"""
            coord2 = coord
            if args.ech is not None:
                coord2 = resampling(coord2, dist)
            linestring = LineString(coord2)
            print("Polyligne {} avec {} points".format(count, len(coord2)))
            count += 1
            if args.shift is not None:
                linestring = aff.translate(linestring, xoff=args.shift[0], yoff=args.shift[1])
            out_i2s.write_polyline(linestring, value)


        for i, obj in enumerate(filein):
            print("{},{}".format(i, count))

            if obj['geometry'] is None:
                sys.exit("Object {} is None".format(i))

            else:
                obj_type = obj['geometry']['type']
                coord = obj['geometry']['coordinates']

                # Lecture distance si re-echantionnage si nécessaire
                dist = None
                if args.ech is not None:
                    if ech_int:
                        dist = float(args.ech)
                    else:
                        dist = get_attr_value(obj, args.ech)

                # Récupération l'attribut value
                if value_type == 'int':
                    value = float(args.value)
                elif value_type == 'iter':
                    value = i
                else:
                    value = get_attr_value(obj, args.value)

                # Export des données
                if obj_type == 'MultiLineString':
                    print("Un objet {} MutliLineString est converti en {} objets LineString".format(i, len(coord)))
                    for sub_coord in coord:
                        write_single_polyline(sub_coord, value, dist)

                elif obj_type == 'LineString':
                    write_single_polyline(coord, value, dist)

                elif obj_type == 'Polygon':
                    if len(coord)== 1:  #FIXME: Astuce selon le formatage du fichier
                        coord = coord[0]
                        write_single_polyline(coord, value, dist)
                    else:
                        for sub_coord in coord:
                            write_single_polyline(sub_coord, value, dist)

                else:
                    sys.exit("ERREUR: L'objet n'est pas une polyligne, mais vaut {}".format(obj_type))
