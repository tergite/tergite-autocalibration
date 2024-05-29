# How to use SRegistry

## 1. Purpose

We need a simpler way to read and write the values stored in the redis server instead of invoking its builtin method and dealing with complex key names.

## 2. Initialize 

It's quite easy after launching the redis server.
You can initialize a `SRegistry` as follows
```
In [1]: from tergite_autocalibration.tools.sreg import SRegistry
In [2]: s = SRegistry()
```
`SRegistry` object has wrapped up a redis connection which is imported from the `setting.py` file.

## 3. Read and write
To read values from the redis server for a specific qubit such as `q07`, it becomes effortless with a simple command `s.q07`
```
In [4]: s.q07
Out[4]: 
{'measure': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'acq_delay': '2.2e-07',
              'pulse_amp': '0.025',
              'pulse_duration': '3e-06',
              'integration_time': '2.5e-06'}),
 'clock_freqs': 'nan',
 'Ql': '14677.032656082309',
 'resonator_minimum': '7086670000.0',
 'extended_clock_freqs': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'readout_1': '7086400037.630422',
              'readout_2': 'nan',
              'readout_2state_opt': 'nan',
              'readout_3state_opt': 'nan'}),
 'Ql_1': '13150.72366833144',
 'resonator_minimum_1': '7086390000.0',
 'measure_2state_opt': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'ro_ampl_2st_opt': 'nan',
              'acq_rotation': 'nan',
              'acq_threshold': 'nan'}),
 'measure_3state_opt': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'ro_ampl_3st_opt': 'nan'}),
 'inv_cm_opt': 'nan',
 'spec_ampl_optimal': 'nan',
 'anharmonicity': 'nan',
 'spec_ampl_12_optimal': 'nan',
 'rxy': 'nan',
 'r12': 'nan',
 'fidelity': 'nan',
 't1_time': 'nan',
 't2_time': 'nan',
 't2_echo_time': 'nan',
 'selectivity': 'nan',
 'reset_amplitude_qc': 'nan',
 'reset_duration_qc': 'nan',
 'measure_1': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'acq_delay': '2.2e-07',
              'pulse_duration': '3e-06',
              'integration_time': '2.5e-06',
              'pulse_amp': '0.001'}),
 'measure_2': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'acq_delay': '2.2e-07',
              'pulse_duration': '3e-06',
              'integration_time': '2.5e-06',
              'pulse_amp': '0.001'}),
 'reset': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'duration': '0.0006'}),
 'spec': defaultdict(<function tergite_autocalibration.tools.sreg.lib.nested_dd()>,
             {'spec_duration': '4e-06',
              'spec_ampl_optimal': '0.003',
              'spec_ampl_12_optimal': '0.001',
              'spec_amp': 'nan'}),
 'parking_current': 'nan'}

```
To be more explicit, if you only want to know the value of a subkey, you can easily access it by navigating through the attributes one by one
```
In [5]: s.q07.measure.acq_delay
Out[5]: '2.2e-07'
```
The example code is equivalent to read the value of the key `transmons:q07:measure:acq_delay` by using the `hget` method of a redis connection.

It, of course, allows to override the value in a straightforward way
```
In [6]: s.q07.measure.acq_delay = 2.3e-8
freshing...

In [7]: s.q07.measure.acq_delay
Out[7]: 2.3e-08
```



