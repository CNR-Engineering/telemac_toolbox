PyTelTools
==========

# Python
Version: tested with 3.4
Dependencies: numpy, pandas, ...

# Conventions
* encoding: utf-8
* linux line breaking
* shebang: #!/usr/bin/python3
* indent: 4 spaces
* comment language: english as much as possible
* use argparse as much as possible. Some classical arguments:
    * -h, --help: get help and exit
    * -f, --force: force overwrite output
    * -v, --verbose: increase output verbosit

# Classes
* Serafin
* Read(Serafin)
* Write(Serafin)

# TODO
## Bugs, optimization
* Exception and sys.exit
* documentation and argparse
* see FIXME
* change function names (underscore, ...)
* new class Mesh??
* examples
* sampling and interpolation:
    * n polylignes brutes
    * +maillage => n objets XX
    * +valeurs => tableau csv

## Other usefull scripts to do
* slf_int3d.py (at given plan, elevation from above bottom or below free surface)
* slf_3dto2d.py : subset a single layer (constitute SL,B,...) OR subset max/min/mean/median? over the deepth ?
* slf_waterline.py
* slf_flux.py
* visu? export graph...
