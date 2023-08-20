import numpy as np
from quantify_scheduler.device_under_test.quantum_device import Instrument, QuantumDevice
from calibration_schedules.rabi_oscillations import Rabi_Oscillations
from calibration_schedules.punchout import Punchout
from quantify_scheduler.device_under_test.transmon_element import BasicTransmonElement
from quantify_scheduler.backends import SerialCompiler
from config_files.test_hw_config import hardware_config
from quantify_core.data.handling import set_datadir
from datetime import datetime
set_datadir('.')

schedule_map = {
    'rabi_oscillations': Rabi_Oscillations,
    'punchout': Punchout,
}
node = 'punchout'
qubits = [f'q{i}' for i in range(10)]

if node == 'punchout':
    samplespace = {
        'ro_frequencies': {qubit: np.linspace(6e9,6.1e9, 50) for qubit in qubits},
        'ro_amplitudes': {qubit : np.linspace(5e-3, 0.8e-1, 7) for qubit in qubits}
    }
elif node == 'rabi_oscillations':
    samplespace = {
        'mw_amplitudes': { qubit : np.linspace(0.002,0.20,50) for qubit in qubits}
    }

def load_bte(transmon: BasicTransmonElement, channel:int):
    qubit = transmon.name
    transmon.reset.duration(300e-6)
    transmon.rxy.amp180(50e-3)
    transmon.rxy.motzoi(0.1)
    transmon.rxy.duration(40e-9)

    # transmon.ports.microwave(redis_config['mw_port'])
    # transmon.ports.readout(redis_config['ro_port'])
    transmon.clock_freqs.f01(4e9)
    transmon.clock_freqs.f12(3.8e9)
    transmon.clock_freqs.readout(6e9)
    transmon.measure.pulse_amp(20e-3)
    transmon.measure.pulse_duration(3e-6)
    # transmon.measure.pulse_type(redis_config['ro_pulse_type'])
    transmon.measure.acq_channel(channel)
    transmon.measure.acq_delay(200e-9)
    transmon.measure.integration_time(2.4e-6)
    return


device = QuantumDevice('Loki')
device.hardware_config(hardware_config)
device.cfg_sched_repetitions(1024)

transmons = {}

for channel, qubit in enumerate(qubits):
    q = BasicTransmonElement(qubit)
    load_bte(q,channel)
    device.add_element(q)
    transmons[qubit] = q

node_class = schedule_map[node](transmons)
schedule_function = node_class.schedule_function
static_parameters = node_class.static_kwargs

schedule = schedule_function(**static_parameters , **samplespace)

compiler = SerialCompiler(name=node)

t0 = datetime.now()
compiled_schedule = compiler.compile(schedule=schedule, config=device.generate_compilation_config())
t1 = datetime.now()
delta = t1-t0
print(delta)

# with open(f'TIMING_TABLE_rabi.html', 'w') as file:
#      file.write(
#          compiled_schedule.timing_table.hide(['is_acquisition','wf_idx'],axis="columns"
#              ).to_html()
#          )

schedule_duration = compiled_schedule.get_schedule_duration()
# print(schedule_duration)
# plot = compiled_schedule.plot_pulse_diagram(plot_backend='plotly')
# plot.show()
