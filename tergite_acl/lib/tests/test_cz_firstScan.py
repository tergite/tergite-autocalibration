import matplotlib
import pytest
from pathlib import Path
import xarray as xr
import numpy as np
from tergite_acl.lib.analysis.cz_firstScan import CZFirstScan
from tergite_acl.lib.analysis.cz_firstScanResult import FitResultStatus

@pytest.fixture(autouse=True)
def setup_good_data():
    dataset_path = Path(__file__).parent / 'data' / 'dataset_goodQuality.hdf5'
    print(dataset_path)
    ds = xr.open_dataset(dataset_path) 
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs['qubit'] = 'q17'
    d22.yq22.attrs['qubit'] = 'q22'
    return d17, d22

def test_canCreate(setup_good_data):
    d17, d22 = setup_good_data
    CZFirstScan(d17)
    pass
    
def test_datasetHasQubitDefined(setup_good_data):
    d17, d22 = setup_good_data
    r = CZFirstScan(d17)
    assert r.qubit == 'q17'
    r = CZFirstScan(d22)
    assert r.qubit == 'q22'

def test_canGetBestFrequencyFromGoodChevronQ17(setup_good_data):
    d17, d22  = setup_good_data
    first_scan = CZFirstScan(d17)
    result = first_scan.run_fitting()
    freq = d17[f'cz_pulse_frequencies_sweepq17'].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq == freq[6]
    assert max(result.pvalues) > 0.99
    assert result.status == FitResultStatus.FOUND

def test_canGetBestFrequencyFromGoodChevronQ22(setup_good_data):
    d17, d22  = setup_good_data
    first_scan = CZFirstScan(d22)
    result = first_scan.run_fitting()
    freq = d22[f'cz_pulse_frequencies_sweepq22'].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq == freq[6]
    assert max(result.pvalues) > 0.99
    assert result.status == FitResultStatus.FOUND

@pytest.fixture(autouse=True)
def setup_medium_data():
    dataset_path = Path(__file__).parent / 'data' / 'dataset_mediumQuality.hdf5'
    ds = xr.open_dataset(dataset_path) 
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs['qubit'] = 'q17'
    d22.yq22.attrs['qubit'] = 'q22'
    return d17, d22

def test_canGetBestFrequencyFromMediumChevronQ17(setup_medium_data):
    d17, d22  = setup_medium_data
    first_scan = CZFirstScan(d17)
    result  = first_scan.run_fitting()
    freq = d17[f'cz_pulse_frequencies_sweepq17'].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq == freq[5]
    assert max(result.pvalues) < 0.99 
    assert result.status == FitResultStatus.FOUND

def test_canGetBestFrequencyFromMediumChevronQ22(setup_medium_data):
    d17, d22  = setup_medium_data
    first_scan = CZFirstScan(d22)
    result = first_scan.run_fitting()
    freq = d22[f'cz_pulse_frequencies_sweepq22'].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq == freq[3]
    assert max(result.pvalues) < 0.99 
    assert result.status == FitResultStatus.FOUND

@pytest.fixture(autouse=True)
def setup_poor_data():
    dataset_path = Path(__file__).parent / 'data' / 'dataset_poorQuality.hdf5'
    ds = xr.open_dataset(dataset_path) 
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs['qubit'] = 'q17'
    d22.yq22.attrs['qubit'] = 'q22'
    return d17, d22

def test_CatchBadFitFromPoorChevronQ17(setup_poor_data):
    d17, d22  = setup_poor_data
    first_scan = CZFirstScan(d17)
    result  = first_scan.run_fitting()
    assert result.status == FitResultStatus.NOT_FOUND

def test_canGetBestFrequencyFromPoorChevronQ22(setup_poor_data):
    d17, d22  = setup_poor_data
    first_scan = CZFirstScan(d22)
    result = first_scan.run_fitting()
    freq = d22[f'cz_pulse_frequencies_sweepq22'].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq > freq[6]
    assert max(result.pvalues) < 0.8 or (max(p[1] for p in result.fittedParams))
    assert result.status == FitResultStatus.FOUND

@pytest.fixture(autouse=True)
def setup_bad_data():
    dataset_path = Path(__file__).parent / 'data' / 'dataset_badQuality.hdf5'
    print(dataset_path)
    ds = xr.open_dataset(dataset_path) 
    ds = ds.isel(ReIm=0) + 1j * ds.isel(ReIm=1)
    d17 = ds.yq17.to_dataset()
    d22 = ds.yq22.to_dataset()
    d17.yq17.attrs['qubit'] = 'q17'
    d22.yq22.attrs['qubit'] = 'q22'
    return d17, d22

def test_canGetBestFrequencyFromBadChevronQ17(setup_bad_data):
    d17, d22  = setup_bad_data
    first_scan = CZFirstScan(d17)
    result  = first_scan.run_fitting()
    freq = d17[f'cz_pulse_frequencies_sweepq17'].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq > freq[6]
    assert max(result.pvalues) < 0.8 or (max(p[0] for p in result.fittedParams)) < 0.2
    assert result.status == FitResultStatus.FOUND

def test_canGetBestFrequencyFromBadChevronQ22(setup_bad_data):
    d17, d22  = setup_bad_data
    first_scan = CZFirstScan(d22)
    result = first_scan.run_fitting()
    freq = d22[f'cz_pulse_frequencies_sweepq22'].values  # MHz
    bestFreq = freq[np.argmax(result.pvalues)]
    assert bestFreq == freq[3]
    assert (max(result.pvalues) < 0.8) or (max(p[0] for p in result.fittedParams)) < 0.2
    assert result.status == FitResultStatus.FOUND

def test_plotsAreCreated(setup_good_data):
    matplotlib.use('Agg')
    d17, d22  = setup_good_data
    first_scan = CZFirstScan(d17)
    result  = first_scan.run_fitting()
    folder_path = Path(__file__).parent / 'results'
    first_scan.plotter(folder_path)

    figure_path = folder_path / 'AllFits_q17.png'
    assert figure_path.exists(), "The PNG file should exist"
    from PIL import Image
    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"

    figure_path = folder_path / 'SummaryScan_q17.png'
    assert figure_path.exists(), "The PNG file should exist"
    from PIL import Image
    with Image.open(figure_path) as img:
        assert img.format == "PNG", "File should be a PNG image"