'''Given the requested node
fetch and compile the appropriate schedule'''

from logger.tac_logger import logger
from math import isnan
import numpy as np
from quantify_scheduler.device_under_test.quantum_device import Instrument, QuantumDevice
import redis
import json
from calibration_schedules.resonator_spectroscopy import Resonator_Spectroscopy
from calibration_schedules.two_tones_spectroscopy import Two_Tones_Spectroscopy
from calibration_schedules.rabi_oscillations import Rabi_Oscillations
from calibration_schedules.T1 import T1_BATCHED
from calibration_schedules.XY_crosstalk import XY_cross
from calibration_schedules.punchout import Punchout
from calibration_schedules.ramsey_fringes import Ramsey_fringes
from calibration_schedules.ro_frequency_optimization import RO_frequency_optimization
from calibration_schedules.ro_amplitude_optimization import RO_amplitude_optimization
from calibration_schedules.state_discrimination import Single_Shots_RO
# from calibration_schedules.drag_amplitude import DRAG_amplitude
from calibration_schedules.motzoi_parameter import Motzoi_parameter
from utilities.extended_transmon_element import ExtendedTransmon
from quantify_scheduler.backends import SerialCompiler
from config_files.settings import hw_config_json
#from config_files.settings import hw_config
from quantify_core.data.handling import set_datadir
from quantify_scheduler.json_utils import ScheduleJSONEncoder

set_datadir('.')

with open(hw_config_json) as hw:
    hw_config = json.load(hw)

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
    'resonator_spectroscopy_1': Resonator_Spectroscopy,
    'qubit_12_spectroscopy_pulsed': Two_Tones_Spectroscopy,
    'rabi_oscillations_12': Rabi_Oscillations,
    'ramsey_correction_12': Ramsey_fringes,
    'resonator_spectroscopy_2': Resonator_Spectroscopy,
    'ro_frequency_optimization': RO_frequency_optimization,
    'ro_amplitude_optimization': RO_amplitude_optimization,
    'state_discrimination': Single_Shots_RO,
}

redis_connection = redis.Redis(decode_responses=True)

def load_redis_config(transmon: ExtendedTransmon, channel:int):
    qubit = transmon.name
    redis_config = redis_connection.hgetall(f"transmons:{qubit}")
    transmon.reset.duration(float(redis_config['init_duration']))
    transmon.rxy.amp180(float(redis_config['mw_amp180']))
    transmon.r12.ef_amp180(float(redis_config['mw_ef_amp180']))
    #print(f'{transmon.rxy.amp180()=}')
    motzoi_val = float(redis_config['mw_motzoi'])
    if isnan(motzoi_val):
        motzoi_val = 0
    transmon.rxy.motzoi(motzoi_val)
    transmon.rxy.duration(float(redis_config['mw_pulse_duration']))

    transmon.spec.spec_amp(float(redis_config['spec_amp']))
    transmon.spec.spec_duration(float(redis_config['spec_pulse_duration']))
    # transmon.ports.microwave(redis_config['mw_port'])
    # transmon.ports.readout(redis_config['ro_port'])
    transmon.clock_freqs.f01(float(redis_config['freq_01']))
    transmon.clock_freqs.f12(float(redis_config['freq_12']))
    transmon.clock_freqs.readout(float(redis_config['ro_freq']))
    transmon.extended_clock_freqs.readout_1(float(redis_config['ro_freq_1']))
    transmon.extended_clock_freqs.readout_opt(float(redis_config['ro_freq_opt']))
    transmon.measure.pulse_amp(float(redis_config['ro_pulse_amp']))
    transmon.measure.pulse_duration(float(redis_config['ro_pulse_duration']))
    transmon.measure.acq_channel(channel)
    transmon.measure.acq_delay(float(redis_config['ro_acq_delay']))
    transmon.measure.integration_time(float(redis_config['ro_acq_integration_time']))
    transmon.measure_1.pulse_amp(float(redis_config['ro_pulse_amp']))
    transmon.measure_1.pulse_duration(float(redis_config['ro_pulse_duration']))
    transmon.measure_1.acq_channel(channel)
    transmon.measure_1.acq_delay(float(redis_config['ro_acq_delay']))
    transmon.measure_1.integration_time(float(redis_config['ro_acq_integration_time']))

    transmon.measure_opt.pulse_amp(float(redis_config['ro_pulse_amp']))
    transmon.measure_opt.pulse_duration(float(redis_config['ro_pulse_duration']))
    transmon.measure_opt.acq_channel(channel)
    transmon.measure_opt.acq_delay(float(redis_config['ro_acq_delay']))
    transmon.measure_opt.integration_time(float(redis_config['ro_acq_integration_time']))
    # transmon.measure.pulse_type(redis_config['ro_pulse_type'])
    return


def precompile(node:str, samplespace: dict[str,dict[str,np.ndarray]]):
    if node == 'tof':
        return None, 1

    Instrument.close_all()
    device = QuantumDevice('Loki')
    device.hardware_config(hw_config)
    device.cfg_sched_repetitions(1024)
    sweep_quantities = list(samplespace.keys())
    sweep_parameters = list(samplespace.values())
    #TODO this not the best way to acquire the qubits list
    qubits = sweep_parameters[0].keys()

    transmons = {}

    for channel, qubit in enumerate(qubits):
        transmon = ExtendedTransmon(qubit)
        load_redis_config(transmon,channel)
        device.add_element(transmon)
        transmons[qubit] = transmon
        #breakpoint()

    #for element_name in device.elements():
    #            element = device.get_element(element_name)
    #            with open(f"{element_name}.json","w") as fp:
    #                element_str = json.dump(element,fp, cls=ScheduleJSONEncoder)

    qubit_state = 0
    if node in ['resonator_spectroscopy_1','qubit_12_spectroscopy_pulsed',
                'rabi_oscillations_12', 'ramsey_correction_12']:
        qubit_state = 1
    if node in ['resonator_spectroscopy_2']:
        qubit_state = 2
    node_class = node_map[node](transmons, qubit_state)
    schedule_function = node_class.schedule_function
    static_parameters = node_class.static_kwargs
    schedule = schedule_function(**static_parameters , **samplespace)

    compiler = SerialCompiler(name=f'{node}_compiler')
    logger.info('Starting Compiling')
    compiled_schedule = compiler.compile(schedule=schedule, config=device.generate_compilation_config())
    #breakpoint()

    #TODO
    #ic.retrieve_hardware_logs

    with open(f'TIMING_TABLE_{node}.html', 'w') as file:
         file.write(
             compiled_schedule.timing_table.hide(['is_acquisition','wf_idx'],axis="columns"
                 ).to_html()
             )

    schedule_duration = compiled_schedule.get_schedule_duration()

    logger.info(f'Finished Compiling')
    # compiled_schedule.plot_pulse_diagram(plot_backend='plotly')

    return compiled_schedule, schedule_duration
