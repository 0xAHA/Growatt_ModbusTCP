# VPP Protocol

> **Source documents:** Growatt VPP Communication Protocol of Inverter V2.01 / V2.03
> (`GI-BK-E060_GROWATT.VPP.COMMUNICATION.PROTOCOL.OF.INVERTER_V2.03.xlsx`,
> `growatt_vpp_protocol_v2.01_registers.csv`)
>
> VPP (Virtual Power Plant) is Growatt's advanced monitoring and control protocol.
> It uses registers in the 30000+ range and is only supported by newer inverter models.
> Multiple protocol versions (V2.01, V2.02, V2.03) are in active use  -  all share the
> same core register layout described here.
>
> **Applicable models:** SPH, SPA, MIN TL-XH, MOD TL3-XH, MID TL3-XH, WIT, WIS, and others

---

## Register Ranges

| Range | Purpose |
| --- | --- |
| 30000-30099 | Device identification, rated parameters, system settings |
| 30100-30499 | Control registers (AC power, battery, TOU schedule) |
| 31000-31499 | Real-time data (status, PV, grid, battery, load) |
| 32000+ | Extended / model-specific |

---

## DTC Codes (Table 3-1)

The DTC (Device Type Code) is stored at holding register 30000 and uniquely identifies
the inverter model. The integration reads this at startup for automatic model detection.

| DTC Code | Model |
| --- | --- |
| 3502 | SPH 3000-6000TL BL |
| 3601 | SPH 4000-10000TL3 BH-UP |
| 3725 | SPA 4000-10000TL3 BH-UP |
| 3735 | SPA 3000-6000TL BL |
| 5100 | MIN 2500-6000TL-XH/XH(P) |
| 5200 | MIC/MIN 2500-6000TL-X/X2 |
| 5201 | MIN 7000-10000TL-X/X2 |
| 5400 | MOD-XH\MID-XH |
| 5601 | WIT 100KTL3-H |
| 5800 | WIS 215KTL3 |

---

## Holding Registers (93 registers)

