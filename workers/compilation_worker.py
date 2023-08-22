'''Given the requested node
fetch and compile the appropriate schedule'''

from rq import Queue
from logger.tac_logger import logger
logger.info('finished imports')
from math import isnan
import numpy as np
from quantify_scheduler.device_under_test.quantum_device import Instrument, QuantumDevice
import redis
from calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from calibration_schedules.rabi_oscillations import Rabi_Oscillations
from calibration_schedules.T1 import T1_BATCHED
from calibration_schedules.time_of_flight import Time_Of_Flight
from calibration_schedules.XY_crosstalk import XY_cross
from calibration_schedules.punchout import Punchout
from calibration_schedules.ramsey_fringes import Ramsey_fringes
# from calibration_schedules.drag_amplitude import DRAG_amplitude
from calibration_schedules.motzoi_paramerter import Motzoi_parameter
from quantify_scheduler.device_under_test.transmon_element import BasicTransmonElement
from quantify_scheduler.backends import SerialCompiler
from config_files.IF_hw_config import hardware_config
from quantify_core.data.handling import set_datadir

set_datadir('.')


node_map = {
    'resonator_spectroscopy': Resonator_Spectroscopy,
    'qubit_01_spectroscopy_pulsed': Two_Tones_Spectroscopy,
    'rabi_oscillations': Rabi_Oscillations,
    'T1': T1_BATCHED,
    'XY_crosstalk': XY_cross,
    'punchout': Punchout,
    'ramsey_correction': Ramsey_fringes,
    'motzoi_parameter': Motzoi_parameter,
    # 'drag_amplitude': DRAG_amplitude,
    # 'resonator_spectroscopy_1': Resonator_Spectroscopy,
    # 'qubit_12_spectroscopy_pulsed': Two_Tones_Spectroscopy,
    # 'rabi_oscillations_12': Rabi_Oscillations,
    # 'resonator_spectroscopy_2': Resonator_Spectroscopy,
}

redis_connection = redis.Redis(decode_responses=True)

rq_supervisor = Queue(
        'calibration_supervisor', connection=redis_connection
        )

def load_redis_config(transmon: BasicTransmonElement, channel:int):
    qubit = transmon.name
    redis_config = redis_connection.hgetall(f"transmons:{qubit}")
    transmon.reset.duration(float(redis_config['init_duration']))
    transmon.rxy.amp180(float(redis_config['mw_amp180']))
    motzoi_val = float(redis_config['mw_motzoi'])
    if isnan(motzoi_val):
        motzoi_val = 0
    transmon.rxy.motzoi(motzoi_val)
    transmon.rxy.duration(float(redis_config['mw_pulse_duration']))

    # transmon.ports.microwave(redis_config['mw_port'])
    # transmon.ports.readout(redis_config['ro_port'])
    transmon.clock_freqs.f01(float(redis_config['freq_01']))
    transmon.clock_freqs.f12(float(redis_config['freq_12']))
    transmon.clock_freqs.readout(float(redis_config['ro_freq']))
    transmon.measure.pulse_amp(float(redis_config['ro_pulse_amp']))
    transmon.measure.pulse_duration(float(redis_config['ro_pulse_duration']))
    # transmon.measure.pulse_type(redis_config['ro_pulse_type'])
    transmon.measure.acq_channel(channel)
    transmon.measure.acq_delay(float(redis_config['ro_acq_delay']))
    transmon.measure.integration_time(float(redis_config['ro_acq_integration_time']))
    return


def precompile(node:str, samplespace: dict[str,dict[str,np.ndarray]]):
    Instrument.close_all()

    device = QuantumDevice('Loki')
    device.hardware_config(hardware_config)
    device.cfg_sched_repetitions(1024)
    sweep_quantities = list(samplespace.keys())
    sweep_parameters = list(samplespace.values())
    #TODO this not the best way to acquire the qubits list
    qubits = sweep_parameters[0].keys()

    transmons = {}

    for channel, qubit in enumerate(qubits):
        q = BasicTransmonElement(qubit)
        load_redis_config(q,channel)
        device.add_element(q)
        transmons[qubit] = q

    node_class = node_map[node](transmons)
    schedule_function = node_class.schedule_function
    static_parameters = node_class.static_kwargs

    schedule = schedule_function(**static_parameters , **samplespace)

    compiler = SerialCompiler(name=f'{node}_compiler')
    logger.info('Starting Compiling')
    compiled_schedule = compiler.compile(schedule=schedule, config=device.generate_compilation_config())
    with open(f'TIMING_TABLE_{node}.html', 'w') as file:
         file.write(
             compiled_schedule.timing_table.hide(['is_acquisition','wf_idx'],axis="columns"
                 ).to_html()
             )

    schedule_duration = compiled_schedule.get_schedule_duration()

    logger.info(f'finished Compiling')
    # compiled_schedule.plot_pulse_diagram(plot_backend='plotly')

    return compiled_schedule, schedule_duration
