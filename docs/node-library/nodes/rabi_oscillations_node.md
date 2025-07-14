---
title: Rabi Oscillations
---

## Rabi oscillations calibration and analysis

The rabi oscillations are essential when determining the amplitude of the signal send to the qubit. The \($\pi$)-pulses, which amplitudes is varying is a Gaussian pulses. By varying the amplitude a cosine function appears when measuring transmission coefficient (S21) and with that one can determine the optimal amplitude for qubit operations. This can also be done for 12 operations with the only difference being the 1 state being initialized. 

### Measurement class: `RabiOscillationsMeasurement`

The `RabiOscillationsMeasurement` class facilitates the creation of schedules for Rabi oscillations. 

#### Method: `schedule_function`

The `schedule_function` generates an experimental schedule for performing Rabi oscillations. The sequence involves:

1. **Reset**: Resets all qubits to a known state.
2. **Initialize Qubit**: Initialize the qubit to state 0 or 1, depending what qubit frequency you want to attain.
3. **Amplitude Sweeping**: Iteratively adjusts the probing amplitude.
4. **Measurement**: Captures the qubit response at each probing point.

**Parameters**:

- `mw_amplitudes` (`dict[str, np.ndarray]`): Amplitudes of the probing \($\pi$)-pulses.
- `repetitions` (`int`): Number of times the schedule will repeat.
- `qubit_state` (`int`): The state for the qubit.

**Returns**:

- A `Schedule` object representing the experimental procedure.

### Analysis class: `RabiQubitAnalysis`

The `RabiQubitAnalysis` class analyzes the results of Rabi oscillations experiments. It fits a cosine function to the qubit response for different amplitudes of the \($\pi$)-pulse, determinaning the Rabi frequencies.

#### Method: `analyse_qubit`

The `analyse_qubit` method processes the Rabi oscillations data to extract key parameters:

- **Optimal \($\pi$)-pulse amplitude**: The optimal amplitude resulting in the qubit getting to the desired state.

**Steps**:

1. **Load Data**:  
   Extract the drive amplitude and magnitude values from the dataset for analysis.

2. **Parameter Guessing**:  
   - Compute an initial guess for the cosine model parameters:
     - **Amplitude**: Based on the difference between maximum and minimum magnitudes.
     - **Offset**: As the mean of the magnitude values.
     - **Frequency**: Using a Fast Fourier Transform (FFT) to estimate oscillation frequency.
   - Update the model parameters with the computed guesses.

3. **Fit Model**:  
   Fit the cosine function to the Rabi oscillation data using the guessed parameters. The model adjusts to minimize the error.

4. **Extract Results**:  
   - Calculate the \($\pi$)-pulse amplitude (`amp180`) from the fit.
   - Estimate the uncertainty of the \($\pi$)-pulse amplitude using the standard error from the fit results.

5. **Generate Fit Curve**:  
   Evaluate the fitted model over a finer set of amplitude values for smooth plotting.

6. **Plot Results**:  
   - Plot the fitted curve against the original data points.
   - Annotate the plot with the ($\pi$)-pulse amplitude value.
