import json
from utilities.root_path import project_root
import csv

mixer_file = project_root / 'utilities/mixercorrection25QBClusterA.csv'
json_config_file = project_root / 'config_files/HARDWARE_CONFIGURATION.json'
HW_CONFIG = {}
HW_CONFIG['backend'] = "quantify_scheduler.backends.qblox_backend.hardware_compile"
HW_CONFIG['clusterA'] = {
    'ref': 'internal',
    "instrument_type": "Cluster",
}

module_to_qubit_map = {
        'module1': 'q1',
        'module2': 'q2',
        'module3': 'q3',
        'module4': 'q4',
        'module5': 'q5',
        'module6': 'q6',
        'module7': 'q7',
        'module8': 'q8',
        'module9': 'q9',
        'module10':'q10',
        'module11':'q11',
        'module12':'q12',
        }
qubits = ['q1','q2','q3']

def qrm_hw(qubits,cluster='clusterA', module='module16', lo=6e9, off_I=0.0, off_Q=0.0, amp_ratio=1., phase=0.0):
   hw = {}

   ro = [{"port": f"{qubit}:res", "clock": f"{qubit}.ro" , 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase} for qubit in qubits]
   ro1= [{"port": f"{qubit}:res", "clock": f"{qubit}.ro1", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase} for qubit in qubits]
   ro2= [{"port": f"{qubit}:res", "clock": f"{qubit}.ro2", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase} for qubit in qubits]
   hw = {
       'instrument_type': 'QRM_RF',
       'complex_output_0': {
           'lo_freq': lo,
           'dc_mixer_offset_I': off_I*1e-3,
           'dc_mixer_offset_Q': off_Q*1e-3,
           'portclock_configs': ro + ro1 + ro2,
       },
   }
   return hw

def qcm_hw(cluster='clusterA', module='module1', lo=4e9, off_I=0.0, off_Q=0.0, amp_ratio=1., phase=0.0):
   qubit = module_to_qubit_map[module]
   hw = {
       'instrument_type': 'QCM_RF',
       'complex_output_0': {
           'lo_freq': lo,
           'dc_mixer_offset_I': off_I*1e-3,
           'dc_mixer_offset_Q': off_Q*1e-3,
           'portclock_configs': [
               {"port": f"{qubit}:mw", "clock": f"{qubit}.01", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase},
               {"port": f"{qubit}:mw", "clock": f"{qubit}.12", 'mixer_amp_ratio': amp_ratio, 'mixer_phase_error_deg': phase},
           ],
       },
   }
   return hw

with open(mixer_file) as csvfile:
    reader = csv.reader(csvfile)
    #skip first row
    next(reader)
    for row in reader:
        if all(row):
            (label, module, cmpl_out, seq_indx, lo_freq, if_freq,
            off_I, off_Q, amp_ratio, phase_error_deg) = row
            lo_freq = float(lo_freq)
            off_I = float(off_I)
            off_Q = float(off_Q)
            amp_ratio = float(amp_ratio)
            phase_error_deg = float(phase_error_deg)

            if module == 'module16' or module == 'module17':
                qrm_config = qrm_hw(
                        qubits, module=module, lo=lo_freq,
                        off_I=off_I, off_Q=off_Q, amp_ratio=amp_ratio, phase=phase_error_deg
                        )
                HW_CONFIG[f'clusterA_{module}'] = qrm_config
            else:
                qcm_config = qcm_hw(
                        module=module, lo=lo_freq,
                        off_I=off_I, off_Q=off_Q, amp_ratio=amp_ratio, phase=phase_error_deg
                        )
                HW_CONFIG[f'clusterA_{module}'] = qcm_config


with open(json_config_file,'w') as f:
    json.dump(HW_CONFIG,f,indent=3)
