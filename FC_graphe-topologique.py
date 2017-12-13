#!/usr/bin/env python
"""
@brief:
Générer un schéma topologique sous forme d'image png/svg à partir d'une étude FC (fichier drso)

@warnings:
Les fichiers de sortie est écrasée si elle existe

TODO:
* les orifices ne sont pas orientés en réalité (Pb: avec le type de graph 'digraph' (DIrected graph) cela ne semble pas possible d'avoir les deux sur la double flèche)
* fusionner avec le script Crue_dc_graph.py + faire du Qt
"""

import argparse
import sys
import xml.etree.ElementTree as ET

from common.graph_1d_model import *


def key_from_constant(key, CONSTANT):
    """Retourne la valeur de key du dictionnanire CONSTANT"""
    try:
        return CONSTANT[key]
    except KeyError:
        try:
            return CONSTANT['default']
        except KeyError:
            sys.exit("La clé '{}' n'existe pas".format(key))

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text


PREFIX = "{http://www.fudaa.fr/xsd/crue}"
ET.register_namespace('', "http://www.fudaa.fr/xsd/crue")


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=(__doc__))
parser.add_argument("fichier_drso", help="fichier d'entrée drso")
parser.add_argument("--out_png", help="fichier de sortie au format png")
parser.add_argument("--out_svg", help="fichier de sortie au format svg")
parser.add_argument("--sep", help="ratio pour modifier l'espacement (par ex. 0.5 ou 2) [1 par défaut]", default=1)
parser.add_argument("--remove_preffix", help="suppression des préfixes des EMH ('Br_' et 'Nd_')", action='store_true')
args = parser.parse_args()


branches = {}  # dictionnaire de la forme {nom_branche: (noeud_amont, noeud_aval, type)}
nodes = []  # liste de noeuds
casiers = []  # liste de noeuds

# drso
for emh_group in ET.parse(args.fichier_drso).getroot():
    if emh_group.tag == (PREFIX+'Branches'):
        for branche in emh_group:
            is_active = branche.find(PREFIX+'IsActive').text  # a string : "true" or "false"

            if is_active=="true":
                type_branche = branche.tag.replace(PREFIX, '')
                name = branche.attrib['Nom']
                node_up = branche.find(PREFIX+'NdAm').attrib['NomRef']
                node_down = branche.find(PREFIX+'NdAv').attrib['NomRef']
                if args.remove_preffix:
                    name = remove_prefix(name, 'Br_')
                    node_up = remove_prefix(node_up, 'Nd_')
                    node_down = remove_prefix(node_down, 'Nd_')
                print("Ajout de la branche {} ({} -> {})".format(name, node_up, node_down))

                btype = TYPE_BRANCHES[type_branche]

                # Ajout des noeuds si non présents
                if node_up not in nodes:
                    nodes.append(node_up)
                if node_down not in nodes:
                    nodes.append(node_down)

                # Ajout de la branche
                branches[name] = (node_up, node_down, btype)

    elif emh_group.tag == (PREFIX+'Casiers'):
        for casier in emh_group:
            is_active = casier.find(PREFIX+'IsActive').text  # a string : "true" or "false"

            if is_active:
                noeud = casier.find(PREFIX+'Noeud').attrib['NomRef']
                print(noeud)
                if args.remove_preffix:
                    noeud = remove_prefix(noeud, 'Nd_')
                casiers.append(noeud)

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
# graph.write('toto.dot')
