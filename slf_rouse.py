#!/usr/bin/python3
"""
@brief:
Ajouter des varibles supplémentaires pour l'interprétation hydro-sédimentaire à partir d'un résultat 2D

@features:
* Tous les enregistrements temporels sont traités et toutes les variables initiales sont ré-écrites
* Il y a autant que de sédiments que nouvelles variables (une vitesse de chute par sédiment)
* Le Rouse est calculé à partir de la vitesse de chute ws et de la variable US (KARMAN = 0.4) avec la formule: Rouse = ws/(KARMAN*US)
* Le Rouse est affecté à -9999. dans les zones où l'on a l'un des deux cas suivants :
    - la vitesse de frottement est nulle (afin d'éviter la division par zéro)
    - la hauteur d'eau est inférieure à un seuil qui vaut par défaut 1cm et qui est personnalisable avec l'option `--h_corr`
* Le nom des variables ajoutées pour le nombre de Rouse peut être modifié par l'utilisateur avec l'option `--labels` (si l'option est manquante, le nom des variables est construit avec le preffixe 'SEDIMENT')
* Les variables suivantes sont ajoutés :
    - CONTRAINTE (en Pa) = RHO_EAU * US^2
    - DMAX (en mm) selon trois zones basées sur TAU (bornes : 0.1 et 0.34)

@warnings:
Les variables US et H doivent exister
"""

from copy import deepcopy
import numpy as np
import sys

from common.arg_command_line import myargparse
from slf import Serafin, common_data

KARMAN = 0.4
DEFAULT_VAR_PREFIX = 'SEDIMENT'
DEFAULT_VALUE = -9999.
RHO_EAU = 1000.  # kg/m3

parser = myargparse(description=__doc__, add_args=['force', 'verbose'])
parser.add_argument("inname", help="Serafin input filename")
parser.add_argument("outname", help="Serafin output filename")
parser.add_argument("ws", help="Vitesses de chute (m/s)", type=float, nargs='+')
parser.add_argument("--labels", help="Nom des variables (sans accents ou caractères spéciaux)", nargs='+')
parser.add_argument("--h_corr", help="hauteur seuil pour correction (par défaut : 1cm)", type=float, default=0.01)
args = parser.parse_args()

common_data.verbose = args.verbose

nb_sediments = len(args.ws)

if args.labels is not None:
    if len(args.ws) != len(args.labels):
        sys.exit("Il n'y a pas {} noms de variables".len(nb_sediments))

with Serafin.Read(args.inname) as resin:
    resin.readHeader()
    resin.get_time()
    varIDs = deepcopy(resin.varID)  #FIXME: a supprimer lors du debuggage de copy_header avec des deepcopy??? Pb interference resout et resin

    if resin.type != "2D":
        sys.exit("ERREUR: Le fichier n'est pas un resultat 2D")
    if 'US' not in resin.varID:
        sys.exit("ERREUR: La variable US (vitesse de frottement) doit exister")
    if 'H' not in resin.varID:
        sys.exit("ERREUR: La variable H (hauteur d'eau) doit exister")

    pos_H = varIDs.index('H')
    pos_US = varIDs.index('US')
    nbvar = resin._nbvar

    with Serafin.Write(args.outname, args.force) as resout:
        resout.copy_header(resin)

        # Ajout des variables (S1, S2, ...)
        for i, ws in enumerate(args.ws):
            varname = DEFAULT_VAR_PREFIX + ' ' + str(i+1)
            if args.labels is not None:
                varname = args.labels[i]
            if len(varname)>16:
                sys.exit("ERREUR: Le nom de la variable est trop long (limite de 16 caractères): '{}'".format(varname))
            resout.addVarID('S', varname)
            print("Variable: '{}' (ws = {} m/s)".format(varname, ws))

        # Ajout des variables TAU, DMAX
        resout.addVarID('TAU', 'CONTRAINTE', 'PA')
        resout.addVarID('DMAX', 'DIAMETRE', 'MM')

        resout.compute_nbvar()

        resout.write_header()

        time = resin.time[0]
        var2write = np.empty([resout._nbvar, resout.nnode])

        resout.time = []
        for i, time in enumerate(resin.time):
            # Copy existing variables
            resout.time.append(time)
            var = resin.read_vars_in_frame(time, varIDs)
            var2write[:nbvar,:] = var

            H = var[pos_H,:]
            US = var[pos_US,:]
            correction = np.where((US == 0.) | (H <= args.h_corr))
            not_zero = np.where((US != 0.))  #FIXME: what happens if empty

            # Compute Rouse variables
            for i, ws in enumerate(args.ws):
                pos_var = nbvar + i
                var2write[pos_var,not_zero] = ws/(KARMAN*US[not_zero])
                var2write[pos_var,correction] = DEFAULT_VALUE

            # Compute TAU
            TAU = RHO_EAU*np.square(US)
            pos_var += 1
            var2write[pos_var,:] = TAU

            # Compute DMAX
            pos_var += 1
            # Zone 3 : TAU > 3.4
            DMAX = 1.4593*(TAU**0.979)

            # Zone 2 : 0.1 < TAU <= 0.34
            POS_Z = np.where((0.1 < TAU) & (TAU <= 0.34))
            TAU_Z = TAU[POS_Z]
            DMAX[POS_Z] = 1.2912*(TAU_Z**2) + 1.3572*TAU_Z - 0.1154

            # Zone 1 : TAU <= 0.1
            POS_Z = np.where(TAU <= 0.1)
            TAU_Z = TAU[POS_Z]
            DMAX[POS_Z] = 0.9055*(TAU_Z**1.3178)

            var2write[pos_var,:] = DMAX

            resout.write_entire_frame(time, var2write)
        common_data.log("My work is done")
