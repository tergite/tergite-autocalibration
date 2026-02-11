# Automatic mixer calibration

To calibrate the mixers, there is a tool under `tergite_autocalibration.tools.mixer_calibration` and a commandline
endpoint.

## CLI endpoint to run the mixer calibration

You can run the mixer calibration by typing:

```shell
acli cluster mc
```

This will assume that you want to run a mixer calibration on the readout lines and drive lines for all qubits defined in
the run configuration.
You can also specify, which qubits you want to run the mixer calibration on:

```shell
acli cluster mc -q "q03-q08"
```

Where the qubit string takes also a list of comma-separated values as input.

If you are not happy with the results of the automatic mixer calibration, you can reset the values to:

```json
{
  "dc_offset_i": 0,
  "dc_offset_q": 0,
  "amp_ratio": 1,
  "phase_error": 0
}
```

by running:

```shell
acli cluster reset-mc
```

And here again you can pass a parameter to specify the qubits.

## Writing a custom automatic mixer calibration

If you want to make a more customized mixer calibration, you can do it as in this example:

```
from tergite_autocalibration.tools.mixer_calibration import IQMixerCalibration

if __name__ == "__main__":

    # calibration qrm-rf modules
    mc = IQMixerCalibration(["q01", "q02"], "res")
    mc.lo_calibration()
    mc.sideband_calibration()
    mc.export_calibration_parameters(overwrite=False, save_to_disk=True)

    # calibration qcm-rf modules
    mc = IQMixerCalibration(["q01", "q02"], "mw")
    mc.lo_calibration()
    mc.sideband_calibration()
    mc.export_calibration_parameters(overwrite=False, save_to_disk=True)

    # calibration qcm-rf modules for flux ports
    mc = IQMixerCalibration(["q01_q02"], "fl")
    mc.lo_calibration()
    mc.sideband_calibration()
    mc.export_calibration_parameters(overwrite=False, save_to_disk=True)
```

This will run a mixer calibration for the qubits `q01` and `q02` on all drive and readout lines.
