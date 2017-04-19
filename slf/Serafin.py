# -*- coding: utf-8 -*-
"""
Read/Write Serafin files and manipulate associated data
"""

from jinja2 import Environment, Template, FileSystemLoader
import math
import matplotlib.tri as mtri
import numpy as np
import os
import pandas as pd
import shapely.geometry as geom
import struct
import sys

from .common_data import log, varTable, varUnit, varName
from geom.dataset import BlueKenueRead_i2s

# nodes and elements are 0-indexed in saved arrays !!!
# nearest_node, ponderation => 1-indexed


# For LandXML export
env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')))
template = env.get_template("LandXML_template.xml")


class Serafin:
    """Handling Serafin binary file"""

    lang = 'fr'  # FIXME: automatic detection?

    def __init__(self, filename, mode):
        self.fileName = filename
        self.mode = mode

    # Handle properly opening and exiting of Serafin file
    # through a "with ... as ..." statement
    def __enter__(self):
        log(">>> Open {} in '{}' mode".format(self.fileName, self.mode))
        self.file = open(self.fileName, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log("<<< Close {}".format(self.fileName))
        self.file.close()
        return False

    # ~> General function for interpolation

    def get_coord(self, node):
        """
        @brief: return X and Y coordinate of a single node
        @node <int>: node number
        """
        return (self.x[node - 1], self.y[node - 1])

    def triangle_nodes(self, element):
        """
        @brief: get summits/nodes of a single triangular element
        @element <int>: element number
        @return <list int>: list of the 3 nodes
        """
        return list(self.ikle2d[element - 1])

    def nearest_node(self, target_x, target_y):
        """Find the nearest node of a target point (from x and y coordinates)"""
        dist = np.sqrt(np.power(self.x - target_x, 2) + np.power(self.y - target_y, 2))
        return np.argmin(dist) + 1

    # ~> Manipulation mesh

    def compute_element_barycenters(self):
        """Compute barycenters coordinates of each elements"""

        # Length of arrays = number of elements (self.nelem)
        self.x_bary = np.mean(self.x[self.ikle2d-1], 1)
        self.y_bary = np.mean(self.y[self.ikle2d-1], 1)

    def element_contains_point(self, target_x, target_y):
        """
        /!\ compute_element_barycenter should be called once firstly
        Return element number containing target point (1-indexed)
        If not in the domain return -1
        """
        # FIXME: optimize => check if inside domain firstly?
        square_dist_to_bary = np.power(self.x_bary - target_x, 2) + np.power(self.y_bary - target_y, 2)  # minimize square root is not necessary
        elements_ordered = np.argsort(square_dist_to_bary)+1  # +1 because it was 0-indexed

        point = geom.Point(target_x, target_y)
        inside = False
        for i, element in enumerate(elements_ordered):
            nodes = self.triangle_nodes(element)
            triangle = [self.get_coord(node) for node in nodes]
            if point.within(geom.Polygon(triangle)):
                log("Point is inside element {} ({} iteration(s))".format(element, i+1))
                return element
        return -1

    def element_contains_geomPoint(self, point):
        """
        Call element_contains_point with a Point object from shapely package
        """
        (target_x, target_y) = point.coords
        return self.element_contains_(target_x, target_y)

    def ponderation_in_element(self, target_x, target_y):
        """
        /!\ compute_element_barycenter should be called once firstly
        Method for a single target point:
          iterate over ordered elements (minimal distance to
          element barycenters) and find if inpoly

        ponderation = dict{node1: value1, node2: value2, node3: value3}
        (case of triangulation)
        """
        element = self.element_contains_point(target_x, target_y)
        if element>=0:  # inside
            nodes = self.triangle_nodes(element)
            triangle = [self.get_coord(node) for node in nodes]
            [(x1, y1), (x2, y2), (x3, y3)] = triangle
            # Barycentric coordinate system
            # a = |PB,PC|, b = |PC,PA|, c = |PA,PB|
            a = abs((x2 - target_x) * (y3 - target_y) - (y2 - target_y) * (x3 - target_x))
            b = abs((x3 - target_x) * (y1 - target_y) - (y3 - target_y) * (x1 - target_x))
            c = abs((x1 - target_x) * (y2 - target_y) - (y1 - target_y) * (x2 - target_x))

            # Compute dimensionless coefficients
            total = a + b + c
            coeff = [a / total, b / total, c / total]

            return {node: coeff[i] for i, node in enumerate(nodes)}
        else:
            nearest_node = self.nearest_node(target_x, target_y)
            log("Point is outside the domain, the value of closest node is used for interpolation")
            return {nearest_node: 1.0}

    def compute_ponderations(self, points):
        """
        /!\ compute_element_barycenters() is called in this function
        Compute ponderation of each individual points:
        [((x1,y1), n1: c1, n1: c2, n3: c3), ...]
        points <pd.DataFrame columns=['x','y']>"""
        self.compute_element_barycenters()
        ponderations = []
        for ptID, coord in points.iterrows():
            log("Search position of point {}".format(ptID))
            ponderation = (ptID, self.ponderation_in_element(coord['x'], coord['y']))
            # log("Ponderation coefficient: {}".format({n: round(c,2) for n,c in ponderation[ptID].items()})) # FIXME: round is not working...
            log("Ponderation coefficients: {}".format(ponderation)) # FIXME: round is not working...
            ponderations.append(ponderation)
        return ponderations

    def get_sampled_polylines(self, i2s_name):
        # class segment_on_mesh:
        #     def __init__(self):
        #         self.name = "PK176.000"
        #         self.df_points = n points (x,y,dist)
        #         self.orientation = (dx, dy)
        #
        # local: df_points
        # global: df_poly, df_all_points

        final = []
        df_poly = pd.DataFrame()
        df_all_points = []

        # Read input polylines file
        with BlueKenueRead_i2s(i2s_name) as in_i2s:
            in_i2s.read_header()

            # Loop on input polylines
            for ipoly, (value, poly) in enumerate(in_i2s.iter_on_polylines()):
                print("Lecture polyligne {} de valeur {}".format(ipoly, value))
                [(xa, ya), (xb, yb)] = list(poly.coords)
                long = math.sqrt((xb - xa)**2 + (yb - ya)**2)
                df_poly = df_poly.append(pd.DataFrame({'dx': [(xb-xa)/long], 'dy': [(yb-ya)/long], 'value': [value]}), ignore_index=True)
                final.append([])
                df_points = pd.DataFrame(columns=['id_poly', 'id_pt', 'x', 'y'])
                for i, ((x,y), ponderation) in enumerate(self.iter_intersect_segment(xa, ya, xb, yb)):
                    final[ipoly].append(((x,y), ponderation))
                    df_points.loc[i] = [ipoly, i, x, y]

                # Compute cumulative distance (of the current polyline)
                df_points['dx'] = np.sqrt(np.power(np.roll(df_points['x'], 1) - df_points['x'], 2) +
                                          np.power(np.roll(df_points['y'], 1) - df_points['y'], 2))
                df_points['dx'].iloc[0] = 0.0
                df_points['dist'] = df_points['dx'].cumsum()  # cumulative sum
                df_all_points.append(df_points)
        return (df_poly, df_all_points, final)




    # ~> Compare Serafin object (self and other are permutable)

    def sameMesh(self, other):
        """Check if the mesh is similar with another Serafin object"""
        if self.type != other.type:
            return False
        elif self.nnode != other.nnode:
            return False
        elif self.nelem != other.nelem:
            return False
        else:
            return True

    def sameVarID(self, other):
        """Check if variables lists are similar"""
        return all(self.varID == other.varID)

    # ~> Find common data of two Serafin objects (self and other are permutable)

    def commonVarID(self, other):
        """Return common varID with another Serafin object"""
        varID_list = []
        for varID in self.varID:
            if varID in other.varID: varID_list.append(varID)
        return varID_list

    def commonTime(self, other):
        """Return common time serie with another other object"""
        timeSerie = []
        for time in self.time:
            if time in other.time:
                timeSerie.append(time)
        return timeSerie


    # ~> Geometric transformation of mesh
    # Is not using shapely because transformations are simple
    #   and faster directly
    def mesh_shift(self, shift):
        """Shift mesh coordinates with shift vector"""
        self.x += shift[0]
        self.y += shift[1]


    def mesh_rotate(self, center_coord, angle_deg):
        """
        Shift mesh coordinates with shift vector
        center_coord <tuple of 2 floats>: coordinates of rotation center
        angle_deg <float>: rotation angle in degree (in anticlockwise sense)
        """
        xc = center_coord[0]
        yc = center_coord[1]
        angle_rad = math.radians(angle_deg)

        # Build local copies (avoid working and modifying same variables)
        x = self.x
        y = self.y

        # Compute transformation
        self.x = xc + (x - xc)*math.cos(angle_rad) - (y - yc)*math.sin(angle_rad)
        self.y = yc + (x - xc)*math.sin(angle_rad) + (y - yc)*math.cos(angle_rad)


    def mesh_homothety(self, center_coord, ratio):
        """
        Compute transformed coordinates obtained by homothety
        center_coord <tuple of 2 floats>: coordinates of rotation center
        ratio <float>: transformation ratio (>1 for enlargement)
        """
        xc = center_coord[0]
        yc = center_coord[1]

        # Build local copies (avoid working and modifying same variables)
        x = self.x
        y = self.y

        self.x = xc + ratio*(x - xc)
        self.y = yc + ratio*(y - yc)


    def export_as_LandXML(self, pos, var, xmlname, shift=None, digits=4, force=False):
        """
        @brief: toto
        /!\ pos => 0-indexed (not a frame id!)
        """
        time = self.time[pos]
        data = self.read_var_in_frame(time, var)

        if shift is None:
            values_at_nodes = np.column_stack((self.x, self.y, data))
        else:
            values_at_nodes = np.column_stack((self.x + shift[0], self.y + shift[1], data))
        triangles = self.ikle2d

        template_render = template.render(
            nodes = np.round(values_at_nodes, digits),
            ikle = self.ikle2d
        )

        # Ecriture du fichier XML
        if force:
            mode = 'w'
        else:
            mode = 'x'
        with open(xmlname, mode) as fileout:
            fileout.write(template_render)


    def compute_triangulation(self):
        """..."""
        self.triang = mtri.Triangulation(self.x, self.y, self.ikle2d-1)
        self.triang_neighbors = self.triang.neighbors + 1 # 1-indexed


    def iter_intersect_segment(self, xa, ya, xb, yb):
        """"REQUIRE compute_element_barycenters and triangulation..."""
        # Ajout A
        ptA = (xa, ya)
        ptB = (xb, yb)
        elementa = self.element_contains_point(xa, ya)
        elementb = self.element_contains_point(xb, yb)
        yield ((xa, ya), self.ponderation_in_element(xa, ya))
        prev_element = None

        # Ajout intersections
        i = 0
        while (elementa != elementb):
            i += 1
            print('>> Iteration {} - elements : {} et {}'.format(i, elementa, elementb))
            transect = geom.LineString([ptA, ptB])

            elements_voisins = self.triang_neighbors[elementa-1]  # 1-indexed
            elements_voisins = elements_voisins[elements_voisins != 0]  # if element if at the border

            for element in elements_voisins:
                if element != prev_element:
                    nodes = np.intersect1d(self.ikle2d[elementa-1], self.ikle2d[element-1])
                    print(nodes)
                    (n1, n2) = nodes # FIXME try: len==2 !
                    segment = geom.LineString([self.get_coord(n1), self.get_coord(n2)])
                    if transect.crosses(segment): # FIXME: touches?
                        pt_intersection = transect.intersection(segment)
                        pond_n2 = segment.project(pt_intersection, normalized=True)
                        ponderation = {n1: 1 - pond_n2, n2: pond_n2}
                        yield (list(pt_intersection.coords)[0], ponderation)
                        print("Element {}, nodes {} and {}".format(element, n1, n2))
                        break

            prev_element = elementa
            elementa = element

        # Ajout B
        yield ((xb, yb), self.ponderation_in_element(xb, yb))

    # def iter_intersect_segment(self, xa, ya, xb, yb):
    #     """"REQUIRE compute_element_barycenters and triangulation..."""
    #     final = []  # [(x1,y1): pond1, (x2,y2): pond2, ...]

    #     # Ajout A
    #     ptA = (xa, ya)
    #     ptB = (xb, yb)
    #     elementa = self.element_contains_point(xa, ya)
    #     elementb = self.element_contains_point(xb, yb)
    #     final.append(((xa, ya), self.ponderation_in_element(xa, ya)))
    #     prev_element = None

    #     # Ajout intersections
    #     i = 0
    #     while (elementa != elementb):
    #         i += 1
    #         print('>> Iteration {} - elements : {} et {}'.format(i, elementa, elementb))
    #         transect = geom.LineString([ptA, ptB])

    #         elements_voisins = self.triang_neighbors[elementa-1] # 1-indexed
    #         for element in elements_voisins:
    #             if element != prev_element:
    #                 nodes = np.intersect1d(self.ikle2d[elementa-1], self.ikle2d[element-1])
    #                 (n1, n2) = nodes # FIXME try: len==2 !
    #                 segment = geom.LineString([self.get_coord(n1), self.get_coord(n2)])
    #                 if transect.crosses(segment): # FIXME: touches?
    #                     pt_intersection = transect.intersection(segment)
    #                     pond_n2 = segment.project(pt_intersection, normalized=True)
    #                     ponderation = {n1: 1 - pond_n2, n2: pond_n2}
    #                     final.append((list(pt_intersection.coords)[0], ponderation))
    #                     print("Element {}, nodes {} and {}".format(element, n1, n2))
    #                     break

    #         prev_element = elementa
    #         elementa = element

    #     # Ajout B
    #     final.append(((xb, yb), self.ponderation_in_element(xb, yb)))
    #     return final




class Read(Serafin):
    """Read Serafin binary file"""

    def __init__(self, filename):
        Serafin.__init__(self, filename, 'rb')
        self.fileSize = os.path.getsize(self.fileName)

    def readHeader(self):
        """
        @brief: read header (file caracteristics) and assign attributes
        Attributes assigned: title, nbvar, nbvar2... TOCOMPLETE
        """
        # Read title
        self.file.read(4)
        self.title = self.file.read(80)
        self.file.read(4)

        # Read nbvar and nbvar2
        self.file.read(4)
        self._nbvar = struct.unpack('>i', self.file.read(4))[0]
        self._nbvar2 = struct.unpack('>i', self.file.read(4))[0]
        self.file.read(4)

        # Read variable names and units
        self.varNames = []
        self.varUnits = []
        for ivar in range(self._nbvar):
            self.file.read(4)
            self.varNames.append(self.file.read(16))
            self.varUnits.append(self.file.read(16))
            self.file.read(4)

        # IPARAM: 10 integers (not all are useful...)
        self.file.read(4)
        self._param = struct.unpack('>10i', self.file.read(40))
        self.file.read(4)
        self.nplan = self._param[6]
        if self._param[-1] is 1:
            # Read 6 integers which correspond to simulation starting date
            self.file.read(4)
            self.date = struct.unpack('>6i', self.file.read(6 * 4))
            self.file.read(4)

        # 4 integers
        self.file.read(4)
        self.nelem = struct.unpack('>i', self.file.read(4))[0]
        self.nnode = struct.unpack('>i', self.file.read(4))[0]
        self.ndp = struct.unpack('>i', self.file.read(4))[0]

        self._var_i = struct.unpack('>i', self.file.read(4))[0]  # not interesting value?
        self.file.read(4)
        if self.nplan != 0:
            self.nnode2d = int(self.nnode/self.nplan)
        else:
            self.nnode2d = self.nnode

        # IKLE
        self.file.read(4)
        nb_val = '>%ii' % (self.nelem * self.ndp)
        self.ikle = np.array(struct.unpack(nb_val, self.file.read(4 * self.nelem * self.ndp)))
        self.file.read(4)

        # IPOBO
        self.file.read(4)
        nb_val = '>%ii' % self.nnode
        self.ipobo = np.array(struct.unpack(nb_val, self.file.read(4 * self.nnode)))
        # self.ipobo = self.ipobo.astype(int) # FIXME: bricolage pour integer
        self.file.read(4)

        # x coordinates
        self.file.read(4)
        nb_val = '>%if' % self.nnode
        self.x = np.array(struct.unpack(nb_val, self.file.read(4 * self.nnode)))
        self.file.read(4)

        # y coordinates
        self.file.read(4)
        nb_val = '>%if' % self.nnode
        self.y = np.array(struct.unpack(nb_val, self.file.read(4 * self.nnode)))
        self.file.read(4)

        # Header size
        self.headerSize = (80 + 8) + (8 + 8) + (self._nbvar * (8 + 32)) + (40 + 8) + (
            self._param[-1] * ((6 * 4) + 8)) + (16 + 8) + ((int(self.nelem) * self.ndp * 4) + 8) + (
                              3 * (int(self.nnode) * 4 + 8))

        # Frame size (all variable values for one time step)
        self.frameSize = 12 + (self._nbvar * (8 + int(self.nnode) * 4))

        # Deduce number of frames (integer division)
        self.nb_frame = (self.fileSize - self.headerSize) // self.frameSize

        # Deduce type
        if self.ndp == 3 and self.nplan is 0:
            self.type = "2D"
        elif self.ndp is 6 and self.nplan >= 2:
            self.type = "3D"
        else:
            raise ValueError("Unknown mesh type")

        # Deduce varID (abbreviation of variables)
        self.varID = []
        for varName in self.varNames:
            for varID, line in varTable(self.type).iterrows():  #FIXME: optimiser le parcours du tableau
                if line[Serafin.lang] == varName.decode(encoding='utf-8'):
                    self.varID.append(varID)
                    break
        if len(self.varID) != len(self.varNames):
            print(self.varNames)
            print(self.varID)
            sys.exit("ERROR : could not found a varID for all varNames")

        # Build ikle2d
        ikle = self.ikle.reshape(self.nelem, self.ndp)  #FIXME npd en 2d?
        if self.type == '3D':
            # FIXME: bricolage pour avoir un ikle2d a partir du 3D
            self.ikle2d = np.empty([int(self.nelem/(self.nplan-1)), 3], dtype=int)  #FIXME: avoid int() function here (check the result should be always an integer)
            for i, line in enumerate(self.ikle2d):
                self.ikle2d[i] = ikle[i, np.array([0,1,2])]  # in bottom frame
        else:
            self.ikle2d = ikle

        log("{} result (with {} plans)".format(self.type, self.nplan))

    def get_time(self):
        """
        @brief: assign time serie (in seconds) in a list
        """
        self.file.seek(self.headerSize, 0)
        self.time = []
        for i in range(self.nb_frame):
            self.file.read(4)
            self.time.append(struct.unpack('>f', self.file.read(4))[0])
            self.file.read(4)
            self.file.seek(self.frameSize - 12, 1)

    def read_entire_frame(self, time2read):
        """
        @brief: read an entire frame (all the variables)
        @param time2read <float>: simulation time (in seconds) of the target frame
        @return var <numpy 2D-array>: shape = (nb var, nb node)
        """
        nb_val = '>%if' % (self.nnode)
        try:
            pos_time2read = self.time.index(time2read)
        except IndexError:
            print("ERROR: possible variables are {}".format(self.varID))
            sys.exit(1)

        var = np.empty([self._nbvar, self.nnode], dtype='float64')

        self.file.seek(self.headerSize + pos_time2read * self.frameSize + 12, 0)
        for pos_var in range(self._nbvar):
            self.file.read(4)
            var[pos_var] = struct.unpack(nb_val, self.file.read(4 * self.nnode))
            self.file.read(4)

        return var

    def read_var_in_frame(self, time2read, varID):
        """
        @brief: read a single variable in a frame
        @param time2read <float>: simulation time (in seconds) from the target frame
        @param varID <str>: variable ID
        @return var <numpy 1D-array>: size = nb node
        """
        nb_val = '>%if' % (self.nnode)
        pos_time2read = self.time.index(time2read)
        var = np.empty(self.nnode, dtype='float64')
        try:
            pos_var = self.varID.index(varID)
        except ValueError:
            print("ERROR: possible variables are {}".format(self.varID))
            sys.exit(1)

        log("read_var_in_frame (var={}): {}".format(varID, time2read))
        self.file.seek(self.headerSize + pos_time2read * self.frameSize + 12 + pos_var * (4 + 4 * self.nnode + 4), 0)
        self.file.read(4)
        return np.array(struct.unpack(nb_val, self.file.read(4 * self.nnode)))

    def read_vars_in_frame(self, time2read, varID_list):
        """
        @brief: read selected variables in a frame
        @param time2read <float>: simulation time (in seconds) from the target frame
        @param varID_list <str list>: list of variable ID
        @return var <numpy 2D-array>: shape = (nb target var, nb node)
        """
        nb_val = '>%if' % self.nnode
        pos_time2read = self.time.index(time2read)
        var = np.empty([len(varID_list), self.nnode], dtype='float64')

        if isinstance(varID_list, list):
            pos_vars = [self.varID.index(varID) for varID in varID_list]
        else:
            sys.exit("varID_list doit etre une liste ! Utiliser read_var_in_frame a la place")

        log("read_vars_in_frame (var={}): {}".format(varID_list, time2read))
        for i, pos_var in enumerate(pos_vars):
            self.file.seek(self.headerSize + pos_time2read * self.frameSize + 12 + pos_var * (4 + 4 * self.nnode + 4),
                           0)
            self.file.read(4)
            var[i] = struct.unpack(nb_val, self.file.read(4 * self.nnode))

        return var


class Write(Serafin):
    """Read Serafin binary file"""

    def __init__(self, filename, overwrite=False):
        if overwrite: mode = 'wb'
        else: mode = 'xb'
        Serafin.__init__(self, filename, mode)
        self.time = []
        print(mode)

    def __enter__(self):
        try:
            return Serafin.__enter__(self)
        except FileExistsError:
            sys.exit("File {} already exists (remove the file or change the option and then re-run the program)".format(self.fileName))

    def copy_header(self, other):
        """
        @brief: copy attributes (corresponding to Serafin header) of res2copy
        @param res2copy <Serafin>: Serafin object to copy
        """
        # FIXME: use copy.copy instead but problem with .file or other variables?
        self.title = other.title

        self.type = other.type
        self.varID = other.varID
        self.varNames = other.varNames
        self.varUnits = other.varUnits
        self._nbvar = other._nbvar
        self._nbvar2 = other._nbvar2

        self._param = other._param
        self.nplan = self._param[6]
        if (self._param[-1] == 1):
            self.date = other.date
        self.nelem = other.nelem
        self.nnode = other.nnode
        self.nnode2d = other.nnode2d
        self.ndp = other.ndp
        self._var_i = other._var_i

        self.ikle = other.ikle
        self.ipobo = other.ipobo
        self.x = other.x
        self.y = other.y

        self.type = other.type

    def assignVarIDs(self, var2assign):
        """Assign Serafin variables from a varID list"""
        self.varID = var2assign
        self.compute_nbvar()
        self.varNames = [varName(self.type, Serafin.lang, x) for x in self.varID]
        self.varUnits = [varUnit(self.type, Serafin.lang, x) for x in self.varID]
        log('Assigned variables {}'.format(var2assign))

    def addVarID(self, id, name, unit=""):
        """Add a single variable"""
        if len(name)>16:
            sys.exit("ERREUR: Le nom de la variable est trop long (limite de 16 caractères): '{}'".format(name))
        if len(unit)>16:
            sys.exit("ERREUR: Le nom de l'unité est trop long (limite de 16 caractères): '{}'".format(unit))
        self.varID.append(id)
        self.varNames.append(bytes(name.ljust(16), 'utf-8'))
        self.varUnits.append(bytes(unit.ljust(16), 'utf-8'))

    def compute_nbvar(self):
        self._nbvar = len(self.varID)

    def removeVarIDs(self, var2del):
        """Remove variables with a varID list"""
        for curVar in var2del: self.varID.remove(curVar)
        if len(self.varID) is 0:
            raise ValueError("No variables to export")
        self.assignVarIDs(self.varID)

    def write_header(self):
        """Write Serafin header from attributes"""
        # Title
        self.file.write(struct.pack('>i', 80))
        self.file.write(self.title)
        self.file.write(struct.pack('>i', 80))

        # _nbvar and _nbvar2
        self.file.write(struct.pack('>i', 2 * 4))
        self.file.write(struct.pack('>i', self._nbvar))
        self.file.write(struct.pack('>i', self._nbvar2))
        self.file.write(struct.pack('>i', 2 * 4))

        # Variable name
        for j in range(self._nbvar):
            self.file.write(struct.pack('>i', 2 * 16))
            self.file.write(self.varNames[j].ljust(16))
            self.file.write(self.varUnits[j].ljust(16))
            self.file.write(struct.pack('>i', 2 * 16))

        # Date
        self.file.write(struct.pack('>i', 10 * 4))
        self.file.write(struct.pack('>10i', *self._param))
        self.file.write(struct.pack('>i', 10 * 4))
        if self._param[-1] == 1:
            self.file.write(struct.pack('>i', 6 * 4))
            self.file.write(struct.pack('>6i', *self.date))
            self.file.write(struct.pack('>i', 6 * 4))

        # nelem, nnode, nplan and _var_i
        self.file.write(struct.pack('>i', 4 * 4))
        self.file.write(struct.pack('>i', self.nelem))
        self.file.write(struct.pack('>i', self.nnode))
        self.file.write(struct.pack('>i', self.ndp))
        self.file.write(struct.pack('>i', self._var_i))
        self.file.write(struct.pack('>i', 4 * 4))

        # IKLE
        self.file.write(struct.pack('>i', 4 * self.nelem * self.ndp))
        nb_val = '>%ii' % (self.nelem * self.ndp)
        self.file.write(struct.pack(nb_val, *self.ikle))
        self.file.write(struct.pack('>i', 4 * self.nelem * self.ndp))

        # IPOBO
        self.file.write(struct.pack('>i', 4 * self.nnode))
        nb_val = '>%ii' % (self.nnode)
        self.file.write(struct.pack(nb_val, *self.ipobo))
        self.file.write(struct.pack('>i', 4 * self.nnode))

        # X coordinates
        self.file.write(struct.pack('>i', 4 * self.nnode))
        nb_val = '>%if' % (self.nnode)
        self.file.write(struct.pack(nb_val, *self.x))
        self.file.write(struct.pack('>i', 4 * self.nnode))

        # Y coordinates
        self.file.write(struct.pack('>i', 4 * self.nnode))
        nb_val = '>%if' % (self.nnode)
        self.file.write(struct.pack(nb_val, *self.y))
        self.file.write(struct.pack('>i', 4 * self.nnode))


    def write_entire_frame(self, time, values):
        """
        @brief: write all variables/nodes values
        @param time <float>: time in second
        @param values <numpy 2D-array>: values to write
        """
        nb_val = '>%if' % (self.nnode)
        self.file.write(struct.pack('>i', 4))
        self.file.write(struct.pack('>f', time))
        self.file.write(struct.pack('>i', 4))
        for i in range(self._nbvar):
            self.file.write(struct.pack('>i', 4 * self.nnode))
            self.file.write(struct.pack(nb_val, *values[i]))
            self.file.write(struct.pack('>i', 4 * self.nnode))


def interpolate_from_ponderations(var, ponderations, points, varID_list, add_columns=None, digits=None):
    """
    ...
    """
    values = pd.DataFrame(points)

    # Add columns
    if add_columns is not None:
        for col, value in add_columns.items():
            values[col] = value

    # Add empty column values
    for varID in varID_list:
        values[varID] = np.nan

    # for ponderation in ponderations:
    row_values = np.zeros(var.shape[0])  # len(varID_list)
    for ptID, ponderation in ponderations:
        for node, coeff in ponderation.items():
            row_values = row_values + var[:,node]*coeff
            values.loc[ptID,varID_list] = row_values

    # Round values
    if digits is not None:
        for varID in varID_list:
            values[varID] = values[varID].map(lambda x: '%1.{}e'.format(digits-1) % x)  # e for exponential format (use f for decimal)

    return values

if __name__ == "__main__":
    global resin, resout, a
    inname = os.path.join('..', 'examples', 'r2d.slf')
    outname = os.path.join('..', 'examples', 'r3d_copy2.slf')
    with Read(inname) as resin:
        resin.readHeader()
        resin.get_time()
        resin.compute_element_barycenters()

        with Write(outname, True) as resout:
            resout.copyHeader(resin)
            resout.writeHeader()

            for time in resin.time:
                if time > 600: break
                values = resin.read_vars_in_frame(time, resin.varID)
                resout.writeEntireFrame(time, values)

