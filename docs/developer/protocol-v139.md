# Modbus RTU Protocol II V1.39

> **Source document:** Growatt WIT Modbus RTU Protocol II V1.39
> (`Growatt_WIT-Modbus-RTU-Protocol-II-V1.39.xlsx`)
>
> This is the definitive Protocol II document. V1.39 is a verified superset of
> V1.13, V1.20, and V1.24.
>
> **Applicable models:** WIT, WIS, SPH, SPA, MIN, MOD, MID, MAX, MAC

---

## Register Ranges by Model Family

| Family | Register Ranges |
| --- | --- |
| TL-X / TL-XH (MIN type) | 0–124, 3000–3124, 3125–3249, 3250–3374 |
| TL3-X (MAX / MID / MAC) | 0–124, 3000–3124, 3125–3249 |
| SPA / SPH (hybrid) | 0–124, 1000–1124, 2000–2124, 3000–3124, 3125–3249 |
| WIT TL3 | 0–124, 875–999, 3000–3124, 3125–3249, 8000–8139 |

---

## Holding Registers (682 registers)

| Address | Name | Description | Access |
| --- | --- | --- | --- |
| 0 | OnOff | Remote On/Off . On（1）;Off（0） Inverter On（3）;Off（2） BDC | W |
| 1 | Safty | Bit0: SPI enable Bit1: AutoTestStart Bit2: LVFRT enable Bit3:FreqDerating Enable Bit4: Softstart enable Bit5: DRMS enable Bit6:PowerVoltFun c Enable Bit7: HVFRT enable Bit8:ROCOF enable Bit9: Recover FreqDeratingMode Enable Bit10:Split phase Bit11: AC Couple enable Bit12~15:Reserve | W |
| 2 | PF CMD | Set holding register 3,4,5,99 CMD will be set or not(1/0), if not, these settings are the initial value. | W |
| 3 | Active Power Rate | Inverter Max output active power percent | W |
| 4 | Reactive Power Rate | Inverter max output reactive power percent | W |
| 5 | Power factor | Inverter output power factor’s 10000 times | W |
| 6 | Pmax H | Normal (high) |  |
| 7 | Pmax L | Normal (low) |  |
| 8 | Vnormal | Normal work PV voltage |  |
| 9 | Fw version H | Firmware version (high) |  |
| 10 | Fw version M | Firmware version (middle) |  |
| 11 | Fw version L | Firmware version (low) |  |
| 12 | Fw version2 H | Control Firmware version (high) |  |
| 13 | Fw version2 M | Control Firmware version (middle) |  |
| 14 | Fw version2 L | Control Firmware version (low) |  |
| 15 | LCD language | LCD language | W |
| 16 | Country Selected | Country Selected or not | W |
| 17 | Vpv start | Input start voltage | W |
| 18 | Time start | Start time | W |
| 19 | RestartDel ayTime | Restart Delay Time after fault back; | W |
| 20 | Power Start Slope | Power start slope | W |
| 21 | Power Restart Slope | Power restart slope | W |
| 22 | Select Baud rate | Select communication baud rate | W |
| 23 | Serial NO | Serial number 1-2 |  |
| 24 | Serial NO | Serial number 3-4 |  |
| 25 | Serial NO | Serial number 5-6 |  |
| 26 | Serial NO | Serial number 7-8 |  |
| 27 | Serial NO | Serial number 9-10 |  |
| 28 | Module H | Inverter Module (high) |  |
| 29 | Module L | Inverter Module (low) |  |
| 30 | Com Address | Communicate ad dress | W |
| 31 | FlashStart | Update firmware | W |
| 32 | Reset User Info | Reset User Information | W |
| 33 | Reset to factory | Reset to factory | W |
| 34 | Manufactu rer Info 8 | Manufacturer information (high) |  |
| 35 | Manufactu rer Info 7 | Manufacturer information (middle) |  |
| 36 | Manufactu rer Info 6 | Manufacturer information (low) |  |
| 37 | Manufac.t urer Info 5 | Manufacturer information (high) |  |
| 38 | Manufactu rer Info 4 | Manufacturer information (middle) |  |
| 39 | Manufactu rer Info3 | Manufacturer information (low) |  |
| 40 | Manufactu rer Info 2 | Manufacturer information (low) |  |
| 41 | Manufactu rer Info 1 | Manufacturer information (high) |  |
| 42 | bfailsafeEn ; | G100 fail safe | W |
| 43 | DTC | Device Type Code |  |
| 44 | TP | Input tracker num and output phase num |  |
| 45 | Sys Year | System time-year | W |
| 46 | Sys Month | System time- Month | W |
| 47 | Sys Day | System time- Day | W |
| 48 | Sys Hour | System time- Hour | W |
| 49 | Sys Min | System time- Min | W |
| 50 | Sys Sec | System time- Second | W |
| 51 | Sys Weekly | System Weekly | W |
| 52 | Vac low | Grid voltage low limit protect | W |
| 53 | Vac high | Grid voltage high limit protect | W |
| 54 | Fac low | Grid frequency low limit protect | W |
| 55 | Fac high | Grid high frequencylimit protect | W |
| 56 | Vac low 2 | Grid voltage low limit protect 2 | W |
| 57 | Vac high 2 | Grid voltage high limit protect 2 | W |
| 58 | Fac low 2 | Grid frequency low limit protect 2 | W |
| 59 | Fac high 2 | Grid high frequency limit protect 2 | W |
| 60 | Vac low 3 | Grid voltage low limit protect 3 | W |
| 61 | Vac high 3 | Grid voltage high limit protect 3 | W |
| 62 | Fac low 3 | Grid frequency low limit protect 3 | W |
| 63 | Fac high 3 | Grid frequency high limit protect 3 | W |
| 64 | Vac low C | Grid low voltage limit connect to Grid | W |
| 65 | Vac high C | Grid high voltage limit connect to Grid | W |
| 66 | Fac low C | Grid low frequency limit connect to Grid | W |
| 67 | Fac high C | Grid high frequency limit connect to Grid | W |
| 68 | Vac low1 time | Grid voltage low limit protect time 1 | W |
| 69 | Vac high1 time | Grid voltage high limit protect time 1 | W |
| 70 | Vac low2 time | Grid voltage low limit protect time 2 | W |
| 71 | Vac high2 time | Grid voltage high limit protect time 2 | W |
| 72 | Fac low1 time | Grid frequency low limit protect time 1 | W |
| 73 | Fac high1 time | Grid frequency high limit protect time 1 | W |
| 74 | Fac low2 .time | Grid frequency low limit protect time 2 | W |
| 75 | Fac high2 time | Grid frequency high limit protect time 2 | W |
| 76 | Vac low3 time | Grid voltage low limit protect time 3 | W |
| 77 | Vac high3 time | Grid voltage high limit protect time 3 | W |
| 78 | Fac low3 time | Grid frequency low limit protect time 3 | W |
| 79 | Fac high3 time | Grid frequency high limit protect time 3 | W |
| 80 | U10min | Volt protection for 10 min | W |
| 81 | PV Voltage High Fault | PV Voltage High Fault | W |
| 82 | FW Build No. 5 | Model letter version number (TJ) |  |
| 83 | FW Build No. 4 | Model letter version number (AA) |  |
| 84 | FW Build No. 3 | DSP1 FW Build No. |  |
| 85 | FW Build No. 2 | DSP2/M0 FW Build No. |  |
| 86 | FW Build No. 1 | CPLD/AFCI FW Build No. |  |
| 87 | FW Build No. 0 | M3 FW Build No. |  |
| 88 | Modbus Version | Modbus Version |  |
| 89 | PFModel | Set PF function Model | W |
| 90 | GPRS IP Flag | Bit0-3:read: 1:Set GPRS IP Successed Write:2:Read GPRS IP Successed Bit4-7:GPRS status | W |
| 91 | FreqDerat eStart | Frequency derating start point | W |
| 92 | FLrate | Frequency – load limit rate | W |
| 93 | V1S | CEI021 V1S Q(v) | W |
| 94 | V2S | CEI021 V2S Q(v) | W |
| 95 | V1L | CEI021 V1L Q(v) | W |
| 96 | V2L | CEI021 V2L Q(v) | W |
| 97 | Qlockinpo wer | Q(v) lock in active power of CEI021 | W |
| 98 | QlockOutp ower | Q(v) lock Out active power of CEI021 | W |
| 99 | LIGridV | Lock in gird volt of CEI021 PF line | W |
| 100 | LOGridV | Lock out gird volt of CEI021 PF line | W |
| 101 | PFAdj1 | PF adjust value 1 |  |
| 102 | PFAdj2 | PF adjust value 2 |  |
| 103 | PFAdj3 | PF adjust value 3 |  |
| 104 | PFAdj4 | PF adjust value 4 |  |
| 105 | PFAdj5 | PF adjust value 5 |  |
| 106 | PFAdj6 | PF adjust value 6 |  |
| 107 | QVRPDela yTimeEE | QV Reactive Power delaytime | W |
| 108 | OverFDera tDelayTim eEE | Overfrequency de ratingdelaytime | W |
| 109 | Qpercent Max | Qmax for Q(V) curve | W |
| 110 | PFLineP1_ LP | PF limit line point 1 load percent | W |
| 111 | PFLineP1_ PF | PF limit line point 1 power factor | W |
| 112 | PFLineP2_ LP | PF limit line point 2 load percent | W |
| 113 | PFLineP2_ PF | PF limit line point 2power factor | W |
| 114 | PFLineP3_ LP | PF limit line point 3 load percent | W |
| 115 | PFLineP3_ PF | PF limit line point 3 power factor | W |
| 116 | PFLineP4_ LP | PF limit line point 4 load percent | W |
| 117 | PFLineP4_ PF | PF limit line point 4 power factor | W |
| 118 | Module 4 | Inverter Module (4) |  |
| 119 | Module 3 | Inverter Module (3) |  |
| 120 | Module 2 | Inverter Module (2) |  |
| 121 | Module 1 | Inverter Module (1) |  |
| 122 | ExportLimi t_En/dis | ExportLimit_En/dis | R/W |
| 123 | ExportLimi tPowerRat e | ExportLimitPowerR ate | R/W |
| 124 | TrakerMod el | Traker Model | W |
| *Second group* |  |  |  |
| 125 | INV Type-1 | Inverter type-1 | R |
| 126 | INV Type-2 | Inverter type-2 | R |
| 127 | INV Type-3 | Inverter type-3 | R |
| 128 | INV Type-4 | Inverter type-4 | R |
| 129 | INV Type-5 | Inverter type-5 | R |
| 130 | INV Type-6 | Inverter type-6 | R |
| 131 | INV Type-7 | Inverter type-7 | R |
| 132 | INV Type-8 | Inverter type-8 | R |
| 133 | BLVersion1 | Boot loader version1 | R |
| 134 | BLVersion2 | Boot loader version2 | R |
| 135 | BLVersion3 | Boot loader version3 | R |
| 136 | BLVersion4 | Boot loader version4 | R |
| 137 | Reactive P ValueH | Reactive PowerH | R/W |
| 138 | Reactive P ValueL | Reactive PowerL | R/W |
| 139 | ReactiveO utputPriori tyEnable | Reactive Output Priority Enable | R/W |
| 140 | Reactive P Value(Rati o) | Reactive Power Ratio | R/W |
| 141 | SvgFunctio nEnable | Svg enable on night | R/W |
| 142 | uwUnderF UploadPoi nt | UnderF Upload Point | R/W |
| 143 | uwOFDera teRecover Point | OFDerate RecoverPoint | R/W |
| 144 | uwOFDera teRecover DelayTime | OFDerate RecoverDelayTime | R/W |
| 145 | ZeroCurre ntEnable | ZeroCurrent Enable | R/W |
| 146 | uwZeroCur rentStaticl owVolt | ZeroCurrent StaticlowVolt | R/W |
| 147 | uwZeroCur rentStatic HighVolt | ZeroCurrent StaticHighVolt | R/W |
| 148 | uwHVoltD erateHighP oint | HVoltDerate HighPoint | R/W |
| 149 | uwHVoltD erateLowP oint | HVoltDerate LowPoint | R/W |
| 150 | uwQVPow erStableTi me | QVPower Stable Time | R/W |
| 151 | uwUnderF UploadSto pPoint | UnderF Upload StopPoint | R/W |
| 152 | fUnderFre qPoint | Underfrequency load start point | R/W |
| 153 | fUnderFre qEndPoint | Underfrequency down load end point | R/W |
| 154 | fOverFreq Point | Over frequency loading start point | R/W |
| 155 | fOverFreq EndPoint | Over frequency loading end point | R/W |
| 156 | fUnderVolt Point | Undervoltage load shedding start point | R/W |
| 157 | fUnderVolt EndPoint | Undervoltage derating end point | R/W |
| 158 | fOverVoltP oint | Overvoltage loading start point | R/W |
| 159 | fOverVoltE ndPoint | Overvoltage loading end point | R/W |
| 160 | uwNomina lGridVolt | NominalGridVolt Select | R/W |
| 161 | uwGridWa ttDelay | GridWatt DelayTime | R/W |
| 162 | uwReconn ectStartSlo pe | Reconnect StartSlope | R/W |
| 163 | uwLFRTEE | LFRT1 Freq | R/W |
| 164 | uwLFRTTi meEE | LFRT1 Time | R/W |
| 165 | uwLFRT2E E | LFRT2 Freq | R/W |
| 166 | uwLFRTTi me2EE | LFRT2 Time | R/W |
| 167 | uwHFRTEE | HFRT1 Freq | R/W |
| 168 | uwHFRTTi meEE | HFRT1 Time | R/W |
| 169 | uwHFRT2E E | HFRT2 Freq | R/W |
| 170 | uwHFRTTi me2EE | HFRT2 Time | R/W |
| 171 | uwHVRTEE | HVRT1 Volt | R/W |
| 172 | uwHVRTTi meEE | HVRT1 Time | R/W |
| 173 | uwHVRT2E E | HVRT2 Volt | R/W |
| 174 | uwHVRTTi me2EE | HVRT2 Time | R/W |
| 175 | uwUnderF UploadDel ayTime | UnderF UploadDelayTime | R/W |
| 176 | uwUnderF UploadRat eEE | UnderF UploadRate | R/W |
| 177 | uwGridRes tart_H_Fre q | GridRestart HighFreq | R/W |
| 178 | OverFDera tResponse Time | OverFDerat ResponseTime | W/R |
| 179 | UnderFUpl oadRespo nseTime | UnderFUpload ResponseTime | W/R |
| 180 | MeterLink | Whether to elect the meter | R/W |
| 181 | OPT Number | Number of connection optimizers | R/W |
| 182 | OPT ConfigOK Flag | Optimizer configuration completion flag | R/W |
| 183 | PvStrScan | String Num | R/W |
| 184 | BDCLinkN um | BDC parallel Num | R/W |
| 185 | PackNum | Number of battery modules | R |
| 186 | Reserved |  |  |
| 187 | VPPFuncti onEnableS tatus | VPP function enable status | R |
| 188 | DataLog Connect ServerStat us | dataLog Connect Server status |  |
| 192 | INVAndCol lectorInter action Function | INV and collectorInteractio n function | R |
| 200 | Reserved |  |  |
| 201 | PID Working Model | PID Operating mode | W |
| 202 | PID On/Off Ctrl | PID Break control | W |
| 203 | PID Volt Option | PID Output voltage option | W |
| 209 | New Serial NO | Serial number 1-2 |  |
| 210 | New Serial NO | Serial number 3-4 |  |
| 211 | New Serial NO | Serial number 5-6 |  |
| 212 | New Serial NO | Serial number 7-8 |  |
| 213 | New Serial NO | Serial number 9-10 |  |
| 214 | New Serial NO | Serial number 11-12 |  |
| 215 | New Serial NO | Serial 13-14 |  |
| 216 | New Serial NO | Serial 15-16 |  |
| 217 | New Serial NO | Serial 17-18 |  |
| 218 | New Serial NO | Serial 19-20 |  |
| 219 | New Serial NO | Serial 21-22 |  |
| 220 | New Serial NO | Serial 23-24 |  |
| 221 | New Serial NO | Serial 25-26 |  |
| 222 | New Serial NO | Serial 27-28 |  |
| 223 | New Serial NO | Serial 29-30 |  |
| 229 | EnergyAdj ust | Power generation incremental calibration coefficient | W/R |
| 230 | IslandDisa ble | Island not. | W |
| 231 | FanCheck | Start Fan Check | W |
| 232 | EnableNLi ne | Enable N Line of grid | W |
| 233 | CheckHard ware | Check Hardware |  |
| 234 | CheckHard ware2 |  |  |
| 235 | NToGNDD etect | Dis/enable N to GND detect function | W |
| 236 | NonStdVac Enable | Enable/Disable Nonstandard Grid voltage range | W |
| 237 | EnableSpe cSet | Disablse/enable appointed spec setting | W |
| 238 | Fast MPPT enable | About Fast mppt |  |
| 239 | reg_239 |  |  |
| 240 | Check Step |  | W |
| 241 | INV-Lng | Inverter Longitude | W |
| 242 | INV-Lat | Inverter Latitude | W |
| 304 | uwAntiBac kflowFailP owerLimit EE | Anti-backflow failure power percentage | R/W |
| 305 | Qloadspee d | Reactive loading speed | R/W |
| 306 | ParallelAnt iBackflowE n | ParallelAnti-Backfl ow Enable | R/W |
| 307 | AntiBackfl owFailure ResponseT ime | AntiBackflowFailur e ResponseTime | R/W |
| 308 | ParallelAnt iBackflowP owerLimit EE | Parallel Anti-Back flow Power | R/W |
| 309 | bISOCheck Cmd | ISO detection command | R/W |
| 310 | bGPRSStat us | GPRS Status 1: module not working 2: no sim card 3: No internet 4. TCP not connecting to server 5. TCP connection succeeded | R/W |
| 311 | Qmax_Ind uctive | The inductive Qmax of the Q(V) curve | R/W |
| 312 | Qmax_Cap active | The Capactive Qmax of the Q(V) curve | R/W |
| 313 | ReactivePo werAdjust FailureRes ponseTim e | Reactive Power Adjust Failure Response Time | R/W |
| 314 | SuperAnti BackflowE nable | Super Anti-Back flow Enable | R/W |
| 315 | ReactivePo werStable Time | Reactive Power Stable Time | R/W |
| 316 | QpStableTi me | QpStableTime | R/W |
| 317 | PuDerateT ime | PuDerateTime | R/W |
| 318 | QVModel Q2Point | QV mode Q2 set point reactive power percentage | R/W |
| 319 | QVModel Q3Point | QV mode Q3 set point reactive power percentage | R/W |
| 320 | VrefModel Enable | VrefModelEnable 0:Vref mode for QV curve is not active 1:Vref mode for QV curve is active | R/W |
| 321 | uwVrefMo delFilterTi me | VrefModelFilterTi me | R/W |
| 322 | uwUserQP ModeP1Kr ate | Active power P1 set point percentage for QP mode | R/W |
| 323 | uwUserQP ModeP2Kr ate | Active power P2 set point percentage for QP mode | R/W |
| 324 | uwUserQP ModeP3Kr ate | Active power P3 set point percentage for QP mode | R/W |
| 325 | uwUserQP ModeQ1Kr ate | Reactive power Q1 set point percentage for QP mode | R/W |
| 326 | uwUserQP ModeQ2Kr ate | Reactive power Q2 set point percentage for QP mode | R/W |
| 327 | uwUserQP ModeQ3Kr ate | Reactive power Q3 set point percentage for QP mode | R/W |
| 328 | uwAcVolt HighDerat PowerLimi t | AcVoltHighDeratPo werLimit | R/W |
| 329 | BackflowSi ngleCtrl | BackflowSingleCtrl | R/W |
| 330 | bAntiBackf lowProtect Mode | AntiBackflowProte ctMode | R/W |
| 331 | uwUnderF UploadZer oPowerPoi nt | UnderfreqUploadZ eroPowerPoint | W |
| 332 | FreqDerat eZeroPow erPoint | FreqDerateZeroPo werPoint | W |
| 333 | bFreqDera tingStopM odeEnable | FreqDeratingStop ModeEnable | R/W |
| 334 | bFreqIncre asingEnabl e | FreqIncreasingEna ble | R/W |
| 335 | FreqIncrea singRecov erTime | FreqIncreasingRec overTime | R/W |
| 336 | FreqIncrea singEndLo wPoint | FreqIncreasingEnd LowPoint | R/W |
| 337 | bFreqIncre asingStop ModeEnab le | FreqIncreasingStop ModeEnable | R/W |
| 338 | UserQpCh rP1Krate | User QP function, charge P1 set point percentage | R/W |
| 339 | UserQpCh rP2Krate | User QP function, charge P2 set point percentage | R/W |
| 340 | UserQpCh rP3Krate | User QP function, charge P3 set point percentage | R/W |
| 341 | UserQpCh rQ1Krate | User QP function, charge Q1 set point percentage | R/W |
| 342 | UserQpCh rQ2Krate | User QP function, charge Q2 set point percentage | R/W |
| 343 | UserQpCh rQ3Krate | User QP function, charge Q3 set point percentage | R/W |
| 344 | FreqDerati ngRecover LowPoint | FreqDeratingRecov erLowPoint | R/W |
| 345 | FreqIncrea singRecov erHighPoi nt | FreqIncreasingRec overHighPoint | R/W |
| 355 | DSPDebug FwVer | DSP debug software version | R |
| 359 | M3Debug FwVer | M3 debug software version | R |
| 532 | TurnOffUn loadSpeed | Turn Off Unload Speed | W/R |
| 533 | LimitDevic e | Anti-backflow equipment selection | W/R |
| 534 | PowerSet OnDCSour ceMode | Power settings in dc source mode | W/R |
| 535 | OUFreqGr ade1En | Over-under-freque ncy Grade1Enable, currently only used by CEI0-21 | W/R |
| 536 | Country Set | Country settings under the same safety regulations | W/R |
| 538 | InterlockE nable | Three-machine communication Interlock function mode | W/R |
| 539 | OvTemper DeratePoi nt | Over temperature derate point | W/R |
| 540 | SafetySetP assword | Switch between different safety regulations to set the password | W/R |
| 541 | AFCI Onoff | AFCI Onoff | W/R |
| 542 | AfciSelfCh eck | Afci Self Check | W/R |
| 543 | AfciReset | Afci Reset | W/R |
| 544 | AFCIValue 1 | AFCIThresholdValu e（low） | W/R |
| 545 | AFCIValue 2 | AFCIThresholdValu e（middle） | W/R |
| 546 | AFCIValue 3 | AFCIThresholdValu e（High） | W/R |
| 547 | OverThres holdValue MaxCnt | OverThresholdValu eMaxCnt | W/R |
| 548 | AFCIScanT ypeEnable | AFCI curve scan type | W/R |
| 549 | PowerVolt StopMode En | PowerVoltStopMo deEn | W/R |
| 550 | VoltWattR ecoverTim e | Voltage active power recovery time | W/R |
| 551 | HVoltDerat eStopPow er | Voltage active cut-off power | W/R |
| 552 | QVTimeEx ponent | QV Time Exponent | WR |
| 553 | Volt-Watt Watt1 | Voltage active V1 point, corresponding active power | WR |
| 554 | Volt-Watt Watt2 | Voltage active V2 point, corresponding active power | WR |
| 600 | Volt-Var Var1 | Voltage reactive V1 point, Corresponding reactive power percentage(Capaci tive Qmax) | WR |
| 601 | Volt-Var Var2 | Voltage reactive V2 point,Correspondin g reactive power percentage | WR |
| 602 | Volt-Var Var3 | Voltage reactive V3 point,Correspondin g reactive power percentage | WR |
| 603 | Volt-Var Var4 | Voltage reactive V4 point,Correspondin g reactive power per-centage(Induct ive Qmax) | WR |
| 604 | Reserve |  |  |
| 605 | OPModEn ergize | Allowed inverter output power | R/W |
| 608 | OneKeySet BDCMode | One key to set battery mode function | R/W |
| 609 | PowerOut putEnable | Zero Power Output Enable |  |
| 610 | DealDebug ParaFlag | Flag bit for clearing debug variables |  |
| 645 | BuzzerOn Off | Buzzer enable/disable | R/W |
| 659 | BatSNSetti ngLock | Bat serial number setting lock | R/W |
| 660 | ReloadCm d | M3 remote command |  |
| 700 | bBMSType | Indicates the type of battery connected to the inverter |  |
| 871 | GridPhase Sequence |  | R/W |
| 874 | ParallelEna ble |  | R/W |
| 875 | FW Build No. 5 | ATS Model letter version number （MB） |  |
| 876 | FW Build No. 4 | ATS Model letter versionnumber （AA） |  |
| 877 | FW Build No. 3 | ATS-DSP1 FW Build No |  |
| 878 | FW Build No. 2 | ATS-DSP2/M3 FW Build No |  |
| 879 | ProductSet Enable |  | R/W |
| 897 | ReConnTi mGridRest ore | Wait time for the grid to be restored and reconnected | R/W |
| 900 | STSEnable |  | R/W |
| 901 | OilEnable |  | R/W |
| 902 | OnOffCha ngeMode | Toggle modes | R/W |
| 903 | PcsType |  | R/W |
| 904 | uwBattTyp e |  | R/W |
| 905 | uwACChar gePowerR ate | AC allow charge Power Rate | R/W |
| 906 | uwBattMa xChargeVo l | Battery Max charge voltage | R/W |
| 907 | uwBattEO DVol | Battery End of Discharge voltage | R/W |
| 908 | uwConnec tPhaseMo de | On Grid wireMode | R/W |
| 909 | uwDisCon nectPhase Mode | Off Grid wireMode | R/W |
| 910 | uwBatMax ChargeCur rent | Battery chargeCurrent | R/W |
| 911 | uwBatMax DisCharge Current | Battery Max Discharge Current | R/W |
| 912 | uwOnOffC hangeMan ualMode | OnOffGrid Change Mode | R/W |
| 913 | uwOnOffG ridSet | OnOffGrid Set | R/W |
| 914 | uwOffGrid SoftStartE nable | OffGrid volt Start Enable | R/W |
| 915 | uwOffgrid SoftStartTi me | Off grid volt soft start time | R/W |
| 917 | uwBatCap | Bat cap | R/W |
| 918 | uwPowerD ispatchEna ble | Vpp enable | R/W |
| 919 | uwPowerD ispatchActi vePowerSe t | Power Dispatch Active Power Set | R/W |
| 936 | uwOffGrid Vol | Off grid volt | R/W |
| 937 | uwOffGrid Freq | Off grid frequency | R/W |
| 938 | uwLoadPvI nverter | PCS Load Port has Invert or not | R/W |
| 939 | uwDgStart Soc | The soc point Start oil engine on Off grid | R/W |
| 940 | uwDgStop Soc | The soc point close oil engine on Off grid | R/W |
| 941 | uwLoadPvI nvStartFre q | The invert On load port Over frequency derating point | R/W |
| 942 | uwLoadPvI nvFreqDer ateRate | The invert On load port Over frequency derating slope | R/W |
| 943 | uwLoadPvI nvFreqDer ateMinPo wer | the invert On load port Over frequency derating Min power | R/W |
| 944 | uwDeman dMangeDi sChargePo werLimit | Demand management AC port discharge limit power | R/W |
| 945 | uwDeman dMangeCh argePower Limit | Demand management AC port charge limit power | R/W |
| 946 | uwDeman dMangeEn able | Demand management enable | R/W |
| 947 | uwPowerU nblanceCtr lEnable | AC Power unbalance ctrl enable | R/W |
| 948 | PcsParallel Num | Pcs parallel num | R/W |
| 949 | uwACChar geEnable | AC charge enable | R/W |
| 950 | uwOffGrid Enable | Off grid enable | R/W |
| 951 | uwBatChar geStopSoc | Battery charge stop SOC | R/W |
| 952 | uwBatDisC hargeStop Soc | Battery discharge stop SOC | R/W |
| 953 | uwSingleP haseAntiB ackflowEn able | Single phase AntiBackflow | R/W |
| 954 | Time 1 Enable |  | R/W |
| 955 | Time 1 start time | Start Time | R/W |
| 956 | Time 1 end time | End Time | R/W |
| 957 | Time 2 Enable |  | R/W |
| 958 | Time 2 start time | Start Time | R/W |
| 959 | Time 2 end time | End Time | R/W |
| 960 | Time 3 Enable |  | R/W |
| 961 | Time 3 start time | Start Time | R/W |
| 962 | Time 3 end time | End Time | R/W |
| 963 | Time 4 Enable |  | R/W |
| 964 | Time 4 start time | Start Time | R/W |
| 965 | Time 4 end time | End Time | R/W |
| 966 | Time 5 Enable |  | R/W |
| 967 | Time 5 start time | Start Time | R/W |
| 968 | Time 5 end time | End Time | R/W |
| 969 | Time 6 Enable |  | R/W |
| 970 | Time 6 start time | Start Time | R/W |
| 971 | Time 6 end time | End Time | R/W |
| 972 | BMS Enable |  | R/W |
| 973 | parallel Enable | uwParallelEnable | R/W |
| 974 | BatCharge PowerLimi t | Battle Charge Power Limit | R/W |
| 975 | BatDisChar gePowerLi mit | Battle DisCharge Power Limit | R/W |
| 976 | ATS SpecPowe r | ATS SpecPower | R/W |
| 987 | ESPConstN CEnable | Emergency stop and normal closure are enabled, which distinguishes between the American version and the European version | R/W |
| 988 | MachineTy pe |  | R/W |
| 989 | ForcePowe rSlowChan ge | Power is forcibly slowly enabled | R/W |
| 990 | ForceChrD ischrPowe r[TIME1] | Time period 1 power setting, only WIS models are allowed to set | R/W |
| 991 | ForceChrD ischrPowe r[TIME2] | Time period 2 power setting, only WIS models are allowed to set | R/W |
| 992 | ForceChrD ischrPowe r[TIME3] | Time period 3 power setting, only WIS models are allowed to set | R/W |
| 993 | ForceChrD ischrPowe r[TIME4] | Time period 4 power setting, only WIS models are allowed to set | R/W |
| 994 | ForceChrD ischrPowe r[TIME5] | Time period 5 power setting, only WIS models are allowed to set | R/W |
| 995 | ForceChrD ischrPowe r[TIME6] | Time period 6 power setting, only WIS models are allowed to set | R/W |
| 996 | BakSoc |  | R/W |
| 997 | BakSocEna ble | The standby SOC is enabled under the demand management function | R/W |
| 998 | OffGridDis ChgStopSo c |  | R/W |
| *Six group for Storage Power* |  |  |  |
| 1000 | Float charge current limit | When charge current battery need is lower than this value, enter into float charge | W |
| 1001 | PF CMD memory state | Set the following 19-22 CMD will be memory ornot(1/0), if not, these settings are the initial value. | W |
| 1002 | VbatStartF orDischarg e | LV Vbat | R/W |
| 1003 | VbatlowW arnClr | Load Percent(only lead-Acid): 45.5V:<20%, 48.0V:20%~50% 49.0V:>50 | W |
| 1004 | Vbatstopfo rdischarge | Should stop dischar-ge when lower than this voltage (only lead-Acid): 46.0V:<20% 44.8V:20%~50% 44.2V:>50% | W |
| 1005 | Vbat stop for charge | Should stop charge when higher than this voltage | W |
| 1006 | Vbatstartf ordischarg e | Should not discharge when lower than this voltage | W |
| 1007 | Vbat constant charge | Can charge when lower than this voltage | W |
| 1008 | EESysInfo. SysSetEn | Bit0:Resved; Bit1:Resved; Bit2:Resved; Bit3:Resved; Bit4:Resved; Bit5:bDischargeEn; Bit6:ForceDischrEn ; Bit7:ChargeEn; Bit8:bForceChrEn; Bit9:bBackUpEn; Bit10:bInvLimitLoa dE; Bit11:bSpLimitLoad En; Bit12:bACChargeEn ; Bit13:bPVLoadLimi tEn; Bit14,15:UnUsed; | W |
| 1009 | Battemp lower limit d | Battery temperature lower limit for discharge | W |
| 1010 | Battemp upper limit d | Battery temperature upper limit for discharge | W |
| 1011 | Battemp lower limit c | Battery temperature lower limit for charge | W |
| 1012 | Battemp upper limit c | Battery temperature upper limit for charge | W |
| 1013 | uwUnderF reDischarg eDelyTime | Under Fre Delay Time |  |
| 1014 | BatMdlSer ialNum | Battery serial number | W |
| 1015 | BatMdlPar allNum | Battery parallel section | W |
| 1016 | DRMS_EN |  |  |
| 1017 | Bat First Start Time 4 | High eight:hours Low eight: minutes |  |
| 1018 | Bat First Stop Time 4 | High eight:hours Low eight: minutes |  |
| 1019 | BatFirst on/off Switch 4 | Enable:1 Disable:0 |  |
| 1020 | Bat First Start Time 5 | High eight:hours Low eight: minutes |  |
| 1021 | Bat First Stop Time 5 | High eight:hours Low eight: minutes |  |
| 1022 | BatFirst on/off Switch 5 | Enable:1 Disable:0 |  |
| 1023 | Bat First Start Time 6 | High eight:hours Low eight: minutes |  |
| 1024 | Bat First Stop Time 6 | High eight:hours Low eight: minutes |  |
| 1025 | BatFirst on/off Switch 6 | Enable:1 Disable:0 |  |
| 1026 | Grid First Start Time 4 | High eight:hours Low eight: minutes |  |
| 1027 | Grid First Stop Time 4 | High eight:hours Low eight: minutes |  |
| 1028 | Grid First Stop Switch 4 | Enable:1 Disable:0 |  |
| 1029 | Grid First Start Time 5 | High eight:hours Low eight: minutes |  |
| 1030 | Grid First Stop Time 5 | High eight:hours Low eight: minutes |  |
| 1031 | Grid First Stop Switch 5 | Enable:1 Disable:0 |  |
| 1032 | Grid First Start Time 6 | High eight:hours Low eight: minutes |  |
| 1033 | Grid First Stop Time 6 | High eight:hours Low eight: minutes |  |
| 1034 | Grid First Stop Switch 6 | Enable:1 Disable:0 |  |
| 1035 | Bat First Start Time 4 | High eight:hours Low eight: minutes |  |
| 1036 | reg_1036 |  |  |
| 1037 | bCTMode | Use the CTMode to Choose RFCT \ Cable CT\METER | W |
| 1038 | CTAdjust | CTAdjust enable | W |
| 1044 | Priority | ForceChrEn/ForceD ischrEn Load first/bat first /grid first | R |
| 1045 | Reserve |  |  |
| 1046 | Reserve |  |  |
| 1047 | AgingTestS tep Cmd | Command for aging test |  |
| 1048 | BatteryTyp e | Battery type choose of buck-boost input |  |
| 1049 | Reserve |  |  |
| 1060 | BuckUpsF unEn | Ups function enable or disable |  |
| 1061 | BuckUPSV oltSet | UPS output voltage |  |
| 1062 | UPSFreqSe t | UPS output frequency |  |
| 1070 | GridFirstDi schargePo werRate | Discharge Power Rate when Grid First |  |
| 1071 | GridFirstSt opSOC | Stop Discharge SOC when Grid First |  |
| 1080 | Grid First Start Time 1 | High eight bit:hour Low eight bit:minute |  |
| 1081 | Grid First Stop Time 1 | High eight bit:hour Low eight bit:minute |  |
| 1082 | Grid First Stop Switch 1 | Enable :1 Disable:0 |  |
| 1083 | Grid First Start Time 2 | High eight bit:hour Low eight bit:minute |  |
| 1084 | Grid First Stop Time 2 | High eight bit:hour Low eight bit:minute |  |
| 1085 | Grid First Stop Switch 2 | ForceDischarge.bSwitch&LC D_SET_FORCE_TRUE_2)==L CD_SET_FORCE_TRUE_2 |  |
| 1086 | Grid First Start Time 3 | High eight bit:hour Low eight bit:minute |  |
| 1087 | Grid First Stop Time 3 | High eight bit:hour Low eight bit:minute |  |
| 1088 | Grid First Stop Switch 3 | Enable :1 Disable:0 |  |
| 1089 | reg_1089 |  |  |
| 1090 | BatFirstPo werRate | Charge Power Rate when Bat First |  |
| 1091 | wBatFirst stop SOC | Stop Charge soc when Bat First |  |
| 1092 | AC charge Switch | When Bat First Enable:1 Disable:0 |  |
| 1100 | Bat First Start Time 1 | High eight bit:hour Low eight bit:minute |  |
| 1101 | Bat First Stop Time 1 | High eight bit:hour Low eight bit:minute |  |
| 1102 | BatFirst on/off Switch 1 | Enable :1 Disable:0 |  |
| 1103 | Bat First Start Time 2 | High eight bit:hour Low eight bit:minute |  |
| 1104 | Bat First Stop Time 2 | High eight bit:hour Low eight bit:minute |  |
| 1105 | BatFirston /off Switch 2 | Enable :1 Disable:0 |  |
| 1106 | Bat First Start Time 3 | High eight bit:hour Low eight bit:minute |  |
| 1107 | Bat First Stop Time 3 | High eight bit:hour Low eight bit:minute |  |
| 1108 | BatFirston /off Switch 3 | Enable :1 Disable:0 |  |
| 1109 | reg_1109 |  |  |
| 1110 | Load First Start Time 1 | High eight bit:hour Low eight bit:minute |  |
| 1111 | Load First Stop Time 1 | High eight bit:hour Low eight bit:minute |  |
| 1112 | Load First Switch 1 | Enable :1 Disable:0 |  |
| 1113 | Load First Start Time2 | High eight bit:hour Low eight bit:minute |  |
| 1114 | Load First Stop Time 2 | High eight bit:hour Low eight bit:minute |  |
| 1115 | Load First Switch 2 | Enable :1 Disable:0 |  |
| 1116 | Load First Start Time 3 | High eight bit:hour Low eight bit:minute |  |
| 1117 | Load First Stop Time 3 | High eight bit:hour Low eight bit:minute |  |
| 1118 | Load First Switch 3 | Enable :1 Disable:0 |  |
| 1119 | NewEPow erCalcFlag |  |  |
| 1120 | BackUpEn | BackUp Enable |  |
| 1121 | SGIPEn | SGIP Enable |  |
| 1125 | BatSerialN O. 8 | Product serial number of the first PACK of energy storage batteries |  |
| 1126 | BatSerialN O. 7 |  |  |
| 1127 | BatSerialN O. 6 |  |  |
| 1128 | BatSerialN O. 5 |  |  |
| 1129 | BatSerialN O. 4 |  |  |
| 1130 | BatSerialN O. 3 |  |  |
| 1131 | BatSerialN O. 2 |  |  |
| 1132 | BatSerialN O. 1 | The serial number of the second to tenth packs of the energy storage battery consists of nine packs, and the format of the serial number of each PACK is 1125 to 1132 Reserve |  |
| 1244 | Com version NameH | Name of the battery main control firmware version |  |
| 1245 | Com version NameL | Name of the battery main control firmware version |  |
| 1246 | Com version No | Version of the battery main control firmware |  |
| 1247 | Com version NameH | Name of battery monitoring firmware version |  |
| 1248 | Com version NameL | Name of battery monitoring firmware version |  |
| 1249 | Com version No | Battery monitoring firmware version |  |
| *Use for TL-X and TL-XH* |  |  |  |
| 3000 | ExportLimi tFailedPow erRate | The power rate when exportLimit failed |  |
| 3001 | New Serial NO | Serial number 1-2 |  |
| 3002 | New Serial NO | Serial number 3-4 |  |
| 3003 | New Serial NO | Serial number 5-6 |  |
| 3004 | New Serial NO | Serial number 7-8 |  |
| 3005 | New Serial NO | Serial number 9-10 |  |
| 3006 | New Serial NO | Serial number 11-12 |  |
| 3007 | New Serial NO | Serial number 13-14 |  |
| 3008 | New Serial NO | Serial number 15-16 |  |
| 3009 | New Serial NO | Serial number 17-18 |  |
| 3010 | New Serial NO | Serial number 19-20 |  |
| 3011 | New Serial NO | Serial number 21-22 |  |
| 3012 | New Serial NO | Serial number 23-24 |  |
| 3013 | New Serial NO | Serial number 25-26 |  |
| 3014 | New Serial NO | Serial number 27-28 |  |
| 3015 | New Serial NO | Serial number 29-30 |  |
| 3016 | DryContac tFuncEn | Dry Contact function enable |  |
| 3017 | DryContac tOnRate | The power rate of dry contact turn on |  |
| 3018 | WorkMod e | WorkMode 0:default,1: System Retrofit 2: Multi-Parallel |  |
| 3019 | DryContac tOffRate | Dry Contact Off Rate, Dry contact closure power |  |
| 3020 | BoxCtrlInv Order | Box Ctrl Inv Order |  |
| 3021 | ExterCom mOffGridE n | External communication setting manual off-network enable |  |
| 3022 | uwBdcSto pWorkOfB usVolt | BdcStopWorkOfBusVolt |  |
| 3023 | bGridType | GridType---0:SinglePhase 1:ThreePhase 2:SplitPhase |  |
| 3024 | Float charge current limit | When charge current battery need is lower than this value, enter into float charge |  |
| 3025 | VbatWarni ng | "Battery-low" warning setup voltage |  |
| 3026 | VbatlowW arnClr | "Battery-low" warning clear voltage Clear battery low voltage error voltage point Load Percent (only lead-Acid): 45.5V(Load < 20%); 48.0V(20%<=Load <=50%); 49.0V(Load > 50%); |  |
| 3027 | Vbatstopfo rdischarge | Battery cut off voltage Should stop discharge when lower than this voltage(only lead-Acid): 46.0V(Load < 20%); 44.8V(20%<=Load <=50%); 44.2V(Load > 50%); |  |
| 3028 | Vbat stop for charge | Battery over charge volt, Should stop charge when higher than this voltage |  |
| 3029 | Vbat start for discharge | Battery start discharge volt, Should not discharge when lower than this voltage |  |
| 3030 | Vbat constant charge | Battery constant charge voltage,CV voltage（acid） can charge when lower than this voltage |  |
| 3031 | Battemp lower limit d | Battery temperature lower limit for discharge |  |
| 3032 | Bat temp upper limit d | Battery temperature upper limit for discharge |  |
| 3033 | Bat temp lower limit c | Battery temperature lower limit for charge |  |
| 3034 | Bat temp upper limit c | Battery temperature upper limit for charge |  |
| 3035 | uwUnderF reDischarg eDelyTime | Under Fre Delay Time |  |
| 3036 | GridFirstDi schargePo werRate | Discharge Power Rate when Grid First |  |
| 3037 | GridFirstSt opSOC | Stop Discharge soc when Grid First |  |
| 3038 | Time 1(xh) | Period 1: [Start Time ~ End Time], [Charge/Discharge], [Disable/Enable] 3038 enable, charge and discharge, start time, end time 3039 |  |
| 3039 | reg_3039 |  |  |
| 3040 | Time 2(xh) | Time period 2: [start time ~ end time], [charge / discharge], [disable / enable] 3040 enable, charge and discharge, start time, 3041 end time |  |
| 3041 | reg_3041 |  |  |
| 3042 | Time 3(xh) | With Time1 |  |
| 3043 | reg_3043 |  |  |
| 3044 | Time 4(xh) | With Time1 |  |
| 3045 | reg_3045 |  |  |
| 3046 | INVHWVer sion | US inverter hardware version |  |
| 3047 | BatFirstPo werRate | Charge Power Rate when Bat First |  |
| 3048 | wBatFirst stop SOC | Stop Charge soc when Bat First |  |
| 3049 | AcChargeE nable | AcChargeEnable |  |
| 3050 | Time 5(xh) | With Time1 |  |
| 3051 | reg_3051 |  |  |
| 3052 | Time 6(xh) | With Time1 |  |
| 3053 | reg_3053 |  |  |
| 3054 | Time 7(xh) | With Time1 |  |
| 3055 | reg_3055 |  |  |
| 3056 | Time 8(xh) | With Time1 |  |
| 3057 | reg_3057 |  |  |
| 3058 | Time 9(xh) | With Time1 |  |
| 3059 | reg_3059 | Reserve |  |
| 3067 | OnGridGri dFirstStop SOC | Stop Discharge soc when Grid First and on-grid Reserve |  |
| 3070 | BatteryTyp e | Battery type choose of buck-boost input |  |
| 3071 | BatMdlSer ia/ParalNu m | BatMdlSeria/ParalNum The upper 8 bits indicate the number of series segments; The lower 8 bits indicate the number of parallel sections; |  |
| 3072 | bTurnoffA cEnable | Enable Pre-PTO function |  |
| 3073 | Generator ChargeEna ble | Enable battery charge from generator function |  |
| 3074 | Generator OnCmd | Force the generator on,off or not forced [1.27 add] [1.31 Modify] Reserved |  |
| 3077 | uwGenera torSpecPo wer | generator rated power |  |
| 3078 | Reserved |  |  |
| 3079 | UpsFunEn | Ups function enable or disable |  |
| 3080 | UPSVoltSe t | UPS output voltage |  |
| 3081 | UPSFreqSe t | UPS output frequency |  |
| 3082 | bLoadFirst StopSocSe t | StopSoc When LoadFirst |  |
| 3082 | BackUpBo xEnable | BackUp Box Enable Stop Discharge soc when on-grid mode |  |
| 3083 | AustraliaR egion | Australian region |  |
| 3084 | Reserved |  |  |
| 3085 | Com Address | Communication addr |  |
| 3086 | BaudRate | Communication BaudRate |  |
| 3087 | Serial NO. 1 | Serial Number 1-2 |  |
| 3088 | Serial NO. 2 | Serial Number 3-4 |  |
| 3089 | Serial NO. 3 | Serial Number 5-6 |  |
| 3090 | Serial NO. 4 | Serial Number 7-8 |  |
| 3091 | Serial No. 5 | Serial Number 9-10 |  |
| 3092 | Serial No.6 | Serial Number 11-12 |  |
| 3093 | Serial No. 7 | Serial Number 13-14 |  |
| 3094 | Serial No. 8 | Serial Number 15-16 |  |
| 3095 | BdcResetC md | BDC Reset command |  |
| 3096 | ARKM3 Code | BDCMonitoring software code |  |
| 3097 | reg_3097 |  |  |
| 3098 | DTC | DTC |  |
| 3099 | FW Code | DSP software code |  |
| 3100 | reg_3100 |  |  |
| 3101 | Processor1 FW Vision | DSP Software Version |  |
| 3102 | BusVoltRef | Minimum BUS voltage for charging and discharging batteries |  |
| 3103 | ARKM3Ver | BDC monitoring software version |  |
| 3104 | BMS_MCU Version | BMS hardware version information |  |
| 3105 | BMS_FW | BMS software version information |  |
| 3106 | BMS_Info | BMS ManufacturerName |  |
| 3107 | BMSCom mType | BMS Communication interface type: |  |
| 3108 | Module 4 | BDCmodel (4) |  |
| 3109 | Module 3 | BDCmodel (3) |  |
| 3110 | Module 2 | BDCmodel (2) |  |
| 3111 | Module 1 | BDCmodel (1) |  |
| 3112 | BDCParalle lNomber | Number of BDC parallel |  |
| 3113 | unProtocol Ver | BDC Protocol Version Bit8-bit15:The major version number ranges from 0-256. In principle, it cannot be changed Bit0-bit7:Minor version number [0-256]. |  |
| 3114 | uwCertific ationVer | BDC CertificationVer |  |
| 3115 | BDCHardw areVersion | BDC hardware version number |  |
| 3116 | BCUSoftw areVer | BCU software code |  |
| 3117 | reg_3117 |  |  |
| 3118 | HistoricalF aultNum | Historical fault number |  |
| 3119 | RatedCellC apacity | Cell rated capacity |  |
| 3120 | BDCNumA ndBatNum | BDC number and number of battery modules in parallel Bit15 to bit13: indicates the number of the BDC in the range [1-4]. Bit12 to bit10: reserved Bit7~bit0: Parallel number of battery modules range[1,25] |  |
| 3121 | RatedBatC apacity | Battery rated capacity Reserved |  |
| 3124 | ClearTime Settings | Clear EMS time settings .Clear holding3125-3238 and holding608 |  |
| 3125 | Time Month1 | Use with Time1-9（us） ,Add month time |  |
| 3126 | Time Month2 | Use with Time10-18（us） ,Add month time |  |
| 3127 | Time Month3 | Use with Time19-27（us） ,Add month time |  |
| 3128 | Time Month4 | Use with Time28-36（us） ,Add month time |  |
| 3129 | Time 1 （us） | time1:[starttime~endtime] |  |
| 3130 | reg_3130 | Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above |  |
| 3201 | SpecialDay 1 | SpecialDay1（month,Day） |  |
| 3202 | SpecialDay 1_Time1 | Start time |  |
| 3203 | reg_3203 | endtime Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above |  |
| 3220 | SpecialDay 2 | SpecialDay2（month,Day） |  |
| 3221 | SpecialDay 2_Time1 | Start time |  |
| 3222 | reg_3222 | endtime Same as above Same as above Same as above Same as above Same as above Same as above Same as above Same as above Reserve |  |
| 3250 | bBoxData UploadFla g | Backup box Data Upload Flag |  |
| 3251 | uwFirmwa reCode_H | Backup box firmware code |  |
| 3252 | uwFirmwa reCode_L |  |  |
| 3253 | ubFirmwar eVersion | Backup box firmware version |  |
| 3254 | uwSerialN um0 | Backup box serial number 0 |  |
| 3255 | uwSerialN um1 | Backup box serial number 1 |  |
| 3256 | uwSerialN um2 | Backup box serial number 2 |  |
| 3257 | uwSerialN um3 | Backup box serial number 3 |  |
| 3258 | uwSerialN um4 | Backup box serial number 4 |  |
| 3259 | uwSerialN um5 | Backup box serial number 5 |  |
| 3260 | uwSerialN um6 | Backup box serial number 6 |  |
| 3261 | uwSerialN um7 | Backup box serial number 7 |  |
| 3262 | uwSerialN um8 | Backup box serial number 8 |  |
| 3263 | uwSerialN um9 | Backup box serial number 9 |  |
| 3264 | uwSerialN um10 | Backup box serial number 10 |  |
| 3265 | uwSerialN um11 | Backup box serial number 11 |  |
| 3266 | uwSerialN um12 | Backup box serial number 12 |  |
| 3267 | uwSerialN um13 | Backup box serial number 13 |  |
| 3268 | uwSerialN um14 | Backup box serial number 14 |  |
| 3269 | uwAFCIFir mwareCod e_H | AFCI software code |  |
| 3270 | uwAFCIFir mwareCod e_L | AFCI software code |  |
| 3271 | uwAFCIFir mwareVer | AFCI software version |  |
| 3272 | BusbarPro tectEn | Busbar protect enable |  |
| 3273 | BusbarPro tectCurren t | Busbar protect current |  |
| 3274 | BusbarPro tectFailCur rent | Busbar protect current when meter connect error Reserve |  |
| 3282 | BypassMo deEnterEn | Bypass mode enter enable 1 2 N |  |
| *Battery module information (support up to 64 parallel BDC)（Special for APX）* |  |  |  |
| 5400 | Serial NO. 1 |  |  |
| 5401 | Serial NO. 2 |  |  |
| 5402 | Serial NO. 3 |  |  |
| 5403 | Serial NO. 4 |  |  |
| 5404 | Serial No. 5 |  |  |
| 5405 | Serial No.6 |  |  |
| 5406 | Serial No. 7 |  |  |
| 5407 | Serial No. 8 |  |  |
| 5408 | BatDSPCode |  |  |
| 5409 | reg_5409 |  |  |
| 5410 | BatDSPVersio n |  |  |
| 5411 | BatMCUCode |  |  |
| 5412 | reg_5412 |  |  |
| 5413 | BatMCUVersi on |  |  |
| 5414 | BatManufact urerInfor |  |  |
| 5415 | BatNumber |  |  |
| 5416 | SOX firmware version |  |  |
| 5417 | PowerCmd |  |  |
| 5418 | MaxPowerPe cnent |  |  |
| 5419 | SOCLimit | Reserved |  |
| 7960 | uwSerialNum0 |  |  |
| 7961 | uwSerialNum1 |  |  |
| 7962 | uwSerialNum2 |  |  |
| 7963 | uwSerialNum3 |  |  |
| 7964 | uwSerialNum4 |  |  |
| 7965 | uwSerialNum5 |  |  |
| 7966 | uwSerialNum6 |  |  |
| 7967 | uwSerialNum7 |  |  |
| 7968 | uwSerialNum8 |  |  |
| 7969 | uwSerialNum9 |  |  |
| 7970 | uwSerialNum10 |  |  |
| 7971 | uwSerialNum11 |  |  |
| 7972 | uwSerialNum12 |  |  |
| 7973 | uwSerialNum13 |  |  |
| 7974 | uwSerialNum14 |  |  |
| 8560 | uwSerialNum0 |  |  |
| 8561 | uwSerialNum1 |  |  |
| 8562 | uwSerialNum2 |  |  |
| 8563 | uwSerialNum3 |  |  |
| 8564 | uwSerialNum4 |  |  |
| 8565 | uwSerialNum5 |  |  |
| 8566 | uwSerialNum6 |  |  |
| 8567 | reg_8567 |  |  |
| 8568 | reg_8568 |  |  |
| 8569 | reg_8569 |  |  |
| 8570 | reg_8570 |  |  |
| 8571 | reg_8571 |  |  |
| 8572 | reg_8572 |  |  |
| 8573 | reg_8573 |  |  |
| 8574 | reg_8574 |  |  |

