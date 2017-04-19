Conventions
===========

## Coding conventions
* encoding: utf-8
* linux line breaking
* shebang: `#!/usr/bin/python3`
* indent: 4 spaces
* comment language: english as much as possible

## Module imports
No import with *

### Common abbreviations
import numpy as np
import pandas as pd
import shapely.affinity as aff

## Logging
Use with following logging levels (with corresponding numeric value) :
* CRITICAL (40)
* WARNING (30)
* INFO (20)
* DEBUG (10)

## Command line arguments
Use `common/arg_command_line.py`

Some arguments are defined as general rule:
* -h, --help: get help and exit
* -f, --force: force overwrite output
* -v, --verbose: increase output verbosit

## Documentation
### Developer
TODO

### User
User documentation for command line scripts is described in the first docstring of the Python file.

This docstring is displayed with the help of the command line usage (with `-h` argument) and can be parsed to be included in a wiki (with Mediawiki syntax).

Un certain nombre de mot-cl�s :
* `@brief`: Description
* `@info`: Informations
* `@help`: Aide compl�te
* `@features`: Fonctionnalites
* `@prerequisites`: Pr�-requis
* `@warnings`: Avertissements

Exemple
```
@brief:
Texte court (sur une ligne) d�crivant l'objectif du script

@features:
Liste de quelques fonctionnalit�s.
Pour faciliter la lisibilit� ce bloc peut contenir une liste � puce par exemple :
* fonctionnalit� 1
* fonctionnalit� 2

@info:
Pr�cisions sur le fonctionnement et les options particuli�res

@warnings:
Pr�ciser les cas d'erreurs, les incompatibilit�s des options...
```
