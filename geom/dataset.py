# -*- coding: utf-8 -*-

import collections, sys
import shapely.geometry as geom
from time import gmtime, strftime

# Parseur (avec lecture/écriture) pour les formats de fichier :
# * BlueKenue
#     * i2s
#     * i3s
#     * xyz
# * sinusx (sx)

# Structure/héritage de classes :
# WriteFile
# |- BlueKenueWrite_xyz
# |- BlueKenueWrite_i2s
# |- BlueKenueWrite_i3s
# |- Write_SX
# BlueKenue
# |- BlueKenueRead
#   |- BlueKenueRead_xyz
#   |- BlueKenueRead_i2s
#   |- BlueKenueRead_i3s
# |- BlueKenueWrite
#   |- BlueKenueWrite_xyz
#   |- BlueKenueWrite_i2s
#   |- BlueKenue_Write_i3s
# Read_SX (TODO)

#TODO
# * Read_SX
# * validateur de fichiers
# * take value into account "value" (in i2s/i3s files)
# * append (ex: LineString in MultiLineString?)
# * except/check data before writing (None, empty)

class WriteFile:
    """Writable files"""
    eol = '\n'
    digits = 4  # float values (e.g. x,y,z)

    def __init__(self, force, digits=None):
        # Overwrite output file if force is True
        if force:
            self.mode = 'w'
        else:
            self.mode = 'x'

        # Digits
        if digits is None:
            self.digits = WriteFile.digits
        else:
            self.digits = digits

    def write(self, content):
        """Write content with ending line breaking"""
        self.file.write(content+WriteFile.eol)


