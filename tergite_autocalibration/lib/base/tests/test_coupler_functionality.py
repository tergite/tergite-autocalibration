# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025, 2026
# (C) Copyright Eleftherios Moschandreou 2026
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from tergite_autocalibration.config.globals import CONFIG
from tergite_autocalibration.lib.nodes.coupler.cz_chevron.node import CZChevronNode
from tergite_autocalibration.scripts.calibration_supervisor import (
    CalibrationConfig,
    HardwareManager,
)
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.utils.dto.enums import MeasurementMode
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon

redis_mock = get_fixture_path("redis", "standard_redis_mock.json")


@with_redis(redis_mock)
def test_set_parking_current_from_redis():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = CZChevronNode(couplers=CONFIG.run.couplers, qubits=CONFIG.run.qubits)
    cfg = CalibrationConfig(cluster_mode=MeasurementMode.dummy, cluster_ip=None)
    # calib_sup = CalibrationSupervisor(config=cfg)
    hwm = HardwareManager(cfg)
    spi_manager = hwm.create_spi(CONFIG.run.couplers)
    node.spi_manager = spi_manager
    # assert isinstance(calib_sup.hardware_manager, HardwareManager)
    # hardware_manager = HardwareManager(config=CONFIG)
    node.set_parking_current_from_redis()
    breakpoint()
