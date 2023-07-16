import redis
import sys
import toml
from utilities import user_input

red = redis.Redis(decode_responses=True)
qubits = user_input.qubits
nodes = user_input.nodes

transmon_configuration = toml.load('./config_files/transmons_config.toml')
quantities_of_interest = transmon_configuration['qoi']
remove_node = sys.argv[1]
print(f'{ remove_node = }')
if not remove_node == 'all':
    remove_fields = quantities_of_interest[remove_node].keys()
    # print('remove_fields', remove_fields)

#TODO Why flush?
# red.flushdb()
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
