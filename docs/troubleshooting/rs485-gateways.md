# RS485-to-TCP Gateways

Most problems that look like integration bugs turn out to be the box between Home Assistant and the inverter. This page collects what has actually been measured on real hardware, with the issue numbers behind each claim.

> A gateway can look correctly configured, pass a casual test, and still be the thing that's broken. Some fail loudly. The dangerous ones fail quietly.

---

## The one setting that matters most

Your gateway must do **Modbus TCP to RTU translation**, not transparent passthrough.

This integration uses `pymodbus`'s `ModbusTcpClient`, which speaks Modbus TCP with MBAP framing. A transparent passthrough forwards raw RTU bytes with no MBAP header, and the client cannot parse them. It will not work at all, no matter how good the hardware is.

That is a **mode setting**, not a hardware quality question. Check it before buying anything or blaming anything else.

### Buying a gateway: check the feature, not the firmware version

Two units from the same manufacturer, even with similar names, can be different product lines with separate firmware and separate behaviour. A version number that works for someone else tells you nothing about a different model.

The question that *is* answerable from a product page:

> Does it offer a genuine **Modbus TCP to RTU** mode with a configurable instruction timeout?

If yes, it will probably work. If it only does transparent passthrough, it cannot work with this integration at all — regardless of build quality, price, or how well it performs for other protocols.

---

## Field-tested hardware

### ✅ Waveshare RS485 TO POE ETH (B) — known good

Firmware V1.523, reported in [#367](https://github.com/0xAHA/Growatt_ModbusTCP/issues/367) on a MID 25KTL3-XH.

| Setting | Value |
|---|---|
| Protocol | `Modbus TCP to RTU` — **not** "None"/transparent |
| Instruction Timeout | 288 ms — must exceed the transmission time of your largest block |
| RS485 Conflict Gap | 20 ms |

Measured: zero short/misaligned reads, 89 sensors populated, two full register scans of 2300 registers across 17 ranges with no read errors, and **26 days of statistics from before the v1.3.7 guard existed with no corrupt values at all**. On this gateway there was never anything to catch.

### ✅ Elfin EW11 / EW11A — known good

Running on the maintainer's own MIN 10000TL-X without issue, and the reference setup most fixes in this integration are verified against. An Elfin EW11 also produced the register readings behind [#326](https://github.com/0xAHA/Growatt_ModbusTCP/issues/326).

Set the work mode so it performs **Modbus TCP to RTU** conversion rather than plain transparent passthrough — see the section above for why that is the one setting that decides whether a gateway can work at all.

One EW11A report ([#309](https://github.com/0xAHA/Growatt_ModbusTCP/issues/309)) showed all entities reading zero, but the same symptom followed the reporter onto a Waveshare adapter, so the gateway was not the cause. They resolved it with a Growatt WiLan-X2.

### ✅ Growatt WiLan-X2 — known good

Growatt's own dongle, which exposes Modbus directly. Reported working in [#309](https://github.com/0xAHA/Growatt_ModbusTCP/issues/309) after two third-party adapters had been ruled out. It also buffers roughly a month of data and re-synchronises after a power cut, which no generic serial server does.

### ⚠️ PUSR / ShineWiFi-class serial bridges — replay stale frames

Reported in [#360](https://github.com/0xAHA/Growatt_ModbusTCP/issues/360) and [#367](https://github.com/0xAHA/Growatt_ModbusTCP/issues/367).

These can return **a complete, valid response to an earlier request** when answering the current one. Measured at roughly **one poll in three**, with 30 of 31 mismatches returning exactly 125 registers regardless of what was asked for.

Since v1.3.7 the integration detects this and discards the frame, so the data is safe — but you will see `Short/misaligned read at N: got X of Y registers` warnings. If you are on an older version, this is the failure mode that published a serial-number fragment as 85,893,614.8 W of AC power.

Two settings materially improved a PUSR unit on #360:

| Setting | Change | Why |
|---|---|---|
| TCP timeout | disabled → **30 s** | With it disabled, dead sessions are never reaped and eventually every connection slot is held by a connection to nobody |
| UART AutoFrame | disabled → **100 ms** | Frame fragmentation causes the parser to lock onto the wrong byte offset and read a nonsense unit ID |

### ❌ Olimex ESP32-POE-ISO + `esphome_modbus_bridge` — unstable

Reported in [#367](https://github.com/0xAHA/Growatt_ModbusTCP/issues/367). Repeated dropouts, TCP host unreachable for two to three minutes at a time, recovering on its own with no pattern tied to load, time of day or PV production. RS485 bias resistors made no difference, which pointed at the network side rather than the serial side. Replaced with the Waveshare above.

---

## Diagnosing your own gateway

**Is it replaying stale frames?** Look for `Short/misaligned read` warnings. Note whether the count returned is *larger* than requested — a reply longer than the request cannot be a truncation, and points at a replayed earlier response.

**Is latency per-request or per-register?** This decides whether a smaller block size helps or hurts. Read the same register range at several block sizes and compare total time:

- If time scales with the number of registers, smaller blocks help.
- If time is roughly **fixed per request**, smaller blocks are much worse.

On the PUSR unit in #367, 113 registers cost the same as 1 — every read landed in one of two clusters ~500 ms apart, which looks like an internal scheduling tick. Block size 1 would have meant ~113 requests of ~0.8 s each in place of a single 1.3 s read. **Block size 25 was kept.**

**Careful measuring latency from logs.** A 15-18 s figure reported on #367 turned out to be the integration's own failure cycle — a 10 s timeout plus reset and retry — not gateway latency. Measure with raw sockets and the integration disabled.

**Symptom survives a gateway swap?** Then the gateway is not the variable. One reporter saw every entity read zero on an EW11A, fitted a Waveshare, and got exactly the same result — which ruled out both adapters in a single step and pointed at the inverter side instead ([#309](https://github.com/0xAHA/Growatt_ModbusTCP/issues/309)). Swapping hardware is slow, but it is decisive in a way that reading logs often is not.

**Running a register scan?** Disable the integration entry first (**⋮ → Disable**, don't delete), wait ~30 s, then scan. The scanner opens a second connection, and on a sensitive gateway that contends with the poller. A scan taken while polling came back with 9 successful reads out of 1304 rows, every range reporting "no response" on a device that was working fine.

---

## Does a persistent connection cause this?

No — and this was tested directly.

The integration holds one socket per host:port across polls. It was suspected of allowing a stale frame to linger in the buffer, but the clean Waveshare setup uses **the same shared connection and the same 60 s interval** with zero mismatches. A persistent socket is not the mechanism; it is what exposes a gateway that replays. Since v1.3.7 a detected mismatch also drains the receive buffer, so a misaligned stream does not persist into the next read.

| Gateway | Socket | Result |
|---|---|---|
| ShineWiFi-class | persistent | mismatch ~1 poll in 3 |
| ShineWiFi-class | fresh per read | 21/21 clean |
| Waveshare RS485 TO POE ETH (B) | persistent | clean |

---

## Keeping the cloud app working

You do not necessarily have to choose. On both systems in #367 the inverter has a **`SYS COM` port separate from the USB port the ShineWiFi dongle occupies**, so a second RS485 master can run alongside the stock dongle. Home Assistant gets a local Modbus path, and the dongle keeps feeding Growatt's own app.

Note this is one local path and one cloud path — not two paths into Home Assistant. If you keep the dongle, be aware the Growatt cloud can overwrite local writes to control registers within seconds; the integration logs a `Write reversion detected` warning when it sees this.
