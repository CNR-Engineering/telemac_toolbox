# -*- coding: utf-8 -*-

"""
Convertir un résultat Telemac en fichier LandXML
Le maillage 2D est écrit avec une valeur par noeud, en choissisant :
* le numéro de l'enregistrement (par défaut le dernier: -1)
* la variable à extraire (ex: S ou M)

Format LandXML:
- <Pnts> avec les coordonnées (X, Y, Z)
- <Faces> contenant le tableau de connectivité (ikle2d)
"""

from common.arg_command_line import myargparse
from slf import Serafin, common_data


if __name__ == "__main__":
    parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
    parser.add_argument("resname", help="Fichier Serafin d'entrée")
    parser.add_argument("xmlname", help="Fichier LandXML de sortie")
    parser.add_argument("--var", help="variable 2D du résultat Telemac")
    parser.add_argument("--shift", type=float, nargs=2, help="decalage en X et Y (en metre)")
    parser.add_argument("--digits", type=int, help="nombre de chiffres après la virgule", default=4)
    parser.add_argument("--pos", type=int, help="position de l'enregistrement temporel (commence à 0, valeur négative possible)", default=-1)
    args = parser.parse_args()

    common_data.verbose = args.verbose

    if args.force:
        mode = 'w'
    else:
        mode = 'x'

    with Serafin.Read(args.resname) as res:
        res.readHeader()
        res.get_time()

        res.export_as_LandXML(args.pos, args.var, args.xmlname, args.shift, args.digits, args.force)
