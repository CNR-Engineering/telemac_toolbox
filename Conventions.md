Conventions
===========

## Coding conventions
* encoding: utf-8
* linux line breaking
* shebang: `#!/usr/bin/python3`
* indent: 4 spaces
* comment language: English
* naming: lowercase_with_underscores for variables, functions and method names

## Module imports
No import with *

### Common abbreviations
```python
import numpy as np
import pandas as pd
import shapely.affinity as aff
```

## Logging
Use with following logging levels (with corresponding numeric value) :
* CRITICAL (40)
* WARNING (30)
* INFO (20)
* DEBUG (10)

## Command line arguments
Use `common/arg_command_line.py`

Some arguments are defined as general rule:
* `-h`, `--help`: get help and exit
* `-f`, `--force`: force overwrite output
* `-v`, `--verbose`: increase output verbosity

## Documentation
### Developer
TODO

### User
User documentation for command line scripts is described in the first docstring of the Python file.

This docstring is displayed with the help of the command line usage (with `-h` argument) and can be parsed to be included in a wiki (with Mediawiki syntax).

Un certain nombre de mot-clés :
* `@brief`: Description
* `@info`: Informations
* `@help`: Aide complète
* `@features`: Fonctionnalites
* `@prerequisites`: Pré-requis
* `@warnings`: Avertissements

Exemple
```markdown
@brief:
Texte court (sur une ligne) décrivant l'objectif du script

@features:
Liste de quelques fonctionnalités.
Pour faciliter la lisibilité ce bloc peut contenir une liste à puce par exemple :
* fonctionnalité 1
* fonctionnalité 2

@info:
Précisions sur le fonctionnement et les options particulières

@warnings:
Préciser les cas d'erreurs, les incompatibilités des options...
```
