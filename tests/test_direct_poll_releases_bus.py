"""A direct (serial) poll gives the bus back between attempts (#501).

Two MOD TL3-X on one RS485 adapter share a bus lock. When one stopped answering at dusk,
its poll held the lock through three attempts and the pauses between them - past the
other entry's 60 s lock timeout - so an inverter still producing skipped its polls and
went unavailable.

The coordinator needs Home Assistant to import, so `_fetch_data` and
`_fetch_data_direct` are lifted out of the source with `ast` and run against a fake
client that counts how deeply the bus is held.
"""
from __future__ import annotations

import ast
import logging
from contextlib import contextmanager
from pathlib import Path

import pytest

SOURCE = (
    Path(__file__).parent.parent / "custom_components" / "growatt_modbus" / "coordinator.py"
).read_text(encoding="utf-8")


class _ModbusWriteError(Exception):
    pass


def _methods() -> dict:
    tree = ast.parse(SOURCE)
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "GrowattModbusCoordinator")
    wanted = {"_fetch_data", "_fetch_data_direct"}
    funcs = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    assert {f.name for f in funcs} == wanted
    consts = [n for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id.startswith("DIRECT_POLL_")
                      for t in n.targets)]
    module = ast.Module(body=consts + funcs, type_ignores=[])
    return ast.unparse(module)


class _Clock:
    def __init__(self, client):
        self.client = client
        self.sleeps: list[tuple[float, int]] = []

    def sleep(self, seconds):
        self.sleeps.append((seconds, self.client.bus_depth))


class _Client:
    def __init__(self, answers):
        self.answers = list(answers)
        self.bus_depth = 0
        self.reads = 0
        self.read_depths: list[int] = []

    @contextmanager
    def _bus(self, what):
        self.bus_depth += 1
        try:
            yield
        finally:
            self.bus_depth -= 1

    def connect(self):
        return True

    def disconnect(self):
        pass

    def read_all_data(self):
        self.reads += 1
        self.read_depths.append(self.bus_depth)
        return self.answers.pop(0) if self.answers else None


class _Coordinator:
    def __init__(self, client, failures):
        self._client = client
        self._consecutive_failures = failures
        self._hub = None
        self._identification_complete = True
        self.config = {}

    def _apply_client_options(self):
        pass

    def _refresh_inverter_clock(self):
        pass

    def _refresh_onoff(self):
        pass

    def _recheck_profile_against_dtc(self):
        pass


def _run(answers, failures):
    client = _Client(answers)
    clock = _Clock(client)
    ns = {
        "time": clock, "ModbusWriteError": _ModbusWriteError,
        "_LOGGER": logging.getLogger("test"), "GrowattData": object,
        "CONF_DEVICE_PATH": "device_path", "CONF_HOST": "host",
    }
    exec(compile("from __future__ import annotations\n" + _methods(), "coordinator", "exec"), ns)
    coord = _Coordinator(client, failures)
    for name in ("_fetch_data", "_fetch_data_direct"):
        setattr(coord, name, ns[name].__get__(coord))
    return coord._fetch_data(), client, clock


def test_the_pause_between_attempts_is_taken_with_the_bus_free():
    """THE #501 regression: the sleeps ran inside the bus lock."""
    _, client, clock = _run([], failures=0)
    assert clock.sleeps, "a failing poll on a working link should still retry"
    assert all(depth == 0 for _, depth in clock.sleeps), (
        f"bus held during the retry pause: {clock.sleeps}"
    )


def test_a_working_link_still_gets_three_attempts():
    _, client, _ = _run([], failures=0)
    assert client.reads == 3


def test_an_inverter_that_already_failed_a_poll_gets_one_attempt():
    """Asleep at dusk: three tries per cycle all night only blocks the other entry."""
    result, client, clock = _run([], failures=1)
    assert result is None
    assert client.reads == 1
    assert clock.sleeps == []


def test_a_retry_that_succeeds_returns_its_data():
    data = object()
    result, client, _ = _run([None, data], failures=0)
    assert result is data
    assert client.reads == 2


def test_success_first_time_does_not_pause():
    data = object()
    result, _, clock = _run([data], failures=0)
    assert result is data
    assert clock.sleeps == []


@pytest.mark.parametrize("failures", [0, 2])
def test_every_read_still_happens_under_the_bus(failures):
    """Releasing between attempts must not release DURING one (#398)."""
    _, client, _ = _run([], failures=failures)
    assert client.read_depths and all(d == 1 for d in client.read_depths)
