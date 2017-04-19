
def sampling(coord, dist_max):
    """
    @brief: sampling a polyline
    coord: vertices coordinates as list of tuples [(x1, y1), (x2, y2), ...]
    """
    global xnew, ynew
    # resampled_linestring = linestring.interpolate
    new_coord = [coord[0]]  # add first point

    for coord_line in zip(coord, coord[1:]):
        # Iterate over each segment
        [(x1, y1), (x2, y2)] = coord_line
        length = sqrt( (x1-x2)**2 + (y1-y2)**2 )

        if length > dist_max:
            # Nombre de points pour la nouvelle ligne (en incluant les 2 points d'origine)
            nb_pts = ceil(length/dist_max) + 1
            # Sampling with prescribe number of points
            #   (and ignore first point which was in the previous
            xnew = np.linspace(x1, x2, num=nb_pts)[1:]
            ynew = np.linspace(y1, y2, num=nb_pts)[1:]

            for x, y in zip(xnew, ynew):
                new_coord.append((x,y))

    return(new_coord)

