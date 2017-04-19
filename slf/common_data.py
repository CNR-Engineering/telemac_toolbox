import os
import pandas as pd

# Manage verbosity
verbose = True
def log(text):
    if verbose: print(text)

baseFolder = os.path.dirname(os.path.realpath(__file__))
var2D = pd.read_csv(os.path.join(baseFolder, 'data', 'Serafin_var2D.csv'), index_col=0, header=0, sep=',')
var3D = pd.read_csv(os.path.join(baseFolder, 'data', 'Serafin_var3D.csv'), index_col=0, header=0, sep=',')

def varTable(type):
    if type is '2D':
        return var2D
    elif type is '3D':
        return var3D

def stringForSerafin(string):
    return bytes(string.ljust(16), encoding='utf-8')

def varName(type, lang, varID):
    if type is '2D':
        return stringForSerafin(var2D[lang][varID])
    elif type is '3D':
        return stringForSerafin(var3D[lang][varID])

def varUnit(type, lang, varID):
    if type is '2D':
        return stringForSerafin(var2D['unit'][varID])
    elif type is '3D':
        return stringForSerafin(var3D['unit'][varID])

#
# telemac3d/sources/nomvar_telemac3d.f (V6P3)
#
# VARIABLES 3D DE TELEMAC-3D
#
#'Z':  b"ELEVATION Z     M               ",
#'U':  b"VELOCITY U      M/S             ",
#'V':  b"VELOCITY V      M/S             ",
#'W':  b"VELOCITY W      M/S             ",
#'NUX':b"NUX FOR VELOCITYM2/S            ",
#'NUY':b"NUY FOR VELOCITYM2/S            ",
#'NUZ':b"NUZ FOR VELOCITYM2/S            ",
#'K':  b"TURBULENT ENERGYJOULE/KG        ",
#'EPS':b"DISSIPATION     WATT/KG         ",
#'RI': b"RICHARDSON NUMB                 ",
#'RHO':b"RELATIVE DENSITY                ",
#'DP': b"DYNAMIC PRESSUREPA              ",
#'':   b"HYDROSTATIC PRESPA              ",
#'':   b"U ADVECTION     M/S             ",
#'':   b"V ADVECTION     M/S             ",
#'':   b"W ADVECTION     M/S             ",
#'':   b"????????????????????????????????",
#'':   b"DM1                             ",
#'':   b"DHHN            M               ",
#'':   b"UCONVC          M/S             ",
#'':   b"VCONVC          M/S             ",
#'':   b"UD              M/S             ",
#'':   b"VD              M/S             ",
#'':   b"WD              M/S             ",
#'':   b"PRIVE 1         ?               ",
#'':   b"PRIVE 2         ?               ",
#'':   b"PRIVE 3         ?               ",
#'':   b"PRIVE 4         ?               "
#
#'Z':  b"COTE Z          M               ",
#'U':  b"VITESSE U       M/S             ",
#'V':  b"VITESSE V       M/S             ",
#'W':  b"VITESSE W       M/S             ",
#'NUX':b"NUX POUR VITESSEM2/S            ",
#'NUY':b"NUY POUR VITESSEM2/S            ",
#'NUZ':b"NUZ POUR VITESSEM2/S            ",
#'K':  b"ENERGIE TURBULENJOULE/KG        ",
#'EPS':b"DISSIPATION     WATT/KG         ",
#'RI': b"NB DE RICHARDSON                ",
#'RHO':b"DENSITE RELATIVE                ",
#'DP': b"PRESSION DYNAMIQPA              ",
#'':   b"PRESSION HYDROSTPA              ",
#'':   b"U CONVECTION    M/S             ",
#'':   b"V CONVECTION    M/S             ",
#'':   b"W CONVECTION    M/S             ",
#'':   b"VOLUMES TEMPS N M3              ",
#'':   b"DM1                             ",
#'':   b"DHHN            M               ",
#'':   b"UCONVC          M/S             ",
#'':   b"VCONVC          M/S             ",
#'':   b"UD              M/S             ",
#'':   b"VD              M/S             ",
#'':   b"WD              M/S             ",
#'':   b"PRIVE 1         ?               ",
#'':   b"PRIVE 2         ?               ",
#'':   b"PRIVE 3         ?               ",
#'':   b"PRIVE 4         ?               "
#
# VARIABLES 2D DE TELEMAC-3D
# telemac3d/sources/nomvar_2d_in_3d.f (V6P3)
#
#'':    b"VELOCITY U      M/S             ",
#'':    b"VELOCITY V      M/S             ",
#'':    b"CELERITY        M/S             ",
#'':    b"WATER DEPTH     M               ",
#'':    b"FREE SURFACE    M               ",
#'':    b"BOTTOM          M               ",
#'':    b"FROUDE NUMBER                   ",
#'':    b"SCALAR FLOWRATE M2/S            ",
#'':    b"TRACER                          ",
#'':    b"TURBULENT ENERG.JOULE/KG        ",
#'':    b"DISSIPATION     WATT/KG         ",
#'':    b"VISCOSITY       M2/S            ",
#'':    b"FLOWRATE ALONG XM2/S            ",
#'':    b"FLOWRATE ALONG YM2/S            ",
#'':    b"SCALAR VELOCITY M/S             ",
#'':    b"WIND ALONG X    M/S             ",
#'':    b"WIND ALONG Y    M/S             ",
#'':    b"AIR PRESSURE    PASCAL          ",
#'':    b"BOTTOM FRICTION                 ",
#'':    b"DRIFT ALONG X   M               ",
#'':    b"DRIFT ALONG Y   M               ",
#'':    b"COURANT NUMBER                  ",
#'':    b"RIGID BED       M               ",
#'':    b"FRESH DEPOSITS  M               ",
#'':    b"EROSION FLUX    UNIT   ??       ",
#'':    b"DEPOSITION PROBA                ",
#'':    b"PRIVE 1         ??              ",
#'':    b"PRIVE 2         ??              ",
#'':    b"PRIVE 3         ??              ",
#'':    b"PRIVE 4         ??              ",
#'':    b"FRICTION VELOCITM/S             ",
#'':    b"SOLID DISCHARGE M2/S            ",
#'':    b"SOLID DIS IN X  M2/S            ",
#'':    b"SOLID DIS IN Y  M2/S            ",
#'':    b"HIGH WATER MARK M               ",
#'':    b"HIGH WATER TIME S               "
#
#'U':   b"VITESSE U       M/S             ",
#'V':   b"VITESSE V       M/S             ",
#'C':   b"CELERITE        M/S             ",
#'H':   b"HAUTEUR D'EAU   M               ",
#'S':   b"SURFACE LIBRE   M               ",
#'B':   b"FOND            M               ",
#'F':   b"FROUDE                          ",
#'Q':   b"DEBIT SCALAIRE  M2/S            ",
#'':    b"TRACEUR                         ",
#'':    b"ENERGIE TURBUL. JOULE/KG        ",
#'':    b"DISSIPATION     WATT/KG         ",
#'':    b"VISCOSITE TURB. M2/S            ",
#'I':   b"DEBIT SUIVANT X M2/S            ",
#'J':   b"DEBIT SUIVANT Y M2/S            ",
#'M':   b"VITESSE SCALAIREM/S             ",
#'X':   b"VENT X          M/S             ",
#'Y':   b"VENT Y          M/S             ",
#'P':   b"PRESSION ATMOS. PASCAL          ",
#'W':   b"FROTTEMENT                      ",
#'':    b"DERIVE EN X     M               ",
#'':    b"DERIVE EN Y     M               ",
#'':    b"NBRE DE COURANT                 ",
#'RB':  b"FOND RIGIDE     M               ",
#'FD':  b"DEPOT FRAIS     M               ",
#'EF':  b"FLUX D'EROSION  UNITES ??       ",
#'DP':  b"PROBA DE DEPOT                  ",
#'P1':  b"PRIVE 1         ??              ",
#'P2':  b"PRIVE 2         ??              ",
#'P3':  b"PRIVE 3         ??              ",
#'P4':  b"PRIVE 4         ??              ",
#'US':  b"VITESSE DE FROT.M/S             ",
#'':    b"DEBIT SOLIDE    M2/S            ",
#'':    b"DEBIT SOL EN X  M2/S            ",
#'':    b"DEBIT SOL EN Y  M2/S            ",
#'MAXZ':b"COTE MAXIMUM    M               ",
#'TMXZ':b"TEMPS COTE MAXI S               "
