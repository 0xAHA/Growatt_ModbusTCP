# Growatt ShineTools firmware acquisition and static analysis

This document records how firmware download URLs were recovered from the
Growatt **ShineTools** Android application using ADB/logcat, how the
`ALBA18xxxxZABA22FFFFxx-C.zip` package was downloaded and unpacked, and what
subsequent static analysis revealed about the two processor firmware images in
that package.

The acquisition and reverse-engineering steps described here were performed on
local copies. No firmware flashing is required to reproduce the catalogue
capture or the static analysis.

## Executive summary

The key discovery was that ShineTools logs the complete response body of its
firmware-catalogue request to Android logcat. When the firmware-download screen
was opened, the application requested:

```text
GET https://oss.growatt.com/api/v3/userCenter?op=getOssFileUploadListByServer
```

The HTTP 200 response contained a JSON firmware catalogue with direct
`cdn.growatt.com` URLs in the fields `-C`, `-U`, `bsdiff`, and `bsdiffC`, plus
`zipSize` metadata.

The captured manifest contains **75 unique firmware/update URLs**:

- **51** URLs in manifest field `-C`
- **23** URLs in manifest field `-U`
- **1** URL in `bsdiff`
- **0** URLs in `bsdiffC`

By filename, these are **51 `-C.zip` files,
12 `-U.zip` files, 11 plain
version-number ZIP files, and 1 binary differential
patch**.

A separate ShineTools request returned one `Safety_330.bin` grid/safety file.
That file is listed separately because it came from `findSafetyFile`, not from
the firmware catalogue.

For the Growatt MIN 2.5–6KTL-XH/XH2 family, model key `e86c21` exposes:

```text
ALBA18xxxxZABA22FFFFxx-C.zip
```

That ZIP is especially important because it contains **two separate firmware
images, one for each processor in the inverter**:

1. `ALBA18.hex` — firmware for the TI C2000/C28x-side processor, associated
   with inverter/power-control functions.
2. `ZABA22.bin` — firmware for the ARM Cortex-M communication-side processor.

`UpdateConfig.txt` explicitly defines the update order:

```text
1=ALBA18.hex
2=ZABA22.bin
```

This explains the two-stage `(1/2)` and `(2/2)` firmware update shown by
ShineTools.

In the Growatt/ShineTools version information observed during this work, the
**ZABA** component is presented as the **communication firmware/version**.
That is the primary basis for referring to `ZABA22` as the communication-
processor firmware below. The static analysis is independently consistent with
that assignment.

---

## 1. Capturing the firmware catalogue with ADB

### Requirements

- An Android device with ShineTools installed
- Developer options and USB debugging enabled
- `adb` installed on the host
- The host authorized on the Android device

Verify the connection:

```bash
adb devices
```

No Android root access was required for the successful method. In fact,
ShineTools' private app storage was not needed: the useful information was
exposed by the application's own HTTP logging.

### Logcat command used

The log buffer was cleared and filtered for firmware/download-related messages:

```bash
adb logcat -c

adb logcat -v time | grep --line-buffered -Ei \
'CollectorDownLoadManager|FirmWareDownload|CollectorUpgradeFileInfo|diffFile|fullAmountFile|bsdiff|ALBA|ZABA|oss\.growatt|upgrade'
```

With that running, the firmware download/update screen was opened in
ShineTools.

The relevant log sequence was:

```text
D/UserManager: cacheBaseUrl=https://oss.growatt.com/
D/UserManager: currentOssBaseUrl:set():BaseUrl=https://oss.growatt.com/,...

I/EasyHttp: --> GET https://oss.growatt.com/api/v3/userCenter?op=getOssFileUploadListByServer
I/EasyHttp: <-- http/1.1 200 https://oss.growatt.com/api/v3/userCenter?op=getOssFileUploadListByServer
I/EasyHttp: body:{"msg":"","result":1,"request":null,"obj":{...}}
```

The JSON body contained the complete firmware catalogue and direct download
URLs.

### Safer way to preserve the complete response

Because logcat may wrap a large JSON body across multiple physical lines, it is
convenient to save the full stream first:

```bash
adb logcat -c
adb logcat -v time | tee shinetools.log
```

Open the ShineTools firmware screen, wait until the catalogue is fetched, then
stop logcat and inspect the saved log:

