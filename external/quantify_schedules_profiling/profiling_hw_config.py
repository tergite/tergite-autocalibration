hardware_config = {
   'backend': 'quantify_scheduler.backends.qblox_backend.hardware_compile',
   'clusterA': {
      'ref': 'internal',
      'instrument_type': 'Cluster',
      'clusterA_module1': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q0:mw', 'clock': 'q0.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q0:mw', 'clock': 'q0.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q10:mw', 'clock': 'q10.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q10:mw', 'clock': 'q10.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module2': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0080698,
            'dc_mixer_offset_Q': -0.0005428,
            'portclock_configs': [
               {'port': 'q1:mw', 'clock': 'q1.01', 'mixer_amp_ratio': 0.9928, 'mixer_phase_error_deg': -15.1988,'interm_freq':-100e6},
               {'port': 'q1:mw', 'clock': 'q1.12', 'mixer_amp_ratio': 0.9928, 'mixer_phase_error_deg': -15.1988,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q11:mw', 'clock': 'q11.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q11:mw', 'clock': 'q11.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module3': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0051748,
            'dc_mixer_offset_Q': -0.0113991,
            'portclock_configs': [
               {'port': 'q2:mw', 'clock': 'q2.01', 'mixer_amp_ratio': 1.0632, 'mixer_phase_error_deg': -18.7452,'interm_freq':-100e6},
               {'port': 'q2:mw', 'clock': 'q2.12', 'mixer_amp_ratio': 1.0632, 'mixer_phase_error_deg': -18.7452,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q12:mw', 'clock': 'q12.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q12:mw', 'clock': 'q12.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module4': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0087937,
            'dc_mixer_offset_Q': -0.0024969000000000002,
            'portclock_configs': [
               {'port': 'q3:mw', 'clock': 'q3.01', 'mixer_amp_ratio': 0.9907, 'mixer_phase_error_deg': -13.4618,'interm_freq':-100e6},
               {'port': 'q3:mw', 'clock': 'q3.12', 'mixer_amp_ratio': 0.9907, 'mixer_phase_error_deg': -13.4618,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q13:mw', 'clock': 'q13.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q13:mw', 'clock': 'q13.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module5': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0107838,
            'dc_mixer_offset_Q': -0.0018574,
            'portclock_configs': [
               {'port': 'q4:mw', 'clock': 'q4.01', 'mixer_amp_ratio': 1.0174, 'mixer_phase_error_deg': -23.01532,'interm_freq':-100e6},
               {'port': 'q4:mw', 'clock': 'q4.12', 'mixer_amp_ratio': 1.0174, 'mixer_phase_error_deg': -23.01532,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q14:mw', 'clock': 'q14.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q14:mw', 'clock': 'q14.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module6': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.010784,
            'dc_mixer_offset_Q': -0.00010860000000000001,
            'portclock_configs': [
               {'port': 'q5:mw', 'clock': 'q5.01', 'mixer_amp_ratio': 0.9827, 'mixer_phase_error_deg': -8.82979,'interm_freq':-100e6},
               {'port': 'q5:mw', 'clock': 'q5.12', 'mixer_amp_ratio': 0.9827, 'mixer_phase_error_deg': -8.82979,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q15:mw', 'clock': 'q15.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q15:mw', 'clock': 'q15.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module7': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0111097,
            'dc_mixer_offset_Q': -0.008974600000000001,
            'portclock_configs': [
               {'port': 'q6:mw', 'clock': 'q6.01', 'mixer_amp_ratio': 1.0384, 'mixer_phase_error_deg': -26.6341,'interm_freq':-100e6},
               {'port': 'q6:mw', 'clock': 'q6.12', 'mixer_amp_ratio': 1.0384, 'mixer_phase_error_deg': -26.6341,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q16:mw', 'clock': 'q16.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q16:mw', 'clock': 'q16.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module8': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.006369,
            'dc_mixer_offset_Q': -0.0015923,
            'portclock_configs': [
               {'port': 'q7:mw', 'clock': 'q7.01', 'mixer_amp_ratio': 0.9893, 'mixer_phase_error_deg': -18.45569,'interm_freq':-100e6},
               {'port': 'q7:mw', 'clock': 'q7.12', 'mixer_amp_ratio': 0.9893, 'mixer_phase_error_deg': -18.45569,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q17:mw', 'clock': 'q17.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q17:mw', 'clock': 'q17.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module9': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.017912900000000002,
            'dc_mixer_offset_Q': -0.0077442000000000006,
            'portclock_configs': [
               {'port': 'q8:mw', 'clock': 'q8.01', 'mixer_amp_ratio': 1.0615, 'mixer_phase_error_deg': -20.04796,'interm_freq':-100e6},
               {'port': 'q8:mw', 'clock': 'q8.12', 'mixer_amp_ratio': 1.0615, 'mixer_phase_error_deg': -20.04796,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q18:mw', 'clock': 'q18.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q18:mw', 'clock': 'q18.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module10': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0060072,
            'dc_mixer_offset_Q': -0.005536800000000001,
            'portclock_configs': [
               {'port': 'q9:mw', 'clock': 'q9.01', 'mixer_amp_ratio': 0.9914, 'mixer_phase_error_deg': -17.73194,'interm_freq':-100e6},
               {'port': 'q9:mw', 'clock': 'q9.12', 'mixer_amp_ratio': 0.9914, 'mixer_phase_error_deg': -17.73194,'interm_freq':-100e6}
            ]
         },
         'complex_output_1': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.009517300000000001,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q19:mw', 'clock': 'q19.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q19:mw', 'clock': 'q19.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         },
      },
      'clusterA_module16': {
         'instrument_type': 'QRM_RF',
         'complex_output_0': {
            'lo_freq': 6e9,
            'dc_mixer_offset_I': -0.0088298,
            'dc_mixer_offset_Q': 0.0012304,
            'portclock_configs': [
               {'port': 'q0:res', 'clock': 'q0.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q1:res', 'clock': 'q1.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q2:res', 'clock': 'q2.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q3:res', 'clock': 'q3.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q4:res', 'clock': 'q4.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q5:res', 'clock': 'q5.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
            ]
         }
      },
      'clusterA_module17': {
         'instrument_type': 'QRM_RF',
         'complex_output_0': {
            'lo_freq': 6e9,
            'dc_mixer_offset_I': -0.0050663,
            'dc_mixer_offset_Q': 0.0015922,
            'portclock_configs': [
               {'port': 'q6:res', 'clock': 'q6.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q7:res', 'clock': 'q7.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q8:res', 'clock': 'q8.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q9:res', 'clock': 'q9.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q10:res', 'clock':'q10.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q11:res', 'clock':'q11.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
            ]
         }
      }
   },
}
