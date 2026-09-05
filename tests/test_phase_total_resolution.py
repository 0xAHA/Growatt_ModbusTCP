"""Grid import is the whole service, not one phase (#419).

V1.39 lays the storage power-flow range out as R / S / T / Total. Every SPH profile read
grid import from **1015/1016 = `PactouserR`** - one phase - while the whole-service total at
1021/1022 was mapped under a suffixed name the coordinator would not resolve. Export
(1029/1030) and load (1037/1038) already used their totals; import alone did not.

On single-phase hardware R and Total are the same measurement, which is why this survived:
it was introduced by copying a block from another profile ([#326](https://github.com/0xAHA/Growatt_ModbusTCP/issues/326),
whose reporter had a single-phase SPH 5000 and said in the issue that his findings were from
one device), then preserved through [#369](https://github.com/0xAHA/Growatt_ModbusTCP/issues/369)
for naming reasons. It reports a third of the truth on a three-phase SPH-TL3 and half on a
US split-phase HU.

The total is not blindly trusted. We know 1015 populates on at least one device and have
never confirmed 1021 does everywhere, so a straight swap could take working users to zero.
Hence: total if populated, else the phase sum, and **never a zero total while the phases
carry real values** - that zero is a register the firmware does not fill, not a measurement.

These execute the real method against a fake register map rather than reading its source,
because the branch that matters is the one a modern single-phase test machine never takes.
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "tests")

COMPONENT = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
SOURCE = (COMPONENT / "growatt_modbus.py").read_text(encoding="utf-8")
PROFILES = importlib.import_module("growatt_under_test.profiles").REGISTER_MAPS

IMPORT_PHASES = ("power_to_user_r_low", "power_to_user_s_low", "power_to_user_t_low")

SPH_PROFILES = [
    "SPH_3000_6000", "SPH_3000_6000_V201",
    "SPH_7000_10000", "SPH_7000_10000_V201",
    "SPH_8000_10000_HU",
    "SPH_TL3_3000_10000", "SPH_TL3_3000_10000_V201",
]


def _load_resolver():
    """Extract _resolve_phase_total and execute it against stubs."""
    fn = next(
        n for n in ast.walk(ast.parse(SOURCE))
        if isinstance(n, ast.FunctionDef) and n.name == "_resolve_phase_total"
    )
    namespace: dict = {"logger": _Logger()}
    exec(compile(ast.parse(ast.get_source_segment(SOURCE, fn)), "<r>", "exec"), namespace)
    return namespace["_resolve_phase_total"]


class _Logger:
    def debug(self, *a, **k):
        pass


class _Data:
    def __init__(self):
        self.power_to_user = 0.0
        self.unread_fields: set[str] = set()


class _Client:
    """Register map as {name: value}. None means the read failed this poll."""

    def __init__(self, values: dict):
        self._values = values
        self._addr = {name: 1000 + i for i, name in enumerate(values)}

    def _find_all_registers_by_name(self, name):
        return [self._addr[name]] if name in self._values else []

    def _find_register_by_name(self, name):
        return self._addr.get(name)

    def _get_register_value(self, addr):
        for name, a in self._addr.items():
            if a == addr:
                return self._values[name]
        return None


resolve = _load_resolver()


def _run(values):
    data = _Data()
    resolve(_Client(values), data, "power_to_user", "power_to_user_low", IMPORT_PHASES)
    return data


# --------------------------------------------------------------------------- profiles


@pytest.mark.parametrize("profile", SPH_PROFILES)
def test_the_total_carries_the_resolvable_name(profile):
    """THE regression. 1021/1022 must be plain `power_to_user`, or the coordinator looks it
    up, fails, and falls back to the R phase exactly as before."""
    registers = PROFILES[profile]["input_registers"]

    assert registers[1021]["name"] == "power_to_user_high"
    assert registers[1022]["name"] == "power_to_user_low", (
        f"{profile} still hides PactouserTotal behind a suffix the coordinator cannot "
        f"resolve"
    )


@pytest.mark.parametrize("profile", SPH_PROFILES)
def test_the_r_phase_is_still_mapped_but_named_as_a_phase(profile):
    """Kept so the phase-sum fallback has something to sum, and so nothing silently loses a
    register that is known to populate."""
    registers = PROFILES[profile]["input_registers"]

    if profile == "SPH_8000_10000_HU":
        assert registers[1015]["name"] == "ct_grid_import_l1_high"
        assert registers[1015]["alias"] == "power_to_user_r_high"
        assert registers[1016]["name"] == "ct_grid_import_l1_low"
        assert registers[1016]["alias"] == "power_to_user_r_low"
    else:
        assert registers[1015]["name"] == "power_to_user_r_high"
        assert registers[1016]["name"] == "power_to_user_r_low"


@pytest.mark.parametrize("profile", SPH_PROFILES)
def test_all_three_phases_are_mapped(profile):
    """Summing needs S and T present, or a three-phase inverter whose firmware fills only
    the per-phase registers would fall back to R alone - the original bug."""
    registers = PROFILES[profile]["input_registers"]

    expected = [
        (1017, "power_to_user_s_high"), (1018, "power_to_user_s_low"),
        (1019, "power_to_user_t_high"), (1020, "power_to_user_t_low"),
    ]
    if profile == "SPH_8000_10000_HU":
        expected[0] = (1017, "ct_grid_import_l2_high")
        expected[1] = (1018, "ct_grid_import_l2_low")

    for addr, name in expected:
        assert registers[addr]["name"] == name, f"{profile} is missing {name}"

    if profile == "SPH_8000_10000_HU":
        assert registers[1017]["alias"] == "power_to_user_s_high"
        assert registers[1018]["alias"] == "power_to_user_s_low"


# --------------------------------------------------------------------------- behaviour


def test_a_populated_total_wins():
    data = _run({"power_to_user_low": 2400.0, "power_to_user_r_low": 800.0,
                 "power_to_user_s_low": 800.0, "power_to_user_t_low": 800.0})
    assert data.power_to_user == 2400.0


def test_a_zero_total_does_not_beat_live_phases():
    """THE case this exists for. A firmware that does not populate the total would
    otherwise report zero import while three phases are visibly drawing power."""
    data = _run({"power_to_user_low": 0.0, "power_to_user_r_low": 800.0,
                 "power_to_user_s_low": 700.0, "power_to_user_t_low": 900.0})
    assert data.power_to_user == pytest.approx(2400.0)


def test_single_phase_sums_to_the_r_phase():
    """S and T read zero on single-phase hardware, so the sum degenerates to R with no
    knowledge of the phase count needed anywhere."""
    data = _run({"power_to_user_low": 0.0, "power_to_user_r_low": 950.0,
                 "power_to_user_s_low": 0.0, "power_to_user_t_low": 0.0})
    assert data.power_to_user == 950.0


def test_genuine_zero_is_still_zero():
    """Guard against over-correcting: nothing flowing must report nothing flowing, not
    unknown."""
    data = _run({"power_to_user_low": 0.0, "power_to_user_r_low": 0.0,
                 "power_to_user_s_low": 0.0, "power_to_user_t_low": 0.0})
    assert data.power_to_user == 0.0
    assert not data.unread_fields


def test_a_failed_phase_read_withholds_rather_than_summing_a_partial_set():
    """Unread is not zero. Summing R and T while S is missing understates the total, and a
    quietly low grid import is exactly the class of wrong-but-plausible value this project
    keeps removing."""
    data = _run({"power_to_user_low": 0.0, "power_to_user_r_low": 800.0,
                 "power_to_user_s_low": None, "power_to_user_t_low": 900.0})
    assert "power_to_user" in data.unread_fields


def test_a_quantity_with_no_phases_mapped_uses_its_total():
    """Export and load keep total-only behaviour, so one rule serves all three without
    mapping registers nobody has evidence for."""
    data = _Data()
    resolve(_Client({"power_to_user_low": 1500.0}), data, "power_to_user",
            "power_to_user_low", ())
    assert data.power_to_user == 1500.0
