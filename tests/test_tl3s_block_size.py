"""TL3-S must poll in blocks its firmware accepts (#432).

A TL3-S on firmware dhaa01 answers Illegal Function to the poll's single 113-register input
read (0-112), which failed every poll with every entity unavailable - while the same data
read cleanly in smaller requests. The reporter confirmed block sizes 50, 25, 10, 5 and 1 all
poll correctly and only Auto fails. The DH1.0 unit the profile was built from (#299) reads
125 at once, so a 50 limit suits both known units.

Driven through the real read path with a fake inverter that refuses input reads over 50
registers, not by inspecting the profile dict: the poll's block logic decides the request
sizes, and that is what has to be right.
"""
from __future__ import annotations

import importlib

_gm = importlib.import_module("growatt_under_test.growatt_modbus")

LIMIT = 50


def _poll_against_limited_inverter():
    client = _gm.GrowattModbus(connection_type="tcp", host="10.0.0.1", port=502,
                               slave_id=1, register_map="TL3_S_3000_15000")
    requests: list[tuple[int, int]] = []

    def read_input_registers(start, count, log_errors=True):
        requests.append((start, count))
        if count > LIMIT:
            return None  # what an Illegal Function exception becomes at this layer
        return [1000 + start + i for i in range(count)]

    client.read_input_registers = read_input_registers
    client.read_holding_registers = lambda start, count: None
    return client.read_all_data(), requests


def test_no_input_request_exceeds_what_dhaa01_accepts():
    _, requests = _poll_against_limited_inverter()
    assert requests, "the poll made no input reads at all"
    oversized = [r for r in requests if r[1] > LIMIT]
    assert not oversized, (
        f"the TL3-S poll still sends input reads larger than {LIMIT} registers: "
        f"{oversized} - firmware dhaa01 refuses these with Illegal Function (#432)"
    )


def test_the_poll_succeeds_on_that_inverter():
    data, _ = _poll_against_limited_inverter()
    assert data is not None, (
        "the TL3-S poll fails outright against an inverter that only accepts "
        f"reads of up to {LIMIT} registers (#432)"
    )
