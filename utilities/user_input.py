from typing import List
import numpy as np
import redis
from uuid import uuid4
import logging
#logging.basicConfig(level=logging.DEBUG,
        #format='File: %(filename)s -- %(funcName)s --%(message)s')

red = redis.Redis(decode_responses=True)

nodes = [
        "resonator_spectroscopy",
        # "punchout",
        "qubit_01_spectroscopy_pulsed",
        "rabi_oscillations",
        "ramsey_correction",
        "motzoi_parameter",
        # "DRAG_amplitude",
        "SSRO_simple",
        # "randomized_benchmarking",
        "resonator_spectroscopy_1",
        "qubit_12_spectroscopy_pulsed",
        "rabi_oscillations_12",
        # "ramsey_correction_12",
        "resonator_spectroscopy_2",
        ]

VNA_resonator_frequencies_A = {'q1' : 6.4796e9, 'q2' : 6.2576e9}
VNA_qubit_frequencies_A = {'q1' : 3.870e9, 'q2' : 3.4035e9}
VNA_f12_frequencies_A = {'q1' : 3.620e9, 'q2' : 3.200e9}

VNA_resonator_frequencies = {
        'q11': 6.934e9, 'q12': 6.605e9, 'q13': 6.688e9, 'q14': 6.332e9, 'q15': 6.933e9,
        'q16': 6.491e9, 'q17': 7.059e9, 'q18': 6.712e9, 'q19': 6.818e9, 'q20': 6.494e9,
        'q21': 6.751e9, 'q22': 6.477e9, 'q23': 7.052e9, 'q24': 6.583e9, 'q25': 6.853e9,
        }

VNA_qubit_frequencies = {
        'q11': 3.749e9,
        'q12': 3.382e9,
        'q13': 3.336e9,
        'q14': 3.347e9,
        'q15': 3.889e9,
        'q16': 3.195e9,
        'q17': 3.948e9,
        'q18': 3.264e9,
        'q19': 3.939e9,
        'q20': 3.350e9,
        'q21': 3.784e9,
        'q22': 3.3395e9,
        'q23': 3.933e9,
        'q24': 3.2865e9,
        'q25': 4.024e9
        }

VNA_f12_frequencies= {
        'q11': 3.749e9-230e6,
        'q12': 3.189e9,
        'q13': 3.336e9-230e6,
        'q14': 3.147e9,
        'q15': 3.889e9-230e6,
        'q16': 3.195e9-200e6,
        'q17': 3.948e9-230e6,
        'q18': 3.067e9,
        'q19': 3.700e9,
        'q20': 3.150e9,
        'q21': 3.769e9-230e6,
        'q22': 3.140e9,
        'q23': 3.697e9,
        'q24': 3.085e9,
        'q25': 3.784e9
        }


# assert(list(VNA_resonator_frequencies.keys()) == list(VNA_qubit_frequencies.keys()))
# qubits = list(VNA_resonator_frequencies.keys())
#qubits = [
#        'q11', 'q12', 'q14', 'q15', #****q11, q15, q13 got the axe ****
#        'q16', 'q17', 'q18', 'q19', 'q20',
#        'q21', 'q22', 'q23', 'q24', 'q25'
#        ]
# qubits = [ 'q13']
# qubits = ['q12', 'q18', 'q23']
# qubits = ['q12','q18','q19','q20','q23','q25']
# qubits = ['q19','q25']
# qubits = ['q16','q17']
# qubits = ['q16']

qubits = ['q12', 'q14', 'q16', 'q17', 'q18', 'q19', 'q20',
          'q21', 'q22', 'q23', 'q24', 'q25' ]

# qubits = ['q21','q23']
# qubits = ['q23']

N_qubits = len(qubits)

res_spec_samples = 10
qub_spec_samples =101

def resonator_samples(qubit:str, punchout=False):
    sweep_range = 4.5e6
    punchout_range = 2e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq =  VNA_frequency - sweep_range / 2
    min_freq =  min_freq if not punchout else min_freq - punchout_range
    max_freq =  VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, res_spec_samples)

def qubit_samples(qubit:str, transition:str = '01'):
    sweep_range = 5e6
    if transition=='01':
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition=='12':
        # rough_anharmonicity = 200e6 if int(qubit[1:])%2==0 else 170e6
        # VNA_frequency = VNA_qubit_frequencies[qubit] - rough_anharmonicity
        VNA_frequency = VNA_f12_frequencies[qubit]
    else : print('Invalid Transition')
    min_freq =  VNA_frequency - sweep_range / 2
    max_freq =  VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)

