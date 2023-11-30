import redis
import toml
import argparse
from utilities import user_input
#TODO this is a bit slow so better just keep a copy of the nodes here
#from nodes.node import all_nodes
<<<<<<< HEAD
nodes = ['cz_calibration','resonator_spectroscopy_2','n_rabi_oscillations','motzoi_parameter','tof', 'resonator_spectroscopy', 'qubit_01_spectroscopy_pulsed', 'qubit_01_spectroscopy_multidim', 'rabi_oscillations', 'ramsey_correction', 'resonator_spectroscopy_1', 'ro_frequency_optimization', 'T1', 'qubit_12_spectroscopy_pulsed', 'ro_amplitude_optimization', 'rabi_oscillations_12', 'state_discrimination', 'ramsey_correction_12','coupler_spectroscopy','coupler_resonator_spectroscopy', 'punchout' ]
=======
nodes = ['resonator_spectroscopy_2','n_rabi_oscillations','motzoi_parameter','tof', 'resonator_spectroscopy', 'qubit_01_spectroscopy_pulsed', 'qubit_01_spectroscopy_multidim', 'rabi_oscillations', 'ramsey_correction', 'resonator_spectroscopy_1', 'ro_frequency_optimization', 'T1', 'qubit_12_spectroscopy_pulsed', 'ro_amplitude_optimization', 'rabi_oscillations_12', 'state_discrimination', 'ramsey_correction_12','coupler_spectroscopy','coupler_resonator_spectroscopy', 'punchout' ]
>>>>>>> 1ea8206 (chore: pre-merge backup)

#nodes = all_nodes
red = redis.Redis(decode_responses=True)
qubits = user_input.qubits
bus_list = [ [qubits[i],qubits[i+1]] for i in range(len(qubits)-1) ]
couplers = [bus[0]+'_'+bus[1] for bus in bus_list]

parser = argparse.ArgumentParser()
parser.add_argument('node', choices=['all']+nodes)
args = parser.parse_args()

transmon_configuration = toml.load('./config_files/device_config.toml')
quantities_of_interest = transmon_configuration['qoi']
remove_node = args.node
print(f'{ remove_node = }')
if not remove_node == 'all':
    remove_fields = quantities_of_interest[remove_node].keys()
    #print('remove_fields', remove_fields)

#TODO Why flush?
#red.flushdb()
for qubit in qubits:
    fields =  red.hgetall(f'transmons:{qubit}').keys()
    key = f'transmons:{qubit}'
    cs_key = f'cs:{qubit}'
    if remove_node == 'all':
        for field in fields:
            red.hset(key, field, 'nan' )
        for node in nodes:
            red.hset(cs_key, node, 'not_calibrated' )
    elif remove_node in nodes:
        for field in remove_fields:
            red.hset(key, field, 'nan')
        red.hset(cs_key, remove_node, 'not_calibrated' )
    else:
        raise ValueError('Invalid Field')

for coupler in couplers:
    fields =  red.hgetall(f'couplers:{coupler}').keys()
    key = f'couplers:{coupler}'
    cs_key = f'cs:{coupler}'
    if remove_node == 'all':
        for field in fields:
            red.hset(key, field, 'nan' )
        for node in nodes:
            red.hset(cs_key, node, 'not_calibrated' )
    elif remove_node in nodes:
        for field in remove_fields:
            red.hset(key, field, 'nan')
        red.hset(cs_key, remove_node, 'not_calibrated' )
    else:
        raise ValueError('Invalid Field')
