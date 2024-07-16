from pathlib import Path
import numpy as np
import pytest
import xarray as xr
from tergite_autocalibration.lib.base.analysis import BaseAnalysis
from tergite_autocalibration.lib.nodes.coupler.cz_characterisation.CZ_Characterisation_Frequency_vs_Amplitude_Q1_Analysis import CZ_Characterisation_Frequency_vs_Amplitude_Q1_Analysis
from tergite_autocalibration.lib.nodes.coupler.cz_characterisation.CZ_Characterisation_Frequency_vs_Amplitude_Q2_Analysis import CZ_Characterisation_Frequency_vs_Amplitude_Q2_Analysis

@pytest.fixture(autouse=True)
def setup_good_data():
    dataset_path = Path(__file__).parent / "data" / "dataset_good_quality_freq_amp.hdf5"
    print(dataset_path)
    ds = xr.open_dataset(dataset_path)
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d14 = ds.yq14.to_dataset()
    d15 = ds.yq15.to_dataset()
    d14.yq14.attrs["qubit"] = "q14"
    d15.yq15.attrs["qubit"] = "q15"
    freqs = ds[f"cz_pulse_frequenciesq14_q15"].values / 1e6  # MHz
    amps = ds[f"cz_pulse_amplitudesq14_q15"].values # uA
    return d14, d15, freqs, amps
    
def test_canCreateCorrectClass(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c = CZ_Characterisation_Frequency_vs_Amplitude_Q1_Analysis(d14)
    assert isinstance(c, CZ_Characterisation_Frequency_vs_Amplitude_Q1_Analysis)
    assert isinstance(c, BaseAnalysis)
    c = CZ_Characterisation_Frequency_vs_Amplitude_Q2_Analysis(d15)
    assert isinstance(c, CZ_Characterisation_Frequency_vs_Amplitude_Q2_Analysis)
    assert isinstance(c, BaseAnalysis)

def test_datasetHasQubitDefined(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    c = CZ_Characterisation_Frequency_vs_Amplitude_Q1_Analysis(d14)
    assert c.qubit == "q14"
    c = CZ_Characterisation_Frequency_vs_Amplitude_Q2_Analysis(d15)
    assert c.qubit == "q15"

def test_canGetMaxFromQ1(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    first_scan = CZ_Characterisation_Frequency_vs_Amplitude_Q1_Analysis(d14)
    result = first_scan.run_fitting()
    indexBestFreq = np.where(freqs == result[0])[0]
    indexBestAmp = np.where(amps == result[1])[0] 
    assert indexBestFreq[0] == 9
    assert indexBestAmp[0] == 13

def test_canGetMinFromQ2(setup_good_data):
    d14, d15, freqs, amps = setup_good_data
    first_scan = CZ_Characterisation_Frequency_vs_Amplitude_Q2_Analysis(d15)
    result = first_scan.run_fitting()
    indexBestFreq = np.where(freqs == result[0])[0]
    indexBestAmp = np.where(amps == result[1])[0] 
    assert indexBestFreq[0] == 10
    assert indexBestAmp[0] == 12


