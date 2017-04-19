#!/usr/bin/python3
"""
@brief:
Echantionner une polyligne...
"""

from shapely.geometry import Point

from common.arg_command_line import myargparse
from geom.dataset import BlueKenueRead_i2s, BlueKenueWrite_i2s


parser = myargparse(description=__doc__)
parser.add_argument("inname", help="fichier i2s d'entrée")
parser.add_argument("outname", help="fichier i2s de sortie")
args = parser.parse_args()

with BlueKenueRead_i2s(args.inname) as in_i2s:
    in_i2s.read_header()
    
    wi


