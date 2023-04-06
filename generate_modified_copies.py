#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@brief:
Script de génération de copies de fichier(s) en lisant les modifications dans un fichier CSV

@info:
Le fichier CSV doit respecter les conventions suivantes :

* la première ligne correspond à l'entête du CSV et reprend tous les mots-clés à chercher
* ensuite une ligne par fichier de sortie avec dans chaque cellule la valeur à remplacer
"""

import os.path
import pandas as pd

from common.arg_command_line import myargparse


parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname", help="fichier d'origine")
parser.add_argument("filecsv", help="fichier CSV des valeurs à attribuer")
parser.add_argument("--out_folder", help="dossier de sortie")
parser.add_argument("--sep", help="séparateur de colonnes", default=',')
parser.add_argument("--encoding", help="encodage du fichier inname et des fichiers de sortie", default='utf-8')
args = parser.parse_args()


# Ouverture du fichier CSV (traite tout en tant que texte avec dtype=str, sinon le replace derrière bug)
data = pd.read_csv(args.filecsv, sep=args.sep, dtype=str, index_col=0)
(nrow, ncol) = data.shape
print("Le fichier {} contient :".format(args.filecsv))
print("* {} lignes, correspondant aux fichiers suivantes : {}".format(nrow, list(data.index)))
print("* {} colonnes, correspondant aux mots-clés suivantes : {}".format(ncol, list(data.columns)))

# Créé dossier de sortie s'il n'existe pas
if args.out_folder is not None:
    if not os.path.exists(args.out_folder):
        os.makedirs(args.out_folder)

# Ouverture du fichier ews d'entrée
with open(args.inname, 'r', encoding=args.encoding) as filein:
    filein_content = filein.readlines()

    # Boucle sur le contenu du fichier CSV
    for i, row in data.iterrows():
        outname = row.name
        if args.out_folder is not None:
            outname = os.path.join(args.out_folder, outname)
        list2replace = row.index
        print("> Export de {}".format(outname))

        # Export du fichier modifie
        with open(outname, 'w', encoding=args.encoding) as fileout:
            count = {key: 0 for key in data.columns}
            # Boucle sur les mots-clés à remplacer (en-tête du CSV)
            for line in filein_content:
                for key in list2replace:
                    if key in line:
                        line = line.replace(key, row[key], 1)  # que 1ere occurence (pour consistance avec le conteur)
                        count[key] += 1
                fileout.write(line)

            # Cherche si le nombre de remplacements est cohérant
            unique_replacement = True
            for (key, value) in count.items():
                if value != 1:
                    print("ATTENTION : Le mot-clé {} a été remplacé {} fois".format(key,value))
                    unique_replacement = False
            if unique_replacement:
                print("Tous les mots-clés ont été remplacés une seule fois")
