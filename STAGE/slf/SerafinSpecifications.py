# -*- coding: utf-8 -*-

import os
import pandas as pd
import bisect


def index(a, x):
    """Return the index of the leftmost value exactly equal to x"""
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    raise ValueError


class SerafinVariableNames:
    """
    manage variables names (fr/eng): loading, adding and removing
    """
    def __init__(self, is_2d, language):
        self.language = language
        base_folder = os.path.dirname(os.path.realpath(__file__))
        if is_2d:
            self.var_table = pd.read_csv(os.path.join(base_folder, 'data', 'Serafin_var2D.csv'),
                                         index_col=0, header=0, sep=',')
        else:
            self.var_table = pd.read_csv(os.path.join(base_folder, 'data', 'Serafin_var3D.csv'),
                                         index_col=0, header=0, sep=',')
        self.var_table.sort_values(self.language, inplace=True)

    def find(self, var_name):
        var_index = index(self.var_table[self.language], var_name)
        var_ID = self.var_table.index.values[var_index]
        return var_ID