class BlueKenue:
    """BlueKenue filetype"""
    # mode attribute HAS TO be present !
    # /!\ Keywords should be unique and should not contain any space
    def __init__(self, filename):
        self.filename = filename

        self.keywords = collections.OrderedDict()
        self.data_type = None
        self.file_type = None

    def __enter__(self):
        print(">>> Open {} in {} mode".format(self.filename, self.mode))
        self.file = open(self.filename, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("<<< Close {}".format(self.filename))
        self.file.close()
        return False

    def assign_types(self, file_type, data_type):
        """Assign file_type and data_type"""
        self.file_type = file_type
        self.data_type = data_type

    def write_header(self):
        """Write BlueKenue header with keywords"""
        # Construction is always:
        # * hr
        # * FileType keyword
        # * comments
        # * other keywords
        # * end of header
        self.write("#########################################################################")
        self.write(":FileType {}".format(self.file_type))
        self.write("# Canadian Hydraulics Centre/National Research Council (c) 1998-2012")
        self.write("# DataType                 {}".format(self.data_type))
        self.write("#")

        # Write others keywords and value
        key_width = 25
        for key, value in self.keywords.items():
            self.write(":{} {}".format(key.ljust(key_width), value))

        self.write(":EndHeader")

    def auto_keywords(self):
        self.keywords['Application'] = 'scripts_LDN'
        self.keywords['CreationDate'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())  #FIXME: arrange appearance

    def copy_header(self, other):
        self.data_type = other.data_type
        self.file_type = other.file_type
        self.keywords = other.keywords


class BlueKenueRead(BlueKenue):

    def __init__(self, filename):
        self.mode = 'r'
        BlueKenue.__init__(self, filename)

    def read_header(self):
        """Read BlueKenue entire file (header and data)"""
        # data_type, file_type, keywords

        line = None
        while line != 'EndHeader':  #FIXME: dangerous if not valid file (not EndHeader... infinite loop)
            line = self.file.readline().replace('\n','')

            if line.startswith('#'):
                if 'DataType' in line:
                    self.data_type = line.split(' ', 2)[2].strip()
                # else:
                #     Ignore commented line

            elif line.startswith(':'):
                line = line[1:]  # remove leading colon character
                if line.startswith('FileType'):
                    self.file_type = line.split(' ', 1)[1]
                elif line != 'EndHeader':
                    (key, long_value) = line.split(' ', 1)
                    self.keywords[key] = long_value.strip()

            else: #BRICOLAGE: eviter boucle infinie
                line = 'EndHeader'

    def _iter(self, ndim):
        """Iterate over polylines: for (value, LineString) in ..."""
        while True:
            line = self.file.readline()
            if line is '': break  # end of file... break the infinte loop
            line = line.replace('\n','').split(' ')
            try:
                nb_pt = int(line[0])
            except:
                sys.exit("Le nombre '{}' n'est pas convertible en entier".format(line[0]))
            value = float(line[1])
            cur_polyline = []
            for i in range(nb_pt):
                line = self.file.readline().replace('\n','')
                coord = tuple(float(x) for x in line.split(' '))

                if len(coord) != ndim:
                    print("ERROR in reading content:")
                    print("number of values/columns is {} but {} was expected.".format(len(coord), ndim))
                    print("Guilty line is display below:")
                    print(line)
                    sys.exit(1)
                cur_polyline.append(coord)

            yield (value, geom.LineString(cur_polyline))
        # cur_line = []
        # npt_remaining = 0  # for 1st iteration
        # value = None
        # for line in self.file:
        #     line = line.replace('\n', '')
        #
        #     if npt_remaining == 0:
        #         # New polyline
        #         npt_remaining = int(line.split(' ', 1)[0])
        #         value = float(line.split(' ', 1)[1])
        #         if len(cur_line) != 0:
        #             # Add previous polyline if not empty (to ignore first iteration)
        #             print(value)
        #             yield (value, geom.LineString(cur_line))
        #         cur_line = []
        #
        #     else:
        #         # Read coordinates
        #         coord = tuple(float(x) for x in line.split(' '))
        #
        #         if len(coord) != ndim:
        #             print("ERROR in reading content:")
        #             print("number of values/columns is {} but {} was expected.".format(len(coord), ndim))
        #             print("Guilty line is display below:")
        #             print(line)
        #             sys.exit(1)
        #
        #         cur_line.append(coord)
        #         npt_remaining -= 1
        #
        # yield (value, geom.LineString(cur_line))


class BlueKenueWrite_xyz(WriteFile, BlueKenue):
    def __init__(self, filename, force=False, digits=WriteFile.digits):
        WriteFile.__init__(self, force, digits)
        BlueKenue.__init__(self, filename)
        self.file_type = 'xyz  ASCII  EnSim 1.0'
        self.data_type = 'XYZ Point Set'

    def write_point(self, point, default_z=0.0):
        if not point.has_z:
            coord = (point.x, point.y, default_z)
        else:
            coord = (point.x, point.y, point.z)
        self.write(' '.join(str(round(f, self.digits)) for f in coord))

    def write_points(self, points):
        for point in points:
            self.write_point(point)


class BlueKenueRead_xyz(BlueKenueRead):
    def __init__(self, filename):
        BlueKenueRead.__init__(self, filename)

    def iter_on_points(self):
        for line in self.file:
            coord = line.split()
            if len(coord) != 3:
                sys.exit("A point has not 3 coordinates (x,y,z)...")
            coord = [float(x) for x in coord]
            yield geom.Point(coord)


class BlueKenueRead_i2s(BlueKenueRead):
    def iter_on_polylines(self):
        return self._iter(2)


class BlueKenueRead_i3s(BlueKenueRead):
    def iter_on_polylines(self):
        return self._iter(3)


class BlueKenueWrite_i2s(WriteFile, BlueKenue):
    def __init__(self, filename, force=False, digits=WriteFile.digits):
        WriteFile.__init__(self, force, digits)
        BlueKenue.__init__(self, filename)
        self.file_type = 'i2s  ASCII  EnSim 1.0'
        self.data_type = '2D Line Set'

    def write_polyline(self, polyline, value=0):
        coords = polyline.coords
        # if polyline.is_ring:
        #     # Duplicate starting point
        #     coords.append(coords[0])
        self.write("{} {}".format(len(coords), value))
        for point in coords:
            self.write(' '.join(str(round(f, self.digits)) for f in point[0:2]))  # Ignore Z value


class BlueKenueWrite_i3s(WriteFile, BlueKenue):
    def __init__(self, filename, force=False, digits=WriteFile.digits):
        WriteFile.__init__(self, force, digits)
        BlueKenue.__init__(self, filename)
        self.file_type = 'i3s  ASCII  EnSim 1.0'
        self.data_type = '3D Line Set'

    def write_polyline(self, polyline, value=0):
        self.write("{} {}".format(len(polyline.coords), value))
        for point in polyline.coords:
            if polyline.has_z:
                self.write(' '.join(str(round(f, self.digits)) for f in point))
            else:
                self.write(' '.join(str(round(f, self.digits)) for f in point) + ' {}'.format(str(round(0.0, self.digits))))


class Write_SX(WriteFile):
    def __init__(self, filename, force=False, digits=WriteFile.digits):
        WriteFile.__init__(self, force, digits)
        self.filename = filename

    def __enter__(self):
        print(">>> Open {} in {} mode".format(self.filename, self.mode))
        self.file = open(self.filename, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("<<< Close {}".format(self.filename))
        self.file.close()
        return False

    def write_header(self):
        """Write SX file header"""
        self.write("C")
        self.write("C Fichier cree par un script python3 (by LDN)")
        self.write("C")

    def write_polyline(self, polyline, id=None):
        """Write a single polyline with its header"""
        # FIXME: use official format??? B C Niveau?
        if id is not None:
            self.write("C element {}".format(id))
        self.write("B C")
        for point in polyline.coords:
            if len(point) == 3:
                self.write(' '.join(str(round(f, self.digits)) for f in point))
            else:  # has no Z
                self.write(' '.join(str(round(f, self.digits)) for f in point) + ' {}'.format(str(round(0.0, self.digits))))




if __name__ == "__main__":
# if True:
    # COPYING: checking READING AND WRITING
    # with BlueKenueRead_i3s('old/ligne3d_fond.i3s') as in_i3s:
    #     in_i3s.read_header()
    #     with BlueKenueWrite_i3s('old/ligne3d_fond_out.i3s', True) as out_i3s:
    #         out_i3s.copy_header(in_i3s)
    #         out_i3s.auto_keywords()
    #         out_i3s.write_header()
    #         for value, polyline in in_i3s.iter_on_polylines():
    #             out_i3s.write_polyline(polyline, value)

    # COPYING: checking READING AND WRITING
    with BlueKenueRead_i2s('../examples/contour_pour_submesh.i2s') as in_i2s:
        in_i2s.read_header()
        with BlueKenueWrite_i2s('../examples/contour_pour_submesh_copy.i2s', True) as out_i2s:
            out_i2s.copy_header(in_i2s)
            out_i2s.auto_keywords()
            out_i2s.write_header()
            for value, polyline in in_i2s.iter_on_polylines():
                out_i2s.write_polyline(polyline, value)
                toto = polyline

    # WRITING FROM SCRATCH
    # with BlueKenueWrite_xyz('old/test.xyz') as out_xyz:
    #     out_xyz.auto_keywords()
    #     out_xyz.write_header()
    #     out_xyz.write_points(geom.MultiPoint([(0,0,0), (1,1,1), (2,2,2), (3,3.4,3.5)]))

    # with BlueKenueWrite_i2s('old/test.i2s') as out_i2s:
    #     out_i2s.auto_keywords()
    #     out_i2s.write_header()
    #     out_i2s.write_polyline(geom.LineString([(0,0.1345678901), (1,1), (2,2), (3,3.12345678901234)]))

    # with BlueKenue_Write_i3s('old/test.i3s') as out_i3s:
    #     out_i3s.auto_keywords()
    #     out_i3s.write_header()
    #     out_i3s.write_polyline(geom.LineString([(0,0,0), (1,1,1), (2,2,2), (3,3.4,3.12345678901234)]))

    # with Write_SX('old/test_single.sx') as out_sx:
    #     out_sx.write_header()
    #     out_sx.write_polyline(geom.LineString([(0,0,0), (1,1,1), (2,2,2), (3,3.4,3.12345678901234)]))

    # with Write_SX('old/test_multi.sx') as out_sx:
    #     out_sx.write_header()
    #     out_sx.write_multi_polylines(geom.MultiLineString([((0, 0, 0), (1, 1, 1)), ((-1, 0, -0.001), (1, 0, 1.002415678e20))]))
