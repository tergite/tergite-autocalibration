from calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from calibration_schedules.two_tone_multidim import Two_Tones_Multidim
from calibration_schedules.rabi_oscillations import Rabi_Oscillations
from calibration_schedules.T1 import T1_BATCHED
from calibration_schedules.XY_crosstalk import XY_cross
from calibration_schedules.punchout import Punchout
from calibration_schedules.ramsey_fringes import Ramsey_fringes
from calibration_schedules.ro_frequency_optimization import RO_frequency_optimization
from calibration_schedules.ro_amplitude_optimization import RO_amplitude_optimization
from calibration_schedules.state_discrimination import Single_Shots_RO
from analysis.motzoi_analysis import MotzoiAnalysis
from analysis.resonator_spectroscopy_analysis import (
    ResonatorSpectroscopyAnalysis,
    ResonatorSpectroscopy_1_Analysis,
    ResonatorSpectroscopy_2_Analysis
)
from analysis.qubit_spectroscopy_analysis import QubitSpectroscopyAnalysis
from analysis.qubit_spectroscopy_multidim import QubitSpectroscopyMultidim
from analysis.optimum_ro_frequency_analysis import (
    OptimalROFrequencyAnalysis,
    OptimalRO_012_FrequencyAnalysis
)
from analysis.optimum_ro_amplitude_analysis import OptimalROAmplitudeAnalysis
from analysis.state_discrimination_analysis import StateDiscrimination
from analysis.rabi_analysis import RabiAnalysis
from analysis.punchout_analysis import PunchoutAnalysis
from analysis.ramsey_analysis import RamseyAnalysis
from analysis.tof_analysis import analyze_tof
from analysis.T1_analysis import T1Analysis

# from calibration_schedules.drag_amplitude import DRAG_amplitude
from calibration_schedules.motzoi_parameter import Motzoi_parameter
class Node():
    def __init__(self, name:str, field:str, measurement_obj, analysis_obj):
        self.name = name
        self.redis_field = field
        self.measurement = measurement_obj
        self.analysis = analysis_obj


nodes = {
    'resonator_spectroscopy': Node(
        name = 'resonator_spectroscopy',
        redis_field = 'ro_freq',
        measurement_obj = Resonator_Spectroscopy,
        analysis_obj = ResonatorSpectroscopyAnalysis
    ),
    'qubit_01_spectroscopy_pulsed': Node(
        name = 'qubit_01_spectroscopy_pulsed',
        redis_field = 'f01',
        measurement_obj = Two_Tones_Spectroscopy,
        analysis_obj = QubitSpectroscopyAnalysis
    )
}