```bash
grep -nEi \
'getOssFileUploadListByServer|CollectorDownLoadManager|FirmWareDownload|bsdiff|ALBA|ZABA|cdn\.growatt' \
shinetools.log
```

In the captured session the same manifest was fetched more than once,
including when `FirmWareDownload2Activity` was opened.

### Manifest endpoint

Observed endpoint:

```text
https://oss.growatt.com/api/v3/userCenter?op=getOssFileUploadListByServer
```

This report only claims that the running ShineTools application received an
HTTP 200 response from this endpoint. Independent unauthenticated access to the
manifest was not required in order to recover the download URLs.

The firmware files themselves were subsequently downloadable directly from the
captured CDN URLs.

---

## 2. Downloading the MIN XH/XH2 ALBA18/ZABA22 package

For model key `e86c21`, the manifest contained:

```text
https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/e86c21/ALBA18xxxxZABA22FFFFxx/ALBA18xxxxZABA22FFFFxx-C.zip
```

Example download:

```bash
wget 'https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/e86c21/ALBA18xxxxZABA22FFFFxx/ALBA18xxxxZABA22FFFFxx-C.zip'
```

Observed package properties:

```text
size:   271372 bytes
SHA256: 0f2b17a2be514c2fe97628bb86b2d1f86b665660fcddab413f10354bd4f2d15f
```

The file size exactly matches the manifest's `zipSize` value for the package.

### Package contents

```text
      640  UpdateOldFw.txt
   349862  ALBA18.hex
      177  remarkLog.txt
       88  MD5Config.txt
       26  UpdateConfig.txt
   262164  ZABA22.bin
```

`remarkLog.txt` identifies the package as:

```text
MIN 2.5-6KTL-XH/XH2 Latest Firmware-ALBA18ZABA22
This Update
1.Fix of Known Bugs
```

`UpdateOldFw.txt` contains, among many compatible prior versions, `ZAba29` and
the `ALba10yyyy` family.

---

## 3. Two firmware versions, two processors

This is a central result of the analysis.

The firmware package is **not** one monolithic image. It contains two firmware
versions for two separate processors:

| ShineTools phase | File | Processor / role | Evidence |
|---|---|---|---|
| 1/2 | `ALBA18.hex` | TI C2000 / C28x, inverter/power-control side | C28x instruction decoding, word-addressed flash layout, PWM/ADC-heavy peripheral use |
| 2/2 | `ZABA22.bin` | ARM Cortex-M, communication side | Cortex-M vector table, STM32F1-like peripheral map, Growatt/ShineTools communication-version naming |

The update order is explicitly stored in `UpdateConfig.txt`:

```text
1=ALBA18.hex
2=ZABA22.bin
```

Therefore the two firmware numbers in the combined package name,
**ALBA18 + ZABA22**, are not two labels for the same binary. They are separate
processor firmware versions.

### ZABA22 as the communication firmware

Growatt/ShineTools version information observed during this work identifies the
**ZABA** component as the communication firmware/version. For that reason this
report uses the term **communication processor firmware** for `ZABA22`.

The static analysis agrees with that interpretation:

- `ZABA22` is an ARM Cortex-M image rather than C28x inverter-control code.
- It contains boot/programming/status strings.
- It references GPIO, SPI, USART, clock-control and flash-control-like
  peripherals.
- `ALBA18`, by contrast, has strong PWM, ADC, GPIO and C2000 peripheral
  activity consistent with inverter/power-control responsibilities.

The exact ARM MCU derivative is not yet proven.

---

## 4. Growatt's 20-byte firmware wrapper

Both firmware images use the same 20-byte Growatt wrapper before their payload.

The header is five big-endian 32-bit words:

```text
offset  size  meaning
0x00    4     0
0x04    4     payload length, big-endian
0x08    4     CRC32(payload), big-endian
0x0C    4     0
0x10    4     0
0x14    ...   payload
```

This was verified independently on both images.

### ALBA18 header

```text
0x00000000
0x00055692    payload length = 349842 bytes
0xDD6182F0    CRC32(payload)
0x00000000
0x00000000
```

The actual payload length is exactly 349842 bytes and its CRC32 is exactly
`0xDD6182F0`.

`MD5Config.txt` contains:

