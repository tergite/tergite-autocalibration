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
               {'port': 'q16:mw', 'clock': 'q16.01', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,},
               {'port': 'q16:mw', 'clock': 'q16.12', 'mixer_amp_ratio': 1.0685, 'mixer_phase_error_deg': -16.21206, "interm_freq":-100e6,}
            ]
         }
      },
      'clusterA_module2': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0080698,
            'dc_mixer_offset_Q': -0.0005428,
            'portclock_configs': [
               {'port': 'q17:mw', 'clock': 'q17.01', 'mixer_amp_ratio': 0.9928, 'mixer_phase_error_deg': -15.1988,'interm_freq':-100e6},
               {'port': 'q17:mw', 'clock': 'q17.12', 'mixer_amp_ratio': 0.9928, 'mixer_phase_error_deg': -15.1988,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module3': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0051748,
            'dc_mixer_offset_Q': -0.0113991,
            'portclock_configs': [
               {'port': 'q18:mw', 'clock': 'q18.01', 'mixer_amp_ratio': 1.0632, 'mixer_phase_error_deg': -18.7452,'interm_freq':-100e6},
               {'port': 'q18:mw', 'clock': 'q18.12', 'mixer_amp_ratio': 1.0632, 'mixer_phase_error_deg': -18.7452,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module4': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0087937,
            'dc_mixer_offset_Q': -0.0024969000000000002,
            'portclock_configs': [
               {'port': 'q19:mw', 'clock': 'q19.01', 'mixer_amp_ratio': 0.9907, 'mixer_phase_error_deg': -13.4618,'interm_freq':-100e6},
               {'port': 'q19:mw', 'clock': 'q19.12', 'mixer_amp_ratio': 0.9907, 'mixer_phase_error_deg': -13.4618,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module5': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0107838,
            'dc_mixer_offset_Q': -0.0018574,
            'portclock_configs': [
               {'port': 'q20:mw', 'clock': 'q20.01', 'mixer_amp_ratio': 1.0174, 'mixer_phase_error_deg': -23.01532,'interm_freq':-100e6},
               {'port': 'q20:mw', 'clock': 'q20.12', 'mixer_amp_ratio': 1.0174, 'mixer_phase_error_deg': -23.01532,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module6': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.010784,
            'dc_mixer_offset_Q': -0.00010860000000000001,
            'portclock_configs': [
               {'port': 'q21:mw', 'clock': 'q21.01', 'mixer_amp_ratio': 0.9827, 'mixer_phase_error_deg': -8.82979,'interm_freq':-100e6},
               {'port': 'q21:mw', 'clock': 'q21.12', 'mixer_amp_ratio': 0.9827, 'mixer_phase_error_deg': -8.82979,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module7': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0111097,
            'dc_mixer_offset_Q': -0.008974600000000001,
            'portclock_configs': [
               {'port': 'q22:mw', 'clock': 'q22.01', 'mixer_amp_ratio': 1.0384, 'mixer_phase_error_deg': -26.6341,'interm_freq':-100e6},
               {'port': 'q22:mw', 'clock': 'q22.12', 'mixer_amp_ratio': 1.0384, 'mixer_phase_error_deg': -26.6341,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module8': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.006369,
            'dc_mixer_offset_Q': -0.0015923,
            'portclock_configs': [
               {'port': 'q23:mw', 'clock': 'q23.01', 'mixer_amp_ratio': 0.9893, 'mixer_phase_error_deg': -18.45569,'interm_freq':-100e6},
               {'port': 'q23:mw', 'clock': 'q23.12', 'mixer_amp_ratio': 0.9893, 'mixer_phase_error_deg': -18.45569,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module9': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.017912900000000002,
            'dc_mixer_offset_Q': -0.0077442000000000006,
            'portclock_configs': [
               {'port': 'q24:mw', 'clock': 'q24.01', 'mixer_amp_ratio': 1.0615, 'mixer_phase_error_deg': -20.04796,'interm_freq':-100e6},
               {'port': 'q24:mw', 'clock': 'q24.12', 'mixer_amp_ratio': 1.0615, 'mixer_phase_error_deg': -20.04796,'interm_freq':-100e6}
            ]
         }
      },
      'clusterA_module10': {
         'instrument_type': 'QCM_RF',
         'complex_output_0': {
            'lo_freq':None,
            'dc_mixer_offset_I': -0.0060072,
            'dc_mixer_offset_Q': -0.005536800000000001,
            'portclock_configs': [
               {'port': 'q25:mw', 'clock': 'q25.01', 'mixer_amp_ratio': 0.9914, 'mixer_phase_error_deg': -17.73194,'interm_freq':-100e6},
               {'port': 'q25:mw', 'clock': 'q25.12', 'mixer_amp_ratio': 0.9914, 'mixer_phase_error_deg': -17.73194,'interm_freq':-100e6}
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
   #'clusterB': {
   #   'ref': 'internal',
   #   'instrument_type': 'Cluster',
   #   'clusterB_module6': {
   #      'instrument_type': 'QCM_RF',
   #      'complex_output_0': {
   #         'lo_freq':None,
   #         'dc_mixer_offset_I': -0.008974600000000001,
   #         'dc_mixer_offset_Q': -7.240000000000001e-05,
   #         'portclock_configs': [
   #            {'port': 'q11:mw', 'clock': 'q11.01', 'mixer_amp_ratio': 0.9844, 'mixer_phase_error_deg': -23.81146,'interm_freq':-100e6},
   #            {'port': 'q11:mw', 'clock': 'q11.12', 'mixer_amp_ratio': 0.9844, 'mixer_phase_error_deg': -23.81146,'interm_freq':-100e6}
   #         ]
   #      }
   #   },
   #   'clusterB_module7': {
   #      'instrument_type': 'QCM_RF',
   #      'complex_output_0': {
   #         'lo_freq':None,
   #         'dc_mixer_offset_I': -0.0103496,
   #         'dc_mixer_offset_Q': -0.007237599999999999,
   #         'portclock_configs': [
   #            {'port': 'q12:mw', 'clock': 'q12.01', 'mixer_amp_ratio': 1.0111, 'mixer_phase_error_deg': -23.30484,'interm_freq':-100e6},
   #            {'port': 'q12:mw', 'clock': 'q12.12', 'mixer_amp_ratio': 1.0111, 'mixer_phase_error_deg': -23.30484,'interm_freq':-100e6}
   #         ]
   #      }
   #   },
   #   'clusterB_module8': {
   #      'instrument_type': 'QCM_RF',
   #      'complex_output_0': {
   #         'lo_freq':None,
   #         'dc_mixer_offset_I': -0.0103497,
   #         'dc_mixer_offset_Q': -0.0024246,
   #         'portclock_configs': [
   #            {'port': 'q13:mw', 'clock': 'q13.01', 'mixer_amp_ratio': 0.9955, 'mixer_phase_error_deg': -10.63916,'interm_freq':-100e6},
   #            {'port': 'q13:mw', 'clock': 'q13.12', 'mixer_amp_ratio': 0.9955, 'mixer_phase_error_deg': -10.63916,'interm_freq':-100e6}
   #         ]
   #      }
   #   },
   #   'clusterB_module9': {
   #      'instrument_type': 'QCM_RF',
   #      'complex_output_0': {
   #         'lo_freq':None,
   #         'dc_mixer_offset_I': -0.010639200000000001,
   #         'dc_mixer_offset_Q': -0.0101687,
   #         'portclock_configs': [
   #            {'port': 'q14:mw', 'clock': 'q14.01', 'mixer_amp_ratio': 1.0188, 'mixer_phase_error_deg': -18.96232,'interm_freq':-100e6},
   #            {'port': 'q14:mw', 'clock': 'q14.12', 'mixer_amp_ratio': 1.0188, 'mixer_phase_error_deg': -18.96232,'interm_freq':-100e6}
   #         ]
   #      }
   #   },
   #   'clusterB_module10': {
   #      'instrument_type': 'QCM_RF',
   #      'complex_output_0': {
   #         'lo_freq':None,
   #         'dc_mixer_offset_I': -0.0054282,
   #         'dc_mixer_offset_Q': -0.0010132000000000001,
   #         'portclock_configs': [
   #            {'port': 'q15:mw', 'clock': 'q15.01', 'mixer_amp_ratio': 0.986, 'mixer_phase_error_deg': -17.51481,'interm_freq':-100e6},
   #            {'port': 'q15:mw', 'clock': 'q15.12', 'mixer_amp_ratio': 0.986, 'mixer_phase_error_deg': -17.51481,'interm_freq':-100e6}
   #         ]
   #      }
   #   },
   #   'clusterB_module17': {
   #      'instrument_type': 'QRM_RF',
   #      'complex_output_0': {
   #         'lo_freq': 6740000000,
   #         'dc_mixer_offset_I': -0.0073461,
   #         'dc_mixer_offset_Q': -0.006332900000000001,
   #         'portclock_configs': [
   #            {'port': 'q11:res', 'clock': 'q11.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q12:res', 'clock': 'q12.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q13:res', 'clock': 'q13.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q14:res', 'clock': 'q14.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q15:res', 'clock': 'q15.ro', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q11:res', 'clock': 'q11.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q12:res', 'clock': 'q12.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q13:res', 'clock': 'q13.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q14:res', 'clock': 'q14.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q15:res', 'clock': 'q15.ro1', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q11:res', 'clock': 'q11.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q12:res', 'clock': 'q12.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q13:res', 'clock': 'q13.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q14:res', 'clock': 'q14.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0},
   #            {'port': 'q15:res', 'clock': 'q15.ro2', 'mixer_amp_ratio': 1, 'mixer_phase_error_deg': 0}
   #         ]
   #      }
   #   }
   #}
}
