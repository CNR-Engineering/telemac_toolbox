#!/usr/bin/env python
"""
@brief:
Générer un schéma topologique sous forme d'image png à partir d'un fichier dc (fichier de géométrie de Crue 9)

@info:
* il s'agit d'une vue schématique avec tous les noeuds et les branches du modèle (aucune information géographique)
* toutes les branches sont orientées de l'amont vers aval (mais certains types de branches ne devraient pas être orientées)
* la coloration dépent du type de branches et les casiers et noeuds ont des formes différentes
* les parties commentées ou shunter (par un GOTO) sont ignorées
* Les noms des branches et noeuds sont écrits en masjuscules
* les mots-clés (BRANCHE et GOTO) peuvent être indifférement en minuscules ou en majuscules.
* l'espacement est réglable avec l'option `--sep`

@warnings:
L'image de sortie est écrasée si elle existe
"""
# Tout le fichier dc est lu et les variables affectées
# Ensuite l'arbre puis le graphique sont générés

import argparse
import sys

from common.graph_1d_model import *


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=(__doc__))
parser.add_argument("fichier_dc", help="fichier d'entrée dc (format géométrie Crue9)")
parser.add_argument("--out_png", help="fichier de sortie au format png")
parser.add_argument("--out_svg", help="fichier de sortie au format svg")
parser.add_argument("--sep", help="ratio pour modifier l'espacement (par ex. 0.5 ou 2) [1 par défaut]", default=1)
args = parser.parse_args()

dc_file = args.fichier_dc
with open(dc_file, 'r', encoding="ISO-8859-1") as filein:
    print("Traitement du fichier {}".format(dc_file))
    branches = {}  # dictionnaire de la forme {nom_branche: (noeud_amont, noeud_aval, type)}
    nodes = []  # liste de noeuds
    casiers = []  # liste de noeuds
    label = None  # pour les goto

    for line in filein:
        line = line.replace('\n', '').strip()
        line = line.upper()  # nom des branches/noeuds non-sensible à la casse

        if not line.startswith('*'):
            if label is not None:
                # Il y a un goto en cours...
                if line.startswith(label):
                    print("/!\ Partie shunter par un GOTO de label : {}".format(label))
                    label = None

            else:
                # On est en dehors du goto
                if line.startswith('GOTO'):
                    # Mais on rentre dans un autre GOTO...
                    (key, label) = line.split()

                elif line.startswith('BRANCHE'):
                    # Une nouvelle branche est trouvée
                    (key, name, node_up, node_down, btype) = line.split()
                    print("Ajout de la branche {} ({} -> {})".format(name, node_up, node_down))

                    # Ajout des noeuds si non présents
                    if node_up not in nodes:
                        nodes.append(node_up)
                    if node_down not in nodes:
                        nodes.append(node_down)

                    # Ajout de la branche
                    branches[name] = (node_up, node_down, btype)

                elif line.startswith('CASIER'):
                    (key, node) = line.split()
                    casiers.append(node)
                    print("Casier {} détecté".format(node))

try:
    import pydot
except:
    sys.exit("Le module pydot ne fonctionne pas !")

# Création de l'arbre
graph = pydot.Dot(graph_type='digraph', nodesep=args.sep)  # vertical : rankdir='LR'

## Ajout des noeuds
for node in nodes:
    if node in casiers:
        shape = 'box3d'
    else:
        shape = 'ellipse'
    graph.add_node(pydot.Node(node, style="filled", fillcolor="white", shape=shape))

## Ajout des branches
for nom_branche, (node_up, node_down, btype) in branches.items():
    edge = pydot.Edge(node_up, node_down,
                      arrowhead=key_from_constant(btype, ARROWHEAD),
                      # arrowtail="inv",
                      label=nom_branche,
                      color=key_from_constant(btype, COLORS),
                      fontcolor=key_from_constant(btype, COLORS),
                      penwidth=key_from_constant(btype, SIZE)
                      # arrowtail="normal",
                      # dirType="back", marche pas
                      # shape="dot"
    )
    graph.add_edge(edge)

# Export(s) en png et/ou svg
# prog='neato' optimise l'espace
if args.out_png:
    print("Génération du fichier {}".format(args.out_png))
    graph.write_png(args.out_png)
if args.out_svg:
    print("Génération du fichier {}".format(args.out_svg))
    graph.write_svg(args.out_svg)
