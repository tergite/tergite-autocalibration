---
title: Qubit Spectroscopy
---
## Qubit Spectroscopy Calibration and Analysis

Qubit spectroscopy is a vital technique for identifying qubit resonance frequencies. By applying a probing signal to a qubit at various frequencies and measuring the response, we can accurately locate resonance frequencies and optimize qubit operation. In this node, both qubit frequecies for both 01 and 12 can be attained depending on the initial qubit state. 

### Measurement class: `TwoTonesMultidimMeasurement`

The `TwoTonesMultidimMeasurement` class facilitates the creation of schedules for qubit spectroscopy experiments. It
supports multi-qubit spectroscopy, enabling parallel probing and measurement.

#### Method: `schedule_function`

The `schedule_function` generates an experimental schedule for performing qubit spectroscopy. The sequence involves:

1. **Reset**: Resets all qubits to a known state.
2. **Initialize Qubit**: Initialize the qubit to state 0 or 1, depending what qubit frequency you want to attain.
3. **Frequency Sweeping**: Iteratively adjusts the probing frequency and amplitude.
4. **Measurement**: Captures the qubit response at each probing point.

**Parameters**:

- `spec_frequencies` (`dict[str, np.ndarray]`): Frequencies to probe for each qubit.
- `spec_pulse_amplitudes` (`dict[str, np.ndarray]`, optional): Amplitudes of the probing pulses.
- `repetitions` (`int`): Number of times the schedule will repeat.
- `qubit_state` (`int`): The state for the qubit.

**Returns**:

- A `Schedule` object representing the experimental procedure.

### Analysis class: `QubitSpectroscopyMultidimAnalysis`

The `QubitSpectroscopyMultidimAnalysis` class analyzes the results of qubit spectroscopy experiments. The resonance peak
is identified, enabling the determination of resonance frequencies.

#### Method: `analyse_qubit`

The `analyse_qubit` method processes the spectroscopy data to extract key parameters:

- **Qubit Frequency**: The frequency at which the qubit exhibits a resonance peak.
- **Optimal Spectroscopy Amplitude**: The amplitude yielding the strongest response.

**Steps**:

1. Extract the relevant coordinates (frequencies and amplitudes) from the dataset.
2. Identify the resonance peak.
3. Validate the peak based on prominence and width criteria.

**Returns**:

- A list containing the qubit frequency and the optimal spectroscopy amplitude.

#### Method: `has_peak`

Determines if a resonance peak exists in the data using statistical filters and peak detection.

**Parameters**:

- `x` (`array`): Data array to evaluate.
- `prom_coef` (`float`): Prominence coefficient.
- `wid_coef` (`float`): Width coefficient.
- `outlier_median` (`float`): Threshold for filtering outliers.

**Returns**:

- A boolean indicating whether a peak is present.