| Address | Parameter Name | R/W | Type | Unit | Count | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 30000 | Equipment type (DTC) | RO | UINT16 | - | 1 | See Table 3-1 |
| 30001 | SN | RO | UINT16 | - | 15 | - |
| 30016 | Rated power (Pn) | RO | UINT32 | 0.1W | 2 | - |
| 30018 | Maximum active power (Pmax) | RO | UINT32 | 0.1W | 2 | - |
| 30020 | Maximum reactive power (Qmax fed into the grid) | RO | UINT32 | 0.1VAR | 2 | - |
| 30022 | Maximum reactive power (Qmax absorption grid) | RO | UINT32 | 0.1VAR | 2 | - |
| 30024 | Maximum apparent power (Smax) | RO | UINT32 | 0.1VA | 2 | - |
| 30026 | Rated charging and discharging power of BDC | RO | UINT32 | 0.1W | 2 | - |
| 30028 | PV input maximum power | RO | UINT32 | 0.1W | 2 | - |
| 30030 | Battery type | RO | UINT8 | - | 1 | 0: lead acid battery, 1: lithium battery |
| 30031 | Reserve | RO | UINT16 | - | 29 | - |
| 30060 | Machine Model | RO | UINT16 | ASCII | 1 | Example: TL |
| 30061 | Machine Model | RO | UINT16 | ASCII | 1 | Example: AA |
| 30062 | Version Num 1 | RO | UINT16 | Digit | 1 | - |
| 30063 | Version Num 2 | RO | UINT16 | Digit | 1 | - |
| 30064 | Version Num 3 | RO | UINT16 | Digit | 1 | - |
| 30065 | M3 Version Name | RO | UINT16 | ASCII | 1 | Example: ZB |
| 30066 | M3 Version Name | RO | UINT16 | ASCII | 1 | Example: AA |
| 30067 | Version Num 1 | RO | UINT16 | Digit | 1 | - |
| 30068 | Machine Model | RO | UINT16 | ASCII | 1 | Example: VC |
| 30069 | Machine Model | RO | UINT16 | ASCII | 1 | Example: AA |
| 30070 | Version Num 1 | RO | UINT16 | Digit | 1 | - |
| 30071 | DSP2 Software Version Name | RO | UINT16 | ASCII | 1 | Example: VC |
| 30072 | DSP2 Software Version Name | RO | UINT16 | ASCII | 1 | Example: BA |
| 30073 | Version Num 1 | RO | UINT16 | Digit | 1 | - |
| 30074 | BCU Software Version Name | RO | UINT16 | ASCII | 1 | Example: QB |
| 30075 | BCU Software Version Name | RO | UINT16 | ASCII | 1 | Example: AA |
| 30076 | Version Num 1 | RO | UINT16 | Digit | 1 | - |
| 30077 | M3 Software Version Name | RO | UINT16 | ASCII | 1 | Example: ZE |
| 30078 | M3 Software Version Name | RO | UINT16 | ASCII | 1 | Example: BA |
| 30079 | Version Num 1 | RO | UINT16 | Digit | 1 | - |
| 30080 | Machine Model | RO | UINT16 | ASCII | 1 | Example: ZO |
| 30081 | Machine Model | RO | UINT16 | ASCII | 1 | Example: AA |
| 30082 | Version Num 1 | RO | UINT16 | 1 | 1 | - |
| 30083 | Reserved | RO | UINT16 | - | 1 | Reserved |
| 30084 | Reserved | RO | UINT16 | - | 1 | Reserved |
| 30099 | VPP Protocol Version | RO | UINT16 | - | 15 | 200 represents V2.00, 201 represents V2.01 |
| 30100 | Control authority | RW | UINT16 | - | 1 | 0: not enabled, 1: Enable, Default: 0 |
| 30101 | On off command | RW | UINT16 | - | 1 | 0: power off, 1: power on, Default: 1, Not storage |
| 30102 | Country / region number | RO | UINT16 | - | 1 | See Table 3-5 |
| 30103 | Reserve | RW | UINT16 | - | 1 | - |
| 30104 | System time | RW | UINT16 | - | 6 | See table 3-6 |
| 30110 | Reserve | RW | UINT32 | - | 2 | - |
| 30112 | Mailing address | RO | UINT16 | - | 1 | [1, 255], Default: 1 |
| 30113 | Communication baud rate | RO | UINT16 | - | 1 | 0:9600 bps, 1:38400 bps, Default: 0 |
| 30114 | Reserved | RW | UINT16 | - | 1 | - |
| 30115 | SYN enable | RW | UINT16 | - | 1 | Offline box enable, 0: not enabled, 1: enable, Default: 0 |
| 30116 | Reserve | RW | UINT16 | - | 34 | - |
| 30150 | Reserve | RW | UINT16 | - | 1 | - |
| 30151 | Active power percentage derating | RW | UINT16 | % | 1 | Power limit percentage: [0,100], Default: 100 |
| 30152 | Reserve | RW | UINT16 | - | 2 | - |
| 30154 | Static active power limitation | RW | UINT16 | % | 1 | Power limit percent: [0,100], Default: 100, Actual active power is the less one, Not storage |
| 30155 | EPS offline enable | RW | UINT16 | - | 1 | 0: not enabled, 1: enable, Default: 0 |
| 30156 | EPS offline frequency | RW | UINT16 | 0.01Hz | 1 | 0:50Hz, 1:60Hz, Default: 0 |
| 30157 | EPS offline voltage | RW | UINT16 | - | 1 | Default: 0 |
| 30158 | Reserve | RW | UINT16 | - | 2 | - |
| 30160 | Fix Q | RW | UINT16 | % | 1 | Power limit percentage: [0,60], Default: 60 |
| 30161 | Reactive power mode | RW | UINT16 | - | 1 | 0: PF=1, 1: Pf value setting, 4: Lagging reactive power (+), 5: Leading reactive power (-), Default: 0 |
| 30162 | Power factor | RW | UINT16 | - | 1 | [0,2000] ∪ [18000,20000], Default: 20000, Actual PF = (set value - 10000) * 0.0001 |
| 30163 | Reserve | RW | INT16 | % | 1 | - |
| 30164 | Reserve (reactive power curve) | RW | UINT16 | - | 36 | - |
| 30200 | Export Limitation Enable | RW | UINT16 | - | 1 | 0: not enabled, 1: single machine enable, Default: 0 |
| 30201 | Export Limitation power Rate | RW | INT16 | % | 1 | [-100,100], Default: 0, Positive=backflow, negative=fair current |
| 30202 | Export Limitation Failure power Rate | RW | UINT16 | % | 1 | [0,100], Default: 0 |
| 30203 | EMS Communicating Failure Time | RW | UINT16 | S | 1 | [1,300], Default: 30 |
| 30204 | EMS Communication Failure Enable | RW | UINT16 | - | 1 | 0: not enabled, 1: enable, Default: 0 |
| 30205 | Super Export Limitation enable | RW | UINT16 | - | 1 | 0: not enabled, 1: enable, Default: 0 |
| 30206 | Export Limitation change slope | RW | UINT16 | *0.01%Pn/s | 1 | [1,20000], Default: 27 |
| 30207 | Export Limitation single phase control enable | RW | UINT16 | - | 1 | 0: not enabled, 1: enable, Default: 0 |
| 30208 | Export Limitation protection mode | RW | UINT16 | - | 1 | 0: Default mode, 1: Combine control, 2: software control, 3: hardware control, Default: 0 |
| 30209 | Reserve | RW | UINT16 | - | 91 | - |
| 30300 | Battery cluster index | RW | UINT16 | - | 1 | [0,3], Default: 0 |
| 30301 | Reserve | RW | UINT16 | - | 99 | - |
| 30400 | Reserve (Battery max charging power) | RW | UINT32 | 0.1W | 2 | Not used |
| 30402 | Reserve (Battery max discharging power) | RW | UINT32 | 0.1W | 2 | Not used |
| 30404 | Charging cut off SOC | RW | UINT8 | % | 1 | [70,100], Default: 100 |
| 30405 | Online discharge cut off SOC | RW | UINT8 | % | 1 | [10,30], Default: 10 |
| 30406 | Load priority discharge cut off SOC | RW | UINT8 | % | 1 | [10,20], Default: 10 |
| 30407 | Remote power control enable | RW | UINT8 | - | 1 | 0: not enabled, 1: Enable, Default: 0, Not storage |
| 30408 | Remote power control charging time | RW | UINT16 | min | 1 | 0: unlimited, 1~1440min, Default: 0, Not storage |
| 30409 | Remote charge and discharge power | RW | INT16 | - | 1 | [-100,100], Positive=charging, Negative=discharge, Default: 0, Not storage |
| 30410 | AC charging enable | RW | UINT8 | - | 1 | 0: not enabled, 1: Enable, Default: 0 |
| 30411 | Charging and discharging in different periods (20 sections) | RW | UINT16 | - | 61 | See Table 3-2, 30412~30471 default: 0 |
| 30472 | Reserve | RO | UINT16 | - | 2 | - |
| 30474 | Actual control value of charging and discharging power | RO | UINT16 | - | 1 | [-100,100], Positive=charging, Negative=discharge |
| 30475 | Offline discharge cut off SOC | RW | UINT16 | % | 1 | [10,30], Default: 10 |
| 30476 | Reserve | RW | UINT16 | - | 20 | - |
| 30496 | Battery charge stop voltage | RW | UINT16 | 0.1V | 1 | Lead-acid only, [0,15000] |
| 30497 | Battery discharge stop voltage | RW | UINT16 | 0.1V | 1 | Lead-acid only, [0,15000] |
| 30498 | Battery max charge current | RW | UINT16 | 0.1A | 1 | Lead-acid only, [0,2000], Default: 1500 |
| 30499 | Battery max discharge current | RW | UINT16 | 0.1A | 1 | Lead-acid only, [0,2000], Default: 1500 |
| 30500 | Safety Information | RW | UINT16 | - | 500 | See GROWATT INVERTER VPP COMMUNICATION PROTOCOL & SAFETY PARAMETERS |
| 32000 | Reserve | RW | UINT16 | - | 100 | - |

