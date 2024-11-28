# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.config.legacy import dh


def test_data_handler():
    assert "q00" in dh.device["qubit"].keys()


def test_data_handler_legacy():
    assert dh.get_legacy("VNA_resonator_frequencies")["q00"] == 6.48213e9
    assert dh.get_legacy("VNA_qubit_frequencies")["q00"] == 3.848e9
    assert dh.get_legacy("VNA_f12_frequencies")["q00"] == 3.592e9

    assert dh.get_legacy("attenuation_setting")["qubit"] == 6
    assert dh.get_legacy("attenuation_setting")["coupler"] == 10
    assert dh.get_legacy("attenuation_setting")["resonator"] == 10
