"""One dropped frame must not blank a VPP control block (#370 follow-up).

Registers 30100 (control authority), 30200-30201 (export limit) and 30407-30410 (remote
power control) are read best-effort inside `_read_device_info`, because some firmware
variants do not implement them. A failing anchor is recorded so the block is skipped
rather than asked again every poll.

#370 made that record expire after 300 s, which fixed the permanent case. It left the
threshold at one: a single failed read still takes the block out of service for five
minutes, and `read_holding_registers` returns None for a transport error and for a
genuine "illegal data address" alike, so an inverter that answers perfectly is treated
exactly like one that does not implement the register.

That is not hypothetical. On a WIT on 2026-09-01T03:46:34Z one transient read failure was
enough; the registers themselves were verified fine by reading them directly for the next
30 h, while the entities derived from them sat on the GrowattData defaults - which are
indistinguishable from a real "Disabled"/0 reading - the whole time.

These tests pin the four properties that make that impossible:

  * a block is skipped only after several CONSECUTIVE failures,
  * the skip expires and the block is retried,
  * a reconnect re-arms the blocks that only failed because the socket was dead, and
    leaves backed off the ones the inverter genuinely did not answer,
  * a block that was not read publishes nothing: its *_available flag stays False and the
    control entities report unavailable instead of the default.
"""
from __future__ import annotations

import importlib
import time

import pytest

_gm = importlib.import_module("growatt_under_test.growatt_modbus")
_const = importlib.import_module("growatt_under_test.const")

GrowattModbus = _gm.GrowattModbus
GrowattData = _gm.GrowattData
SharedModbusConnection = _gm.SharedModbusConnection

WIT_MAP = "WIT_4000_15000TL3"
ANCHORS = (30100, 30200, 30407)


class FakeHoldingReads:
    """Stand-in for `GrowattModbus.read_holding_registers`.

    `fail` holds start addresses that return None (what the real method does for every
    error, including exceptions). `values` supplies register contents for specific start
    addresses; anything else reads back as zeros.
    """

    def __init__(self, fail=(), values=None):
        self.fail = set(fail)
        self.values = dict(values or {})
        self.calls = []

    def __call__(self, start_address, count):
        self.calls.append((start_address, count))
        if start_address in self.fail:
            return None
        if start_address in self.values:
            return list(self.values[start_address])
        return [0] * count

    def starts(self):
        return [start for start, _ in self.calls]


class RaisingHoldingReads(FakeHoldingReads):
    """Raises instead of returning None, which is the other way a read can fail."""

    def __call__(self, start_address, count):
        self.calls.append((start_address, count))
        if start_address in self.fail:
            raise OSError(104, "Connection reset by peer")
        return [0] * count


class KindedHoldingReads(FakeHoldingReads):
    """FakeHoldingReads that also reports *why* a read failed, like the real method."""

    def __init__(self, fail=(), values=None, kind=None, client=None):
        super().__init__(fail=fail, values=values)
        self.kind = kind
        self.client = client

    def __call__(self, start_address, count):
        result = super().__call__(start_address, count)
        if self.client is not None:
            self.client._last_read_error_kind = self.kind if result is None else None
        return result


class FakeHub:
    """Minimal stand-in for SharedModbusConnection (generation counter only)."""

    def __init__(self):
        self.connection_generation = 0
        self.last_error_kind = None

    def reconnect(self):
        self.connection_generation += 1


def _client(hub=None):
    return GrowattModbus(
        connection_type="tcp", host="10.0.0.1", port=502,
        register_map=WIT_MAP, shared_conn=hub,
    )


@pytest.fixture
def wit_client():
    """A WIT client whose holding reads are fully controlled by the test."""
    return _client()


def _read_device_info(client, reads):
    """Run _read_device_info with the given fake reads, returning fresh GrowattData."""
    client.read_holding_registers = reads
    data = GrowattData()
    client._read_device_info(data)
    return data


# ---------------------------------------------------------------------------
# Threshold: a transient failure must not blacklist anything
# ---------------------------------------------------------------------------


def test_single_failure_does_not_skip_the_block(wit_client):
    """One failed read must leave the block eligible on the very next poll."""
    _read_device_info(wit_client, FakeHoldingReads(fail=set(ANCHORS)))

    for anchor in ANCHORS:
        assert wit_client._optional_holding_blocked(anchor) is False

    reads = FakeHoldingReads(fail=set(ANCHORS))
    _read_device_info(wit_client, reads)
    for anchor in ANCHORS:
        assert anchor in reads.starts()


