"""
Is this file necessary? Here we can perform customized experiments
in a more flexiable way rather than using calibration_supervisor.py.
Just for practicing?
Many functions here are overlapped with the calibration schedules.
"""

from quantify_scheduler.backends import SerialCompiler
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from quantify_scheduler.instrument_coordinator.components.qblox import ClusterComponent
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.pulse_library import  SquarePulse, SetClockFrequency, DRAGPulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.resources import ClockResource
from quantify_scheduler import Operation
from qblox_instruments import Cluster
import redis, toml
import numpy as np
from pickle import loads, dumps
from typing import Union
from workers.compilation_worker import ExtendedTransmon, CompositeSquareEdge, hw_config, \
                                        QuantumDevice, SerialCompiler, load_redis_config, load_redis_config_coupler

DEVICE_CONFIG_FILE = 'bring_up_config.toml'

def create_ic(ic_name='lab_ic', cluster='cluster', IP='192.168.1.1') -> InstrumentCoordinator:
    lab_ic = InstrumentCoordinator(ic_name)
    Cluster.close_all()
    clusterA = Cluster(cluster, IP)
    lab_ic.add_component(ClusterComponent(clusterA))
    return lab_ic

def hget_from_redis(*keys):
    try:
        redis_connection = redis.Redis(decode_responses=True)
        value = redis_connection.hget(*keys)
    except UnicodeDecodeError:
        redis_connection = redis.Redis(decode_responses=False)
        value = redis_connection.hget(*keys)
        value = loads(value)
    return value

def hset_into_redis(*paras):
    redis_connection = redis.Redis(decode_responses=True)
    if np.iterable(paras[-1]):
        value = dumps(paras[-1])
    paras = paras[:-1] + (value,)
    redis_connection.hset(*paras)

def load_redis_device_config(qubits:list[str], couplers:list[str]=None, config_file:str=DEVICE_CONFIG_FILE, \
                             device_name='loki-a-bring-up', ic_name='lab_ic') -> QuantumDevice:
    redis_connection = redis.Redis(decode_responses=True)
    transmon_configuration = toml.load(config_file)
    #--------------------- load qubits ----------------------#
    # Populate the Redis database with the quantities of interest, at Nan value
    # Only if the key does NOT already exist
    initial_qubit_parameters = transmon_configuration['initials']['qubits']
    qubit_quantities_of_interest = transmon_configuration['qoi']['qubits']
    for node_name, node_parameters_dictionary in qubit_quantities_of_interest.items():
        # named field as Redis calls them fields
        for qubit in qubits:
            redis_key = f'transmons:{qubit}'
            for field_key, field_value in node_parameters_dictionary.items():
                # check if field already exists
                if not redis_connection.hexists(redis_key, field_key):
                    redis_connection.hset(f'transmons:{qubit}', field_key, field_value)

    # Populate the Redis database with the initial 'reasonable'
    # parameter values from the toml file
    for qubit in qubits:
        # parameter common to all qubits:
        for parameter_key, parameter_value in initial_qubit_parameters['all'].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)

        # parameter specific to each qubit:
        for parameter_key, parameter_value in initial_qubit_parameters[qubit].items():
            redis_connection.hset(f"transmons:{qubit}", parameter_key, parameter_value)
    
    if couplers is not None:
        #--------------------- load couplers ----------------------#
        initial_coupler_parameters = transmon_configuration['initials']['couplers']
        coupler_quantities_of_interest = transmon_configuration['qoi']['couplers']
        # Populate the Redis database with the quantities of interest, at Nan value
        # Only if the key does NOT already exist
        for node_name, node_parameters_dictionary in coupler_quantities_of_interest.items():
            for coupler in couplers:
                redis_key = f'couplers:{coupler}'
                for field_key, field_value in node_parameters_dictionary.items():
                    # check if field already exists
                    if not redis_connection.hexists(redis_key, field_key):
                        redis_connection.hset(f'couplers:{coupler}', field_key, field_value)

        for coupler in couplers:
            for parameter_key, parameter_value in initial_coupler_parameters['all'].items():
                redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)

            if coupler in initial_coupler_parameters:
                for parameter_key, parameter_value in initial_coupler_parameters[coupler].items():
                    redis_connection.hset(f"couplers:{coupler}", parameter_key, parameter_value)
    else:
        couplers = []
    # Define a new quantum device
    device = QuantumDevice(device_name)
    device.hardware_config(hw_config)
    device.instr_instrument_coordinator(ic_name)
    hset_into_redis('qubits_config', 'qubits', qubits)
    hset_into_redis('qubits_config', 'couplers', couplers)
    return device    

#TODO
def get_coupler_parent(coupler:str) -> tuple[str]:
    return ('q1', 'q2')
                    
def load_qubits(device):
    qubits = hget_from_redis('qubits_config', 'qubits')
    couplers = hget_from_redis('qubits_config', 'couplers')
    transmons = []
    for qch, q in enumerate(qubits):
        transmon = ExtendedTransmon(q)
        load_redis_config(transmon, qch)
        device.add_element(transmon)
        transmons.append(transmon)
    if len(couplers):
        transmon_couplers = []
        for cch, q in enumerate(couplers):
            coupler = CompositeSquareEdge(get_coupler_parent(*q))
            load_redis_config_coupler(coupler, cch + qch + 1)
            device.add_element(coupler)
            transmon_couplers.append(coupler)
        return transmons, transmon_couplers
    else:
        return transmons
    
def to_list(l):
        return list(l) if np.iterable(l) else [l]
    