```text
ALBA18.hex=CCB4677C87FC3CA1D6EE21147DD7777D
```

That is exactly the MD5 of the ALBA file **after removing the 20-byte Growatt
wrapper**, not the MD5 of the complete wrapped file.

### ZABA22 header

```text
0x00000000
0x00040000    payload length = 262144 bytes
0x68E0AC7E    CRC32(payload)
0x00000000
0x00000000
```

Again, both payload length and CRC32 match exactly.

---

## 5. ZABA22 static analysis

Removing the 20-byte wrapper gives a 256 KiB raw image:

```bash
dd if=ZABA22.bin of=ZABA22-payload.bin bs=1 skip=20 status=none
```

The first two words are:

```text
f8 0c 00 20  -> 0x20000CF8  initial stack pointer
11 35 00 08  -> 0x08003511  reset vector, Thumb bit set
```

That conclusively identifies a little-endian ARM Cortex-M image loaded at
`0x08000000`; the reset code itself begins at `0x08003510`.

A reproducible Ghidra analysis with `ARM:LE:32:v7` recovered:

- 893 functions
- 2,007 printable strings
- a complete decoded instruction export
- Cortex-M system-vector handlers derived from the vector table

Repeated literal-pool addresses are strongly STM32F1-like, including:

```text
0x40021000  RCC-like
0x40022000  FLASH-like
0x40010800  GPIO-like
0x40010C00  GPIO-like
0x40011400  GPIO-like
0x40013000  SPI-like
0x40013800  USART-like
```

This is strong family-level evidence but does not yet prove the exact STM32
part.

Useful strings and XREF targets include:

```text
BOOTNOTB      @ 0x080020A4
BOOT          @ 0x08002FAC
Programming   @ 0x0800347E
BOOTAL        @ 0x08005800
```

Nearby strings include `Voltage`, `Event ID`, `Waiting`, `Testing`, `Pass`, and
`Fail`.

These are good leads for reconstructing boot/update behavior, but string
presence by itself does not prove a complete upgrade protocol.

---

## 6. ALBA18 static analysis

After removing the 20-byte wrapper, `ALBA18` is Intel-HEX-like data using
**16-bit C28x word addresses**, not normal byte-addressed Intel HEX. A standard
Intel HEX parser therefore sees apparent overlaps.

Reconstructing it as word-addressed data gives:

```text
TI word-address range: 0x003D8000 .. 0x003F7FFF
address span:          128K 16-bit words / 256 KiB
```

The source stores each C28x word high-byte first. A separate per-word
byte-swapped copy is used for the Ghidra C28x loader.

The boot words at `0x3F7FF6` are:

```text
0x007F 0x4132
```

With the generic C28x processor module they decode as:

```text
LB 0x3F4132
```

This is an important consistency check for byte order, addressing and processor
selection.

The flash/peripheral layout is compatible with the 128K-word F2806x-era group,
with F28069/F28068/F28067/F28066 remaining plausible candidates. The exact
derivative has not been proven.

The CSM password area in this image contains eight `0xFFFF` words.

### Ghidra results

The reproducible analysis recovered:

- 734 functions
- 45,523 decoded instructions
- 36 memory blocks
- startup/runtime structure including `_c_int00`, `_system_pre_init`,
  `_args_main`, `main`, `exit`, and `__TI_copy_table_init`

Static register/provenance analysis found 247 candidate peripheral accesses:

| Candidate range | Count |
|---|---:|
| SPIB / SCIB | 81 |
| ECANA mailbox | 18 |
| ePWM1–8 | 84 |
| ADC | 19 |
| GPIO | 33 |
| eCAP1–3 | 2 |
| system control | 7 |
| PIE control | 2 |
| other PF0 range | 1 |

The strongest communication-related ALBA candidate under the current heuristic
is:

```text
FUN_003e159c @ C28x address 0x003E159C
```

with 71 SPIB/SCIB candidate accesses. This is a high-value review target, not a
proven protocol handler.

The substantial ePWM and ADC use is consistent with ALBA being the
inverter/power-control-side firmware.

---

## 7. Modbus, battery-control and VPP status

No clean `Modbus`, `battery`, or `VPP` string was recovered from either image.

That is **not evidence that these features are absent**. Embedded protocol
implementations often contain no human-readable protocol name.

The most useful next analysis steps are data-flow-oriented:

