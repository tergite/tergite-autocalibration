import csv
import json

from tergite_acl.config.settings import CONFIG_DIR

mixer_file = CONFIG_DIR / 'initial.csv'
json_config_file = CONFIG_DIR / 'HARDWARE_CONFIGURATION_LOKIA_20240504.json'
HW_CONFIG = {}
HW_CONFIG['backend'] = "quantify_scheduler.backends.qblox_backend.hardware_compile"
HW_CONFIG['clusterA'] = {
    'ref': 'internal',
    "instrument_type": "Cluster",
}

module_to_qubit_map = {
    'module1': 'q06',
    'module2': 'q07',
    'module3': 'q08',
    'module4': 'q09',
    'module5': 'q10',
    'module6': 'q11',
    'module7': 'q12',
    'module8': 'q13',
    'module9': 'q14',
    'module10':'q15',
}
module_16_qubits = ['q06', 'q07', 'q08', 'q09', 'q10']
module_17_qubits = ['q11', 'q12', 'q13', 'q14', 'q15']
qubits = module_to_qubit_map.values()


def qrm_hw(qubits, cluster='clusterA', module='module16', lo=6e9, off_I=0.0, off_Q=0.0, amp_ratio=1., phase=0.0):
    hw = {}

    ro = [] # readout when qubit at |0>
    ro1 = [] # readout when qubit at |1>
    ro2 = [] # readout when qubit at |2>
    ro_2st_opt = [] # readout for optimum 2 state discrimination
    ro_3st_opt = [] # readout for optimum 3 state discrimination

    for qubit in qubits:
        ro_config = {
            "port": f"{qubit}:res",
            "clock": f"{qubit}.ro",
            'mixer_amp_ratio': amp_ratio,
            'mixer_phase_error_deg': phase
        }

        ro.append(ro_config)

        ro1_config = {
            "port": f"{qubit}:res",
            "clock": f"{qubit}.ro1",
            'mixer_amp_ratio': amp_ratio,
            'mixer_phase_error_deg': phase
        }

        ro1.append(ro1_config)

        ro2_config = {
            "port": f"{qubit}:res",
            "clock": f"{qubit}.ro2",
            'mixer_amp_ratio': amp_ratio,
            'mixer_phase_error_deg': phase
        }

        ro2.append(ro2_config)

        ro_2st_opt_config = {
            "port": f"{qubit}:res",
            "clock": f"{qubit}.ro_2st_opt",
            'mixer_amp_ratio': amp_ratio,
            'mixer_phase_error_deg': phase
        }

        ro_2st_opt.append(ro_2st_opt_config)

        ro_3st_opt_config = {
            "port": f"{qubit}:res",
            "clock": f"{qubit}.ro_3st_opt",
            'mixer_amp_ratio': amp_ratio,
            'mixer_phase_error_deg': phase
        }

        ro_3st_opt.append(ro_3st_opt_config)


    hw = {
        'instrument_type': 'QRM_RF',
        'complex_output_0': {
            'lo_freq': lo,
            'dc_mixer_offset_I': off_I * 1e-3,
            'dc_mixer_offset_Q': off_Q * 1e-3,
            'portclock_configs': ro + ro1 + ro2 + ro_2st_opt + ro_3st_opt,
        },
    }
    return hw


def qcm_hw(
    cluster='clusterA',
    module='module1',
    sequencer=0,
    lo=4e9,
    off_I=0.0,
    off_Q=0.0,
    amp_ratio=1.,
    phase=0.0,
    amp_ratio_2=1.,
    phase_2=0.0,
):
    qubit = module_to_qubit_map[module]
    hw = {
        'instrument_type': 'QCM_RF',
        'complex_output_0': {
            'lo_freq': lo,
            'dc_mixer_offset_I': off_I * 1e-3,
            'dc_mixer_offset_Q': off_Q * 1e-3,
            'portclock_configs': [
                {
                    'port': f'{qubit}:mw',
                    'clock': f'{qubit}.01',
                    'mixer_amp_ratio': amp_ratio,
                    'mixer_phase_error_deg': phase
                },
                {
                    'port': f'{qubit}:mw',
                    'clock': f'{qubit}.12',
                    'mixer_amp_ratio': amp_ratio_2,
                    'mixer_phase_error_deg': phase_2
                },
            ],
        },
    }
    return hw


with open(mixer_file) as csvfile:
    reader = csv.reader(csvfile)
    # skip first row
    next(reader)
    for row in reader:
        if all(row):
            # (label, module, cmpl_out, seq_indx, lo_freq, if_freq,
            #  off_I, off_Q, amp_ratio, phase_error_deg, amp_ratio_2, phase_error_deg_2) = row
            label = row[0]
            module = row[1]
            complex_out = row[2]
            lo_freq = float(row[3])

            # off_I = float(off_I)
            # off_Q = float(off_Q)
            # amp_ratio = float(amp_ratio)
            # phase_error_deg = float(phase_error_deg)
            # amp_ratio_2 = float(amp_ratio_2)
            # phase_error_deg_2 = float(phase_error_deg_2)

            if module == 'module16' or module == 'module17':
                if module == 'module16':
                    qrm_qubits = module_16_qubits
                if module == 'module17':
                    qrm_qubits = module_17_qubits
                qrm_config = qrm_hw(
                    qrm_qubits, module=module, lo=lo_freq,
                    # off_I=off_I, off_Q=off_Q, amp_ratio=amp_ratio, phase=phase_error_deg
                )
                HW_CONFIG['clusterA'][f'clusterA_{module}'] = qrm_config
            else:
                qcm_config = qcm_hw(
                    module=module, lo=lo_freq,
                    # off_I=off_I, off_Q=off_Q, amp_ratio=amp_ratio, phase=phase_error_deg, amp_ratio_2=amp_ratio_2,
                    # phase_2=phase_error_deg_2
                )
                HW_CONFIG['clusterA'][f'clusterA_{module}'] = qcm_config

with open(json_config_file, 'w') as f:
    json.dump(HW_CONFIG, f, indent=3)