def test_block_skipped_only_after_threshold_consecutive_failures(wit_client):
    threshold = _gm._VPP_HOLDING_FAIL_THRESHOLD
    assert threshold >= 2, "a threshold of 1 is the bug this test guards against"

    for poll in range(1, threshold + 1):
        reads = FakeHoldingReads(fail={30407})
        _read_device_info(wit_client, reads)
        assert 30407 in reads.starts(), f"poll {poll} should still attempt the block"

    assert wit_client._optional_holding_blocked(30407) is True

    reads = FakeHoldingReads(fail={30407})
    _read_device_info(wit_client, reads)
    assert 30407 not in reads.starts()


def test_an_exception_counts_as_a_failure(wit_client):
    """read_holding_registers can raise as well as return None. Both used to be handled,
    but only one of them was counted, so a block failing that way was retried at full
    price on every poll for the life of the process."""
    threshold = _gm._VPP_HOLDING_FAIL_THRESHOLD
    for _ in range(threshold):
        _read_device_info(wit_client, RaisingHoldingReads(fail={30407}))

    assert wit_client._optional_holding_blocked(30407) is True


def test_success_clears_the_failure_count(wit_client):
    """A good read resets the streak, so the threshold counts *consecutive* failures."""
    threshold = _gm._VPP_HOLDING_FAIL_THRESHOLD

    for _ in range(threshold - 1):
        _read_device_info(wit_client, FakeHoldingReads(fail={30407}))

    _read_device_info(wit_client, FakeHoldingReads(values={30407: [1, 20, 65436, 1]}))
    assert 30407 not in wit_client._failed_optional_holding_addrs

    _read_device_info(wit_client, FakeHoldingReads(fail={30407}))
    assert wit_client._optional_holding_blocked(30407) is False


# ---------------------------------------------------------------------------
# Expiry (#370, kept)
# ---------------------------------------------------------------------------


def test_blacklist_expires_and_the_block_is_retried(wit_client):
    threshold = _gm._VPP_HOLDING_FAIL_THRESHOLD

    for _ in range(threshold):
        _read_device_info(wit_client, FakeHoldingReads(fail={30407}))
    assert wit_client._optional_holding_blocked(30407) is True

    # Age the entry past the retry window.
    _, fail_count = wit_client._failed_optional_holding_addrs[30407]
    wit_client._failed_optional_holding_addrs[30407] = (
        time.time() - _gm._VPP_HOLDING_RETRY_S - 1, fail_count,
    )
    assert wit_client._optional_holding_blocked(30407) is False

    reads = FakeHoldingReads(values={30407: [1, 20, 65436, 1]})
    data = _read_device_info(wit_client, reads)
    assert 30407 in reads.starts()
    assert data.vpp_remote_power_available is True
    assert data.remote_power_control_enable == 1
    assert wit_client._failed_optional_holding_addrs == {}


def test_an_expired_entry_keeps_its_count(wit_client):
    """Re-failing after expiry must increment, not restart, the streak - otherwise the
    block oscillates between blocked and eligible forever and logs the transition each
    time round."""
    threshold = _gm._VPP_HOLDING_FAIL_THRESHOLD

    for _ in range(threshold):
        _read_device_info(wit_client, FakeHoldingReads(fail={30407}))
    wit_client._failed_optional_holding_addrs[30407] = (
        time.time() - _gm._VPP_HOLDING_RETRY_S - 1, threshold,
    )

    _read_device_info(wit_client, FakeHoldingReads(fail={30407}))
    assert wit_client._failed_optional_holding_addrs[30407][1] == threshold + 1
    assert wit_client._optional_holding_blocked(30407) is True


# ---------------------------------------------------------------------------
# Clear on (re-)connect
# ---------------------------------------------------------------------------


def test_reconnect_clears_both_blacklists():
    hub = FakeHub()
    client = _client(hub)
    now = time.time()
    client._failed_optional_ranges = {(31200, 24): (now, 4)}
    client._failed_optional_holding_addrs = {30407: (now, 4), 30200: (now, 4)}

    # Same connection: the state survives.
    client._sync_optional_blacklists_with_connection()
    assert client._failed_optional_holding_addrs != {}

    hub.reconnect()
    client._sync_optional_blacklists_with_connection()
    assert client._failed_optional_ranges == {}
    assert client._failed_optional_holding_addrs == {}


