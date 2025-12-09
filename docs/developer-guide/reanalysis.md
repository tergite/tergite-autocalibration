# Reanalysis

This document describes how to re-analyse data. The term re-analyse is used because only the analysis happens, which always happens during the postprocessing of every node, so it's technically a "re"-analysis.

## How to re-analyse data
The flag to use is `--re-analyse` or shorthand `-r`. Example:

```
acli start --re-analyse "out/2025-07-28/16-51-33_ro_amplitude_three_state_optimization-SUCCESS"
```

This will open up a prompt summarising the available data and asking you which one you want to re-analyse
```
Detected the following measurements in the specified folder:
1: resonator_spectroscopy (measured: 2025-07-28 16:51:36)
2: qubit_01_spectroscopy (measured: 2025-07-28 16:51:42)
3: rabi_oscillations (measured: 2025-07-28 16:52:19)
4: ramsey_correction (measured: 2025-07-28 16:52:37)
5: motzoi_parameter (measured: 2025-07-28 16:53:46)
6: n_rabi_oscillations (measured: 2025-07-28 16:54:26)
7: resonator_spectroscopy_1 (measured: 2025-07-28 16:54:58)
8: qubit_12_spectroscopy (measured: 2025-07-28 16:55:24)
9: rabi_oscillations_12 (measured: 2025-07-28 16:56:02)
10: ramsey_correction_12 (measured: 2025-07-28 16:56:20)
11: motzoi_parameter_12 (measured: 2025-07-28 16:57:30)
12: n_rabi_oscillations_12 (measured: 2025-07-28 16:58:07)
13: resonator_spectroscopy_2 (measured: 2025-07-28 16:58:43)
14: ro_frequency_three_state_optimization (measured: 2025-07-28 16:59:10)
15: ro_amplitude_three_state_optimization (measured: 2025-07-28 17:00:30)

Which would you like to reanalyse? Please enter a number between 1 and 15: 2
```
Which would re-analyse the qubit spectroscopy. If you changed your mind and you don't want to re-analyse, you can type 0 to abort re-analysis.

The `-r` argument is also compatibile with the `--node-name` argument (shorthand `-n`). So for example:

```
acli start --re-analyse "out/2025-07-28/16-51-33_ro_amplitude_three_state_optimization-SUCCESS" -n qubit_01_spectroscopy
```

Will do the same thing. The data will be copied to a new folder in your default data directory (usually `"out"`), together with a new `autocalibration.log` and the new re-analysis output (figures, etc).

It is also possible to directly specify the name of the measurement folder, like so:
```
acli start --re-analyse 20250728-165142-378-6c2eaa-qubit_01_spectroscopy
```
In which case `acli` will look in your default data folder and automatically fetch the data for you.

If the data that you are requesting does not exist on your PC locally, then the re-analysis will fail with a `FileNotFoundException`.

## Important: re-analysis updates REDIS
After an analysis, usually some REDIS quantity of interest (QOI) will be updated. Often re-analysis is used in practice when we
are developing an analysis node, or when REDIS data has been cleared or is inaccurate for some other reason. The idea is then that
the REDIS QOI is updated to the correct value with the re-analysis.