from typing import List
import numpy as np
import redis
from uuid import uuid4
from utilities.visuals import box_print
import logging
#logging.basicConfig(level=logging.DEBUG,
        #format='File: %(filename)s -- %(funcName)s --%(message)s')

nodes = [
        #"resonator_spectroscopy",
        "punchout",
        "qubit_01_spectroscopy_pulsed",
        "rabi_oscillations",
        "XY_crosstalk",
        "ramsey_correction",
        ]

VNA_resonator_frequencies = {
        'q13': 6.740e9, 'q14': 6.393e9, 'q15': 6.944e9,
        'q16': 6.386e9, 'q17': 6.620e9, 'q18': 7.030e9, 'q19': 6.711e9,
        'q21': 6.551e9, 'q22': 6.387e9, 'q23': 7.026e9,
        }

VNA_qubit_frequencies = {
        'q13': 3.720e9,
        'q14': 3.341e9,
        'q15': 3.748e9,
        'q16': 3.262e9,
        'q17': 3.357e9,
        'q18': 4.077e9,
        'q19': 3.835e9,
        'q21': 3.783e9,
        'q22': 3.406e9,
        'q23': 3.941e9,
        }

qubits = ['q16', 'q18', 'q19', 'q21', 'q22', 'q23']
# qubits = ['q23']

N_qubits = len(qubits)

res_spec_samples = 60
qub_spec_samples =1100

def resonator_samples(qubit:str, punchout=False) -> np.ndarray:
    sweep_range = 7e6
    punchout_range = 0e6
    VNA_frequency = VNA_resonator_frequencies[qubit]
    min_freq =  VNA_frequency - sweep_range / 2
    #min_freq =  min_freq if not punchout else min_freq - punchout_range
    max_freq =  VNA_frequency + sweep_range / 2 - 2e6
    return np.linspace(min_freq, max_freq, res_spec_samples)

def qubit_samples(qubit:str, transition:str = '01') -> np.ndarray:
    sweep_range = 200e6
    if transition=='01':
        VNA_frequency = VNA_qubit_frequencies[qubit]
    elif transition=='12':
        # rough_anharmonicity = 200e6 if int(qubit[1:])%2==0 else 170e6
        # VNA_frequency = VNA_qubit_frequencies[qubit] - rough_anharmonicity
        VNA_frequency = VNA_f12_frequencies[qubit]
    else :
        raise ValueError('Invalid transition')

    min_freq =  VNA_frequency - sweep_range / 2
    max_freq =  VNA_frequency + sweep_range / 2
    return np.linspace(min_freq, max_freq, qub_spec_samples)

def experiment_parameters(node:str, qubits:List[str]) -> dict:
    '''
    Dictionary that contains the parameter space for each calibration node.
    The keys order is:
    1. Node key
    2. Sweep parameter key
    3. qubit key
    For example, if the calibrtation node is 'resonator_spectroscopy'
    and we have two qubits labeled 'q1' and 'q2', it returns the dictionary:
    sweep_parameters = {
        'resonator_spectroscopy': {
             'ro_freq':
                  {'q1': array_of_frequencies,
                   'q2': array_of_frequencies
                  }
        }
    }
    '''
    sweep_parameters = {
        'resonator_spectroscopy': {
            'ro_frequencies': {qubit: resonator_samples(qubit) for qubit in qubits}
        },

        'punchout': {
            'ro_frequencies': {qubit: resonator_samples(qubit, punchout=True) for qubit in qubits},
            'ro_amplitudes': {qubit : np.linspace(5e-3, 1e-1, 9) for qubit in qubits}
        },

        'qubit_01_spectroscopy_pulsed': {
            'mw_frequencies': {qubit: qubit_samples(qubit) for qubit in qubits}
        },

        'rabi_oscillations': {
            'mw_amplitudes': { qubit : np.linspace(0.002,0.22,41) for qubit in qubits}
        },

        'XY_crosstalk': {
            'mw_amplitudes': { qubit : np.linspace(0.002,0.22,5) for qubit in qubits },
            'mw_pulse_durations': { qubit : np.arange(20e-9,300e-9,41) for qubit in qubits },
            'drive_qubit': 'q18'
        },

        'ramsey_correction': {
            'ramsey_delay': { qubit :{"sweep_min": 4e-9, "sweep_max": 2048e-9, "step": 6*8e-9} for qubit in qubits }
                },
    }
    return sweep_parameters

#node_to_be_calibrated = "resonator_spectroscopy"
node_to_be_calibrated = "punchout"
print()
box_print(f'Target Node: {node_to_be_calibrated}, Qubits: {N_qubits}')

def user_requested_calibration(node: str):
    job = {
        "job_id": str(uuid4()),
        "name": node,
        "qubits": qubits,
        "experiment_params": experiment_parameters(node,qubits),
    }

    return job
