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
    def __init__(
        self, name:str, redis_field:str, qubit_state:int, measurement_obj, analysis_obj
    ):
        self.name = name
        self.redis_field = redis_field
        self.qubit_state = qubit_state # e.g. qubit_state=1 for resonator_spectroscopy_1
        self.measurement_obj = measurement_obj
        self.analysis_obj = analysis_obj

node_definitions = {
    'resonator_spectroscopy': Node(
        name = 'resonator_spectroscopy',
        redis_field = 'ro_freq',
        qubit_state = 0,
        measurement_obj = Resonator_Spectroscopy,
        analysis_obj = ResonatorSpectroscopyAnalysis
    ),
    'qubit_01_spectroscopy_pulsed': Node(
        name = 'qubit_01_spectroscopy_pulsed',
        redis_field = 'freq_01',
        qubit_state = 0,
        measurement_obj = Two_Tones_Spectroscopy,
        analysis_obj = QubitSpectroscopyAnalysis
    ),
    'rabi_oscillations': Node(
        name = 'rabi_oscillations',
        redis_field = 'mw_amp180',
        qubit_state = 0,
        measurement_obj = Rabi_Oscillations,
        analysis_obj = RabiAnalysis
    ),
    'ramsey_correction': Node(
        name = 'ramsey_correction',
        redis_field = 'freq_01',
        qubit_state = 0,
        measurement_obj = Ramsey_fringes,
        analysis_obj = RamseyAnalysis
    ),
    'motzoi_parameter': Node(
        name = 'motzoi_parameter',
        redis_field = 'mw_motzoi',
        qubit_state = 0,
        measurement_obj = Motzoi_parameter,
        analysis_obj = MotzoiAnalysis
    ),
    'resonator_spectroscopy_1': Node(
        name = 'resonator_spectroscopy_1',
        redis_field = 'ro_freq_1',
        qubit_state = 1,
        measurement_obj = Resonator_Spectroscopy,
        analysis_obj = ResonatorSpectroscopy_1_Analysis
    ),
    'T1': Node(
        name = 'T1',
        redis_field = 't1_time',
        qubit_state = 0,
        measurement_obj = T1_BATCHED,
        analysis_obj = T1Analysis
    ),
    'two_tone_multidim': Node(
        name = 'two_tone_multidim',
        redis_field = 'freq_01',
        qubit_state = 0,
        measurement_obj = Two_Tones_Multidim,
        analysis_obj = QubitSpectroscopyMultidim
    ),
    'qubit_12_spectroscopy_pulsed': Node(
        name = 'qubit_12_spectroscopy_pulsed',
        redis_field = 'freq_12',
        qubit_state = 1,
        measurement_obj = Two_Tones_Spectroscopy,
        analysis_obj = QubitSpectroscopyAnalysis
    ),
    'rabi_oscillations_12': Node(
        name = 'rabi_oscillations_12',
        redis_field = 'mw_ef_amp180',
        qubit_state = 1,
        measurement_obj = Rabi_Oscillations,
        analysis_obj = RabiAnalysis
    ),
    'ramsey_correction_12': Node(
        name ='ramsey_correction_12',
        redis_field = 'freq_12',
        qubit_state = 1,
        measurement_obj = Ramsey_fringes,
        analysis_obj = RamseyAnalysis
    ),
    'resonator_spectroscopy_2': Node(
        name = 'resonator_spectroscopy_2',
        redis_field = 'ro_freq_2',
        qubit_state = 2,
        measurement_obj = Resonator_Spectroscopy,
        analysis_obj = ResonatorSpectroscopy_2_Analysis
    ),
    'punchout': Node(
        name = 'punchout',
        redis_field = 'ro_amp',
        qubit_state = 0,
        measurement_obj = Punchout,
        analysis_obj = PunchoutAnalysis
    ),
    'ro_frequency_optimization': Node(
        name = 'ro_frequency_optimization',
        redis_field = 'ro_freq_opt',
        qubit_state = 0, #doesn't matter
        measurement_obj = RO_frequency_optimization,
        analysis_obj = OptimalROFrequencyAnalysis
    ),
    'ro_frequency_optimization_gef': Node(
        name = 'ro_frequency_optimization_gef',
        redis_field = 'ro_freq_opt',
        qubit_state = 2,
        measurement_obj = RO_frequency_optimization,
        analysis_obj = OptimalROFrequencyAnalysis
    ),
    'ro_amplitude_optimization': Node(
        name = 'ro_amplitude_optimization',
        redis_field = 'ro_pulse_amp_opt',
        qubit_state = 0, #doesn't matter
        measurement_obj = RO_amplitude_optimization,
        analysis_obj = OptimalROAmplitudeAnalysis
    ),
    'state_discrimination': Node(
        name = 'state_discrimination',
        redis_field = 'discriminator',
        qubit_state = 0, #doesn't matter
        measurement_obj = Single_Shots_RO,
        analysis_obj = StateDiscrimination
    ),
}