def qubit_def(qubits:dict[str, ExtendedTransmon], measure, measure_xy=None, measure_z=None, measure_rr=None, measure_read=None, measure_cz=None):
    '''
        Define qubits. 
        Do experiment on qubits indexed by measure.
        Qubits indexed by measure are drived by xy line on qubits indexed by measure_xy.
        Add rr pulse on qubits indexed by measure_rr.
        Readout qubits indexed by measure_read.
        
    '''
    measure = list(measure) if np.iterable(measure) else [measure]
    if measure_xy == None: measure_xy = measure
    if measure_z == None: measure_z = measure
    if measure_rr == None: measure_rr = measure
    if measure_read == None: measure_read = measure_rr
    
    measure_xy, measure_z, measure_rr, measure_read = to_list(measure_xy), to_list(measure_z), to_list(measure_rr), to_list(measure_read)
    assert len(measure_xy) == len(measure)
    assert set(measure_read).issubset(set(measure_rr)), 'measure_rr must contain elements in measure_read'

    q = [qubits[int(ii)] for ii in measure]
    qxy = [qubits[int(ii)] for ii in measure_xy]
    qz = [qubits[int(ii)] for ii in measure_z]
    qrr = [qubits[int(ii)] for ii in measure_rr]
    qread = [qubits[int(ii)] for ii in measure_read]
    qrrNames = [qubits[int(ii)].__name__ for ii in measure_rr]
    qreadNames = [qubits[int(ii)].__name__ for ii in measure_read]
    readout = [True if qii in qreadNames else False for qii in qrrNames]    
    if measure_post != None:
        measure_post = measure_post if np.iterable(measure_post) else [measure_post]
        q_post = [qubits[ii] for ii in measure_post]
        readout = [True if qii in q_post else readout[ii] for ii,qii in enumerate(qrr)]
    if len(q) == 1: q = q[0]
    if len(qz) == 1: qz = qz[0]
    if len(qxy) == 1: qxy = qxy[0]
    if len(qrr) == 1: qrr = qrr[0]
    if len(qread) == 1: qread = qread[0]
    if measure_cz is not None:
        qc = [qubits[int(ii)] for ii in to_list(measure_cz)]
        if len(qc) == 1: qc = qc[0]
        return q, qxy, qz, qrr, qread, qc
    else:
        return q, qxy, qz, qrr, qread

def add_readout(sched:Schedule, index:int, qrr:Union[list, ExtendedTransmon], qread:Union[list, ExtendedTransmon], ref_op:Operation, \
                pulse_duration:Union[None, float]=None, pulse_amp:Union[None, float]=None, integration_time:Union[None, float]=None, acq_delay:[Union, float]=None):
    """
    Add readout pulses and demodulation operations to corresponding qubits.
    """
    if not np.iterable(pulse_duration): pulse_duration = [pulse_duration] * len(qrr)
    if not np.iterable(pulse_amp): pulse_amp = [pulse_amp] * len(qrr)
    if not np.iterable(integration_time): integration_time = [integration_time] * len(qread)
    if not np.iterable(acq_delay): acq_delay = [acq_delay] * len(qread)
    for i, q in enumerate(qrr):
        ipulse_duration = pulse_duration[i] or q.measure.pulse_duration.get()
        ipulse_amp = pulse_amp[i] or qrr.mesure.pulse_amp.get()
        ro_pulse = sched.add(
                SquarePulse(
                    duration=ipulse_duration,
                    amp=ipulse_amp,
                    port=q.name + ':res',
                    clock=q.name + '.ro',
                ),
                ref_op=ref_op
            )
        
    for i, q in enumerate(qread):
        sched.add(
            SSBIntegrationComplex(
                duration=integration_time[i] or q.measure.integration_time.get(),
                port=q.name + ':res',
                clock=q.name + '.ro',
                acq_index=index,
                acq_channel=i,
                bin_mode=BinMode.AVERAGE
            ),
            ref_op=ro_pulse, ref_pt="start",
            rel_time=acq_delay[i] or q.measure.acq_delay.get(),
        )

def tunneling_qubits(data, qubits:list[ExtendedTransmon]):
    """
    Convert IQ data into probabilities of tensor product states.
    """
    return 

def tunneling_qubits_v2(data, qubits:list[ExtendedTransmon]):
    return

def s21_scan(ic, dev, freqs, measure=0, measure_xy=None, measure_z=None, measure_read=None, measure_rr=None, 
             pulse_amp=1, pulse_duration=None, integration_time=None, acq_delay=None, bias=None, reps=3000):
    sched = Schedule("multiplexed_resonator_spectroscopy", reps)
    qubits = load_qubits(dev)
    q, qxy, qz, qrr, qread = qubit_def(qubits, measure, measure_xy, measure_z, measure_rr, measure_read)
    for freq in freqs:
        sched.add_resource(ClockResource(name=ro_clock, freq=freq))
    root_relaxation = sched.add(Reset(*qubits), label="Reset")

    for acq_index, ro_frequency in enumerate(freqs):
        ro_clock = qrr.name + '.ro'
        sched.add(
            SetClockFrequency(clock=ro_clock, clock_freq_new=ro_frequency),
        )
        add_readout(sched, acq_index, qrr, qread, root_relaxation, pulse_duration=pulse_duration, pulse_amp=pulse_amp, \
                    integration_time=integration_time, acq_delay=acq_delay)
        sched.add(Reset(q))

    compilation_config = dev.generate_compilation_config()
    compiler = SerialCompiler(name=f'sq_compiler')
    compiled_schedule = compiler.compile(schedule=sched, config=compilation_config)
    ic.prepare(compiled_schedule)
    ic.start()
    ic.wait_done(timeout_sec=10)
    acquisition = ic.retrieve_acquisition()
    


