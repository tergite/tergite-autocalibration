hardware_config = {
   'backend': 'quantify_scheduler.backends.qblox_backend.hardware_compile',
   'clusterA': {
      'ref': 'internal',
      'instrument_type': 'Cluster',
      'clusterA_module1': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq': 3.330e9,
            'dc_mixer_offset_I': -0.0095173,
            'dc_mixer_offset_Q': -0.0013028,
            'portclock_configs': [
               {'port': 'q16:mw', 'clock': 'q16.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206,},
               {'port': 'q16:mw', 'clock': 'q16.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206,}
            ]
         }
      },
      'clusterA_module7': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq': 3.455e9,
            'dc_mixer_offset_I': -0.0111097,
            'dc_mixer_offset_Q': -0.008974600000000001,
            'portclock_configs': [
               {'port': 'q22:mw', 'clock': 'q22.01', 'mixer_amp_ratio': 1.0384, 'mixer_phase_error_deg': -26.6341,},
               {'port': 'q22:mw', 'clock': 'q22.12', 'mixer_amp_ratio': 1.0384, 'mixer_phase_error_deg': -26.6341,}
            ]
         }
      },
      'clusterA_module8': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq': 4.080e9,
            'dc_mixer_offset_I': -0.006369,
            'dc_mixer_offset_Q': -0.0015923,
            'portclock_configs': [
               {'port': 'q23:mw', 'clock': 'q23.01', 'mixer_amp_ratio': 0.9893, 'mixer_phase_error_deg': -18.45569,},
               {'port': 'q23:mw', 'clock': 'q23.12', 'mixer_amp_ratio': 0.9893, 'mixer_phase_error_deg': -18.45569,}
            ]
         }
      },

      'clusterA_module16': {
         'instrument_type': 'QRM_RF',
         'complex_output_0': {
            'lo_freq': 6620000000.0,
            'dc_mixer_offset_I': -0.0088298,
            'dc_mixer_offset_Q': 0.0012304,
            'portclock_configs': [
               {'port': 'q16:res', 'clock': 'q16.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q17:res', 'clock': 'q17.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q18:res', 'clock': 'q18.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q19:res', 'clock': 'q19.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q20:res', 'clock': 'q20.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q16:res', 'clock': 'q16.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q17:res', 'clock': 'q17.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q18:res', 'clock': 'q18.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q19:res', 'clock': 'q19.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q20:res', 'clock': 'q20.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q16:res', 'clock': 'q16.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q17:res', 'clock': 'q17.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q18:res', 'clock': 'q18.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q19:res', 'clock': 'q19.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q20:res', 'clock': 'q20.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0}
            ]
         }
      },
      'clusterA_module17': {
         'instrument_type': 'QRM_RF',
         'complex_output_0': {
            'lo_freq': 6680000000,
            'dc_mixer_offset_I': -0.0050663,
            'dc_mixer_offset_Q': 0.0015922,
            'portclock_configs': [
               {'port': 'q21:res', 'clock': 'q21.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q22:res', 'clock': 'q22.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q23:res', 'clock': 'q23.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q24:res', 'clock': 'q24.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q25:res', 'clock': 'q25.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q21:res', 'clock': 'q21.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q22:res', 'clock': 'q22.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q23:res', 'clock': 'q23.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q24:res', 'clock': 'q24.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q25:res', 'clock': 'q25.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q21:res', 'clock': 'q21.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q22:res', 'clock': 'q22.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q23:res', 'clock': 'q23.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q24:res', 'clock': 'q24.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
               {'port': 'q25:res', 'clock': 'q25.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0}
            ]
         }
      }
   },
}
