# ESS Protocol (BMS block)

> **Source document:** *Growatt xxSxxP ESS Protocol*, rev 2.3, 2017-11-28
> (`Protocols/1xSxxP_ESS_Protocol_rev2.3_20171128.pdf`)

## Why this page exists

Protocol V1.39 documents the BMS block at input registers **1082-1124** by name only. Against
the first row, register 1082 `BMS_StatusOld`, it carries this note and nothing else:

> Detail information, refer to document: **GrowattxxSxxP ESS Protocol**

So V1.39 gives you the register *names* for the whole block and defers the units, scales and
encodings to a separate document. That document is the one above, and it is the reason
several of these registers were mapped by guesswork for a long time.

!!! warning "This is not a register map you can poll"

    The ESS Protocol describes the link between the **inverter, the battery and an
    application program** — a separate Modbus conversation in its own address space
    (`0x0010`-`0x0052`). You cannot read these addresses from the inverter.

    What it gives us is the **meaning of the values** the inverter republishes in its own
    input registers at 1082+. The address correspondence below is the useful part.

## Address correspondence

Evident from the names, and confirmed on hardware where marked.

| ESS address | ESS name | V1.39 input register | Unit / encoding |
|---|---|---|---|
| `0x0010` | Gauge IC current | 1100 `BMS_GaugeICCurr` | 10 mA |
| `0x0013` | Status | 1083 `BMS_Status` | bitfield |
| `0x0014` | Error | 1085 `BMS_Error` | bitfield |
| `0x0015` | SOC | 1086 `BMS_SOC` | **%** ✅ |
| `0x0016` | Voltage | 1087 `BMS_BatteryVolt` | **10 mV** ✅ |
| `0x0017` | Current | 1088 `BMS_BatteryCurr` | **10 mA**, two's complement ✅ |
| `0x0018` | Temperature | 1089 `BMS_BatteryTemp` | **°C, -127 to 127** ✅ |
| `0x0019` | Max charge/discharge current | 1090 `BMS_MaxCurr` | — |
| `0x001A` | Gauge RM | 1091 `BMS_GaugeRM` | 10 mAh |
| `0x001B` | Gauge FCC | 1092 `BMS_GaugeFCC` | 10 mAh |
| `0x001C` | YW / FW | 1093 `BMS_FW` | byte 1 hardware, byte 2 software |
| `0x001D` | Delta | 1094 `BMS_DeltaVolt` | V, cell voltage |
| `0x001E` | Cycle Count | 1095 `BMS_CycleCnt` | — |
| `0x0020` | SOH | 1096 `BMS_SOH` | bits 0-6 counter, bit 7 flag |
| `0x0021` | CV Voltage | 1097 `BMS_ConstantVolt` | 10 mV |
| `0x0022` | Warning | 1099 `BMS_WarnInfo` | bitfield |

✅ = confirmed against instruments on an SPH3620
([#397](https://github.com/0xAHA/Growatt_ModbusTCP/issues/397)): SOC against the inverter's
own sensor, voltage against a meter reading 54.2 V, **current against a clamp DC ammeter
reading 16.4 A**, temperature against a thermal camera.

The correspondence is not a fixed offset — 1082 `BMS_StatusOld` and 1084 `BMS_ErrorOld` are
inverter-side copies with no ESS equivalent, which shifts the run.

## The three that matter most

### Current is 10 mA, not 100 mA

`0x0017` is documented in units of **10 mA**, so the scale is **0.01 A**. Raw 1640 is 16.4 A.

This settled a real disagreement. Four SPH maps use 0.01, confirmed against a clamp meter;
`SPH_8000_10000_HU` used 0.1, which was neither documented nor measured and was most likely
taken by analogy from register **3170 `Ibat`**, which genuinely *is* 0.1 A on the MIN/MOD
range. Corrected to 0.01.

### Current is signed, and the encoding is explicit

The document's *"See Current explain"* table:

| Range | Meaning |
|---|---|
| `0x0000`-`0x7FFF` | current is positive |
| `0x8000`-`0xFFFF` | current is negative |

Plain two's complement. That is why these registers carry `'signed': True`.

!!! note "What it does *not* define"

    The spec fixes the **numeric encoding** and never states which physical direction is
    positive. Whether charging reads positive is a property of the firmware, not of this
    document.

    On an SPH3620 it is the standard one — **positive charging, negative discharging** —
    confirmed in both directions against the reported power
    ([#397](https://github.com/0xAHA/Growatt_ModbusTCP/issues/397)):

    | State | Current | Voltage | Implied | Reported |
    |---|---|---|---|---|
    | Charging | **+44.30 A** | 54 V | 2392 W | ~2.4 kW |
    | Discharging | **-54.00 A** | 53 V | 2862 W | 2.8 kW |
    | Discharging | **-4.20 A** | 53 V | 223 W | 220 W |

    Those also confirm the 0.01 scale across a 13x range of magnitudes, from 4.2 A to 54 A.

    Still one model, though. See [Invert Battery Power](../hardware/models.md) if your
    battery power reads backwards — noting that option affects battery *power* and not
    battery *current*.

### Temperature is whole degrees

`0x0018` is documented as **°C** with a range of **-127 to 127** — whole degrees, signed. Not
tenths.

This matters because V1.39 documents the inverter's *own* battery temperature at register
**1040** as `0.1C`, and at least one SPH3620 populates 1040 from the BMS value without
rescaling it — so 25 °C arrives as raw 25 and the documented scale renders it as 2.5 °C. The
integration detects and corrects that at read time rather than changing the scale, because
spec-compliant inverters do report tenths there.

## Bitfields

The document also defines the status, error and warning bitfields behind registers 1083,
1085 and 1099. The integration does not currently decode them; the tables are in the PDF if
anyone wants to.

| Register | ESS | Contents |
|---|---|---|
| 1083 `BMS_Status` | `0x0013` | bits 0-1 state (soft start / standby / charging / discharging), bit 3 cell balance, bit 4 sleep, bits 5-6 discharge and charge output, bit 7 terminal status, bits 8-9 master box mode, bits 10-11 SP status |
| 1085 `BMS_Error` | `0x0014` | 15 protection flags — over/under voltage, over-current charge and discharge, short circuit, over/under temperature for charge and discharge separately, MOS and environment temperature |
| 1099 `BMS_WarnInfo` | `0x0022` | warning-level equivalents of the above, plus bits 14-15 giving battery chemistry (00 LiFePO4, 01 ternary lithium, 10 lithium titanate) |

## Applicability

The document is titled for the **1xSxxP** family (SPF 5 kW, MHP 5 kW), and V1.39 references
it generically as *"GrowattxxSxxP"* for the BMS block. Treat the units as reliable for the
BMS block on SPH; treat anything model-specific with the usual caution, and prefer a
measurement where one exists.