- locate Modbus-like function-code dispatch for `0x03`, `0x04`, `0x06`, `0x10`
- search for Modbus CRC16 behavior (`0xA001` / `0x8005`)
- trace register/address validation and exception handling
- trace constants/tables associated with VPP registers such as 30000, 30100,
  30101, 30407, 30408, 30409, 30410 and 30474
- deeply analyze `FUN_003e159c` and its callers/callees
- trace XREFs to the ZABA boot/programming strings

Until stronger call/data-flow evidence exists, this work does not claim an
exact Modbus handler, VPP state machine, or battery-control algorithm.

---

## 8. Reproducible Ghidra environment

The static-analysis environment used:

```text
Ghidra: 12.1.2 build 20260605
ghidra-tms320c28x commit:
f3c1f8add35c2d6b46461237b418c221ca34653a
```

Loader selections:

```text
ZABA22: ARM:LE:32:v7, BinaryLoader base 0x08000000
ALBA18: TMS320C28x:LE:32:default, BinaryLoader base 0x3D8000
```

For ALBA, the raw source image is preserved unchanged; only a separate
byte-swapped analysis copy is generated for the current C28x Ghidra module.

Important interpretation limits:

- generated vector-handler names are derived labels, not original vendor symbols
- `LRETR`-terminated functions are ISR candidates, not automatically proven ISRs
- the F2806x map is a candidate map and does not prove the exact silicon variant
- an independent TI `dis2000` comparison remains useful future validation

---

## 9. Complete firmware/update URL catalogue

The following URLs were recovered from the captured
`getOssFileUploadListByServer` response. Field names are shown exactly as
returned by Growatt. No semantic meaning beyond the observed `-C`, `-U`,
`bsdiff`, and `bsdiffC` field names is assumed here.

### Manifest field `-C` — 51 URLs