---

## Input Registers (1092 registers)

| Address | Name | Description | Access |
| --- | --- | --- | --- |
| *First group* |  |  |  |
| 0 | reg_0 |  |  |
| 1 | reg_1 |  |  |
| 2 | reg_2 |  |  |
| 3 | reg_3 |  |  |
| 4 | reg_4 |  |  |
| 5 | reg_5 |  |  |
| 6 | reg_6 |  |  |
| 7 | reg_7 |  |  |
| 8 | reg_8 |  |  |
| 9 | reg_9 |  |  |
| 10 | reg_10 |  |  |
| 11 | reg_11 |  |  |
| 12 | reg_12 |  |  |
| 13 | reg_13 |  |  |
| 14 | reg_14 |  |  |
| 15 | reg_15 |  |  |
| 16 | reg_16 |  |  |
| 17 | reg_17 |  |  |
| 18 | reg_18 |  |  |
| 19 | reg_19 |  |  |
| 20 | reg_20 |  |  |
| 21 | reg_21 |  |  |
| 22 | reg_22 |  |  |
| 23 | reg_23 |  |  |
| 24 | reg_24 |  |  |
| 25 | reg_25 |  |  |
| 26 | reg_26 |  |  |
| 27 | reg_27 |  |  |
| 28 | reg_28 |  |  |
| 29 | reg_29 |  |  |
| 30 | reg_30 |  |  |
| 31 | reg_31 |  |  |
| 32 | reg_32 |  |  |
| 33 | reg_33 |  |  |
| 34 | reg_34 |  |  |
| 35 | reg_35 |  |  |
| 36 | reg_36 |  |  |
| 37 | reg_37 |  |  |
| 38 | reg_38 |  |  |
| 39 | reg_39 |  |  |
| 40 | reg_40 |  |  |
| 41 | reg_41 |  |  |
| 42 | reg_42 |  |  |
| 43 | reg_43 |  |  |
| 44 | reg_44 |  |  |
| 45 | reg_45 |  |  |
| 46 | reg_46 |  |  |
| 47 | reg_47 |  |  |
| 48 | reg_48 |  |  |
| 49 | reg_49 |  |  |
| 50 | reg_50 |  |  |
| 51 | reg_51 |  |  |
| 52 | reg_52 |  |  |
| 53 | reg_53 |  |  |
| 54 | reg_54 |  |  |
| 55 | reg_55 |  |  |
| 56 | reg_56 |  |  |
| 57 | reg_57 |  |  |
| 58 | reg_58 |  |  |
| 59 | reg_59 |  |  |
| 60 | reg_60 |  |  |
| 61 | reg_61 |  |  |
| 62 | reg_62 |  |  |
| 63 | reg_63 |  |  |
| 64 | reg_64 |  |  |
| 65 | reg_65 |  |  |
| 66 | reg_66 |  |  |
| 67 | reg_67 |  |  |
| 68 | reg_68 |  |  |
| 69 | reg_69 |  |  |
| 70 | reg_70 |  |  |
| 71 | reg_71 |  |  |
| 72 | reg_72 |  |  |
| 73 | reg_73 |  |  |
| 74 | reg_74 |  |  |
| 75 | reg_75 |  |  |
| 76 | reg_76 |  |  |
| 77 | reg_77 |  |  |
| 78 | reg_78 |  |  |
| 79 | reg_79 |  |  |
| 80 | reg_80 |  |  |
| 81 | reg_81 |  |  |
| 82 | reg_82 |  |  |
| 83 | reg_83 |  |  |
| 84 | reg_84 |  |  |
| 85 | reg_85 |  |  |
| 86 | reg_86 |  |  |
| 87 | reg_87 |  |  |
| 88 | reg_88 |  |  |
| 89 | reg_89 |  |  |
| 90 | reg_90 |  |  |
| 91 | reg_91 |  |  |
| 92 | reg_92 |  |  |
| 93 | reg_93 |  |  |
| 94 | reg_94 |  |  |
| 95 | reg_95 |  |  |
| 96 | reg_96 |  |  |
| 97 | reg_97 |  |  |
| 98 | reg_98 |  |  |
| 99 | reg_99 |  |  |
| 100 | reg_100 |  |  |
| 101 | reg_101 |  |  |
| 102 | reg_102 |  |  |
| 103 | reg_103 |  |  |
| 104 | reg_104 |  |  |
| 105 | reg_105 |  |  |
| 106 | reg_106 |  |  |
| 107 | reg_107 |  |  |
| 108 | reg_108 |  |  |
| 109 | reg_109 |  |  |
| 110 | reg_110 |  |  |
| 111 | reg_111 |  |  |
| 112 | reg_112 |  |  |
| 113 | reg_113 |  |  |
| 114 | reg_114 |  |  |
| 115 | reg_115 |  |  |
| 116 | reg_116 |  |  |
| 117 | reg_117 |  |  |
| 118 | reg_118 |  |  |
| 119 | reg_119 |  |  |
| 120 | reg_120 |  |  |
| 124 | reg_124 |  |  |
| *Second group* |  |  |  |
| 125 | reg_125 |  |  |
| 126 | reg_126 |  |  |
| 127 | reg_127 |  |  |
| 128 | reg_128 |  |  |
| 129 | reg_129 |  |  |
| 130 | reg_130 |  |  |
| 131 | reg_131 |  |  |
| 132 | reg_132 |  |  |
| 133 | reg_133 |  |  |
| 134 | reg_134 |  |  |
| 135 | reg_135 |  |  |
| 136 | reg_136 |  |  |
| 137 | reg_137 |  |  |
| 138 | reg_138 |  |  |
| 139 | reg_139 |  |  |
| 140 | reg_140 |  |  |
| 141 | reg_141 |  |  |
| 142 | reg_142 |  |  |
| 143 | reg_143 |  |  |
| 144 | reg_144 |  |  |
| 145 | reg_145 |  |  |
| 146 | reg_146 |  |  |
| 147 | reg_147 |  |  |
| 148 | reg_148 |  |  |
| 149 | reg_149 |  |  |
| 150 | reg_150 |  |  |
| 151 | reg_151 |  |  |
| 152 | reg_152 |  |  |
| 153 | reg_153 |  |  |
| 154 | reg_154 |  |  |
| 155 | reg_155 |  |  |
| 156 | reg_156 |  |  |
| 157 | reg_157 |  |  |
| 158 | reg_158 |  |  |
| 159 | reg_159 |  |  |
| 160 | reg_160 |  |  |
| 161 | reg_161 |  |  |
| 162 | reg_162 |  |  |
| 163 | reg_163 |  |  |
| 164 | reg_164 |  |  |
| 165 | reg_165 |  |  |
| 166 | reg_166 |  |  |
| 167 | reg_167 |  |  |
| 168 | reg_168 |  |  |
| 169 | reg_169 |  |  |
| 170 | reg_170 |  |  |
| 171 | reg_171 |  |  |
| 172 | reg_172 |  |  |
| 173 | reg_173 |  |  |
| 174 | reg_174 |  |  |
| 175 | reg_175 |  |  |
| 176 | reg_176 |  |  |
| 177 | reg_177 |  |  |
| 178 | reg_178 |  |  |
| 179 | reg_179 |  |  |
| 180 | reg_180 |  |  |
| 181 | reg_181 |  |  |
| 182 | reg_182 |  |  |
| 183 | reg_183 |  |  |
| 184 | reg_184 |  |  |
| 185 | reg_185 |  |  |
| 186 | reg_186 |  |  |
| 187 | reg_187 |  |  |
| 188 | reg_188 |  |  |
| 189 | reg_189 |  |  |
| 190 | reg_190 |  |  |
| 191 | reg_191 |  |  |
| 192 | reg_192 |  |  |
| 193 | reg_193 |  |  |
| 194 | reg_194 |  |  |
| 195 | reg_195 |  |  |
| 196 | reg_196 |  |  |
| 197 | reg_197 |  |  |
| 198 | reg_198 |  |  |
| 199 | reg_199 |  |  |
| 200 | reg_200 |  |  |
| 201 | reg_201 |  |  |
| 202 | reg_202 |  |  |
| 203 | reg_203 |  |  |
| 204 | reg_204 |  |  |
| 205 | reg_205 |  |  |
| 206 | reg_206 |  |  |
| 207 | reg_207 |  |  |
| 208 | reg_208 |  |  |
| 209 | reg_209 |  |  |
| 210 | reg_210 |  |  |
| 211 | reg_211 |  |  |
| 212 | reg_212 |  |  |
| 213 | reg_213 |  |  |
| 214 | reg_214 |  |  |
| 215 | reg_215 |  |  |
| 216 | reg_216 |  |  |
| 217 | reg_217 |  |  |
| 218 | reg_218 |  |  |
| 219 | reg_219 |  |  |
| 220 | reg_220 |  |  |
| 221 | reg_221 |  |  |
| 222 | reg_222 |  |  |
| 223 | reg_223 |  |  |
| 224 | reg_224 |  |  |
| 225 | reg_225 |  |  |
| 226 | reg_226 |  |  |
| 227 | reg_227 |  |  |
| 228 | reg_228 |  |  |
| 229 | reg_229 |  |  |
| 230 | reg_230 |  |  |
| 231 | reg_231 |  |  |
| 232 | reg_232 |  |  |
| 233 | reg_233 |  |  |
| 234 | reg_234 |  |  |
| 235 | reg_235 |  |  |
| 236 | reg_236 |  |  |
| 237 | reg_237 |  |  |
| 238 | reg_238 |  |  |
| 239 | reg_239 |  |  |
| 240 | reg_240 |  |  |
| 241 | reg_241 |  |  |
| 242 | reg_242 |  |  |
| 243 | reg_243 |  |  |
| 244 | reg_244 |  |  |
| 245 | reg_245 |  |  |
| 246 | reg_246 |  |  |
| 247 | reg_247 |  |  |
| 248 | reg_248 |  |  |
| 249 | reg_249 |  |  |
| *The eighth group for PV9-PV16 information* |  |  |  |
| 875 | reg_875 |  |  |
| 876 | reg_876 |  |  |
| 877 | reg_877 |  |  |
| 878 | reg_878 |  |  |
| 879 | reg_879 |  |  |
| 880 | reg_880 |  |  |
| 881 | reg_881 |  |  |
| 882 | reg_882 |  |  |
| 883 | reg_883 |  |  |
| 884 | reg_884 |  |  |
| 885 | reg_885 |  |  |
| 886 | reg_886 |  |  |
| 887 | reg_887 |  |  |
| 888 | reg_888 |  |  |
| 889 | reg_889 |  |  |
| 890 | reg_890 |  |  |
| 891 | reg_891 |  |  |
| 892 | reg_892 |  |  |
| 893 | reg_893 |  |  |
| 894 | reg_894 |  |  |
| 895 | reg_895 |  |  |
| 896 | reg_896 |  |  |
| 897 | reg_897 |  |  |
| 898 | reg_898 |  |  |
| 899 | reg_899 |  |  |
| 900 | reg_900 |  |  |
| 901 | reg_901 |  |  |
| 902 | reg_902 |  |  |
| 903 | reg_903 |  |  |
| 904 | reg_904 |  |  |
| 905 | reg_905 |  |  |
| 906 | reg_906 |  |  |
| 907 | reg_907 |  |  |
| 908 | reg_908 |  |  |
| 909 | reg_909 |  |  |
| 910 | reg_910 |  |  |
| 911 | reg_911 |  |  |
| 912 | reg_912 |  |  |
| 913 | reg_913 |  |  |
| 914 | reg_914 |  |  |
| 915 | reg_915 |  |  |
| 916 | reg_916 |  |  |
| 917 | reg_917 |  |  |
| 918 | reg_918 |  |  |
| 919 | reg_919 |  |  |
| 920 | reg_920 |  |  |
| 921 | reg_921 |  |  |
| 922 | reg_922 |  |  |
| 923 | reg_923 |  |  |
| 924 | reg_924 |  |  |
| 925 | reg_925 |  |  |
| 926 | reg_926 |  |  |
| 927 | reg_927 |  |  |
| 928 | reg_928 |  |  |
| 929 | reg_929 |  |  |
| 930 | reg_930 |  |  |
| 931 | reg_931 |  |  |
| 932 | reg_932 |  |  |
| 933 | reg_933 |  |  |
| 934 | reg_934 |  |  |
| 935 | reg_935 |  |  |
| 936 | reg_936 |  |  |
| 937 | reg_937 |  |  |
| 938 | reg_938 |  |  |
| 939 | reg_939 |  |  |
| 940 | reg_940 |  |  |
| 941 | reg_941 |  |  |
| 942 | reg_942 |  |  |
| 943 | reg_943 |  |  |
| 944 | reg_944 |  |  |
| 945 | reg_945 |  |  |
| 946 | reg_946 |  |  |
| 947 | reg_947 |  |  |
| 948 | reg_948 |  |  |
| 949 | reg_949 |  |  |
| 950 | reg_950 |  |  |
| 951 | reg_951 |  |  |
| 952 | reg_952 |  |  |
| 953 | reg_953 |  |  |
| 954 | reg_954 |  |  |
| 955 | reg_955 |  |  |
| 956 | reg_956 |  |  |
| 957 | reg_957 |  |  |
| 958 | reg_958 |  |  |
| 959 | reg_959 |  |  |
| 960 | reg_960 |  |  |
| 961 | reg_961 |  |  |
| 962 | reg_962 |  |  |
| 963 | reg_963 |  |  |
| 964 | reg_964 |  |  |
| 965 | reg_965 |  |  |
| 966 | reg_966 |  |  |
| 967 | reg_967 |  |  |
| 968 | reg_968 |  |  |
| 969 | reg_969 |  |  |
| 970 | reg_970 |  |  |
| 971 | reg_971 |  |  |
| 972 | reg_972 |  |  |
| 973 | reg_973 |  |  |
| 974 | reg_974 |  |  |
| 975 | reg_975 |  |  |
| 976 | reg_976 |  |  |
| 977 | reg_977 |  |  |
| 978 | reg_978 |  |  |
| 979 | reg_979 |  |  |
| 980 | reg_980 |  |  |
| 981 | reg_981 |  |  |
| 982 | reg_982 |  |  |
| 983 | reg_983 |  |  |
| 984 | reg_984 |  |  |
| 985 | reg_985 |  |  |
| 986 | reg_986 |  |  |
| 987 | reg_987 |  |  |
| 988 | reg_988 |  |  |
| 989 | reg_989 |  |  |
| 990 | reg_990 |  |  |
| 991 | reg_991 |  |  |
| 992 | reg_992 |  |  |
| 999 | reg_999 |  |  |
| *Ninth group for Storage power* |  |  |  |
| 1000 | reg_1000 |  |  |
| 1001 | reg_1001 |  |  |
| 1002 | reg_1002 |  |  |
| 1003 | reg_1003 |  |  |
| 1004 | reg_1004 |  |  |
| 1005 | reg_1005 |  |  |
| 1006 | reg_1006 |  |  |
| 1007 | reg_1007 |  |  |
| 1008 | reg_1008 |  |  |
| 1009 | reg_1009 |  |  |
| 1010 | reg_1010 |  |  |
| 1011 | reg_1011 |  |  |
| 1012 | reg_1012 |  |  |
| 1013 | reg_1013 |  |  |
| 1014 | reg_1014 |  |  |
| 1015 | reg_1015 |  |  |
| 1016 | reg_1016 |  |  |
| 1017 | reg_1017 |  |  |
| 1018 | reg_1018 |  |  |
| 1019 | reg_1019 |  |  |
| 1020 | reg_1020 |  |  |
| 1021 | reg_1021 |  |  |
| 1022 | reg_1022 |  |  |
| 1023 | reg_1023 |  |  |
| 1024 | reg_1024 |  |  |
| 1025 | reg_1025 |  |  |
| 1026 | reg_1026 |  |  |
| 1027 | reg_1027 |  |  |
| 1028 | reg_1028 |  |  |
| 1029 | reg_1029 |  |  |
| 1030 | reg_1030 |  |  |
| 1031 | reg_1031 |  |  |
| 1032 | reg_1032 |  |  |
| 1033 | reg_1033 |  |  |
| 1034 | reg_1034 |  |  |
| 1035 | reg_1035 |  |  |
| 1036 | reg_1036 |  |  |
| 1037 | reg_1037 |  |  |
| 1038 | reg_1038 |  |  |
| 1039 | reg_1039 |  |  |
| 1040 | reg_1040 |  |  |
| 1041 | reg_1041 |  |  |
| 1042 | reg_1042 |  |  |
| 1043 | reg_1043 |  |  |
| 1044 | reg_1044 |  |  |
| 1045 | reg_1045 |  |  |
| 1046 | reg_1046 |  |  |
| 1047 | reg_1047 |  |  |
| 1048 | reg_1048 |  |  |
| 1049 | reg_1049 |  |  |
| 1050 | reg_1050 |  |  |
| 1051 | reg_1051 |  |  |
| 1052 | reg_1052 |  |  |
| 1053 | reg_1053 |  |  |
| 1054 | reg_1054 |  |  |
| 1055 | reg_1055 |  |  |
| 1056 | reg_1056 |  |  |
| 1057 | reg_1057 |  |  |
| 1058 | reg_1058 |  |  |
| 1059 | reg_1059 |  |  |
| 1060 | reg_1060 |  |  |
| 1061 | reg_1061 |  |  |
| 1062 | reg_1062 |  |  |
| 1063 | reg_1063 |  |  |
| 1064 | reg_1064 |  |  |
| 1065 | reg_1065 |  |  |
| 1066 | reg_1066 |  |  |
| 1067 | reg_1067 |  |  |
| 1068 | reg_1068 |  |  |
| 1069 | reg_1069 |  |  |
| 1070 | reg_1070 |  |  |
| 1071 | reg_1071 |  |  |
| 1072 | reg_1072 |  |  |
| 1073 | reg_1073 |  |  |
| 1074 | reg_1074 |  |  |
| 1075 | reg_1075 |  |  |
| 1076 | reg_1076 |  |  |
| 1077 | reg_1077 |  |  |
| 1078 | reg_1078 |  |  |
| 1079 | reg_1079 |  |  |
| 1080 | reg_1080 |  |  |
| 1081 | reg_1081 |  |  |
| *BMS Infomation* |  |  |  |
| 1082 | reg_1082 |  |  |
| 1083 | reg_1083 |  |  |
| 1084 | reg_1084 |  |  |
| 1085 | reg_1085 |  |  |
| 1086 | reg_1086 |  |  |
| 1087 | reg_1087 |  |  |
| 1088 | reg_1088 |  |  |
| 1089 | reg_1089 |  |  |
| 1090 | reg_1090 |  |  |
| 1091 | reg_1091 |  |  |
| 1092 | reg_1092 |  |  |
| 1093 | reg_1093 |  |  |
| 1094 | reg_1094 |  |  |
| 1095 | reg_1095 |  |  |
| 1096 | reg_1096 |  |  |
| 1097 | reg_1097 |  |  |
| 1098 | reg_1098 |  |  |
| 1099 | reg_1099 |  |  |
| 1100 | reg_1100 |  |  |
| 1101 | reg_1101 |  |  |
| 1102 | reg_1102 |  |  |
| 1103 | reg_1103 |  |  |
| 1104 | reg_1104 |  |  |
| 1105 | reg_1105 |  |  |
| 1106 | reg_1106 |  |  |
| 1107 | reg_1107 |  |  |
| 1108 | reg_1108 |  |  |
| 1109 | reg_1109 |  |  |
| 1110 | reg_1110 |  |  |
| 1111 | reg_1111 |  |  |
| 1112 | reg_1112 |  |  |
| 1113 | reg_1113 |  |  |
| 1114 | reg_1114 |  |  |
| 1115 | reg_1115 |  |  |
| 1116 | reg_1116 |  |  |
| 1117 | reg_1117 |  |  |
| 1118 | reg_1118 |  |  |
| 1119 | reg_1119 |  |  |
| 1120 | reg_1120 |  |  |
| 1121 | reg_1121 |  |  |
| 1122 | reg_1122 |  |  |
| 1123 | reg_1123 |  |  |
| 1124 | reg_1124 |  |  |
| *Ninth group reserved for storage power* |  |  |  |
| 1125 | reg_1125 |  |  |
| 1126 | reg_1126 |  |  |
| 1127 | reg_1127 |  |  |
| 1128 | reg_1128 |  |  |
| 1129 | reg_1129 |  |  |
| 1130 | reg_1130 |  |  |
| 1131 | reg_1131 |  |  |
| 1132 | reg_1132 |  |  |
| 1133 | reg_1133 |  |  |
| 1134 | reg_1134 |  |  |
| 1135 | reg_1135 |  |  |
| 1136 | reg_1136 |  |  |
| 1137 | reg_1137 |  |  |
| 1138 | reg_1138 |  |  |
| 1139 | reg_1139 |  |  |
| 1140 | reg_1140 |  |  |
| 1141 | reg_1141 |  |  |
| 1142 | reg_1142 |  |  |
| 1143 | reg_1143 |  |  |
| 1144 | reg_1144 |  |  |
| 1145 | reg_1145 |  |  |
| 1146 | reg_1146 |  |  |
| 1147 | reg_1147 |  |  |
| 1148 | reg_1148 |  |  |
| 1149 | reg_1149 |  |  |
| 1150 | reg_1150 |  |  |
| 1151 | reg_1151 |  |  |
| 1152 | reg_1152 |  |  |
| 1153 | reg_1153 |  |  |
| 1154 | reg_1154 |  |  |
| 1155 | reg_1155 |  |  |
| 1156 | reg_1156 |  |  |
| 1157 | reg_1157 |  |  |
| 1158 | reg_1158 |  |  |
| 1159 | reg_1159 |  |  |
| 1160 | reg_1160 |  |  |
| 1161 | reg_1161 |  |  |
| 1162 | reg_1162 |  |  |
| 1163 | reg_1163 |  |  |
| 1164 | reg_1164 |  |  |
| 1165 | reg_1165 |  |  |
| 1166 | reg_1166 |  |  |
| 1167 | reg_1167 |  |  |
| 1168 | reg_1168 |  |  |
| 1169 | reg_1169 |  |  |
| 1170 | reg_1170 |  |  |
| 1199 | reg_1199 |  |  |
| 1200 | reg_1200 |  |  |
| 1201 | reg_1201 |  |  |
| 1202 | reg_1202 |  |  |
| 1203 | reg_1203 |  |  |
| 1204 | reg_1204 |  |  |
| 1205 | reg_1205 |  |  |
| 1206 | reg_1206 |  |  |
| 1207 | reg_1207 |  |  |
| 1208 | reg_1208 |  |  |
| 1209 | reg_1209 |  |  |
| 1210 | reg_1210 |  |  |
| 1211 | reg_1211 |  |  |
| 1212 | reg_1212 |  |  |
| 1213 | reg_1213 |  |  |
| 1214 | reg_1214 |  |  |
| 1215 | reg_1215 |  |  |
| 1216 | reg_1216 |  |  |
| 1217 | reg_1217 |  |  |
| 1218 | reg_1218 |  |  |
| 1248 | reg_1248 |  |  |
| 1249 | reg_1249 |  |  |
| *thirteen group for Storage power’s SPA* |  |  |  |
| 2000 | reg_2000 |  |  |
| 2035 | reg_2035 |  |  |
| 2036 | reg_2036 |  |  |
| 2037 | reg_2037 |  |  |
| 2038 | reg_2038 |  |  |
| 2039 | reg_2039 |  |  |
| 2040 | reg_2040 |  |  |
| 2041 | reg_2041 |  |  |
| 2053 | reg_2053 |  |  |
| 2054 | reg_2054 |  |  |
| 2055 | reg_2055 |  |  |
| 2056 | reg_2056 |  |  |
| 2057 | reg_2057 |  |  |
| 2058 | reg_2058 |  |  |
| 2093 | reg_2093 |  |  |
| 2094 | reg_2094 |  |  |
| 2095 | reg_2095 |  |  |
| 2096 | reg_2096 |  |  |
| 2097 | reg_2097 |  |  |
| 2098 | reg_2098 |  |  |
| 2099 | reg_2099 |  |  |
| 2100 | reg_2100 |  |  |
| 2101 | reg_2101 |  |  |
| 2102 | reg_2102 |  |  |
| 2103 | reg_2103 |  |  |
| 2104 | reg_2104 |  |  |
| 2105 | reg_2105 |  |  |
| 2106 | reg_2106 |  |  |
| 2107 | reg_2107 |  |  |
| 2108 | reg_2108 |  |  |
| 2109 | reg_2109 |  |  |
| 2110 | reg_2110 |  |  |
| 2111 | reg_2111 |  |  |
| 2112 | reg_2112 |  |  |
| 2113 | reg_2113 |  |  |
| 2114 | reg_2114 |  |  |
| 2115 | reg_2115 |  |  |
| 2116 | reg_2116 |  |  |
| 2117 | reg_2117 |  |  |
| 2118 | reg_2118 |  |  |
| 2119 | reg_2119 |  |  |
| 2120 | reg_2120 |  |  |
| 2124 | reg_2124 |  |  |
| *Use for TL-X and TL-XH* |  |  |  |
| 3000 | reg_3000 |  |  |
| 3001 | reg_3001 |  |  |
| 3002 | reg_3002 |  |  |
| 3003 | reg_3003 |  |  |
| 3004 | reg_3004 |  |  |
| 3005 | reg_3005 |  |  |
| 3006 | reg_3006 |  |  |
| 3007 | reg_3007 |  |  |
| 3008 | reg_3008 |  |  |
| 3009 | reg_3009 |  |  |
| 3010 | reg_3010 |  |  |
| 3011 | reg_3011 |  |  |
| 3012 | reg_3012 |  |  |
| 3013 | reg_3013 |  |  |
| 3014 | reg_3014 |  |  |
| 3015 | reg_3015 |  |  |
| 3016 | reg_3016 |  |  |
| 3017 | reg_3017 |  |  |
| 3018 | reg_3018 |  |  |
| 3019 | reg_3019 |  |  |
| 3020 | reg_3020 |  |  |
| 3021 | reg_3021 |  |  |
| 3022 | reg_3022 |  |  |
| 3023 | reg_3023 |  |  |
| 3024 | reg_3024 |  |  |
| 3025 | reg_3025 |  |  |
| 3026 | reg_3026 |  |  |
| 3027 | reg_3027 |  |  |
| 3028 | reg_3028 |  |  |
| 3029 | reg_3029 |  |  |
| 3030 | reg_3030 |  |  |
| 3031 | reg_3031 |  |  |
| 3032 | reg_3032 |  |  |
| 3033 | reg_3033 |  |  |
| 3034 | reg_3034 |  |  |
| 3035 | reg_3035 |  |  |
| 3036 | reg_3036 |  |  |
| 3037 | reg_3037 |  |  |
| 3038 | reg_3038 |  |  |
| 3039 | reg_3039 |  |  |
| 3040 | reg_3040 |  |  |
| 3041 | reg_3041 |  |  |
| 3042 | reg_3042 |  |  |
| 3043 | reg_3043 |  |  |
| 3044 | reg_3044 |  |  |
| 3045 | reg_3045 |  |  |
| 3046 | reg_3046 |  |  |
| 3047 | reg_3047 |  |  |
| 3048 | reg_3048 |  |  |
| 3049 | reg_3049 |  |  |
| 3050 | reg_3050 |  |  |
| 3051 | reg_3051 |  |  |
| 3052 | reg_3052 |  |  |
| 3053 | reg_3053 |  |  |
| 3054 | reg_3054 |  |  |
| 3055 | reg_3055 |  |  |
| 3056 | reg_3056 |  |  |
| 3057 | reg_3057 |  |  |
| 3058 | reg_3058 |  |  |
| 3059 | reg_3059 |  |  |
| 3060 | reg_3060 |  |  |
| 3061 | reg_3061 |  |  |
| 3062 | reg_3062 |  |  |
| 3063 | reg_3063 |  |  |
| 3064 | reg_3064 |  |  |
| 3065 | reg_3065 |  |  |
| 3066 | reg_3066 |  |  |
| 3067 | reg_3067 |  |  |
| 3068 | reg_3068 |  |  |
| 3069 | reg_3069 |  |  |
| 3070 | reg_3070 |  |  |
| 3071 | reg_3071 |  |  |
| 3072 | reg_3072 |  |  |
| 3073 | reg_3073 |  |  |
| 3074 | reg_3074 |  |  |
| 3075 | reg_3075 |  |  |
| 3076 | reg_3076 |  |  |
| 3077 | reg_3077 |  |  |
| 3078 | reg_3078 |  |  |
| 3079 | reg_3079 |  |  |
| 3080 | reg_3080 |  |  |
| 3081 | reg_3081 |  |  |
| 3082 | reg_3082 |  |  |
| 3083 | reg_3083 |  |  |
| 3084 | reg_3084 |  |  |
| 3085 | reg_3085 |  |  |
| 3086 | reg_3086 |  |  |
| 3087 | reg_3087 |  |  |
| 3088 | reg_3088 |  |  |
| 3089 | reg_3089 |  |  |
| 3090 | reg_3090 |  |  |
| 3091 | reg_3091 |  |  |
| 3092 | reg_3092 |  |  |
| 3093 | reg_3093 |  |  |
| 3094 | reg_3094 |  |  |
| 3095 | reg_3095 |  |  |
| 3096 | reg_3096 |  |  |
| 3097 | reg_3097 |  |  |
| 3098 | reg_3098 |  |  |
| 3099 | reg_3099 |  |  |
| 3100 | reg_3100 |  |  |
| 3101 | reg_3101 |  |  |
| 3102 | reg_3102 |  |  |
| 3103 | reg_3103 |  |  |
| 3104 | reg_3104 |  |  |
| 3105 | reg_3105 |  |  |
| 3106 | reg_3106 |  |  |
| 3107 | reg_3107 |  |  |
| 3108 | reg_3108 |  |  |
| 3109 | reg_3109 |  |  |
| 3110 | reg_3110 |  |  |
| 3111 | reg_3111 |  |  |
| 3112 | reg_3112 |  |  |
| 3113 | reg_3113 |  |  |
| 3114 | reg_3114 |  |  |
| 3115 | reg_3115 |  |  |
| 3116 | reg_3116 |  |  |
| 3117 | reg_3117 |  |  |
| 3118 | reg_3118 |  |  |
| 3119 | reg_3119 |  |  |
| 3120 | reg_3120 |  |  |
| 3121 | reg_3121 |  |  |
| 3122 | reg_3122 |  |  |
| 3123 | reg_3123 |  |  |
| 3124 | reg_3124 |  |  |
| 3125 | reg_3125 |  |  |
| 3126 | reg_3126 |  |  |
| 3127 | reg_3127 |  |  |
| 3128 | reg_3128 |  |  |
| 3129 | reg_3129 |  |  |
| 3130 | reg_3130 |  |  |
| 3131 | reg_3131 |  |  |
| 3132 | reg_3132 |  |  |
| 3133 | reg_3133 |  |  |
| 3134 | reg_3134 |  |  |
| 3135 | reg_3135 |  |  |
| 3136 | reg_3136 |  |  |
| 3137 | reg_3137 |  |  |
| 3138 | reg_3138 |  |  |
| 3139 | reg_3139 |  |  |
| 3140 | reg_3140 |  |  |
| 3141 | reg_3141 |  |  |
| 3142 | reg_3142 |  |  |
| 3143 | reg_3143 |  |  |
| 3144 | reg_3144 |  |  |
| 3145 | reg_3145 |  |  |
| 3146 | reg_3146 |  |  |
| 3147 | reg_3147 |  |  |
| 3148 | reg_3148 |  |  |
| 3149 | reg_3149 |  |  |
| 3150 | reg_3150 |  |  |
| 3151 | reg_3151 |  |  |
| 3152 | reg_3152 |  |  |
| 3153 | reg_3153 |  |  |
| 3154 | reg_3154 |  |  |
| 3155 | reg_3155 |  |  |
| 3156 | reg_3156 |  |  |
| 3157 | reg_3157 |  |  |
| 3158 | reg_3158 |  |  |
| 3159 | reg_3159 |  |  |
| 3160 | reg_3160 |  |  |
| 3161 | reg_3161 |  |  |
| 3162 | reg_3162 |  |  |
| 3163 | reg_3163 |  |  |
| 3164 | reg_3164 |  |  |
| 3165 | reg_3165 |  |  |
| 3166 | reg_3166 |  |  |
| 3167 | reg_3167 |  |  |
| 3168 | reg_3168 |  |  |
| 3169 | reg_3169 |  |  |
| 3170 | reg_3170 |  |  |
| 3171 | reg_3171 |  |  |
| 3172 | reg_3172 |  |  |
| 3173 | reg_3173 |  |  |
| 3174 | reg_3174 |  |  |
| 3175 | reg_3175 |  |  |
| 3176 | reg_3176 |  |  |
| 3177 | reg_3177 |  |  |
| 3178 | reg_3178 |  |  |
| 3179 | reg_3179 |  |  |
| 3180 | reg_3180 |  |  |
| 3181 | reg_3181 |  |  |
| 3182 | reg_3182 |  |  |
| 3183 | reg_3183 |  |  |
| 3184 | reg_3184 |  |  |
| 3185 | reg_3185 |  |  |
| 3186 | reg_3186 |  |  |
| 3187 | reg_3187 |  |  |
| 3188 | reg_3188 |  |  |
| 3189 | reg_3189 |  |  |
| 3190 | reg_3190 |  |  |
| 3191 | reg_3191 |  |  |
| 3192 | reg_3192 |  |  |
| 3193 | reg_3193 |  |  |
| 3194 | reg_3194 |  |  |
| 3195 | reg_3195 |  |  |
| 3196 | reg_3196 |  |  |
| 3197 | reg_3197 |  |  |
| 3198 | reg_3198 |  |  |
| 3199 | reg_3199 |  |  |
| 3200 | reg_3200 |  |  |
| 3201 | reg_3201 |  |  |
| 3202 | reg_3202 |  |  |
| 3203 | reg_3203 |  |  |
| 3204 | reg_3204 |  |  |
| 3205 | reg_3205 |  |  |
| 3206 | reg_3206 |  |  |
| 3207 | reg_3207 |  |  |
| 3208 | reg_3208 |  |  |
| 3209 | reg_3209 |  |  |
| 3210 | reg_3210 |  |  |
| 3211 | reg_3211 |  |  |
| 3212 | reg_3212 |  |  |
| 3213 | reg_3213 |  |  |
| 3214 | reg_3214 |  |  |
| 3215 | reg_3215 |  |  |
| 3216 | reg_3216 |  |  |
| 3217 | reg_3217 |  |  |
| 3218 | reg_3218 |  |  |
| 3219 | reg_3219 |  |  |
| 3220 | reg_3220 |  |  |
| 3221 | reg_3221 |  |  |
| 3222 | reg_3222 |  |  |
| 3223 | reg_3223 |  |  |
| 3224 | reg_3224 |  |  |
| 3225 | reg_3225 |  |  |
| 3226 | reg_3226 |  |  |
| 3227 | reg_3227 |  |  |
| 3228 | reg_3228 |  |  |
| 3229 | reg_3229 |  |  |
| 3230 | reg_3230 |  |  |
| 3231 | reg_3231 |  |  |
| 3232 | reg_3232 |  |  |
| 3233 | reg_3233 |  |  |
| 3234 | reg_3234 |  |  |
| 3235 | reg_3235 |  |  |
| 3236 | reg_3236 |  |  |
| 3237 | reg_3237 |  |  |
| 3238 | reg_3238 |  |  |
| 3239 | reg_3239 |  |  |
| 3240 | reg_3240 |  |  |
| 3241 | reg_3241 |  |  |
| 3242 | reg_3242 |  |  |
| 3243 | reg_3243 |  |  |
| 3244 | reg_3244 |  |  |
| 3245 | reg_3245 |  |  |
| 3246 | reg_3246 |  |  |
| 3247 | reg_3247 |  |  |
| 3248 | reg_3248 |  |  |
| 3249 | reg_3249 |  |  |
| 3250 | reg_3250 |  |  |
| 3251 | reg_3251 |  |  |
| 3252 | reg_3252 |  |  |
| 3253 | reg_3253 |  |  |
| 3254 | reg_3254 |  |  |
| 3255 | reg_3255 |  |  |
| 3256 | reg_3256 |  |  |
| 3257 | reg_3257 |  |  |
| 3258 | reg_3258 |  |  |
| 3259 | reg_3259 |  |  |
| 3260 | reg_3260 |  |  |
| 3261 | reg_3261 |  |  |
| 3262 | reg_3262 |  |  |
| 3263 | reg_3263 |  |  |
| 3264 | reg_3264 |  |  |
| 3265 | reg_3265 |  |  |
| 3266 | reg_3266 |  |  |
| 3267 | reg_3267 |  |  |
| 3268 | reg_3268 |  |  |
| 3269 | reg_3269 |  |  |
| 3270 | reg_3270 |  |  |
| 3277 | reg_3277 |  |  |
| 3278 | reg_3278 |  |  |
| 3279 | reg_3279 |  |  |
| 3280 | reg_3280 |  |  |
| 3281 | reg_3281 |  |  |
| 3282 | reg_3282 |  |  |
| 3283 | reg_3283 |  |  |
| 3284 | reg_3284 |  |  |
| 3285 | reg_3285 |  |  |
| 3286 | reg_3286 |  |  |
| 3287 | reg_3287 |  |  |
| 3288 | reg_3288 |  |  |
| 3289 | reg_3289 |  |  |
| 3290 | reg_3290 |  |  |
| 3291 | reg_3291 |  |  |
| 3292 | reg_3292 |  |  |
| 3293 | reg_3293 |  |  |
| 3294 | reg_3294 |  |  |
| 3295 | reg_3295 |  |  |
| 3296 | reg_3296 |  |  |
| 3297 | reg_3297 |  |  |
| 3298 | reg_3298 |  |  |
| 3299 | reg_3299 |  |  |
| 3300 | reg_3300 |  |  |
| 3301 | reg_3301 |  |  |
| 3302 | reg_3302 |  |  |
| 3303 | reg_3303 |  |  |
| 3304 | reg_3304 |  |  |
| 3305 | reg_3305 |  |  |
| 3306 | reg_3306 |  |  |
| 3307 | reg_3307 |  |  |
| 3308 | reg_3308 |  |  |
| 3309 | reg_3309 |  |  |
| 3310 | reg_3310 |  |  |
| 3311 | reg_3311 |  |  |
| 3312 | reg_3312 |  |  |
| 3313 | reg_3313 |  |  |
| 3314 | reg_3314 |  |  |
| 3315 | reg_3315 |  |  |
| 3316 | reg_3316 |  |  |
| 3317 | reg_3317 |  |  |
| 3318 | reg_3318 |  |  |
| 3319 | reg_3319 |  |  |
| 3320 | reg_3320 |  |  |
| 3321 | reg_3321 |  |  |
| 3322 | reg_3322 |  |  |
| 3323 | reg_3323 |  |  |
| 3324 | reg_3324 |  |  |
| 3342 | reg_3342 |  |  |
| 3343 | reg_3343 |  |  |
| 3410 | reg_3410 |  |  |
| 3411 | reg_3411 |  |  |
| 3412 | reg_3412 |  |  |
| 3413 | reg_3413 |  |  |
| 3414 | reg_3414 |  |  |
| 3415 | reg_3415 |  |  |
| 3416 | reg_3416 |  |  |
| 3417 | reg_3417 |  |  |
| *Battery module information (support up to 64 parallel BDC)（Special for APX）* |  |  |  |
| 5080 | reg_5080 |  |  |
| 5081 | reg_5081 |  |  |
| 5082 | reg_5082 |  |  |
| 5083 | reg_5083 |  |  |
| 5084 | reg_5084 |  |  |
| 5085 | reg_5085 |  |  |
| 5086 | reg_5086 |  |  |
| 5087 | reg_5087 |  |  |
| 5088 | reg_5088 |  |  |
| 5089 | reg_5089 |  |  |
| 5090 | reg_5090 |  |  |
| 5091 | reg_5091 |  |  |
| 5092 | reg_5092 |  |  |
| 5093 | reg_5093 |  |  |
| 5094 | reg_5094 |  |  |
| 5095 | reg_5095 |  |  |
| 5096 | reg_5096 |  |  |
| 5097 | reg_5097 |  |  |
| 5098 | reg_5098 |  |  |
| 5099 | reg_5099 |  |  |
| 5100 | reg_5100 |  |  |
| 5101 | reg_5101 |  |  |
| 5102 | reg_5102 |  |  |
| 5103 | reg_5103 |  |  |
| 5104 | reg_5104 |  |  |
| 5105 | reg_5105 |  |  |
| 5106 | reg_5106 |  |  |
| 5107 | reg_5107 |  |  |
| 5108 | reg_5108 |  |  |
| 5109 | reg_5109 |  |  |
| 5110 | reg_5110 |  |  |
| 8000 | reg_8000 |  |  |
| 8001 | reg_8001 |  |  |
| 8002 | reg_8002 |  |  |
| 8003 | reg_8003 |  |  |
| 8004 | reg_8004 |  |  |
| 8005 | reg_8005 |  |  |
| 8006 | reg_8006 |  |  |
| 8007 | reg_8007 |  |  |
| 8008 | reg_8008 |  |  |
| 8009 | reg_8009 |  |  |
| 8010 | reg_8010 |  |  |
| 8011 | reg_8011 |  |  |
| 8012 | reg_8012 |  |  |
| 8013 | reg_8013 |  |  |
| 8014 | reg_8014 |  |  |
| 8015 | reg_8015 |  |  |
| 8016 | reg_8016 |  |  |
| 8017 | reg_8017 |  |  |
| 8015 | reg_8015 |  |  |
| 8016 | reg_8016 |  |  |
| 8017 | reg_8017 |  |  |
| 8018 | reg_8018 |  |  |
| 8019 | reg_8019 |  |  |
| 8020 | reg_8020 |  |  |
| 8021 | reg_8021 |  |  |
| 8022 | reg_8022 |  |  |
| 8023 | reg_8023 |  |  |
| 8024 | reg_8024 |  |  |
| 8028 | reg_8028 |  |  |
| 8029 | reg_8029 |  |  |
| 8030 | reg_8030 |  |  |
| 8031 | reg_8031 |  |  |
| 8032 | reg_8032 |  |  |
| 8033 | reg_8033 |  |  |
| 8034 | reg_8034 |  |  |
| 8035 | reg_8035 |  |  |
| 8036 | reg_8036 |  |  |
| 8037 | reg_8037 |  |  |
| 8038 | reg_8038 |  |  |
| 8039 | reg_8039 |  |  |
| 8040 | reg_8040 |  |  |
| 8041 | reg_8041 |  |  |
| 8042 | reg_8042 |  |  |
| 8043 | reg_8043 |  |  |
| 8044 | reg_8044 |  |  |
| 8045 | reg_8045 |  |  |
| 8046 | reg_8046 |  |  |
| 8047 | reg_8047 |  |  |
| 8048 | reg_8048 |  |  |
| 8049 | reg_8049 |  |  |
| 8050 | reg_8050 |  |  |
| 8051 | reg_8051 |  |  |
| 8052 | reg_8052 |  |  |
| 8053 | reg_8053 |  |  |
| 8054 | reg_8054 |  |  |
| 8055 | reg_8055 |  |  |
| 8056 | reg_8056 |  |  |
| 8057 | reg_8057 |  |  |
| 8058 | reg_8058 |  |  |
| 8059 | reg_8059 |  |  |
| 8060 | reg_8060 |  |  |
| 8061 | reg_8061 |  |  |
| 8062 | reg_8062 |  |  |
| 8063 | reg_8063 |  |  |
| 8064 | reg_8064 |  |  |
| 8065 | reg_8065 |  |  |
| 8066 | reg_8066 |  |  |
| 8067 | reg_8067 |  |  |
| 8068 | reg_8068 |  |  |
| 8069 | reg_8069 |  |  |
| 8070 | reg_8070 |  |  |
| 8071 | reg_8071 |  |  |
| 8072 | reg_8072 |  |  |
| 8073 | reg_8073 |  |  |
| 8074 | reg_8074 |  |  |
| 8075 | reg_8075 |  |  |
| 8076 | reg_8076 |  |  |
| 8077 | reg_8077 |  |  |
| 8078 | reg_8078 |  |  |
| 8079 | reg_8079 |  |  |
| 8080 | reg_8080 |  |  |
| 8081 | reg_8081 |  |  |
| 8082 | reg_8082 |  |  |
| 8083 | reg_8083 |  |  |
| 8084 | reg_8084 |  |  |
| 8085 | reg_8085 |  |  |
| 8086 | reg_8086 |  |  |
| 8087 | reg_8087 |  |  |
| 8088 | reg_8088 |  |  |
| 8089 | reg_8089 |  |  |
| 8090 | reg_8090 |  |  |
| 8091 | reg_8091 |  |  |
| 8092 | reg_8092 |  |  |
| 8093 | reg_8093 |  |  |
| 8094 | reg_8094 |  |  |
| 8095 | reg_8095 |  |  |
| 8096 | reg_8096 |  |  |
| 8097 | reg_8097 |  |  |
| 8098 | reg_8098 |  |  |
| 8099 | reg_8099 |  |  |
| 8100 | reg_8100 |  |  |
| 8101 | reg_8101 |  |  |
| 8102 | reg_8102 |  |  |
| 8103 | reg_8103 |  |  |
| 8104 | reg_8104 |  |  |
| 8105 | reg_8105 |  |  |
| 8106 | reg_8106 |  |  |
| 8107 | reg_8107 |  |  |
| 8108 | reg_8108 |  |  |
| 8109 | reg_8109 |  |  |
| 8110 | reg_8110 |  |  |
| 1 | reg_1 |  |  |
| 2 | reg_2 |  |  |
| 3 | reg_3 |  |  |
| 4 | reg_4 |  |  |
| 5 | reg_5 |  |  |
| 6 | reg_6 |  |  |
| 7 | reg_7 |  |  |
| 8 | reg_8 |  |  |
| 9 | reg_9 |  |  |
| 10 | reg_10 |  |  |
| 11 | reg_11 |  |  |
| 12 | reg_12 |  |  |
| 13 | reg_13 |  |  |
| 14 | reg_14 |  |  |
| 15 | reg_15 |  |  |
| 16 | reg_16 |  |  |
| 17 | reg_17 |  |  |
| 38 | reg_38 |  |  |
| 39 | reg_39 |  |  |
