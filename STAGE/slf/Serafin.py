# -*- coding: utf-8 -*-

"""
Revised version of Serafin.py (in construction)
Read/Write Serafin files and manipulate associated data
"""


import sys
import struct
import numpy as np
import os
import logging
from .SerafinSpecifications import SerafinVariableNames

module_logger = logging.getLogger(__name__)


class SerafinValidationError(Exception):
    """
    @brief: Custom exception for .slf file content check
    """
    pass


class Serafin:
    """
    @brief: A Serafin object corresponds to a single .slf in file IO stream
    """
    def __init__(self, filename, mode, language):
        self.language = language
        self.mode = mode

        self.filename = filename
        self.file_size = os.path.getsize(self.filename)
        self.mode = mode
        self.file = None
        self.specifications = None

        # instance attributes contained in the file header
        self.is_2d = None
        self.title = None
        self.file_type = None  # SERAFIN or SERAFIND
        self.float_type = None  # 'i' or 'd'
        self.float_size = None  # 4 or 8

        self._nb_var = None
        self._nb_var_quadratic = None
        self.var_names = []
        self.var_units = []
        self.var_IDs = []
        self._param = None

        self.nb_planes = None
        self.date = None

        self.nb_elements = None
        self.nb_nodes = None
        self.nb_nodes_2d = None
        self.nb_nodes_per_elem = None

        self.ikle = None
        self.ikle_2d = None
        self.ipobo = None

        self.x = None
        self.y = None

        self.header_size = None
        self.frame_size = None
        self.nb_frames = None

        self.time = []

    def __enter__(self):
        self.file = open(self.filename, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        return False


class Read(Serafin):
    def __init__(self, filename, language='fr'):
        super().__init__(filename, 'rb', language)
        module_logger.info('Reading the input file: "%s"' % filename)

    def read_header(self):
        """
        @brief: read the .slf file header
        """
        # Read title
        self.file.read(4)
        self.title = self.file.read(72)
        self.file_type = self.file.read(8)
        module_logger.debug('The file type is: "%s"' % self.file_type.decode('utf-8'))
        self.file.read(4)
        if self.file_type.decode('utf-8') == 'SERAFIN ':
            self.float_type = 'i'
            self.float_size = 4
        else:
            self.float_type = 'd'
            self.float_size = 8

        # Read the number of linear and quadratic variables
        self.file.read(4)
        self._nb_var = struct.unpack('>i', self.file.read(4))[0]
        self._nb_var_quadratic = struct.unpack('>i', self.file.read(4))[0]
        module_logger.debug('The file has %d variables' % self._nb_var)
        self.file.read(4)
        if self._nb_var_quadratic != 0:
            module_logger.error('ERROR: The number of quadratic variables is not equal to 0')
            raise SerafinValidationError('The number of quadratic variables is not equal to zero')

        # Read variable names and units
        for ivar in range(self._nb_var):
            self.file.read(4)
            self.var_names.append(self.file.read(16))
            self.var_units.append(self.file.read(16))
            self.file.read(4)

        # IPARAM: 10 integers (not all are useful...)
        self.file.read(4)
        self._param = struct.unpack('>10i', self.file.read(40))
        self.file.read(4)
        self.nb_planes = self._param[6]

        self.is_2d = (self.nb_planes == 0)

        if self._param[-1] == 1:
            # Read 6 integers which correspond to simulation starting date
            self.file.read(4)
            self.date = struct.unpack('>6i', self.file.read(6 * 4))
            self.file.read(4)

        # 4 very important integers
        self.file.read(4)
        self.nb_elements = struct.unpack('>i', self.file.read(4))[0]
        self.nb_nodes = struct.unpack('>i', self.file.read(4))[0]
        self.nb_nodes_per_elem = struct.unpack('>i', self.file.read(4))[0]
        test_value = struct.unpack('>i', self.file.read(4))[0]
        if test_value != 1:
            module_logger.error('ERROR: the magic number is not equal to 1')
            raise SerafinValidationError('The magic number is not equal to one')
        self.file.read(4)

        # verify data consistence and determine 2D or 3D
        if self.is_2d:
            if self.nb_nodes_per_elem != 3:
                raise SerafinValidationError('ERROR: Unknown mesh type')
        else:
            if self.nb_nodes_per_elem != 6:
                module_logger.error('ERROR: The number of nodes per element not equal to 6')
            if self.nb_planes < 2:
                module_logger.error('ERROR: The number of planes is less than 2')
                raise SerafinValidationError('Unknown mesh type')

        # construct the variable name specifications
        self.specifications = SerafinVariableNames(self.is_2d, self.language)

        # determine the number of nodes in 2D
        if self.is_2d:
            self.nb_nodes_2d = self.nb_nodes
        else:
            self.nb_nodes_2d = self.nb_nodes // self.nb_planes

        # IKLE
        self.file.read(4)
        nb_ikle_values = self.nb_elements * self.nb_nodes_per_elem
        self.ikle = np.array(struct.unpack('>%ii' % nb_ikle_values,
                                           self.file.read(4 * nb_ikle_values)))
        self.file.read(4)

        # IPOBO
        self.file.read(4)
        nb_ipobo_values = '>%ii' % self.nb_nodes
        self.ipobo = np.array(struct.unpack(nb_ipobo_values, self.file.read(4 * self.nb_nodes)))
        self.file.read(4)

        # x coordinates
        self.file.read(4)
        nb_coord_values = '>%i%s' % (self.nb_nodes, self.float_type)
        coord_size = self.nb_nodes * self.float_size
        self.x = np.array(struct.unpack(nb_coord_values, self.file.read(coord_size)))
        self.file.read(4)

        # y coordinates
        self.file.read(4)
        self.y = np.array(struct.unpack(nb_coord_values, self.file.read(coord_size)))
        self.file.read(4)

        # Header size
        self.header_size = (80 + 8) + (8 + 8) + (self._nb_var * (8 + 32)) \
                                    + (40 + 8) + (self._param[-1] * ((6 * 4) + 8)) + (16 + 8) \
                                    + (nb_ikle_values * 4 + 8) + (self.nb_nodes * 4 + 8) + 2 * (coord_size + 8)
        # Frame size (all variable values for one time step)
        self.frame_size = 12 + (self._nb_var * (8 + int(self.nb_nodes) * 4))

        # Deduce the number of frames and test the integer division
        self.nb_frames = (self.file_size - self.header_size) // self.frame_size
        if self.nb_frames * self.frame_size != (self.file_size - self.header_size):
            module_logger.error('ERROR: The file size is not equal to (header size) + (nb frames) * (frame size)')
            raise SerafinValidationError('Something wrong with the file size / header size / frame size')

        # Deduce variable IDs (abbreviation of variables)
        for var_name in self.var_names:
            var_id = self.specifications.find(var_name.decode(encoding='utf-8'))
            self.var_IDs.append(var_id)
        assert len(self.var_IDs) == len(self.var_names), 'Could not find a varID for all varNames'

        # Build ikle2d
        if not self.is_2d:
            ikle = self.ikle.reshape(self.nb_nodes_per_elem, self.nb_elements)  # 3D: ikle has different shape thant 2D
            self.ikle_2d = np.empty([self.nb_elements // (self.nb_planes - 1), 3], dtype=int)
            nb_lines = self.ikle_2d.shape[0]
            # test the integer division
            if nb_lines * (self.nb_planes - 1) != self.nb_elements:
                module_logger.error('ERROR: (3D) The number of elements is not divisible by (number of planes - 1)')
                raise SerafinValidationError('Something wrong with ikle 3D dimension')
            for i in range(nb_lines):
                self.ikle_2d[i] = ikle[[0, 1, 2], i]   # first three rows = bottom frame
        else:
            self.ikle_2d = self.ikle.reshape(self.nb_elements, self.nb_nodes_per_elem)

    def get_time(self):
        """
        @brief: read the time in the .slf file
        """
        self.file.seek(self.header_size, 0)
        for i in range(self.nb_frames):
            self.file.read(4)
            self.time.append(struct.unpack('>f', self.file.read(4))[0])
            self.file.read(4)
            self.file.seek(self.frame_size - 12, 1)

    def read_var_in_frame(self, time_to_read, var_ID):
        """
        @brief: read a single variable in a frame
        @param time_to_read <float>: simulation time (in seconds) from the target frame
        @param var_ID <str>: variable ID
        @return var <numpy 1D-array>: values of the variables, of length equal to the number of nodes
        """
        # check if the time is already read before
        if not self.time:
            self.get_time()
        nb_values = '>%if' % self.nb_nodes
        pos_time_to_read = self.time.index(time_to_read)
        module_logger.info('Reading the variable "%s" at time "%.1f"' % (var_ID, time_to_read))
        try:
            pos_var = self.var_IDs.index(var_ID)
        except ValueError:
            module_logger.error('Requested variable ID not found')
            raise ValueError('ERROR: Possible variables are {}'.format(self.var_IDs))

        self.file.seek(self.header_size + pos_time_to_read * self.frame_size
                                        + 12 + pos_var * (8 + 4 * self.nb_nodes), 0)
        self.file.read(4)
        return np.array(struct.unpack(nb_values, self.file.read(4 * self.nb_nodes)))


class Write(Serafin):
    def __init__(self, filename, overwrite=False, language='fr'):
        mode = 'wb' if overwrite else 'xb'
        super().__init__(filename, mode, language)

    def __enter__(self):
        try:
            return Serafin.__enter__(self)
        except FileExistsError:
            sys.exit('File {} already exists (remove the file or change '
                     'the option and then re-run the program)'.format(self.filename))