| Model key | File | Manifest size (bytes) | Download URL |
|---|---|---:|---|
| `93b0eb` | `YCAA999997ZDBA99FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/3072/9d654/93b0eb/YCAA999997ZDBA99FFFFxx/YCAA999997ZDBA99FFFFxx-C.zip` |
| `d0eede` | `AMBA15xxxxZABA22FFFFxx-C.zip` | 246885 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/d0eede/AMBA15xxxxZABA22FFFFxx/AMBA15xxxxZABA22FFFFxx-C.zip` |
| `d0eede` | `AMAA18xxxxZABA22FFFFxx-C.zip` | 253338 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/d0eede/AMAA18xxxxZABA22FFFFxx/AMAA18xxxxZABA22FFFFxx-C.zip` |
| `2eed36` | `ZQCAxx08-C.zip` | 93117 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/cde3/5ccd1/2eed36/ZQCAxx08/ZQCAxx08-C.zip` |
| `c9788f` | `DMAA10xxxxZBAB24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/c9788f/DMAA10xxxxZBAB24FFFFxx/DMAA10xxxxZBAB24FFFFxx-C.zip` |
| `c9788f` | `DMCA02xxxxZBAC24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/c9788f/DMCA02xxxxZBAC24FFFFxx/DMCA02xxxxZBAC24FFFFxx-C.zip` |
| `c9788f` | `DMAA10xxxxZBAC24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/c9788f/DMAA10xxxxZBAC24FFFFxx/DMAA10xxxxZBAC24FFFFxx-C.zip` |
| `c9788f` | `DMAA10xxxxZBAA24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/c9788f/DMAA10xxxxZBAA24FFFFxx/DMAA10xxxxZBAA24FFFFxx-C.zip` |
| `c9788f` | `DMCA02xxxxZBAB24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/c9788f/DMCA02xxxxZBAB24FFFFxx/DMCA02xxxxZBAB24FFFFxx-C.zip` |
| `c9788f` | `DMCA02xxxxZBAA24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/c9788f/DMCA02xxxxZBAA24FFFFxx/DMCA02xxxxZBAA24FFFFxx-C.zip` |
| `15612d` | `TIAA292405ZBBA27FFFFxx-C.zip` | 326485 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/15612d/TIAA292405ZBBA27FFFFxx/TIAA292405ZBBA27FFFFxx-C.zip` |
| `40f818` | `DNAA12xxxxZBDC19FFFFxx-C.zip` | 447025 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/40f818/DNAA12xxxxZBDC19FFFFxx/DNAA12xxxxZBDC19FFFFxx-C.zip` |
| `40f818` | `DNAA12xxxxZBDB15FFFFxx-C.zip` | 339244 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/40f818/DNAA12xxxxZBDB15FFFFxx/DNAA12xxxxZBDB15FFFFxx-C.zip` |
| `9ae8f2` | `VCAA06FFFFxxQBAB03ZEBA06FFFFxxFFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/d65de/9ae8f2/VCAA06FFFFxxQBAB03ZEBA06FFFFxxFFFFxx/VCAA06FFFFxxQBAB03ZEBA06FFFFxxFFFFxx-C.zip` |
| `e86c21` | `ALBA18xxxxZABA22FFFFxx-C.zip` | 271372 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/e86c21/ALBA18xxxxZABA22FFFFxx/ALBA18xxxxZABA22FFFFxx-C.zip` |
| `e86c21` | `ALBA14xxxxZADA21FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/e86c21/ALBA14xxxxZADA21FFFFxx/ALBA14xxxxZADA21FFFFxx-C.zip` |
| `e86c21` | `ALCA13xxxxZABA22FFFFxx-C.zip` | 248244 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/e86c21/ALCA13xxxxZABA22FFFFxx/ALCA13xxxxZABA22FFFFxx-C.zip` |
| `e86c21` | `ALCA03xxxxZABA15FFFFxxxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/e86c21/ALCA03xxxxZABA15FFFFxxxx/ALCA03xxxxZABA15FFFFxxxx-C.zip` |
| `e86c21` | `ALDA04xxxxZABA22FFFFxx-C.zip` | 248380 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/bdd74/e86c21/ALDA04xxxxZABA22FFFFxx/ALDA04xxxxZABA22FFFFxx-C.zip` |
| `691d37` | `RBBA0604xxZCBC06FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/3072/ff76c/691d37/RBBA0604xxZCBC06FFFFxx/RBBA0604xxZCBC06FFFFxx-C.zip` |
| `691d37` | `RBAA0806xxZCBC08FFFFxx-C.zip` | 265711 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/3072/ff76c/691d37/RBAA0806xxZCBC08FFFFxx/RBAA0806xxZCBC08FFFFxx-C.zip` |
| `d4f559` | `QBdc01QBdc01QBdc01ZEhc01FFFFxxFFFFxx-C.zip` | 362759 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/e8c35/d4f559/QBdc01QBdc01QBdc01ZEhc01FFFFxxFFFFxx/QBdc01QBdc01QBdc01ZEhc01FFFFxxFFFFxx-C.zip` |
| `f59241` | `DOAA06xxxxZBDC19FFFFxx-C.zip` | 477021 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/f59241/DOAA06xxxxZBDC19FFFFxx/DOAA06xxxxZBDC19FFFFxx-C.zip` |
| `266cc1` | `QBAA10FFFFxxFFFFxxZEAA08FFFFxxFFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/e8c35/266cc1/QBAA10FFFFxxFFFFxxZEAA08FFFFxxFFFFxx/QBAA10FFFFxxFFFFxxZEAA08FFFFxxFFFFxx-C.zip` |
| `266cc1` | `QBda99FFFFxxFFFFxxZEha99FFFFxxFFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/e8c35/266cc1/QBda99FFFFxxFFFFxxZEha99FFFFxxFFFFxx/QBda99FFFFxxFFFFxxZEha99FFFFxxFFFFxx-C.zip` |
| `499131` | `ZQCAxx08-C.zip` | 93117 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/cde3/c8eb4/499131/ZQCAxx08/ZQCAxx08-C.zip` |
| `cdcff6` | `DLAA11xxxxZBAC24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/cdcff6/DLAA11xxxxZBAC24FFFFxx/DLAA11xxxxZBAC24FFFFxx-C.zip` |
| `cdcff6` | `DLAA11xxxxZBAB24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/cdcff6/DLAA11xxxxZBAB24FFFFxx/DLAA11xxxxZBAB24FFFFxx-C.zip` |
| `cdcff6` | `DLAA11xxxxZBAA24FFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/cdcff6/DLAA11xxxxZBAA24FFFFxx/DLAA11xxxxZBAA24FFFFxx-C.zip` |
| `81962d` | `YCAA030301ZDBA03FFFFxxxx-C.zip` | 578239 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/f424/12d4c/81962d/YCAA030301ZDBA03FFFFxxxx/YCAA030301ZDBA03FFFFxxxx-C.zip` |
| `f5d1ef` | `YBAA1110xxZDAB16FFFFxx-C.zip` | 304325 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/3072/9d654/f5d1ef/YBAA1110xxZDAB16FFFFxx/YBAA1110xxZDAB16FFFFxx-C.zip` |
| `f5d1ef` | `YBAA1110xxZDAA16FFFFxx-C.zip` | 296244 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/3072/9d654/f5d1ef/YBAA1110xxZDAA16FFFFxx/YBAA1110xxZDAA16FFFFxx-C.zip` |
| `67c3f4` | `DNBA08xxxxZBDB15FFFFxx-C.zip` | 355267 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/67c3f4/DNBA08xxxxZBDB15FFFFxx/DNBA08xxxxZBDB15FFFFxx-C.zip` |
| `67c3f4` | `DNBA08xxxxZBDC19FFFFxx-C.zip` | 463228 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/67c3f4/DNBA08xxxxZBDC19FFFFxx/DNBA08xxxxZBDC19FFFFxx-C.zip` |
| `19417c` | `YFAA020201ZDDA05FFFFxxxx-C.zip` | 567351 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/f424/12d4c/19417c/YFAA020201ZDDA05FFFFxxxx/YFAA020201ZDDA05FFFFxxxx-C.zip` |
| `a5468f` | `QBda99FFFFxxFFFFxxZEha99FFFFxxFFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/e8c35/a5468f/QBda99FFFFxxFFFFxxZEha99FFFFxxFFFFxx/QBda99FFFFxxFFFFxxZEha99FFFFxxFFFFxx-C.zip` |
| `da9dc4` | `TQAA050502ZBBA27FFFFxx-C.zip` | 353362 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/da9dc4/TQAA050502ZBBA27FFFFxx/TQAA050502ZBBA27FFFFxx-C.zip` |
| `da9dc4` | `TNAA211605ZBBA27FFFFxx-C.zip` | 350672 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/da9dc4/TNAA211605ZBBA27FFFFxx/TNAA211605ZBBA27FFFFxx-C.zip` |
| `2c53ce` | `TKAA21xxxxZBAB26FFFFxx-C.zip` | 287441 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/2c53ce/TKAA21xxxxZBAB26FFFFxx/TKAA21xxxxZBAB26FFFFxx-C.zip` |
| `2c53ce` | `TKAB10xxxxZBAB26FFFFxx-C.zip` | 287395 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/2c53ce/TKAB10xxxxZBAB26FFFFxx/TKAB10xxxxZBAB26FFFFxx-C.zip` |
| `2c53ce` | `TKAB11xxxxZBAA27FFFFxx-C.zip` | 275045 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/2c53ce/TKAB11xxxxZBAA27FFFFxx/TKAB11xxxxZBAA27FFFFxx-C.zip` |
| `2c53ce` | `TKAA21xxxxZBAA25FFFFxx-C.zip` | 274080 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/2c53ce/TKAA21xxxxZBAA25FFFFxx/TKAA21xxxxZBAA25FFFFxx-C.zip` |
| `be65f7` | `YGAA020201ZDDA05FFFFxxxx-C.zip` | 569429 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/f424/12d4c/be65f7/YGAA020201ZDDA05FFFFxxxx/YGAA020201ZDDA05FFFFxxxx-C.zip` |
| `f29281` | `VDAA11WAAA11QABA11ZECA11FFFFxxFFFFxx-C.zip` | 537722 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/d65de/f29281/VDAA11WAAA11QABA11ZECA11FFFFxxFFFFxx/VDAA11WAAA11QABA11ZECA11FFFFxxFFFFxx-C.zip` |
| `f69c26` | `RQAA0307xxZCLA03HDRB03-C.zip` | 258537 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/b7da/9bdef/f69c26/RQAA0307xxZCLA03HDRB03/RQAA0307xxZCLA03HDRB03-C.zip` |
| `39ae32` | `YBAA1110xxZDAB16FFFFxx-C.zip` | 304327 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/3072/9d654/39ae32/YBAA1110xxZDAB16FFFFxx/YBAA1110xxZDAB16FFFFxx-C.zip` |
| `39ae32` | `YBAA1110xxZDAA16FFFFxx-C.zip` | 296246 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/3072/9d654/39ae32/YBAA1110xxZDAA16FFFFxx/YBAA1110xxZDAA16FFFFxx-C.zip` |
| `1a90c4` | `DOAA06xxxxZBDC19FFFFxx-C.zip` | 477021 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/1a90c4/DOAA06xxxxZBDC19FFFFxx/DOAA06xxxxZBDC19FFFFxx-C.zip` |
| `80165d` | `TOAA0606xxZBEA06MBAA0505-C.zip` | 764160 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/f424/12d4c/80165d/TOAA0606xxZBEA06MBAA0505/TOAA0606xxZBEA06MBAA0505-C.zip` |
| `77c08f` | `YEAA050502ZDDA05FFFFxxxx-C.zip` | 567859 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/f424/12d4c/77c08f/YEAA050502ZDDA05FFFFxxxx/YEAA050502ZDDA05FFFFxxxx-C.zip` |
| `39c3b9` | `WBAA14QACA14QBBA14ZEDA14FFFFxxFFFFxx-C.zip` | 0 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/d65de/39c3b9/WBAA14QACA14QBBA14ZEDA14FFFFxxFFFFxx/WBAA14QACA14QBBA14ZEDA14FFFFxxFFFFxx-C.zip` |

