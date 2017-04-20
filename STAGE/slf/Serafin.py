# -*- coding: utf-8 -*-

"""
Revised version of Serafin.py (under heavy construction)
Read/Write Serafin files and manipulate associated data
"""


import struct
import numpy as np
import os
import logging
from .SerafinSpecifications import SerafinVariableNames


FLOAT_TYPE = {'f': np.float32, 'd': np.float64}

module_logger = logging.getLogger(__name__)


class SerafinValidationError(Exception):
    """
    @brief: Custom exception for .slf file content check
    """
    pass


class SerafinRequestError(Exception):
    """
    @brief: Custom exception for requesting invalid values from .slf object
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
        self.file_size = None
        self.mode = mode
        self.file = None
        self.specifications = None

        # instance attributes contained in the file header
        self.is_2d = None
        self.title = None
        self.file_type = None  # SERAFIN or SERAFIND
        self.float_type = None  # 'i' or 'd'
        self.float_size = None  # 4 or 8
        self.np_float_type = None  # np.float32 or np.float64

        self.nb_var = None
        self.nb_var_quadratic = None
        self.var_names = []
        self.var_units = []
        self.var_IDs = []

        self._params = None
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

    def var_ID_to_index(self, var_ID):
        """
        @brief: Handle data request by variable ID
        @param var_ID <str>: the ID of the requested variable
        @return index <int> the index of the requested variable
        """
        if not self.var_IDs:
            module_logger.error('ERROR: (forgot read_header ?) var_IDs is empty')
            raise SerafinRequestError('(forgot read_header ?) Cannot extract variable from empty list.')
        try:
            index = self.var_IDs.index(var_ID)
        except ValueError:
            module_logger.error('ERROR: Variable ID not found')
            raise SerafinRequestError('Variable ID not found')
        return index

    def time_to_index(self, time_request):
        """
        @brief: Handle data request by time value
        @param time_request <str>: the ID of the requested time
        @return index <int> the index of the requested time in the time series
        """
        if not self.time:
            module_logger.error('ERROR: (forgot get_time ?) time is empty')
            raise SerafinRequestError('(forgot get_time r ?) Cannot find the requested time from empty list.')
        try:
            index = self.time.index(time_request)
        except ValueError:
            module_logger.error('ERROR: Requested time not found')
            raise SerafinRequestError('Requested time not found')
        return index


class Read(Serafin):
    """
    @brief: .slf file input stream
    """
    def __init__(self, filename, language):
        super().__init__(filename, 'rb', language)
        # additional attribute
        self.file_size = os.path.getsize(self.filename)
        module_logger.info('Reading the input file: "%s" of size %d bytes' % (filename, self.file_size))

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
        if self.file_type.decode('utf-8') == 'SERAFIND':
            self.float_type = 'd'
            self.float_size = 8
        else:
            self.float_type = 'f'
            self.float_size = 4
        self.np_float_type = FLOAT_TYPE[self.float_type]

        # Read the number of linear and quadratic variables
        self.file.read(4)
        self.nb_var = struct.unpack('>i', self.file.read(4))[0]
        self.nb_var_quadratic = struct.unpack('>i', self.file.read(4))[0]
        module_logger.debug('The file has %d variables' % self.nb_var)
        self.file.read(4)
        if self.nb_var_quadratic != 0:
            module_logger.error('ERROR: The number of quadratic variables is not equal to 0')
            raise SerafinValidationError('The number of quadratic variables is not equal to zero')

        # Read variable names and units
        for ivar in range(self.nb_var):
            self.file.read(4)
            self.var_names.append(self.file.read(16))
            self.var_units.append(self.file.read(16))
            self.file.read(4)

        # IPARAM: 10 integers (not all are useful...)
        self.file.read(4)
        self._params = struct.unpack('>10i', self.file.read(40))
        self.file.read(4)
        self.nb_planes = self._params[6]

        self.is_2d = (self.nb_planes == 0)

        if self._params[-1] == 1:
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
        module_logger.debug('The file is determined to be %s' % {True: '2D', False: '3D'}[self.is_2d])

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
        self.x = np.array(struct.unpack(nb_coord_values, self.file.read(coord_size)), dtype=self.np_float_type)
        self.file.read(4)

        # y coordinates
        self.file.read(4)
        self.y = np.array(struct.unpack(nb_coord_values, self.file.read(coord_size)), dtype=self.np_float_type)
        self.file.read(4)

        # Header size
        self.header_size = (80 + 8) + (8 + 8) + (self.nb_var * (8 + 32)) \
                                    + (40 + 8) + (self._params[-1] * ((6 * 4) + 8)) + (16 + 8) \
                                    + (nb_ikle_values * 4 + 8) + (self.nb_nodes * 4 + 8) + 2 * (coord_size + 8)
        # Frame size (all variable values for one time step)
        self.frame_size = 8 + self.float_size + (self.nb_var * (8 + self.nb_nodes * self.float_size))

        # Deduce the number of frames and test the integer division
        self.nb_frames = (self.file_size - self.header_size) // self.frame_size
        module_logger.debug('The file has %d frames of size %d bytes' % (self.nb_frames, self.frame_size))

        if self.nb_frames * self.frame_size != (self.file_size - self.header_size):
            module_logger.error('ERROR: The file size is not equal to (header size) + (nb frames) * (frame size)')
            raise SerafinValidationError('Something wrong with the file size (header and frames) check')

        # Deduce variable IDs (if known from specifications) from names
        for var_name, var_unit in zip(self.var_names, self.var_units):
            name = var_name.decode(encoding='utf-8')
            var_id = self.specifications.name_to_ID(name)
            if var_id is None:
                module_logger.warn('WARNING: The variable name "%s" is not known. The complete name will be used as ID' % name)
                self.specifications.add_new_var(var_name, var_unit)
                var_id = name
            self.var_IDs.append(var_id)

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

        module_logger.info('Finished reading the header')

    def get_time(self):
        """
        @brief: read the time in the .slf file
        """
        module_logger.debug('Reading the time series from the file')
        self.file.seek(self.header_size, 0)
        for i in range(self.nb_frames):
            self.file.read(4)
            self.time.append(struct.unpack('>%s' % self.float_type, self.file.read(self.float_size))[0])
            self.file.read(4)
            self.file.seek(self.frame_size - 8 - self.float_size, 1)

    def read_var_in_frame(self, time_to_read, var_ID):
        """
        @brief: read a single variable in a frame
        @param time_to_read <float>: simulation time (in seconds) from the target frame
        @param var_ID <str>: variable ID
        @return var <numpy 1D-array>: values of the variables, of length equal to the number of nodes
        """
        # appropriate warning when trying to exact a single variable
        if not isinstance(var_ID, str):
            module_logger.warn('ERROR: (use read_vars_in_frame instead?) Cannot read multiple variables')
            raise SerafinRequestError('(use read_vars_in_frame instead?) Cannot read multiple variables')

        nb_values = '>%i%s' % (self.nb_nodes, self.float_type)
        pos_time_to_read = self.time_to_index(time_to_read)
        module_logger.info('Reading the variable "%s" at time "%.1f"' % (var_ID, time_to_read))
        pos_var = self.var_ID_to_index(var_ID)
        self.file.seek(self.header_size + pos_time_to_read * self.frame_size
                                        + 8 + self.float_size + pos_var * (8 + 4 * self.nb_nodes), 0)
        self.file.read(4)
        return np.array(struct.unpack(nb_values, self.file.read(self.float_size * self.nb_nodes)),
                        dtype=self.np_float_type)

    def read_vars_in_frame(self, time_to_read, var_IDs):
        """
        @brief: read multiple variables in a frame
        @param time_to_read <float>: simulation time (in seconds) from the target frame
        @param var_IDs <str>: variable IDs
        @return var <numpy 2D-array>: values of variables of shape = (nb target vars, nb nodes)
        """
        # appropriate warning when trying to exact a single variable
        nb_target_vars = len(var_IDs)
        if nb_target_vars == 1:
            module_logger.warn('WARNING: (use read_var_in_frame instead?) Trying to extract a single variable')

        nb_values = '>%i%s' % (self.nb_nodes, self.float_type)
        pos_time_to_read = self.time_to_index(time_to_read)
        pos_target_vars = map(self.var_ID_to_index, var_IDs)
        var = np.empty([nb_target_vars, self.nb_nodes], dtype=self.np_float_type)
        for i, pos_var in enumerate(pos_target_vars):
            self.file.seek(self.header_size + pos_time_to_read * self.frame_size
                           + 8 + self.float_size + pos_var * (8 + self.float_size * self.nb_nodes),
                           0)
            self.file.read(4)
            var[i] = struct.unpack(nb_values, self.file.read(self.float_size * self.nb_nodes))
        return var


class Write(Serafin):
    """
    @brief: .slf file ouput stream
    """
    def __init__(self, filename, language, overwrite):
        mode = 'wb' if overwrite else 'xb'
        super().__init__(filename, mode, language)
        module_logger.info('Writing the output file: "%s"' % filename)

    def __enter__(self):
        try:
            return Serafin.__enter__(self)
        except FileExistsError:
            module_logger.error('ERROR: Cannot overwrite existing file')
            raise FileExistsError('File {} already exists (remove the file or change the option '
                                  'and then re-run the program)'.format(self.filename))

    def copy_header(self, other):
        """
        @brief: copy attributes of another Serafin object with the SAME header
        @param other <Serafin>: Serafin object to copy
        """
        self.title = other.title
        self.file_type = other.file_type
        self.float_size = other.float_size
        self.float_type = other.float_type
        self.np_float_type = other.np_float_type
        self.is_2d = other.is_2d

        # Copy lists
        self.var_IDs = other.var_IDs[:]
        self.var_names = other.var_names[:]
        self.var_units = other.var_units[:]

        # Copy integers and tuples of integers
        self.nb_var = other.nb_var
        self.nb_var_quadratic = other.nb_var_quadratic
        self._params = other._params
        self.nb_planes = self.nb_planes
        if other.date is not None:
            self.date = other.date
        self.nb_elements = other.nb_elements
        self.nb_nodes = other.nb_nodes
        self.nb_nodes_2d = other.nb_nodes_2d
        self.nb_nodes_per_elem = other.nb_nodes_per_elem

        # Copy numpy arrays
        self.ikle = np.copy(other.ikle)
        self.ipobo = np.copy(other.ipobo)
        self.x = np.copy(other.x)
        self.y = np.copy(other.y)

    def write_header(self):
        """
        @brief: Write Serafin header from attributes
        """
        # Title and file type
        self.file.write(struct.pack('>i', 80))
        self.file.write(self.title)
        self.file.write(self.file_type)
        self.file.write(struct.pack('>i', 80))

        # Number of variables
        self.file.write(struct.pack('>i', 8))
        self.file.write(struct.pack('>i', self.nb_var))
        self.file.write(struct.pack('>i', self.nb_var_quadratic))
        self.file.write(struct.pack('>i', 8))

        # Variable names and units
        for j in range(self.nb_var):
            self.file.write(struct.pack('>i', 2 * 16))
            self.file.write(self.var_names[j].ljust(16))
            self.file.write(self.var_units[j].ljust(16))
            self.file.write(struct.pack('>i', 2 * 16))

        # Date
        self.file.write(struct.pack('>i', 10 * 4))
        self.file.write(struct.pack('>10i', *self._params))
        self.file.write(struct.pack('>i', 10 * 4))
        if self._params[-1] == 1:
            self.file.write(struct.pack('>i', 6 * 4))
            self.file.write(struct.pack('>6i', *self.date))
            self.file.write(struct.pack('>i', 6 * 4))

        # Number of elements, of nodes, of nodes per element and the magic number
        self.file.write(struct.pack('>i', 4 * 4))
        self.file.write(struct.pack('>i', self.nb_elements))
        self.file.write(struct.pack('>i', self.nb_nodes))
        self.file.write(struct.pack('>i', self.nb_nodes_per_elem))
        self.file.write(struct.pack('>i', 1))  # magic number
        self.file.write(struct.pack('>i', 4 * 4))

        # IKLE
        nb_ikle_values = self.nb_elements * self.nb_nodes_per_elem
        self.file.write(struct.pack('>i', 4 * nb_ikle_values))
        nb_val = '>%ii' % nb_ikle_values
        self.file.write(struct.pack(nb_val, *self.ikle))
        self.file.write(struct.pack('>i', 4 * nb_ikle_values))

        # IPOBO
        self.file.write(struct.pack('>i', 4 * self.nb_nodes))
        nb_val = '>%ii' % self.nb_nodes
        self.file.write(struct.pack(nb_val, *self.ipobo))
        self.file.write(struct.pack('>i', 4 * self.nb_nodes))

        # X coordinates
        self.file.write(struct.pack('>i', 4 * self.nb_nodes))
        nb_val = '>%i%s' % (self.nb_nodes, self.float_type)
        self.file.write(struct.pack(nb_val, *self.x))
        self.file.write(struct.pack('>i', 4 * self.nb_nodes))

        # Y coordinates
        self.file.write(struct.pack('>i', 4 * self.nb_nodes))
        nb_val = '>%i%s' % (self.nb_nodes, self.float_type)
        self.file.write(struct.pack(nb_val, *self.y))
        self.file.write(struct.pack('>i', 4 * self.nb_nodes))

    def write_entire_frame(self, time_to_write, values):
        """
        @brief: write all variables/nodes values
        @param time_to_write <float>: time in second
        @param values <numpy 2D-array>: values to write
        """
        nb_values = '>%i%s' % (self.nb_nodes, self.float_type)
        self.file.write(struct.pack('>i', 4))
        self.file.write(struct.pack('>%s' % self.float_type, time_to_write))
        self.file.write(struct.pack('>i', 4))

        if self.nb_var == 1:  # special case when values is 1D-array
            self.file.write(struct.pack('>i', self.float_size * self.nb_nodes))
            self.file.write(struct.pack(nb_values, *values))
            self.file.write(struct.pack('>i', self.float_size * self.nb_nodes))

        else:
            for i in range(self.nb_var):
                self.file.write(struct.pack('>i', self.float_size * self.nb_nodes))
                self.file.write(struct.pack(nb_values, *values[i]))
                self.file.write(struct.pack('>i', self.float_size * self.nb_nodes))

