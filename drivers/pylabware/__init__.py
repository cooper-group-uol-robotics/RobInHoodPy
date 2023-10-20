import sys

# Heidolph
from .devices.buchi_c815 import C815FlashChromatographySystem

# Buchi
from .devices.buchi_r300 import R300Rotovap

# Heidolph
from .devices.heidolph_hei_torque_100_precision import HeiTorque100PrecisionStirrer
from .devices.heidolph_rzr_2052_control import RZR2052ControlStirrer

# Huber
from .devices.huber_petite_fleur import PetiteFleurChiller

# IDEX
from .devices.idex_mxii import IDEXMXIIValve

# IKA
from .devices.ika_microstar_75 import Microstar75Stirrer
from .devices.ika_rct_digital import RCTDigitalHotplate
from .devices.ika_ret_control_visc import RETControlViscHotplate
from .devices.ika_rv10 import RV10Rotovap

# JULABO
from .devices.julabo_cf41 import CF41Chiller

# Kern
from .devices.kern_pcb2500 import PCB2500

# Fisher
from .devices.fisher_pp14102 import PPS4102

# Mettler
from .devices.mettler_quantos_qb1 import QuantosQB1
from .devices.mettler_xpr226drq import XPR226DRQ
from .devices.mettler_mtsc import MTSC

# If windows import Optimax. This "driver" is based on
# controlling the GUI iControl.exe
if sys.platform == "win32":
    from .devices.mettler_optimax import Optimax

# PolarBear
from .devices.polar_bear_plus import PolarBearPlus

# XLP6000 syringe pump
from .devices.tecan_xlp6000 import XLP6000

# Xcalibru syringe pump
from .devices.tecan_xcalibur import XCalibur

# KNF diaphragm pump
from .devices.knf_simdos10_rcplus import RCPlus

# Tricontinent
from .devices.tricontinent_c3000 import C3000SyringePump

# Vacuubrand
from .devices.vacuubrand_cvc_3000 import CVC3000VacuumPump