### Manifest field `-U` — 23 URLs

Several entries in this field are version-number ZIPs rather than files whose
names end in `-U.zip`; the table preserves the manifest categorization.

| Model key | File | Manifest size (bytes) | Download URL |
|---|---|---:|---|
| `91c9f411` | `8.4.1.3.zip` | 26578 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/6cbcc/91c9f4/11/8.4.1.3/8.4.1.3.zip` |
| `6d56d0` | `3.2.0.7.zip` | 0 | `https://cdn.growatt.com/update/device/ZKtest/autoUpgrade/e6b2/f16b5/6d56d0/3.2.0.7/3.2.0.7.zip` |
| `2eed36` | `ZQCAxx08-U.zip` | 92881 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/cde3/5ccd1/2eed36/ZQCAxx08/ZQCAxx08-U.zip` |
| `15612d` | `TIAA292405ZBBA27FFFFxx-U.zip` | 325093 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/15612d/TIAA292405ZBBA27FFFFxx/TIAA292405ZBBA27FFFFxx-U.zip` |
| `40f818` | `DNAA1251xxZBDC19FFFFxx-U.zip` | 455854 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/40f818/DNAA1251xxZBDC19FFFFxx/DNAA1251xxZBDC19FFFFxx-U.zip` |
| `40f818` | `DNAA1251xxZBDB15FFFFxx-U.zip` | 348031 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/40f818/DNAA1251xxZBDB15FFFFxx/DNAA1251xxZBDB15FFFFxx-U.zip` |
| `d8d247` | `1.7.0.8.zip` | 0 | `https://cdn.growatt.com/update/device/ZKtest/autoUpgrade/e6b2/f16b5/d8d247/1.7.0.8/1.7.0.8.zip` |
| `5ad164` | `2.5.0.1.zip` | 1076721 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/247c4/5ad164/2.5.0.1/2.5.0.1.zip` |
| `cff874` | `7.5.1.8.zip` | 729338 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/ba142/cff874/7.5.1.8/7.5.1.8.zip` |
| `f59241` | `DOAA0601xxZBDC19FFFFxx-U.zip` | 491520 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/f59241/DOAA0601xxZBDC19FFFFxx/DOAA0601xxZBDC19FFFFxx-U.zip` |
| `91c9f4` | `8.0.8.1.zip` | 1099385 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/6cbcc/91c9f4/10/8.0.8.1/8.0.8.1.zip` |
| `499131` | `ZQCAxx08-U.zip` | 92881 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/cde3/c8eb4/499131/ZQCAxx08/ZQCAxx08-U.zip` |
| `7d8bfc` | `8.1.2.9.zip` | 1081431 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/ba142/7d8bfc/8.1.2.9/8.1.2.9.zip` |
| `1a2051` | `3.1.1.7.zip` | 652350 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/f16b5/1a2051/3.1.1.7/3.1.1.7.zip` |
| `67c3f4` | `DNBA0851xxZBDB15FFFFxx-U.zip` | 364067 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/67c3f4/DNBA0851xxZBDB15FFFFxx/DNBA0851xxZBDB15FFFFxx-U.zip` |
| `67c3f4` | `DNBA0851xxZBDC19FFFFxx-U.zip` | 472067 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/67c3f4/DNBA0851xxZBDC19FFFFxx/DNBA0851xxZBDC19FFFFxx-U.zip` |
| `30572b` | `3.0.0.2.zip` | 0 | `https://cdn.growatt.com/update/device/ZKtest/autoUpgrade/e6b2/f16b5/30572b/3.0.0.2/3.0.0.2.zip` |
| `da9dc4` | `TQAA050502ZBBA27FFFFxx-U.zip` | 353127 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/da9dc4/TQAA050502ZBBA27FFFFxx/TQAA050502ZBBA27FFFFxx-U.zip` |
| `da9dc4` | `TNAA211605ZBBA27FFFFxx-U.zip` | 345780 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/da9dc4/TNAA211605ZBBA27FFFFxx/TNAA211605ZBBA27FFFFxx-U.zip` |
| `f29281` | `VDAA11WAAA11QABA11ZECA11FFFFxxFFFFxx-U.zip` | 537216 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/545f/d65de/f29281/VDAA11WAAA11QABA11ZECA11FFFFxxFFFFxx/VDAA11WAAA11QABA11ZECA11FFFFxxFFFFxx-U.zip` |
| `c53bc2` | `7.6.2.5.zip` | 1081484 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/ba449/c53bc2/7.6.2.5/7.6.2.5.zip` |
| `1a90c4` | `DOAA0601xxZBDC19FFFFxx-U.zip` | 491520 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/db4d/c416c/1a90c4/DOAA0601xxZBDC19FFFFxx/DOAA0601xxZBDC19FFFFxx-U.zip` |
| `bc8317` | `8.1.8.6.zip` | 998198 | `https://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/ba449/bc8317/8.1.8.6/8.1.8.6.zip` |

