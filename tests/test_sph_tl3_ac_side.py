"""SPH-TL3 AC Power and House Consumption come from the AC side (#447).

Two registers on this firmware are not what their names suggest:

- AC Power read 40/41 through an alias. V1.39 documents 40/41 as apparent power (VA), and
  on SPH-TL3 it is the three-phase VA total. The real output power is Pac, 35/36 (W), which
  the profile did not map. The gap is a near-constant reactive part: ~1% at 3-7 kW, ~25% at
  0.9 kW.
- House Consumption read 1037/1038, which closes the DC balance to within 15 W on two units
  - the inverter computes it from DC terms, so it overstates the house by the conversion
  loss, ~10%. AC output + import - export matched an independent wallbox meter to 0.4%.

Measured by @acsel91 (wallbox cross-check) and confirmed on a second SPH 10000 TL3 BH-UP from
@AzraelsDisk's register scan, whose values are used below.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
REGISTER_MAPS = importlib.import_module("growatt_under_test.const").REGISTER_MAPS
COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SPH_TL3 = ("SPH_TL3_3000_10000", "SPH_TL3_3000_10000_V201")


def _house_consumption():
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(source))
              if isinstance(n, ast.FunctionDef) and n.name == "_house_consumption")
    namespace: dict = {}
    exec(compile(ast.parse(ast.get_source_segment(source, fn)), "<hc>", "exec"), namespace)
    return namespace["_house_consumption"]


house_consumption = _house_consumption()


# ---------------------------------------------------------------------------
# AC Power
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", SPH_TL3)
def test_ac_power_decodes_the_real_power_register(name):
    """AzraelsDisk's scan at 5.5 kW: 35/36 = 5538.9 W, 40/41 = 5561.1 VA. AC Power must be
    the first."""
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map=name)
    client._register_cache = {35: 0, 36: 55389, 40: 0, 41: 55611}
    addr = client._find_register_by_name("ac_power_low")
    assert addr == 36, f"{name}: AC Power resolves to register {addr}, not Pac (35/36)"
    assert client._get_register_value(addr) == pytest.approx(5538.9)


@pytest.mark.parametrize("name", SPH_TL3)
def test_the_apparent_power_register_no_longer_answers_as_ac_power(name):
    inp = REGISTER_MAPS[name]["input_registers"]
    for addr in (40, 41):
        assert "ac_power" not in (inp[addr].get("alias") or ""), (
            f"{name}: {addr} still carries an ac_power alias - two registers answering one "
            f"name leaves which one wins to lookup order"
        )


# ---------------------------------------------------------------------------
# House Consumption
# ---------------------------------------------------------------------------

def _data(*, ac=0.0, pv=0.0, imp=0.0, exp=0.0, charge=0.0, discharge=0.0,
          load=0.0, unread=()):
    d = _gm.GrowattData()
    d.ac_power, d.pv_total_power = ac, pv
    d.power_to_user, d.power_to_grid = imp, exp
    d.charge_power, d.discharge_power = charge, discharge
    d.power_to_load = load
    d.unread_fields = set(unread)
    return d


def test_house_is_ac_output_plus_import_minus_export():
    """AzraelsDisk's scan: AC 5538.9 W, export 1810 W, 1037/1038 = 4110 W (which equals
    the DC input minus export - the DC balance). The AC-side house load is 3728.9 W."""
    d = _data(ac=5538.9, pv=5916.1, exp=1810.0, load=4110.0)
    assert house_consumption(d, ac_side=True) == pytest.approx(3728.9)


def test_acsel91s_measured_operating_point():
    """15:44: PV 3350 W, battery idle, export 2580 W, 35/36 = 3001.3 W, 1037/1038 = 760 W.
    The rest of the house, checked against the wallbox, was ~420 W - not 760."""
    d = _data(ac=3001.3, pv=3350.0, exp=2580.0, load=760.0)
    assert house_consumption(d, ac_side=True) == pytest.approx(421.3)


def test_grid_charging_keeps_the_previous_source():
    """Charging faster than PV supplies means power flows INTO the inverter's AC side,
    which this has not been measured through - so the old path answers."""
    d = _data(ac=0.0, pv=500.0, imp=3000.0, charge=2500.0, load=1000.0)
    assert house_consumption(d, ac_side=True) == pytest.approx(1000.0)


def test_an_unread_ac_output_falls_back_rather_than_guessing():
    d = _data(ac=0.0, pv=3350.0, exp=2580.0, load=760.0, unread=("ac_power",))
    assert house_consumption(d, ac_side=True) == pytest.approx(760.0)


def test_other_profiles_still_use_the_load_register():
    d = _data(ac=3001.3, pv=3350.0, exp=2580.0, load=760.0)
    assert house_consumption(d) == pytest.approx(760.0)


# ---------------------------------------------------------------------------
# Scope: SPH-TL3 only, not SPA-TL3 on the same register map
# ---------------------------------------------------------------------------

_DP = importlib.import_module("growatt_under_test.device_profiles").INVERTER_PROFILES


@pytest.mark.parametrize("key", ["sph_tl3_3000_10000", "sph_tl3_3000_10000_v201"])
def test_both_sph_tl3_profiles_take_the_house_from_the_ac_side(key):
    assert _DP[key].get("house_load_from_ac_output") is True
    assert "ac_power" in _DP[key]["sensors"], f"{key} has a genuine AC total and no entity for it"


def test_spa_tl3_does_not_despite_sharing_the_map():
    """AC-coupled storage: the solar comes from a separate inverter this integration cannot
    see, so AC output + import - export would drop it from the house load entirely."""
    spa = _DP["spa_tl3_4000_10000_v201"]
    assert spa["register_map"].startswith("SPH_TL3"), "precondition: SPA-TL3 shares the map"
    assert not spa.get("house_load_from_ac_output")


def test_the_sensor_reads_the_flag_from_its_own_device_profile():
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    assert '.get("house_load_from_ac_output")' in source
    assert "_house_consumption(data, ac_side=self._house_from_ac_side)" in source
