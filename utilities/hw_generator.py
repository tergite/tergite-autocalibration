# ClusterB,module,complex_output,sequencer index,lo_freq (Hz),if (Hz),dc_mixer_offset_I,dc_mixer_offset_Q,mixer_amp_ratio,mixer_phase_error_deg
from rich import pretty
import numpy as np

calib16 = [16,6.62e+09  ,-8.8298,1.2304,1,0]
calib17 = [17,6680000000,-5.0663,1.5922,1,0]

calib1 = [16,1,3283000000,-9.5173,-1.3028,1.0685,-16.21206]
calib2 = [17,2,4006610000,-8.0698,-0.5428,0.9928,-15.1988]
calib3 = [18,3,3328310000,-5.1748,-11.3991,1.0632,-18.7452]
calib4 = [19,4,3.99e+09,-8.7937,-2.4969,0.9907,-13.4618]
calib5 = [20,5,3413040000,-10.7838,-1.8574,1.0174,-23.01532]
calib6 = [21,6,3848060000,-10.784,-0.1086,0.9827,-8.82979]
calib7 = [22,7,3404090000,-11.1097,-8.9746,1.0384,-26.6341]
calib8 = [23,8,3986040000,-6.369,-1.5923,0.9893,-18.45569]
calib9 = [24,9,3352940000,-17.9129,-7.7442,1.0615,-20.04796]
calib10= [25,10,4081610000,-6.0072,-5.5368,0.9914,-17.73194]

calibB6  = [11,6,3793740000,-8.9746,-0.0724,0.9844,-23.81146]
calibB7  = [12,7,3441770000,-10.3496,-7.2376,1.0111,-23.30484]
calibB8  = [13,8,3666900000,-10.3497,-2.4246,0.9955,-10.63916]
calibB9  = [14,9,3406770000,-10.6392,-10.1687,1.0188,-18.96232]
calibB10 = [15,10,3952580000,-5.4282,-1.0132,0.986,-17.51481]

calibB17 = [17,6740000000,-7.3461,-6.3329,1,0]


def qrm_hw(cluster='clusterA', module_N=0, lo='6e9', off_I=0.0, off_Q=0.0, amp_ratio=1., phase=0.0):
    hw = {}
    key = cluster + '_' + f'module{module_N}'
    if module_N == 16 and cluster=='clusterA':
       qubits = np.arange(16,21).astype(int)
    elif module_N == 17 and cluster=='clusterA':
       qubits = np.arange(21,26).astype(int)
    elif module_N == 17 and cluster=='clusterB':
       qubits = np.arange(11,16).astype(int)
    else:
        raise ValueError('invalid module')

    ro = [{"port": f"q{qubit_N}:res", "clock": f"q{qubit_N}.ro" , 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase} for qubit_N in qubits]
    ro1= [{"port": f"q{qubit_N}:res", "clock": f"q{qubit_N}.ro1", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase} for qubit_N in qubits]
    ro2= [{"port": f"q{qubit_N}:res", "clock": f"q{qubit_N}.ro2", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase} for qubit_N in qubits]
    hw[key] = {
        'instrument_type': 'QRM_RF',
        'complex_output_0': {
            'lo_freq': lo,
            'dc_mixer_offset_I': off_I*1e-3,
            'dc_mixer_offset_Q': off_Q*1e-3,
            'portclock_configs': ro + ro1 + ro2,
        },
    }
    return hw

def qcm_hw(cluster='clusterA', qubit_N=16,module_N=0, lo='6e9', off_I=0.0, off_Q=0.0, amp_ratio=1., phase=0.0):

    hw = {}
    key = cluster + '_' + f'module{module_N}'
    hw[key] = {
        'instrument_type': 'QCM_RF',
        'complex_output_0': {
            'lo_freq': lo,
            'dc_mixer_offset_I': off_I*1e-3,
            'dc_mixer_offset_Q': off_Q*1e-3,
            'portclock_configs': [
                {"port": f"q{qubit_N}:mw", "clock": f"q{qubit_N}.01", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase},
                {"port": f"q{qubit_N}:mw", "clock": f"q{qubit_N}.12", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase},
            ],
        },
    }
    return hw

hw_config = {}
hw_config['backend'] = "quantify_scheduler.backends.qblox_backend.hardware_compile"
hw_config['clusterA'] = {
    'ref': 'internal',
    "instrument_type": "Cluster",
}
hw_config['clusterB'] = {
    'ref': 'internal',
    "instrument_type": "Cluster",
}

hw_config['clusterA'].update(qcm_hw('clusterA',*calib1 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib2 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib3 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib4 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib5 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib6 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib7 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib8 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib9 ))
hw_config['clusterA'].update(qcm_hw('clusterA',*calib10))
hw_config['clusterA'].update(qrm_hw('clusterA',*calib16))
hw_config['clusterA'].update(qrm_hw('clusterA',*calib17))

hw_config['clusterB'].update(qcm_hw('clusterB',*calibB6 ))
hw_config['clusterB'].update(qcm_hw('clusterB',*calibB7 ))
hw_config['clusterB'].update(qcm_hw('clusterB',*calibB8 ))
hw_config['clusterB'].update(qcm_hw('clusterB',*calibB9 ))
hw_config['clusterB'].update(qcm_hw('clusterB',*calibB10))
hw_config['clusterB'].update(qrm_hw('clusterB',*calibB17))

pretty.pprint(hw_config)