---

## Input Registers (87 registers)

| Address | Parameter Name | R/W | Type | Unit | Count | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 31000 | Working state of energy storage machine | RO | UINT16 | 1 | 1 | 0:standby,1:self-test,2:reserved,3:fault,4:upgrade,5:PV online&battery offline,6:battery online&PV online(or offline),7:PV&cell online off-grid,8:Battery online PV offline,9:bypass |
| 31001 | Battery working status | RO | UINT16 | 1 | 1 | 0:standby,1:disconnected,2:charging,3:discharge,4:fault,5:upgrade |
| 31002 | Priority of work | RO | UINT16 | 1 | 1 | 0:load first,1:Battery first,2:grid first |
| 31003 | Reserve | RO | UINT16 | - | 2 | - |
| 31005 | Fault code | RO | UINT16 | - | 1 | See Table 3-3 |
| 31006 | Fault sub code | RO | UINT16 | - | 1 | See Table 3-3 |
| 31007 | Alarm code | RO | UINT16 | - | 1 | See Table 3-4 |
| 31008 | Alarm sub code | RO | UINT16 | - | 1 | See Table 3-4 |
| 31009 | Reserve | RO | UINT16 | - | 1 | - |
| 31010 | PV1 voltage | RO | INT16 | 0.1V | 1 | - |
| 31011 | PV1 current | RO | INT16 | 0.1A | 1 | - |
| 31012 | PV2 voltage | RO | INT16 | 0.1V | 1 | - |
| 31013 | PV2 current | RO | INT16 | 0.1A | 1 | - |
| 31014 | PV3 voltage | RO | INT32 | 0.1W | 1 | - |
| 31015 | PV3 current | RO | INT16 | 0.1A | 1 | - |
| 31016 | PV4 voltage | RO | INT16 | 0.1V | 1 | - |
| 31017 | PV4 current | RO | INT16 | 0.1A | 1 | - |
| 31018 | PV5 voltage | RO | INT16 | 0.1V | 1 | - |
| 31019 | PV5 current | RO | INT16 | 0.1A | 1 | - |
| 31020 | PV6 voltage | RO | INT16 | 0.1V | 1 | - |
| 31021 | PV6 current | RO | INT16 | 0.1A | 1 | - |
| 31022 | PV7 voltage | RO | INT16 | 0.1V | 1 | - |
| 31023 | PV7 current | RO | INT16 | 0.1A | 1 | - |
| 31024 | PV8 voltage | RO | INT16 | 0.1V | 1 | - |
| 31025 | PV8 current | RO | INT16 | 0.1A | 1 | - |
| 31026 | PV9 voltage | RO | INT16 | 0.1V | 1 | - |
| 31027 | PV9 current | RO | INT16 | 0.1A | 1 | - |
| 31028 | PV10 voltage | RO | INT16 | 0.1V | 1 | - |
| 31029 | PV10 current | RO | INT16 | 0.1A | 1 | - |
| 31030 | PV11 voltage | RO | INT16 | 0.1V | 1 | - |
| 31031 | PV11 current | RO | INT16 | 0.1A | 1 | - |
| 31032 | PV12 voltage | RO | INT16 | 0.1V | 1 | - |
| 31033 | PV12 current | RO | INT16 | 0.1A | 1 | - |
| 31034 | PV13 voltage | RO | INT16 | 0.1V | 1 | - |
| 31035 | PV13 current | RO | INT16 | 0.1A | 1 | - |
| 31036 | PV14 voltage | RO | INT16 | 0.1V | 1 | - |
| 31037 | PV14 current | RO | INT16 | 0.1A | 1 | - |
| 31038 | PV15 voltage | RO | INT16 | 0.1V | 1 | - |
| 31039 | PV15 current | RO | INT16 | 0.1A | 1 | - |
| 31040 | PV16 voltage | RO | INT16 | 0.1V | 1 | - |
| 31041 | PV16 current | RO | INT16 | 0.1A | 1 | - |
| 31042 | Reserve | RO | INT16 | - | 16 | - |
| 31058 | PV input power | RO | INT32 | 0.1W | 2 | - |
| 31060 | Reserve | RO | UINT32 | - | 40 | - |
| 31100 | Active power | RO | INT32 | 0.1W | 2 | Positive:export to grid, Negative:import from grid |
| 31102 | Reactive power | RO | INT32 | 0.1VA | 2 | - |
| 31104 | Reserve | RO | INT16 | - | 1 | - |
| 31105 | Grid frequency | RO | UINT16 | 0.01Hz | 1 | - |
| 31106 | Grid voltage / line AB voltage | RO | UINT16 | 0.1V | 1 | When output mode is L/N |
| 31107 | BC line voltage of power grid | RO | UINT16 | 0.1V | 1 | - |
| 31108 | CA line voltage of power grid | RO | UINT16 | 0.1V | 1 | - |
| 31109 | Grid current / A phase current of grid | RO | INT16 | 0.1A | 1 | - |
| 31110 | Phase B current of grid | RO | INT16 | 0.1A | 1 | - |
| 31111 | Phase C current of grid | RO | INT16 | 0.1A | 1 | - |
| 31112 | Meter power | RO | INT32 | 0.1W | 2 | Positive:import from grid, Negative:export to grid |
| 31114 | Inverter temperature | RO | INT16 | 0.1℃ | 1 | [-400,1250] |
| 31115 | Reserve | RO | INT16 | - | 1 | - |
| 31116 | Reserve | RO | INT16 | - | 1 | - |
| 31117 | Reserve | RO | INT16 | - | 1 | - |
| 31118 | Power to user daily | RO | UINT32 | 0.1KWH | 2 | - |
| 31120 | Total power to user | RO | UINT32 | 0.1KWH | 2 | - |
| 31122 | Power to grid daily | RO | UINT32 | 0.1KWH | 2 | - |
| 31124 | Total power to grid | RO | UINT32 | 0.1KWH | 2 | - |
| 31126 | Reserved | RO | INT16 | - | 74 | - |
| 31200 | Charge/discharge power | RO | INT32 | 0.1W | 2 | Positive:charging, Negative:discharge |
| 31202 | Daily charge of battery | RO | UINT32 | 0.1KWH | 2 | - |
| 31204 | Cumulative charge of battery | RO | UINT32 | 0.1KWH | 2 | - |
| 31206 | Daily discharge capacity of battery | RO | UINT32 | 0.1KWH | 2 | - |
| 31208 | Cumulative discharge of battery | RO | UINT32 | 0.1KWH | 2 | - |
| 31210 | Maximum allowable charging power of battery | RO | UINT32 | 0.1W | 2 | - |
| 31212 | Maximum allowable discharge power of battery | RO | UINT32 | 0.1W | 2 | - |
| 31214 | Battery voltage | RO | INT16 | 0.1V | 1 | - |
| 31215 | Battery current | RO | INT32 | 0.1A | 2 | Positive:charging, Negative:discharge |
| 31217 | SOC | RO | UINT8 | - | 1 | [0,100] |
| 31218 | SOH | RO | UINT8 | - | 1 | [0,100] |
| 31219 | Battery capacity rating (FCC) | RO | UINT32 | AH | 2 | - |
| 31221 | Reserved | RO | UINT32 | AH | 2 | Reserved for Battery remaining capacity (RM) |
| 31223 | Battery environmental temperature | RO | INT16 | 0.1℃ | 1 | [-400,1250] |
| 31224 | Reserved | RO | INT16 | 0.1℃ | 1 | Reserved for Maximum battery temperature |
| 31225 | Cluster Sum | RO | UINT16 | 1 | 1 | - |
| 31226 | Single Cluster Module Number | RO | UINT16 | 1 | 1 | - |
| 31227 | Module Rated Voltage | RO | UINT16 | 0.1V | 1 | - |
| 31228 | Module Rated Cap | RO | UINT16 | 0.1AH | 1 | - |
| 31229 | Reserve | RO | UINT16 | - | 71 | - |
| 31300 | Battery Information 2 | RO | - | - | 100 | Refer to 31200~31299 |
| 31400 | Battery Information 3 | RO | - | - | 100 | Refer to 31200~31299 |
| 31500 | Battery Information 4 | RO | - | - | 100 | Refer to 31200~31299 |
