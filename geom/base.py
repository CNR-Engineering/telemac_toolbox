# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
from math import sqrt, ceil
import numpy as np

# class Geodict:

def get_attr_value(obj, attr_name):
    """Obtenir l'attribut de l'objet s'il existe ou planter"""
    try:
        return obj['properties'][attr_name]
    except:
        print("ERREUR: l'attribut {} n'existe pas".format(attr_name), file=sys.stderr)
        sys.exit("Les attributs possibles sont : {}".format(list(obj['properties'].keys())))

def resampling(coord, dist_max):
    """
    @brief: sampling a polyline
    coord: vertices coordinates as list of tuples [(x1, y1), (x2, y2), ...]
    """
    DIST_SEUIL = 0.001

    # resampled_linestring = linestring.interpolate
    new_coord = [coord[0]]  # add first point

    for coord_line in zip(coord, coord[1:]):
        # Iterate over each segment
        [(x1, y1), (x2, y2)] = coord_line
        length = sqrt( (x1 - x2)**2 + (y1 - y2)**2 )

        if dist_max < DIST_SEUIL:
            sys.exit("La distance d'échantionnage est trop petite : {} (min possible = {})".format(dist_max, DIST_SEUIL))

        elif length > dist_max:
            # Nombre de points pour la nouvelle ligne (en incluant les 2 points d'origine)
            nb_pts = ceil(length/dist_max) + 1
            # Sampling with prescribe number of points
            #   (and ignore first point which was in the previous
            xnew = np.linspace(x1, x2, num=nb_pts)[1:]
            ynew = np.linspace(y1, y2, num=nb_pts)[1:]

            for x, y in zip(xnew, ynew):
                new_coord.append((x, y))

        else:
            # Add ending point
            new_coord.append((x2, y2))

    return(new_coord)

def resampling_3D(coord, dist_max): #FIXME merge wih resampling 2D
    """
    @brief: sampling a polyline
    coord: vertices coordinates as list of tuples [(x1, y1), (x2, y2), ...]
    """
    DIST_SEUIL = 0.001

    # resampled_linestring = linestring.interpolate
    new_coord = [coord[0]]  # add first point

    for coord_line in zip(coord, coord[1:]):
        # Iterate over each segment
        [(x1, y1, z1), (x2, y2, z2)] = coord_line
        length = sqrt( (x1 - x2)**2 + (y1 - y2)**2 )

        if dist_max < DIST_SEUIL:
            sys.exit("La distance d'échantionnage est trop petite : {} (min possible = {})".format(dist_max, DIST_SEUIL))

        elif length > dist_max:
            # Nombre de points pour la nouvelle ligne (en incluant les 2 points d'origine)
            nb_pts = ceil(length/dist_max) + 1
            # Sampling with prescribe number of points
            #   (and ignore first point which was in the previous
            xnew = np.linspace(x1, x2, num=nb_pts)[1:]
            ynew = np.linspace(y1, y2, num=nb_pts)[1:]
            znew = np.linspace(z1, z2, num=nb_pts)[1:]

            for x, y, z in zip(xnew, ynew, znew):
                new_coord.append((x, y, z))

        else:
            # Add ending point
            new_coord.append((x2, y2, z2))

    return(new_coord)