### Manifest field `bsdiff` — 1 URL

| Model key | File | Manifest size (bytes) | Download URL |
|---|---|---:|---|
| `cff874` | `7517_7518.bin` | — | `http://cdn.growatt.com/update/device/GB/autoUpgrade/e6b2/ba142/cff874/bsdiff/7517_7518.bin` |

### Manifest field `bsdiffC` — 0 URLs

_None found in this capture._

---

## 10. Separate safety/grid-code file

ShineTools also called:

```text
POST https://oss.growatt.com/api/v3/userCenter/findSafetyFile
```

For model key `e86c21`, the response returned:

```text
https://cdn.growatt.com/update/device/GB/manualUpgrade/db4d/bdd74/e86c21/R-D/Safety/Safety_330.bin
```

This file is listed separately because it came from `findSafetyFile` and a
`manualUpgrade/.../Safety/` path rather than from the firmware catalogue.

---

## 11. `e86c21` / MIN-family catalogue entries

The `e86c21` model key contained these five `-C` packages:

```text
ALBA18xxxxZABA22FFFFxx-C
ALBA14xxxxZADA21FFFFxx-C
ALCA13xxxxZABA22FFFFxx-C
ALCA03xxxxZABA15FFFFxxxx-C
ALDA04xxxxZABA22FFFFxx-C
```

Only `ALBA18xxxxZABA22FFFFxx-C` is analyzed in depth in this document.

---

## 12. Reproducibility and caution

The most important reproducible chain is:

```text
ShineTools firmware screen
        ↓
ADB logcat / EasyHttp response logging
        ↓
getOssFileUploadListByServer JSON manifest
        ↓
direct cdn.growatt.com URL
        ↓
ALBA18xxxxZABA22FFFFxx-C.zip
        ↓
ALBA18.hex + ZABA22.bin
        ↓
20-byte wrapper validation
        ↓
C28x + ARM Cortex-M static analysis in Ghidra
```

The catalogue contains firmware for many different Growatt products and device
families. A URL being present in the manifest does **not** mean that package is
safe or appropriate to flash on a particular inverter. This document is about
acquisition and static analysis, not cross-flashing.
