from utils import IQMixerCalibration

if __name__ == "__main__":

    # calibration qrm-rf modules
    mc = IQMixerCalibration(['q01', 'q02'], "res")
    mc.lo_calibration()
    mc.sideband_calibration()
    mc.export_calibration_parameters(overwrite=False, save_to_disk=True)

    # calibration qcm-rf modules
    mc = IQMixerCalibration(['q01', 'q02'], "mw")
    mc.lo_calibration()
    mc.sideband_calibration()
    mc.export_calibration_parameters(overwrite=False, save_to_disk=True)