def experiment_parameters(node:str, qubits:List[str]) -> dict:
    '''
    TODO this will change it's simpler to sinply pass the whole samples array.
    Dictionary that contains the parameter space for each calibration node.
    The keys order is : 1. Node key 2. Sweep parameter key 3. qubit key.
    For example, if the calibrtation node is 'resonator_spectroscopy'
    and we have two qubits labeled 'q1' and 'q2',
    it returns the dictionary:
    sweep_parameters = {
        'resonator_spectroscopy': {
             'ro_freq':
                  {'q1': {'sweep_min': ..., 'sweep_max': ..., 'samples': ...},
                   'q2': {'sweep_min': ..., 'sweep_max': ..., 'samples': ...}
                  }
        }
    }
    '''
    sweep_parameters = {
            'resonator_spectroscopy': {'ro_freq': {qubit: resonator_samples(qubit) for qubit in qubits}},

            'punchout': {'ro_freq': {qubit: resonator_samples(qubit, punchout=True) for qubit in qubits},
                                 'ro_ampl':{qubit : {"sweep_min": 1e-3, "sweep_max":2.5e-2, "samples": 21} for qubit in qubits}},

            'qubit_01_spectroscopy_pulsed': {'freq_01': {qubit: qubit_samples(qubit) for qubit in qubits}},

            'rabi_oscillations': {'mw_amp180': { qubit :{"sweep_min": 0.002, "sweep_max": 0.22, "samples": 41} for qubit in qubits}},

            'ramsey_correction': {
                'ramsey_delay': {
                    qubit :{"sweep_min": 4e-9, "sweep_max": 2048e-9, "step": 6*8e-9} for qubit in qubits
                    }
                },
            'motzoi_parameter': {'mw_motzoi':{qubit : {"sweep_min": -0.45, "sweep_max": 0.45, "samples": 41} for qubit in qubits},
                                         'X_repetition': {qubit : {"sweep_min": 2, "sweep_max":17, "step": 2} for qubit in qubits}},
            'DRAG_amplitude': {'mw_amp180':{qubit : {"sweep_min": 0.002, "sweep_max": 0.10, "samples": 41} for qubit in qubits},
                                         'X_repetition': {qubit : {"sweep_min": 1, "sweep_max":17, "step": 2} for qubit in qubits}},
            'resonator_spectroscopy_1': {'ro_freq_1': {qubit: resonator_samples(qubit) for qubit in qubits}},
            'qubit_12_spectroscopy_pulsed': {'freq_12': {qubit: qubit_samples(qubit,transition='12') for qubit in qubits}},
            'rabi_oscillations_12': {'mw_amp180': { qubit :{"sweep_min": 0.002, "sweep_max": 0.22, "samples": 51} for qubit in qubits}},
            'ramsey_correction_12': {
                'ramsey_delay': {
                    qubit :{"sweep_min": 4e-9, "sweep_max": 5*2048e-9, "step": 12*1e-9} for qubit in qubits
                    }
                },
            'resonator_spectroscopy_2': {'ro_freq_2': {qubit: resonator_samples(qubit) for qubit in qubits}},

            'SSRO_simple': { 'state_level': {qubit : {"rng": 'rng', "shots": 2000} for qubit in qubits } },

            'randomized_benchmarking': {'number_cliffords': {qubit : {"rb": 'rb', "max_cliffords": 2048} for qubit in qubits } }, #TODO this is aweful

            'state_discrimination': {'ro_freq':{qubit: resonator_samples(qubit) for qubit in qubits},
                                             'ro_pulse_amp_cus': {qubit : {"sweep_min": 0.005, "sweep_max": 0.011, "samples": 5 } for qubit in qubits },
                                             'state_level': {qubit : {"rng": 'rng', "shots": 9 } for qubit in qubits } #TODO this is awful
                                            },
    }
    return sweep_parameters


def box(func):
    def wrapper(text):
        margin = 20
        print(u"\u2554" + u"\u2550" * (len(text)+margin) + u"\u2557")
        print(u"\u2551" + margin//2*" " + text + margin//2*" " + u"\u2551")
        print(u"\u255a" + u"\u2550" * (len(text)+margin) + u"\u255d")
    return wrapper

node_to_be_calibrated = "resonator_spectroscopy"
box_print = box(print)
box_print(f'Target Node: {node_to_be_calibrated}, Qubits: {N_qubits}')

def user_requested_calibration(node: str):
    job = {
        "job_id": str(uuid4()),
        "is_calibration_sup_job": True,
        "name": node,
        "qubits": qubits,
    }
    job["experiment_params"] = experiment_parameters(node,qubits)

    return job