def test_read_all_data_clears_blacklists_after_a_reconnect():
    """The clear must be wired into the poll, not merely available as a helper."""
    hub = FakeHub()
    client = _client(hub)
    # An empty profile makes read_all_data bail immediately after the sync step.
    client.register_map = {"name": "STUB", "input_registers": {}, "holding_registers": {}}
    client._failed_optional_holding_addrs = {30407: (time.time(), 9)}

    hub.reconnect()
    assert client.read_all_data() is None
    assert client._failed_optional_holding_addrs == {}


# ---------------------------------------------------------------------------
# Why a read failed decides whether a reconnect re-arms it
# ---------------------------------------------------------------------------


def _fail_until_blocked(client, anchor, kind):
    """Fail `anchor` enough consecutive polls that the backoff engages."""
    for _ in range(_gm._VPP_HOLDING_FAIL_THRESHOLD):
        _read_device_info(client, KindedHoldingReads(fail={anchor}, kind=kind, client=client))
    assert client._optional_holding_blocked(anchor) is True


def test_no_response_backoff_survives_a_reconnect():
    """A register the inverter ignores must stay backed off across reconnects.

    Otherwise the expensive case loops: a timed-out read closes the socket, the next poll
    reconnects, the reconnect clears the backoff, and the unanswered read is armed again
    for the very next poll - which is what the skip exists to avoid.
    """
    hub = FakeHub()
    client = _client(hub)
    _fail_until_blocked(client, 30407, _gm.ERROR_KIND_NO_RESPONSE)

    hub.reconnect()
    client._sync_optional_blacklists_with_connection()

    assert client._optional_holding_blocked(30407) is True
    reads = KindedHoldingReads(fail={30407}, kind=_gm.ERROR_KIND_NO_RESPONSE, client=client)
    _read_device_info(client, reads)
    assert 30407 not in reads.starts()


def test_link_failure_backoff_is_cleared_by_a_reconnect():
    """The point of the whole change: a dead socket must not silence the VPP blocks."""
    hub = FakeHub()
    client = _client(hub)
    _fail_until_blocked(client, 30407, _gm.ERROR_KIND_LINK)

    hub.reconnect()
    client._sync_optional_blacklists_with_connection()

    assert client._optional_holding_blocked(30407) is False
    reads = KindedHoldingReads(values={30407: [1, 20, 65436, 1]}, client=client)
    data = _read_device_info(client, reads)
    assert 30407 in reads.starts()
    assert data.vpp_remote_power_available is True
    assert data.remote_power_control_enable == 1


def test_unclassified_failure_is_treated_as_a_link_failure():
    """Unknown provenance stays conservative - a transient error never sticks."""
    hub = FakeHub()
    client = _client(hub)
    _fail_until_blocked(client, 30407, None)

    hub.reconnect()
    client._sync_optional_blacklists_with_connection()
    assert client._optional_holding_blocked(30407) is False


def test_a_poll_with_every_block_backed_off_reads_none_of_them():
    """The skip still does its job: a poll must not pay for reads known not to answer."""
    hub = FakeHub()
    client = _client(hub)
    for anchor in ANCHORS:
        _fail_until_blocked(client, anchor, _gm.ERROR_KIND_NO_RESPONSE)

    hub.reconnect()
    client._sync_optional_blacklists_with_connection()

    reads = KindedHoldingReads(fail=set(ANCHORS), kind=_gm.ERROR_KIND_NO_RESPONSE, client=client)
    data = _read_device_info(client, reads)

    assert not (set(ANCHORS) & set(reads.starts()))
    # The poll still completed, and every block correctly reports "not read".
    assert data.vpp_remote_power_available is False
    assert data.vpp_export_limit_available is False
    assert data.vpp_control_authority_available is False


# ---------------------------------------------------------------------------
# The hub classifies the two failure modes
# ---------------------------------------------------------------------------


