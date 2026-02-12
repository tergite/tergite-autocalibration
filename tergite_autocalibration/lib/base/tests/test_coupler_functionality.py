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
from tergite_autocalibration.tests.utils.decorators import with_redis
from tergite_autocalibration.tests.utils.fixtures import get_fixture_path
from tergite_autocalibration.utils.dto.extended_transmon_element import ExtendedTransmon

redis_mock = get_fixture_path("redis", "standard_redis_mock.json")


class DummySpiManager:
    def __init__(self):
        self._currents_dict = None  # internal storage

    def set_dac_current(self, currents_dict: dict):
        self._currents_dict = currents_dict

    def get_dac_current(self) -> dict | None:
        return self._currents_dict


@with_redis(redis_mock)
def test_set_parking_current_from_redis():
    ExtendedTransmon.close_all()  # ensure no other transmon objects are instantiated
    node = CZChevronNode(couplers=CONFIG.run.couplers, qubits=CONFIG.run.qubits)
    # cfg = CalibrationConfig(cluster_mode=MeasurementMode.dummy, cluster_ip=None)
    # calib_sup = CalibrationSupervisor(config=cfg)
    # hwm = HardwareManager(cfg)
    # spi_manager = hwm.create_spi(CONFIG.run.couplers)
    node.spi_manager = DummySpiManager()

    node.set_parking_current_from_redis()
    currents_dict = node.spi_manager.get_dac_current()
    assert "q00_q01" in currents_dict
    assert currents_dict["q00_q01"] == "0.00095"
