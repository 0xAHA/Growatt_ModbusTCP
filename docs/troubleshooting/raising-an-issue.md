# Raising an Issue

Please [search existing issues](https://github.com/0xAHA/Growatt_ModbusTCP/issues) first — your inverter model or symptom may already be covered.

---

## Start here: two attachments answer most questions

You don't need to fill in a long form. These two cover the majority of reports.

### 1. Download diagnostics

**Settings → Devices & Services → Growatt Modbus → ⋮ → Download diagnostics**

Attach the JSON file to your issue. It already contains almost everything that used to be asked for by hand: integration version, inverter model and profile, connection type, block size, poll interval, how many polls have failed, which register ranges responded, and the last full set of decoded values.

Your **IP address, serial number and device path are removed automatically** before the file is written.

### 2. Logs, as text

**Settings → Devices & Services → Growatt Modbus → Enable debug logging**, reproduce the problem, then **Disable debug logging** — Home Assistant downloads the log for you.

Please paste log lines as text in a code block rather than a screenshot. Screenshots can't be searched, and the useful detail is often a register number or a count in the middle of a long line.

!!! tip "Is there anything under Settings → Repairs?"
    Since v1.5.0 the integration raises repair notices for problems it can detect itself, such as an inverter reverting your settings or a gateway returning malformed responses. If one is showing, say so — it usually names the cause outright.

---

## Then: what kind of problem is it?

Different symptoms need different evidence. Find yours below.

### A sensor shows a wrong or impossible value

Say **which sensor**, **what it reads**, and **what you believe it should be** — the last part matters most, and it's the part most often left out.

If you can compare against another source — the ShinePhone app, the Growatt portal, a utility meter — that comparison is the single most valuable thing you can provide. It has repeatedly settled questions that register tables could not, including one register everyone assumed was battery temperature that turned out to be the inverter's DC-DC converter stage.

**One reading proves very little.** Two registers can hold identical values by coincidence at one moment and diverge completely an hour later. If you're reporting that a value looks wrong, a second reading at a different time of day — or a different battery or solar state — turns a guess into evidence.

### A sensor is missing, or you think a register is mapped wrongly

Run the [Universal Register Scanner](diagnostic-service.md) and attach the CSV.

!!! warning "Disable the integration before scanning"
    **⋮ → Disable**, wait about 30 seconds, run the scan, then re-enable. Don't delete it.

    The scanner opens its own connection. If the integration is still polling, the two compete for the same adapter and the results are meaningless — one scan came back with 9 usable rows out of 1304 on a system that was working perfectly.

### The connection drops, or entities go unavailable

Nearly always the RS485 adapter rather than the inverter or the integration. Read [RS485 Gateways](rs485-gateways.md) first — it lists which adapters are known to work, the settings that matter, and how to tell a gateway fault from an inverter one.

Worth including: your adapter model, and whether the problem survives a restart of Home Assistant.

### A control won't stick, or reverts after a few seconds

Usually the Growatt cloud overwriting your change. If a **ShineWiFi or ShineLink dongle** is connected, the cloud can restore its own settings within seconds of a local write. The integration detects this and raises a repair notice.

Say which control, what you set it to, and what it reverted to.

### Your inverter model isn't supported, or auto-detection picks the wrong profile

Attach a register scan (see above) and tell us the **exact model from the inverter's label**, not the marketing name. If you know your DTC code, say so — it's in the diagnostics file and in the scan.

---

## Things that genuinely help

- **Correcting yourself.** Several of the most valuable reports have been people revisiting their own findings after measuring properly. It's never unwelcome — it has repeatedly stopped a working register being "fixed" into a broken one.
- **Saying what you already ruled out**, and how. It prevents the same ground being covered twice.
- **Telling us it's working.** Confirmation that a fix landed is what lets an issue close, and a report that something works on hardware nobody else has is genuinely useful data.

## Things that slow it down

- Screenshots of text.
- "It doesn't work" without saying what *it* is, or what you expected instead.
- A scan taken while the integration was still running (see the warning above).

---

None of this is a barrier to reporting. If you're unsure what to include, **open the issue anyway with the diagnostics file attached** — it's better to ask a follow-up question than to have a problem go unreported.
