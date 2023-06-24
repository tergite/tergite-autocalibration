'''Given the requested node
fetch and compile the appropriate schedule'''
import numpy as np
from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from calibration_schedules.rabi_oscillations import Rabi_Oscillations
from calibration_schedules.ramsey_fringes import Ramsey_fringes
from calibration_schedules.drag_amplitude import DRAG_amplitude 
from calibration_schedules.motzoi_paramerter import Motzoi_parameter
from quantify_scheduler.device_under_test.transmon_element import BasicTransmonElement
from quantify_scheduler.backends import SerialCompiler
from pretty_hw import hardware_config

node_map = {
    'resonator_spectroscopy': Resonator_Spectroscopy,
    'qubit_01_spectroscopy_pulsed': Two_Tones_Spectroscopy,
    'rabi_oscillations': Rabi_Oscillations,
    'ramsey_correction': Ramsey_fringes,
    'motzoi_parameter': Motzoi_parameter,
    'drag_amplitude': DRAG_amplitude,
    'resonator_spectroscopy_1': Resonator_Spectroscopy,
    'qubit_12_spectroscopy_pulsed': Two_Tones_Spectroscopy,
    'rabi_oscillations_12': Rabi_Oscillations,
    'resonator_spectroscopy_2': Resonator_Spectroscopy,
}

def precompile(node:str, samplespace: dict[str,np.ndarray]):
    node_class = node_map[node]
    # device_configuration
    # hardware_configuration
    device = QuantumDevice('Loki')
    device.hardware_config(hardware_config)
    qubits = samplespace.keys()

    for qubit in qubits:
        q = BasicTransmonElement(qubit)
        device.add_element(q)

    schedule_function = node_class.schedule_function
    static_parameters = node_class.static_kwargs
    sweep_parameters = node_class.sweep_parameters
    sweep_parameters = { node+'_'+qubit : samplespace[qubit] for qubit in samplespace }

    schedule = schedule_function(static_parameters | sweep_parameters)
    
    compiler = SerialCompiler(name=f'{node}_compiler')
    compiled_schedule = compiler.compile(schedule=schedule, config=device.generate_compilation_config())

    print('precompiling!!!')
