#!/usr/bin/python3
"""
@brief:
Convertir (et translater) un ensemble de polylignes ouvertes shp en i3s

@features:
* choix du nombre de chiffres significatifs à écrire
* translation possible
* La valeur de chaque polyligne est adapté en fonction de l'option `--value` :
*# si l'option value est un flottant alors les valeurs sont toutes égales à cette constante
*# si l'option value est égale à `iter` alors la valeur correspond à la position/numérotation de la polyligne
*# sinon la valeur est prise dans l'attribut portant le nom de l'option
"""

import fiona
from shapely.geometry import LineString
import shapely.affinity as aff
import sys

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueWrite_i3s
from geom.base import get_attr_value, resampling_3D


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier d'entrée shp")
parser.add_argument("outname", help="fichier de sortie i3s (format BlueKenue)")
parser.add_argument("--value", help="colonne de la table attributaire (voir l'aide)", default=0)
parser.add_argument("--ech", help="colonne de la table attributaire (voir l'aide)")
parser.add_argument("--digits", type=int, help="nombre de chiffres significatifs des flottants")
parser.add_argument("--shift", type=float, nargs=2, help="décalage en X et Y (en mètre)")
parser.add_argument("--force", "-f", help="écrase le fichier de sortie s'il existe", action='store_true')
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

# Ouverture du fichier shape
with fiona.open(args.inname, 'r') as filein:
    with BlueKenueWrite_i3s(args.outname, args.force, args.digits) as out_i3s:
        # Debut ecriture du fichier
        out_i3s.auto_keywords()
        out_i3s.write_header()

        def write_single_polyline(coord, value):
            """Ecrire une seule polyligne à partir d'une liste de coordonnées"""
            # Re-echantionnage si nécessaire
            if args.ech is not None:
                if ech_int:
                    dist = float(args.ech)
                else:
                    dist = get_attr_value(obj, args.ech)
                coord = resampling_3D(coord, dist)
            linestring = LineString(coord)
            if args.shift is not None:
                linestring = aff.translate(linestring, xoff=args.shift[0], yoff=args.shift[1])

            out_i3s.write_polyline(linestring, value)


        for i, obj in enumerate(filein):
            obj_type = obj['geometry']['type']
            coord = obj['geometry']['coordinates']

            # Récupération l'attribut value
            if value_type == 'int':
                value = float(args.value)
            elif value_type == 'iter':
                value = i
            else:
                try:
                    value = obj['properties'][args.value]
                except KeyError:
                    print("ERREUR: l'attribut {} n'existe pas".format(args.value), file=sys.stderr)
                    sys.exit("Les attributs possibles sont : {}".format(list(obj['properties'].keys())))

            # Export des données
            if obj_type == 'MultiLineString':
                print("Un objet MutliLineString est converti en {} objets LineString".format(len(coord)))
                for sub_coord in coord:
                    write_single_polyline(sub_coord, value)

            elif obj_type == 'LineString':
                write_single_polyline(coord, value)

            else:
                sys.exit("ERREUR: L'objet n'est pas une polyligne, mais vaut {}".format(obj_type))
