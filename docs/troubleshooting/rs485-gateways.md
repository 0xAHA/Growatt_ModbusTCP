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

**Two more settings if you see `Very short frame: 0x0` or null bytes**, contributed from a working install ([#356](https://github.com/0xAHA/Growatt_ModbusTCP/issues/356)):

| Setting | Value | Why |
|---|---|---|
| Multi-Client / Max Socket Client | **1** | The default allows up to 8. Several clients querying one RS485 bus at 9600 baud interleave on the wire and corrupt frames |
| Connection / TCP Idle Timeout | **30-60 s** | A dead session is dropped promptly, so a restarted Home Assistant is not refused while the gateway still holds the old socket |

The first matters more than it sounds. The bus is a single shared medium: a second client is not a second conversation but an interruption of the first, and the resulting fragment arrives as a valid-looking short read rather than as an error.

### ✅ Elfin EW11 / EW11A — known good

Running on the maintainer's own MIN 10000TL-X without issue, and the reference setup most fixes in this integration are verified against. An Elfin EW11 also produced the register readings behind [#326](https://github.com/0xAHA/Growatt_ModbusTCP/issues/326).

Set the work mode so it performs **Modbus TCP to RTU** conversion rather than plain transparent passthrough — see the section above for why that is the one setting that decides whether a gateway can work at all.

One EW11A report ([#309](https://github.com/0xAHA/Growatt_ModbusTCP/issues/309)) showed all entities reading zero, but the same symptom followed the reporter onto a Waveshare adapter, so the gateway was not the cause. They resolved it with a Growatt WiLan-X2.

!!! tip "It can hang after its settings are changed — reboot it"
    Changing the EW11's Modbus or network settings can leave it running but refusing every connection. It stays visible on the network and its web interface may still load, yet nothing can open a Modbus session ([#368](https://github.com/0xAHA/Growatt_ModbusTCP/issues/368)).

    The distinguishing feature is that it survives everything done on the Home Assistant side. That reporter downgraded the integration, restored several backups, and built a second Home Assistant instance from scratch — the fault followed all of it, because none of those touch the gateway. **Rebooting the EW11 fixed it immediately.**

    Reboot the gateway before spending time on anything else whenever data stops arriving and nothing about your inverter has changed.

### ✅ Growatt ShineWiLan-X2 — works, within limits

Growatt's own dongle. It exposes a **local Modbus TCP server on port 502 while keeping its cloud connection**, so you get local data in Home Assistant and the ShinePhone app at the same time — no need to choose. It also buffers data and re-synchronises after a power cut, which no generic serial server does.

!!! warning "It must be the **-X2**"
    The earlier ShineWiLan has **no Modbus TCP server** and cannot be used with this integration at all. Confirmed by a user who swapped modules. If you are buying or asking Growatt for one, the `-X2` suffix is the whole difference.

**The one real limitation:** that local Modbus server is built for light polling, not sustained access from a full integration. A WIT owner saw the connection drop repeatedly under normal polling ([#308](https://github.com/0xAHA/Growatt_ModbusTCP/issues/308)), and WIT is the most register-hungry profile here.

If you see intermittent drops on an X2, raise **scan_interval** before suspecting anything else — 60 s or more, and longer again on WIT. A dedicated RS485 adapter is the answer if you want fast polling; the X2 is the answer if you want one device doing both jobs.

Working setups reported in [#309](https://github.com/0xAHA/Growatt_ModbusTCP/issues/309) (after two third-party adapters were ruled out) and [#336](https://github.com/0xAHA/Growatt_ModbusTCP/issues/336) on MOD/MID XH.

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

**Read the failure type before anything else.** A register scan records why each read failed, and the two common answers mean opposite things:

| In the scan's Status column | Meaning |
|---|---|
| `ConnectionException` on **every** row | The TCP socket never opened. Nothing about registers, block sizes or profiles applies — the gateway is unreachable or refusing connections |
| `ModbusIOException`, short reads, or a mix of successes and failures | The connection works and the conversation is failing. Now block size, pacing and gateway settings are worth tuning |

The first case is worth checking first because it is quick to confirm and rules out everything else. In [#368](https://github.com/0xAHA/Growatt_ModbusTCP/issues/368) all 2425 rows carried the same `ConnectionException`, which meant no amount of integration tuning could have helped — and the reporter had already downgraded, restored backups and rebuilt Home Assistant before that was spotted.

**A setting that will not stick, while sensors read fine.** Gateways and dataloggers commonly close a connection that has been idle for a while. Reads recover from that transparently — the next poll reconnects and retries — so the symptom is one-sided and easy to misread: sensors keep updating normally while a switch, number or select silently reverts. It shows up most often on the first change made after a quiet period. From v1.6.2 writes reset and retry on a dropped socket the same way reads always have ([#375](https://github.com/0xAHA/Growatt_ModbusTCP/issues/375)). On earlier versions, making the change a second time straight away usually works, because the connection is live by then.

**Tuning has a floor, and it is the wiring.** Block size, pacing and gateway settings can only make the best of the signal that arrives. If reads keep failing after you have taken block size down and the Modbus delay up, the problem is likely physical:

- **Termination.** RS485 wants a 120 Ω resistor at each end of the run — the two ends, not every device. Without it, signals reflect off the unterminated ends and corrupt the frames behind them. Most gateways have a jumper or DIP switch to enable an internal terminator.
- **Cable and routing.** Use a twisted pair for A/B, keep the run away from anything switching high current, and avoid star topologies — RS485 is a daisy chain.
- **Where the noise is.** An inverter's own power stage is an electrically hostile neighbour, and the gateway is usually mounted right next to it.

Reported in [#370](https://github.com/0xAHA/Growatt_ModbusTCP/issues/370): sustained transport errors every 2-3 minutes across two multi-hour sessions on a bus with no termination, wired directly alongside the inverter's power stage — with the integration already at block size 10 and a 1000 ms delay, which is as far as tuning goes.

Two symptoms point this way rather than at settings:

- **Failures that recur on a rough interval regardless of what you are doing** — the same rate whether polling normally, writing settings, or running a scan
- **Diagnostics showing `recoveries_this_poll` at its ceiling.** The integration allows two connection recoveries per poll. At the limit, whatever is read late in the cycle gets no retry at all, so the last blocks read look far worse than the link actually is

**Symptom survives a gateway swap?** Then the gateway is not the variable. One reporter saw every entity read zero on an EW11A, fitted a Waveshare, and got exactly the same result — which ruled out both adapters in a single step and pointed at the inverter side instead ([#309](https://github.com/0xAHA/Growatt_ModbusTCP/issues/309)). Swapping hardware is slow, but it is decisive in a way that reading logs often is not.

**Running a register scan?** Disable the integration entry first (**⋮ → Disable**, don't delete), wait ~30 s, then scan. The scanner opens a second connection, and on a sensitive gateway that contends with the poller. A scan taken while polling came back with 9 successful reads out of 1304 rows, every range reporting "no response" on a device that was working fine.

Then **select the entry under "Config entry" instead of typing host and port**, so the scan reuses the slave ID, Modbus delay and block size that already work on this gateway. Typing the connection by hand falls back to defaults — 125-register reads at 250 ms — which is exactly the request pattern the tuning existed to avoid, and it produces an equally empty scan for the opposite reason. Selecting a disabled entry is supported from v1.5.2; before that it silently forced the manual path.

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

## Two or more inverters on one adapter

If you run several inverters as separate integration entries over **one** USB-RS485 adapter or one gateway, they share a single physical bus. Only one master can be talking at a time.

The integration handles this for you: every entry pointing at the same device path (or the same host:port) shares one connection and one lock, so their reads are queued rather than interleaved. Nothing to configure.

**Serial setups need v1.7.0 or later for this.** Before that, only TCP entries were coordinated — each serial entry opened its own client on the same adapter and paced only itself, which produced random read failures on *all* the inverters sharing that bus. If you have two entries on one adapter and see unexplained dropouts, this is the first thing to rule out.

Two consequences worth knowing:

- **Polls queue, they do not overlap.** With several inverters the effective cycle is the sum of their polls. If a single poll takes 8 s, three inverters need an interval comfortably above 24 s.
- **A slow or failing inverter slows the others**, because they wait for the bus. If one entry is much worse than the rest, disable it and see whether the others recover — that isolates the problem device quickly.

Raising the scan interval is the main lever here, exactly as it is for a single unit.

---

## Gaps in the graph are the fix, not the fault

Since **v1.6.6** a register that could not be read is published as **unavailable** for that poll, not as `0`.

If you upgraded from an older version, occasional short gaps in your solar or battery graphs are the same dropped frames you always had — they are simply no longer disguised. Before, a single failed block read produced a vertical drop to 0 W and back within one poll, with nothing logged as an error, because from Home Assistant's side the poll had succeeded.

Zero is not a neutral placeholder. It is a plausible measurement, it enters long-term statistics, and afterwards it cannot be told apart from a real one. A gap is unambiguous.

**A genuine zero is still recorded.** Night-time, standby and a truly idle string all still read 0.

### Telling the two apart

This matters when you are judging whether a change actually helped:

| What you see | What it means |
|---|---|
| Vertical drop to 0 and back, **one sample** | Pre-v1.6.6 behaviour — upgrade |
| **Gap**, one or two samples | A dropped frame. Normal on a serial bus; reduce by raising the scan interval |
| **Flat-bottomed dip** across several consecutive polls, with voltage and current still reporting plausible values | Not a comms fault. The inverter reported this — see below |

The third row is the one most often misread as a communication problem. If the reads had failed, every sensor in that block would be gapped together; values that are present, low, and consistent with each other came from the inverter.

To find out why the inverter backed off, overlay **Battery SOC**, **Battery Power**, **Load Power** and **Inverter Status** on the same window — on most profiles these are read in the same block as the PV registers, so they also confirm the read succeeded. A full battery with a low load is the common answer: the inverter has nowhere to send the energy and throttles the MPPT, which is correct behaviour.

Do not use the Growatt cloud app to cross-check a short dip. ShinePhone stores 5-minute averages, so a 30-second event is smoothed to roughly a 10% dent — it cannot confirm or rule out anything at that timescale. Your own recorder has far better resolution.

Occasional dropped frames are normal on RS485 and cannot be eliminated entirely. Raising the scan interval reduces how often they happen by reducing how many reads you make — the failure rate per read stays the same.

---

## Keeping the cloud app working

You do not necessarily have to choose. On both systems in #367 the inverter has a **`SYS COM` port separate from the USB port the ShineWiFi dongle occupies**, so a second RS485 master can run alongside the stock dongle. Home Assistant gets a local Modbus path, and the dongle keeps feeding Growatt's own app.

Note this is one local path and one cloud path — not two paths into Home Assistant. If you keep the dongle, be aware the Growatt cloud can overwrite local writes to control registers within seconds; the integration logs a `Write reversion detected` warning when it sees this.
