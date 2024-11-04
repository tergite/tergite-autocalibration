import pytest
from quantifiles.data import SplitTuid


class TestSplitTuid:
    def test_date_property(self):
        tuid = SplitTuid("20230314-212358-316-ca5ac0-test 0 to 1")
        assert tuid.date == "20230314"

    def test_time_property(self):
        tuid = SplitTuid("20230314-212358-316-ca5ac0-test 0 to 1")
        assert tuid.time == "212358"

    def test_name_property(self):
        tuid = SplitTuid("20230314-212358-316-ca5ac0-test 0 to 1")
        assert tuid.name == "test 0 to 1"

    def test_tuid_property(self):
        tuid = SplitTuid("20230314-212358-316-ca5ac0-test 0 to 1")
        assert tuid.tuid == "20230314-212358-316-ca5ac0"

    def test_full_tuid_property(self):
        tuid = SplitTuid("20230314-212358-316-ca5ac0-test 0 to 1")
        assert tuid.full_tuid == "20230314-212358-316-ca5ac0-test 0 to 1"

    def test_full_tuid_setter(self):
        tuid = SplitTuid("20230314-212358-316-ca5ac0-test 0 to 1")
        tuid.full_tuid = "20220324-105132-aaaa.bbb.cccc"
        assert tuid.full_tuid == "20220324-105132-aaaa.bbb.cccc"
