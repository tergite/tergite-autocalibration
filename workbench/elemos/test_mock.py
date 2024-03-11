import json
import numpy as np
from pprint import pprint
from quantify_scheduler.device_under_test.quantum_device import QuantumDevice
from quantify_scheduler.json_utils import SchedulerJSONEncoder, SchedulerJSONDecoder
from quantify_scheduler.device_under_test.transmon_element import BasicTransmonElement
from tergite_acl.utils import extended_transmon_element
from tergite_acl.utils.extended_transmon_element import ExtendedTransmon
from quantify_scheduler.device_under_test.mock_setup import set_up_mock_transmon_setup, set_standard_params_transmon
QuantumDevice.close_all()


mock = set_up_mock_transmon_setup()
set_standard_params_transmon(mock)

q3 = mock['q3']
e0 = ExtendedTransmon('e0')

dut = QuantumDevice("DUT")

# Then create a transmon element
qubit = BasicTransmonElement("qubit")
# q2 = BasicTransmonElement("q2")


# Finally, add the transmon element to the QuantumDevice
dut.add_element(qubit)
qubit.clock_freqs.f01(6e9)
conf = json.dumps(qubit,cls=SchedulerJSONEncoder)

decoded_conf = json.loads(conf) # --> this is modifyable
re_encoded_conf = json.dumps(decoded_conf)

#---
QuantumDevice.close_all()
# # dut_2 = json.loads(decoded_conf, cls=SchedulerJSONDecoder) # fail
# # dut_2 = json.loads(conf, cls=SchedulerJSONDecoder) # works
# dut_2 = json.loads(re_encoded_conf, cls=SchedulerJSONDecoder) # works


serial = {'data': {'clock_freqs': {'f01': np.nan, 'f12': np.nan, 'readout': np.nan},
                   'extended_clock_freqs': {'readout_1': np.nan,
                                            'readout_2': np.nan,
                                            'readout_3state_opt': np.nan,
                                            'readout_opt': np.nan},
                   'measure': {'acq_channel': 0,
                               'acq_delay': 0,
                               'acq_rotation': 0,
                               'acq_threshold': 0,
                               'acq_weight_type': 'SSB',
                               'acq_weights_a': None,
                               'acq_weights_b': None,
                               'acq_weights_sampling_rate': None,
                               'integration_time': 1e-06,
                               'pulse_amp': 0.25,
                               'pulse_duration': 3e-07,
                               'pulse_type': 'SquarePulse',
                               'reset_clock_phase': True},
                   'measure_1': {'acq_channel': 0,
                                 'acq_delay': 0,
                                 'acq_rotation': 0,
                                 'acq_threshold': 0,
                                 'acq_weight_type': 'SSB',
                                 'acq_weights_a': None,
                                 'acq_weights_b': None,
                                 'acq_weights_sampling_rate': None,
                                 'integration_time': 1e-06,
                                 'pulse_amp': 0.25,
                                 'pulse_duration': 3e-07,
                                 'pulse_type': 'SquarePulse',
                                 'reset_clock_phase': True},
                   'measure_2': {'acq_channel': 0,
                                 'acq_delay': 0,
                                 'acq_rotation': 0,
                                 'acq_threshold': 0,
                                 'acq_weight_type': 'SSB',
                                 'acq_weights_a': None,
                                 'acq_weights_b': None,
                                 'acq_weights_sampling_rate': None,
                                 'integration_time': 1e-06,
                                 'pulse_amp': 0.25,
                                 'pulse_duration': 3e-07,
                                 'pulse_type': 'SquarePulse',
                                 'reset_clock_phase': True},
                   'measure_opt': {'acq_channel': 0,
                                   'acq_delay': 0,
                                   'acq_rotation': 0,
                                   'acq_threshold': 0,
                                   'acq_weight_type': 'SSB',
                                   'acq_weights_a': None,
                                   'acq_weights_b': None,
                                   'acq_weights_sampling_rate': None,
                                   'integration_time': 1e-06,
                                   'pulse_amp': 0.25,
                                   'pulse_duration': 3e-07,
                                   'pulse_type': 'SquarePulse',
                                   'reset_clock_phase': True},
                   'name': 'q12',
                   'ports': {'flux': 'q12:fl',
                             'microwave': 'q12:mw',
                             'readout': 'q12:res'},
                   'r12': {'ef_amp180': np.nan},
                   'reset': {'duration': 0.0002},
                   'rxy': {'amp180': np.nan, 'duration': 2e-08, 'motzoi': 0},
                   'spec': {'spec_amp': np.nan, 'spec_duration': 2e-08}},
          'deserialization_type': 'ExtendedTransmon',
          'mode': '__init__'}



encoded  = json.dumps(serial)
q12 = json.loads(encoded,cls=SchedulerJSONDecoder,modules=[extended_transmon_element])
