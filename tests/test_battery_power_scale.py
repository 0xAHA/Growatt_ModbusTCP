"""WIT battery power scale detection must not act on untrustworthy inputs (#406).

The scale is chosen at runtime by comparing the power register against voltage x current.
That is only sound if the current is right, and on some WIT hardware several registers
claim to be battery current while disagreeing by orders of magnitude.

One reporter's inverter offered -0.1 A, 6.3 A and -4.3 A at the same instant. The largest
was selected, expected power came out about ten times too high, the 1.0 scale was chosen to
match, and the decision latched - producing 40 kW readings on a 6.5 kW battery.

The three-sample consistency check did not help: the current was consistently wrong rather
than noisy. Consistency is not accuracy.

History behind the scale itself, because it has been changed twice already:
  v0.1.4  0.1 -> 1.0 on one user's report of readings 10x too small (#75)
  v0.1.8  reverted to 0.1 - 1.0 had broken every other WIT user, and 0.1 follows the VPP
          specification, recorded as correct for 95%+ of WIT inverters
  same day  V x I auto-detection added to serve both variants
"""
import importlib
import sys

import pytest

sys.path.insert(0, "tests")

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
agree = _gm.GrowattModbus._candidates_agree


class TestCandidatesAgree:
    def test_a_single_candidate_agrees_with_itself(self):
        assert agree([2.7]) is True

    def test_no_candidates_is_not_a_disagreement(self):
        assert agree([]) is True

    def test_close_readings_agree(self):
        """Two registers reporting the same quantity differ only by measurement noise."""
        assert agree([2.7, 2.8]) is True
        assert agree([6.3, 6.1, 6.4]) is True

    def test_the_reporters_candidates_disagree(self):
        """-0.1 A, 6.3 A and -4.3 A at the same instant, from the log on #406."""
        assert agree([-0.1, 6.3, -4.3]) is False

    def test_opposite_signs_disagree(self):
        """Charging and discharging at once is not a measurement error."""
        assert agree([4.2, -4.1]) is False

    def test_near_zero_noise_does_not_count_as_a_sign_disagreement(self):
        """A register hovering either side of zero while another reads the same magnitude
        is agreement, not contradiction."""
        assert agree([0.1, -0.05]) is True

    def test_an_order_of_magnitude_apart_disagrees(self):
        assert agree([0.3, 6.3]) is False

    def test_same_order_of_magnitude_agrees(self):
        assert agree([3.0, 5.0]) is True


class TestDetectionRefusesBadInput:
    def _client(self):
        c = _gm.GrowattModbus.__new__(_gm.GrowattModbus)
        c._battery_power_scale_validated = False
        c._battery_power_scale_override = None
        c._battery_power_scale_samples = []
        c._battery_power_scale_input_warned = False
        c._battery_current_candidates_agree = True
        return c

    def test_it_refuses_when_the_current_registers_disagree(self):
        """The reporter's exact situation: V x I says 144 W, the register at 1.0 says
        159 W, and choosing 1.0 to match is how the 10x error was introduced."""
        c = self._client()
        c._battery_current_candidates_agree = False
        assert c._detect_battery_power_scale(53.5, 2.7, 1590) is None

    def test_it_still_detects_when_the_current_is_trustworthy(self):
        """Refusing on bad input must not disable detection altogether - the firmware
        variant it exists for is real, and the reporter confirmed that rebooting under
        real load selected the correct scale straight away."""
        c = self._client()
        # 53.2 V x 40 A = 2128 W; raw 21280 reads as 2128 W at 0.1 and 21280 W at 1.0
        for _ in range(3):
            result = c._detect_battery_power_scale(53.2, 40.0, 21280)
        assert result == 0.1

    def test_it_does_not_decide_while_the_battery_is_nearly_idle(self):
        """The reporter upgraded with a full battery and the house on PV alone. Detection
        fired at 144 W, chose wrong and latched. Near idle the current registers disagree
        and the arithmetic amplifies whichever one is wrong, so no conclusion is drawn."""
        c = self._client()
        assert c._detect_battery_power_scale(53.5, 2.7, 1590) is None
        assert c._battery_power_scale_validated is False

    def test_the_threshold_is_high_enough_to_exclude_the_reported_failure(self):
        """144 W is the value that produced a 40 kW reading on a 6.5 kW battery."""
        assert _gm._BATTERY_SCALE_MIN_POWER_W > 144.0

    def test_a_refusal_is_not_cached_as_a_decision(self):
        """Declining to decide must leave the question open for a later poll where the
        registers do agree."""
        c = self._client()
        c._battery_current_candidates_agree = False
        c._detect_battery_power_scale(53.5, 2.7, 1590)
        assert c._battery_power_scale_validated is False
        assert c._battery_power_scale_override is None
