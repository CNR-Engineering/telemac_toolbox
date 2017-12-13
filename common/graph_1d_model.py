# Branches
TYPE_BRANCHES = {
    'BrancheBarrageFilEau': '15',
    # 'BrancheBarrageGenerique': '?',
    'BrancheSeuilTransversal': '2',
    'BrancheStrickler': '6',
    'BrancheSeuilLateral': '4',
    'BrancheSaintVenant': '20',
    'BranchePdc': '1',
    'BrancheOrifice': '5',
    # 'BrancheNiveauxAssocies': '?',
    }

ARROWHEAD = {
    '2': 'curve',
    '4': 'tee',
    '5': 'odot',
    '6': 'diamond',
    '15': 'box',
    'default': 'normal'
    # 'BrancheNiveauxAssocies': '?',
}

# Couleurs selon le type de branche
COLORS = {
    '4': 'darkgreen',
    '5': 'green',
    '6': 'purple',
    '9': 'navy',
    '20':'blue',
    'default': 'black'
}

# Taille de la branche
SIZE = {
    '9': 4,
    '15': 4,
    '20': 4,
    'default': 2
}


def key_from_constant(key, CONSTANT):
    """Retourne la valeur de key du dictionnanire CONSTANT"""
    try:
        return CONSTANT[key]
    except KeyError:
        try:
            return CONSTANT['default']
        except KeyError:
            sys.exit("La clé '{}' n'existe pas".format(key))
