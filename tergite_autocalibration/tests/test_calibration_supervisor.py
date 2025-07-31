# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.scripts.calibration_supervisor import (
    CalibrationConfig,
    CalibrationSupervisor,
    HardwareManager,
    NodeManager,
)
from quantify_scheduler.instrument_coordinator import InstrumentCoordinator
from qblox_instruments import Cluster
from tergite_autocalibration.utils.dto.enums import (
    DataStatus,
    MeasurementMode,
)


def test_instantiate_calibration_config():
    confg = CalibrationConfig(cluster_mode=MeasurementMode.dummy, cluster_ip=None)
    assert confg.cluster_mode == MeasurementMode.dummy
    assert confg.cluster_ip is None
    assert confg.cluster_timeout == 222
    assert set(confg.qubits) == {"q00", "q01"}
    assert set(confg.couplers) == {"q00_q01"}
    assert len(confg.user_samplespace.keys()) == 1
    assert "resonator_spectroscopy" in confg.user_samplespace
    assert "ro_frequencies" in confg.user_samplespace["resonator_spectroscopy"]
    assert len(confg.user_samplespace["resonator_spectroscopy"].keys()) == 1
    assert set(
        confg.user_samplespace["resonator_spectroscopy"]["ro_frequencies"].keys()
    ) == {"q00", "q01"}
    assert confg.target_node_name == "ro_amplitude_two_state_optimization"


def test_instantiate_calibration_supervisor():
    cfg = CalibrationConfig(cluster_mode=MeasurementMode.dummy, cluster_ip=None)
    calib_sup = CalibrationSupervisor(config=cfg)

    assert isinstance(calib_sup.hardware_manager, HardwareManager)
    assert isinstance(calib_sup.node_manager, NodeManager)
    assert isinstance(calib_sup.lab_ic, InstrumentCoordinator)
    assert calib_sup.config == cfg
    assert isinstance(calib_sup.topo_order, list)
    assert tuple(calib_sup.topo_order) == (
        "resonator_spectroscopy",
        "qubit_01_spectroscopy",
        "rabi_oscillations",
        "ramsey_correction",
        "motzoi_parameter",
        "n_rabi_oscillations",
        "resonator_spectroscopy_1",
        "ro_frequency_two_state_optimization",
        "ro_amplitude_two_state_optimization",
    )


def test_hardware_manager_creates_dummy_cluster():
    cfg = CalibrationConfig(cluster_mode=MeasurementMode.dummy, cluster_ip=None)
    calib_sup = CalibrationSupervisor(config=cfg)
    hw_manager = calib_sup.hardware_manager
    cl = hw_manager.cluster
    assert isinstance(cl, Cluster)

    for slot_idx in range(1, 16):
        _dummy_qcm_rf = getattr(cl, f"module{slot_idx}")
        assert _dummy_qcm_rf.present()
        assert _dummy_qcm_rf.is_rf_type and _dummy_qcm_rf.is_qcm_type

    assert cl.module16.present()
    assert cl.module17.present()
    assert cl.module16.is_rf_type and cl.module16.is_qrm_type
    assert cl.module17.is_rf_type and cl.module17.is_qrm_type


def test_hardware_manager_creates_ic():
    cfg = CalibrationConfig(cluster_mode=MeasurementMode.dummy, cluster_ip=None)
    calib_sup = CalibrationSupervisor(config=cfg)
    hw_manager = calib_sup.hardware_manager
    assert isinstance(hw_manager.lab_ic, InstrumentCoordinator)
    assert hw_manager.get_instrument_coordinator().name == hw_manager.lab_ic.name


def test_output_attenuation_is_set_to_value_in_device_config(caplog):
    cfg = CalibrationConfig(cluster_mode=MeasurementMode.dummy, cluster_ip=None)

    # output attenuation is set during the instantiation of the HardwareManager
    # which in turn is created during the instantiation of the CalibrationSupervisor

    with caplog.at_level("WARNING"):
        calib_sup = CalibrationSupervisor(config=cfg)

    assert len(caplog.records) == 1

    log_records = caplog.records[0]
    assert log_records.levelname == "WARNING"
    assert (
        log_records.message
        == "Skipping setting attenuation for 'q404:mw', as it is not in the connectivity graph of the cluster_config.json."
    )

    hw_manager = calib_sup.hardware_manager
    assert hw_manager.cluster.module2.out0_att() == 4  # q00:mw
    assert hw_manager.cluster.module2.out1_att() == 8  # q01:mw
    assert hw_manager.cluster.module3.out0_att() == 12  # q00_q01:fl
    assert hw_manager.cluster.module16.out0_att() == 18  # q00:res, q01:res