class _FakeTcpClient:
    """Just enough of a pymodbus TCP client for the hub's connect/close cycle.

    pymodbus is a real test dependency, so an unpatched hub would genuinely dial
    10.0.0.1:502 and block on the connect timeout. Patching the module-level name is the
    idiom used by tests/test_serial_shared_connection.py for `ModbusClient`.
    """

    def __init__(self, *args, **kwargs):
        self.socket = None

    def connect(self):
        self.socket = object()
        return True

    def is_socket_open(self):
        return self.socket is not None

    def close(self):
        # reset() only calls disconnect(), which does not drop the client object, so
        # is_socket_open() going False here is what makes the next ensure_connected()
        # open a genuinely new session and bump the generation.
        self.socket = None


@pytest.fixture
def fake_tcp_client(monkeypatch):
    monkeypatch.setattr(_gm, "ModbusTcpClient", _FakeTcpClient)
    return _FakeTcpClient


class _ErrorResponse:
    def isError(self):  # noqa: N802 - pymodbus spelling
        return True


class _GoodResponse:
    registers = [7]

    def isError(self):  # noqa: N802 - pymodbus spelling
        return False


def test_shared_connection_bumps_generation_on_each_fresh_connect(fake_tcp_client):
    hub = SharedModbusConnection("10.0.0.1", 502)
    assert hub.connection_generation == 0

    assert hub.ensure_connected() is True
    assert hub.connection_generation == 1

    # Socket already open - no new session, no bump.
    assert hub.ensure_connected() is True
    assert hub.connection_generation == 1

    hub.reset("test")
    assert hub.ensure_connected() is True
    assert hub.connection_generation == 2


def test_hub_reports_no_response_for_an_error_response(fake_tcp_client):
    hub = SharedModbusConnection("10.0.0.1", 502)
    hub.ensure_connected()
    hub._client.read_holding_registers = lambda **kw: _ErrorResponse()

    assert hub.read_holding_registers(30099, 1, 1) is None
    assert hub.last_error_kind == _gm.ERROR_KIND_NO_RESPONSE


def test_hub_reports_link_for_a_transport_exception(fake_tcp_client):
    hub = SharedModbusConnection("10.0.0.1", 502)
    hub.ensure_connected()

    def boom(**kw):
        raise OSError(32, "Broken pipe")

    hub._client.read_holding_registers = boom

    assert hub.read_holding_registers(30099, 1, 1) is None
    assert hub.last_error_kind == _gm.ERROR_KIND_LINK


def test_hub_clears_the_error_kind_on_success(fake_tcp_client):
    hub = SharedModbusConnection("10.0.0.1", 502)
    hub.ensure_connected()
    hub.last_error_kind = _gm.ERROR_KIND_LINK
    hub._client.read_holding_registers = lambda **kw: _GoodResponse()

    assert hub.read_holding_registers(30099, 1, 1) == [7]
    assert hub.last_error_kind is None


# ---------------------------------------------------------------------------
# A block that was not read must not reach the controls
# ---------------------------------------------------------------------------


def test_availability_map_covers_every_vpp_block_control():
    flags = _const.VPP_CONTROL_AVAILABILITY_FLAG
    data_fields = GrowattData().__dict__

    for control_name, flag in flags.items():
        assert control_name in _const.WRITABLE_REGISTERS, control_name
        assert flag in data_fields, flag
        assert control_name in data_fields, control_name

    # Every control backed by one of the three optional blocks must be listed, or its
    # entity goes on publishing the dataclass default.
    expected = {
        'control_authority': 'vpp_control_authority_available',
        'vpp_export_limit_enable': 'vpp_export_limit_available',
        'vpp_export_limit_power_rate': 'vpp_export_limit_available',
        'remote_power_control_enable': 'vpp_remote_power_available',
        'remote_power_control_charging_time': 'vpp_remote_power_available',
        'remote_charge_and_discharge_power': 'vpp_remote_power_available',
    }
    assert flags == expected


def test_control_entities_consult_the_availability_map():
    """select.py / number.py cannot be imported without the full HA runtime, so the
    wiring is checked at source level (the approach test_sensor_conditions.py uses)."""
    from pathlib import Path

    component_dir = Path(__file__).parent.parent / "custom_components" / "growatt_modbus"
    for filename in ("select.py", "number.py"):
        src = (component_dir / filename).read_text(encoding="utf-8")
        assert "VPP_CONTROL_AVAILABILITY_FLAG" in src, filename
        # Both the availability property and the value property must gate on it.
        assert src.count("VPP_CONTROL_AVAILABILITY_FLAG.get(self._control_name)") == 2, filename
        assert "def available(self) -> bool:" in src, filename
