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
| TL-X / TL-XH (MIN type) | 0-124, 3000-3124, 3125-3249, 3250-3374 |
| TL3-X (MAX / MID / MAC) | 0-124, 3000-3124, 3125-3249 |
| SPA / SPH (hybrid) | 0-124, 1000-1124, 2000-2124, 3000-3124, 3125-3249 |
| WIT TL3 | 0-124, 875-999, 3000-3124, 3125-3249, 8000-8139 |

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
| 239 | --- | --- | --- | --- |
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
| 1036 | --- | --- | --- | --- |
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
| 1089 | --- | --- | --- | --- |
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
| 1109 | --- | --- | --- | --- |
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
| 3039 | --- | --- | --- | --- |
| 3040 | Time 2(xh) | Time period 2: [start time ~ end time], [charge / discharge], [disable / enable] 3040 enable, charge and discharge, start time, 3041 end time |  |
| 3041 | --- | --- | --- | --- |
| 3042 | Time 3(xh) | With Time1 |  |
| 3043 | --- | --- | --- | --- |
| 3044 | Time 4(xh) | With Time1 |  |
| 3045 | --- | --- | --- | --- |
| 3046 | INVHWVer sion | US inverter hardware version |  |
| 3047 | BatFirstPo werRate | Charge Power Rate when Bat First |  |
| 3048 | wBatFirst stop SOC | Stop Charge soc when Bat First |  |
| 3049 | AcChargeE nable | AcChargeEnable |  |
| 3050 | Time 5(xh) | With Time1 |  |
| 3051 | --- | --- | --- | --- |
| 3052 | Time 6(xh) | With Time1 |  |
| 3053 | --- | --- | --- | --- |
| 3054 | Time 7(xh) | With Time1 |  |
| 3055 | --- | --- | --- | --- |
| 3056 | Time 8(xh) | With Time1 |  |
| 3057 | --- | --- | --- | --- |
| 3058 | Time 9(xh) | With Time1 |  |
| 3059 | --- | --- | --- | --- |
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
| 3097 | --- | --- | --- | --- |
| 3098 | DTC | DTC |  |
| 3099 | FW Code | DSP software code |  |
| 3100 | --- | --- | --- | --- |
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
| 3117 | --- | --- | --- | --- |
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
| 3130 | --- | --- | --- | --- |
| 3201 | SpecialDay 1 | SpecialDay1（month,Day） |  |
| 3202 | SpecialDay 1_Time1 | Start time |  |
| 3203 | --- | --- | --- | --- |
| 3220 | SpecialDay 2 | SpecialDay2（month,Day） |  |
| 3221 | SpecialDay 2_Time1 | Start time |  |
| 3222 | --- | --- | --- | --- |
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
| 5409 | --- | --- | --- | --- |
| 5410 | BatDSPVersio n |  |  |
| 5411 | BatMCUCode |  |  |
| 5412 | --- | --- | --- | --- |
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
| 8567 | --- | --- | --- | --- |
| 8568 | --- | --- | --- | --- |
| 8569 | --- | --- | --- | --- |
| 8570 | --- | --- | --- | --- |
| 8571 | --- | --- | --- | --- |
| 8572 | --- | --- | --- | --- |
| 8573 | --- | --- | --- | --- |
| 8574 | --- | --- | --- | --- |

---

## Input Registers

> All input registers are read-only (R) unless noted. Unit values are resolution (e.g. 0.1V means 1 LSB = 0.1 V).

| Address | Name | Description | Unit | Note |
| --- | --- | --- | --- | --- |
| *First group (0–124)* | | | | |
| 0 | Inverter Status | Inverter run state | — | 0=Waiting, 1=Normal, 3=Fault |
| 1 | Ppv H | Input power (high) | 0.1W | 32-bit pair with reg 2 |
| 2 | Ppv L | Input power (low) | 0.1W | Combined: total PV input power |
| 3 | Vpv1 | PV1 voltage | 0.1V | |
| 4 | PV1Curr | PV1 input current | 0.1A | |
| 5 | Ppv1 H | PV1 input power (high) | 0.1W | 32-bit pair with reg 6 |
| 6 | Ppv1 L | PV1 input power (low) | 0.1W | |
| 7 | Vpv2 | PV2 voltage | 0.1V | |
| 8 | PV2Curr | PV2 input current | 0.1A | |
| 9 | Ppv2 H | PV2 input power (high) | 0.1W | 32-bit pair with reg 10 |
| 10 | Ppv2 L | PV2 input power (low) | 0.1W | |
| 11 | Vpv3 | PV3 voltage | 0.1V | |
| 12 | PV3Curr | PV3 input current | 0.1A | |
| 13 | Ppv3 H | PV3 input power (high) | 0.1W | 32-bit pair with reg 14 |
| 14 | Ppv3 L | PV3 input power (low) | 0.1W | |
| 15 | Vpv4 | PV4 voltage | 0.1V | |
| 16 | PV4Curr | PV4 input current | 0.1A | |
| 17 | Ppv4 H | PV4 input power (high) | 0.1W | 32-bit pair with reg 18 |
| 18 | Ppv4 L | PV4 input power (low) | 0.1W | |
| 19 | Vpv5 | PV5 voltage | 0.1V | |
| 20 | PV5Curr | PV5 input current | 0.1A | |
| 21 | Ppv5 H | PV5 input power (high) | 0.1W | 32-bit pair with reg 22 |
| 22 | Ppv5 L | PV5 input power (low) | 0.1W | |
| 23 | Vpv6 | PV6 voltage | 0.1V | |
| 24 | PV6Curr | PV6 input current | 0.1A | |
| 25 | Ppv6 H | PV6 input power (high) | 0.1W | 32-bit pair with reg 26 |
| 26 | Ppv6 L | PV6 input power (low) | 0.1W | |
| 27 | Vpv7 | PV7 voltage | 0.1V | |
| 28 | PV7Curr | PV7 input current | 0.1A | |
| 29 | Ppv7 H | PV7 input power (high) | 0.1W | 32-bit pair with reg 30 |
| 30 | Ppv7 L | PV7 input power (low) | 0.1W | |
| 31 | Vpv8 | PV8 voltage | 0.1V | |
| 32 | PV8Curr | PV8 input current | 0.1A | |
| 33 | Ppv8 H | PV8 input power (high) | 0.1W | 32-bit pair with reg 34 |
| 34 | Ppv8 L | PV8 input power (low) | 0.1W | |
| 35 | Pac H | AC output power (high) | 0.1W | 32-bit pair with reg 36 |
| 36 | Pac L | AC output power (low) | 0.1W | |
| 37 | Fac | Grid frequency | 0.01Hz | |
| 38 | Vac1 | R-phase / single-phase grid voltage | 0.1V | |
| 39 | Iac1 | R-phase / single-phase grid output current | 0.1A | |
| 40 | Pac1 H | R-phase grid output apparent power (high) | 0.1VA | 32-bit pair with reg 41 |
| 41 | Pac1 L | R-phase grid output apparent power (low) | 0.1VA | |
| 42 | Vac2 | S-phase grid voltage | 0.1V | Three-phase only |
| 43 | Iac2 | S-phase grid output current | 0.1A | Three-phase only |
| 44 | Pac2 H | S-phase grid output power (high) | 0.1VA | 32-bit pair with reg 45 |
| 45 | Pac2 L | S-phase grid output power (low) | 0.1VA | |
| 46 | Vac3 | T-phase grid voltage | 0.1V | Three-phase only |
| 47 | Iac3 | T-phase grid output current | 0.1A | Three-phase only |
| 48 | Pac3 H | T-phase grid output power (high) | 0.1VA | 32-bit pair with reg 49 |
| 49 | Pac3 L | T-phase grid output power (low) | 0.1VA | |
| 50 | Vac_RS | R-S line voltage | 0.1V | Three-phase only |
| 51 | Vac_ST | S-T line voltage | 0.1V | Three-phase only |
| 52 | Vac_TR | T-R line voltage | 0.1V | Three-phase only |
| 53 | Eac today H | Today generate energy (high) | 0.1kWh | 32-bit pair with reg 54 |
| 54 | Eac today L | Today generate energy (low) | 0.1kWh | |
| 55 | Eac total H | Total generate energy (high) | 0.1kWh | 32-bit pair with reg 56 |
| 56 | Eac total L | Total generate energy (low) | 0.1kWh | |
| 57 | Time total H | Work time total (high) | 0.5s | 32-bit pair with reg 58 |
| 58 | Time total L | Work time total (low) | 0.5s | |
| 59 | Epv1_today H | PV1 energy today (high) | 0.1kWh | 32-bit pair with reg 60 |
| 60 | Epv1_today L | PV1 energy today (low) | 0.1kWh | |
| 61 | Epv1_total H | PV1 energy total (high) | 0.1kWh | 32-bit pair with reg 62 |
| 62 | Epv1_total L | PV1 energy total (low) | 0.1kWh | |
| 63 | Epv2_today H | PV2 energy today (high) | 0.1kWh | 32-bit pair with reg 64 |
| 64 | Epv2_today L | PV2 energy today (low) | 0.1kWh | |
| 65 | Epv2_total H | PV2 energy total (high) | 0.1kWh | 32-bit pair with reg 66 |
| 66 | Epv2_total L | PV2 energy total (low) | 0.1kWh | |
| 67 | Epv3_today H | PV3 energy today (high) | 0.1kWh | 32-bit pair with reg 68 |
| 68 | Epv3_today L | PV3 energy today (low) | 0.1kWh | |
| 69 | Epv3_total H | PV3 energy total (high) | 0.1kWh | 32-bit pair with reg 70 |
| 70 | Epv3_total L | PV3 energy total (low) | 0.1kWh | |
| 71 | Epv4_today H | PV4 energy today (high) | 0.1kWh | 32-bit pair with reg 72 |
| 72 | Epv4_today L | PV4 energy today (low) | 0.1kWh | |
| 73 | Epv4_total H | PV4 energy total (high) | 0.1kWh | 32-bit pair with reg 74 |
| 74 | Epv4_total L | PV4 energy total (low) | 0.1kWh | |
| 75 | Epv5_today H | PV5 energy today (high) | 0.1kWh | 32-bit pair with reg 76 |
| 76 | Epv5_today L | PV5 energy today (low) | 0.1kWh | |
| 77 | Epv5_total H | PV5 energy total (high) | 0.1kWh | 32-bit pair with reg 78 |
| 78 | Epv5_total L | PV5 energy total (low) | 0.1kWh | |
| 79 | Epv6_today H | PV6 energy today (high) | 0.1kWh | 32-bit pair with reg 80 |
| 80 | Epv6_today L | PV6 energy today (low) | 0.1kWh | |
| 81 | Epv6_total H | PV6 energy total (high) | 0.1kWh | 32-bit pair with reg 82 |
| 82 | Epv6_total L | PV6 energy total (low) | 0.1kWh | |
| 83 | Epv7_today H | PV7 energy today (high) | 0.1kWh | 32-bit pair with reg 84 |
| 84 | Epv7_today L | PV7 energy today (low) | 0.1kWh | |
| 85 | Epv7_total H | PV7 energy total (high) | 0.1kWh | 32-bit pair with reg 86 |
| 86 | Epv7_total L | PV7 energy total (low) | 0.1kWh | |
| 87 | Epv8_today H | PV8 energy today (high) | 0.1kWh | 32-bit pair with reg 88 |
| 88 | Epv8_today L | PV8 energy today (low) | 0.1kWh | |
| 89 | Epv8_total H | PV8 energy total (high) | 0.1kWh | 32-bit pair with reg 90 |
| 90 | Epv8_total L | PV8 energy total (low) | 0.1kWh | |
| 91 | Epv_total H | PV energy total (high) | 0.1kWh | 32-bit pair with reg 92 |
| 92 | Epv_total L | PV energy total (low) | 0.1kWh | |
| 93 | Temp1 | Inverter temperature | 0.1C | |
| 94 | Temp2 | IPM temperature | 0.1C | |
| 95 | Temp3 | Boost temperature | 0.1C | |
| 96 | Temp4 | Reserved | — | |
| 97 | uwBatVolt_DSP | Battery voltage (DSP) | 0.1V | |
| 98 | P Bus Voltage | P-Bus inside voltage | 0.1V | |
| 99 | N Bus Voltage | N-Bus inside voltage | 0.1V | |
| 100 | IPF | Inverter output power factor | — | 0–20000 |
| 101 | RealOPPercent | Real output power percent | 1% | |
| 102 | OPFullwatt H | Output max power limit (high) | 0.1W | 32-bit pair with reg 103 |
| 103 | OPFullwatt L | Output max power limit (low) | 0.1W | |
| 104 | DeratingMode | Derating mode | — | 0=None,1=PV,3=Vac,4=Fac,5=Tboost,6=Tinv,7=Control,9=OverBackByTime |
| 105 | Fault Maincode | Inverter fault main code | — | |
| 106 | Reserved | — | — | |
| 107 | Fault Subcode | Inverter fault sub code | — | |
| 108 | RemoteCtrlEn | Remote control enable | — | 0=Load First,1=Bat First,2=Grid Storage Power (SPA) |
| 109 | RemoteCtrlPower | Remote control power | — | Storage Power (SPA) |
| 110 | Warning bit H | Warning bit H | — | |
| 111 | Warn Subcode | Inverter warn sub code | — | |
| 112 | Warn Maincode / EACharge_Today_H | Warn main code / AC charge energy today H | — / 0.1kWh | MAX uses warn code; Storage Power uses energy |
| 113 | real Power Percent / EACharge_Today_L | Real power percent / AC charge energy today L | 0–100% / 0.1kWh | |
| 114 | inv start delay / EACharge_Total_H | Inverter start delay / AC charge energy total H | — / 0.1kWh | |
| 115 | bINVAllFaultCode / EACharge_Total_L | All fault code / AC charge energy total L | — / 0.1kWh | |
| 116 | AC charge Power_H | Grid power to local load (high) | 0.1kWh | Storage Power |
| 117 | AC charge Power_L | Grid power to local load (low) | 0.1kWh | Storage Power |
| 118 | Priority | Charge/discharge priority | — | 0=Load First,1=Battery First,2=Grid First |
| 119 | Battery Type | Battery type | — | 0=Lead-acid,1=Lithium |
| 120 | AutoProofreadCMD | Aging mode auto-calibration command | — | Storage Power |
| 121 | Reserved | Reserved | — | |
| 122 | Reserved | Reserved | — | |
| 123 | Reserved | Reserved | — | |
| 124 | Reserved | Reserved | — | |
| *Second group (125–249)* | | | | |
| 125 | PID PV1+ Voltage | PID PV1PE volt / flyspan voltage (MAX HV) | 0.1V | 0–1000V |
| 126 | PID PV1+ Current | PID PV1PE current | 0.1mA | -10–10mA |
| 127 | PID PV2+ Voltage | PID PV2PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 128 | PID PV2+ Current | PID PV2PE current | 0.1mA | |
| 129 | PID PV3+ Voltage | PID PV3PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 130 | PID PV3+ Current | PID PV3PE current | 0.1mA | |
| 131 | PID PV4+ Voltage | PID PV4PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 132 | PID PV4+ Current | PID PV4PE current | 0.1mA | |
| 133 | PID PV5+ Voltage | PID PV5PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 134 | PID PV5+ Current | PID PV5PE current | 0.1mA | |
| 135 | PID PV6+ Voltage | PID PV6PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 136 | PID PV6+ Current | PID PV6PE current | 0.1mA | |
| 137 | PID PV7+ Voltage | PID PV7PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 138 | PID PV7+ Current | PID PV7PE current | 0.1mA | |
| 139 | PID PV8+ Voltage | PID PV8PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 140 | PID PV8+ Current | PID PV8PE current | 0.1mA | |
| 141 | PID Status | PID working status | — | Bit0–7: 1=Wait,2=Normal,3=Fault; Bit8–15: Reserved |
| 142 | V_String1 | PV string 1 voltage | 0.1V | |
| 143 | Curr_String1 | PV string 1 current | 0.1A | -15–15A |
| 144 | V_String2 | PV string 2 voltage | 0.1V | |
| 145 | Curr_String2 | PV string 2 current | 0.1A | |
| 146 | V_String3 | PV string 3 voltage | 0.1V | |
| 147 | Curr_String3 | PV string 3 current | 0.1A | |
| 148 | V_String4 | PV string 4 voltage | 0.1V | |
| 149 | Curr_String4 | PV string 4 current | 0.1A | |
| 150 | V_String5 | PV string 5 voltage | 0.1V | |
| 151 | Curr_String5 | PV string 5 current | 0.1A | |
| 152 | V_String6 | PV string 6 voltage | 0.1V | |
| 153 | Curr_String6 | PV string 6 current | 0.1A | |
| 154 | V_String7 | PV string 7 voltage | 0.1V | |
| 155 | Curr_String7 | PV string 7 current | 0.1A | |
| 156 | V_String8 | PV string 8 voltage | 0.1V | |
| 157 | Curr_String8 | PV string 8 current | 0.1A | |
| 158 | V_String9 | PV string 9 voltage | 0.1V | |
| 159 | Curr_String9 | PV string 9 current | 0.1A | |
| 160 | V_String10 | PV string 10 voltage | 0.1V | |
| 161 | Curr_String10 | PV string 10 current | 0.1A | |
| 162 | V_String11 | PV string 11 voltage | 0.1V | |
| 163 | Curr_String11 | PV string 11 current | 0.1A | |
| 164 | V_String12 | PV string 12 voltage | 0.1V | |
| 165 | Curr_String12 | PV string 12 current | 0.1A | |
| 166 | V_String13 | PV string 13 voltage | 0.1V | |
| 167 | Curr_String13 | PV string 13 current | 0.1A | |
| 168 | V_String14 | PV string 14 voltage | 0.1V | |
| 169 | Curr_String14 | PV string 14 current | 0.1A | |
| 170 | V_String15 | PV string 15 voltage | 0.1V | |
| 171 | Curr_String15 | PV string 15 current | 0.1A | |
| 172 | V_String16 | PV string 16 voltage | 0.1V | |
| 173 | Curr_String16 | PV string 16 current | 0.1A | |
| 174 | StrUnmatch | String 1–16 unmatch flags | — | Bit0–15: String1–16 suggestive |
| 175 | StrCurrentUnblance | String 1–16 current unbalance | — | Bit0–15: suggestive |
| 176 | StrDisconnect | String 1–16 disconnect flags | — | Bit0–15: suggestive |
| 177 | PIDFaultCode | PID fault code | — | Bit0=Output OV, Bit1=ISO, Bit2=BUS abnormal |
| 178 | String Prompt | String prompt flags | — | Bit0=Unmatch, Bit1=Disconnect, Bit2=CurrentUnblance |
| 179 | PVWarningValue | PV warning value | — | |
| 180 | DSP075 Warning Value | DSP075 warning value | — | |
| 181 | DSP075 Fault Value | DSP075 fault value | — | |
| 182 | DSP067 Debug Data1 | DSP067 debug data 1 | — | |
| 183 | DSP067 Debug Data2 | DSP067 debug data 2 | — | |
| 184 | DSP067 Debug Data3 | DSP067 debug data 3 | — | |
| 185 | DSP067 Debug Data4 | DSP067 debug data 4 | — | |
| 186 | DSP067 Debug Data5 | DSP067 debug data 5 | — | |
| 187 | DSP067 Debug Data6 | DSP067 debug data 6 | — | |
| 188 | DSP067 Debug Data7 | DSP067 debug data 7 | — | |
| 189 | DSP067 Debug Data8 | DSP067 debug data 8 | — | |
| 190 | DSP075 Debug Data1 | DSP075 debug data 1 | — | |
| 191 | DSP075 Debug Data2 | DSP075 debug data 2 | — | |
| 192 | DSP075 Debug Data3 | DSP075 debug data 3 | — | |
| 193 | DSP075 Debug Data4 | DSP075 debug data 4 | — | |
| 194 | DSP075 Debug Data5 | DSP075 debug data 5 | — | |
| 195 | DSP075 Debug Data6 | DSP075 debug data 6 | — | |
| 196 | DSP075 Debug Data7 | DSP075 debug data 7 | — | |
| 197 | DSP075 Debug Data8 | DSP075 debug data 8 | — | |
| 198 | bUSBAgingTestOkFlag | USB aging test OK flag | — | 0–1 |
| 199 | bFlashEraseAgingOkFlag | Flash erase aging OK flag | — | 0–1 |
| 200 | PVISO | PV ISO value | — | KOhm |
| 201 | R_DCI | R-phase DCI current | 0.1mA | |
| 202 | S_DCI | S-phase DCI current | 0.1mA | |
| 203 | T_DCI | T-phase DCI current | 0.1mA | |
| 204 | PID_Bus | PID bus voltage | 0.1V | |
| 205 | GFCI | GFCI current | mA | |
| 206 | SVG/APF Status | SVG/APF status + equal ratio | — | High 8-bit=EqualRatio; Low 8-bit: 0=None,1=SVG run,2=APF run,3=Both |
| 207 | CT_I_R | R-phase load side current for SVG | 0.1A | |
| 208 | CT_I_S | S-phase load side current for SVG | 0.1A | |
| 209 | CT_I_T | T-phase load side current for SVG | 0.1A | |
| 210 | CT_Q_R H | R-phase load side reactive power for SVG (high) | 0.1Var | |
| 211 | CT_Q_R L | R-phase load side reactive power for SVG (low) | 0.1Var | |
| 212 | CT_Q_S H | S-phase load side reactive power for SVG (high) | 0.1Var | |
| 213 | CT_Q_S L | S-phase load side reactive power for SVG (low) | 0.1Var | |
| 214 | CT_Q_T H | T-phase load side reactive power for SVG (high) | 0.1Var | |
| 215 | CT_Q_T L | T-phase load side reactive power for SVG (low) | 0.1Var | |
| 216 | CT HAR_I_R | R-phase load side harmonic current | 0.1A | |
| 217 | CT HAR_I_S | S-phase load side harmonic current | 0.1A | |
| 218 | CT HAR_I_T | T-phase load side harmonic current | 0.1A | |
| 219 | COMP_Q_R H | R-phase compensate reactive power for SVG (high) | 0.1Var | |
| 220 | COMP_Q_R L | R-phase compensate reactive power for SVG (low) | 0.1Var | |
| 221 | COMP_Q_S H | S-phase compensate reactive power for SVG (high) | 0.1Var | |
| 222 | COMP_Q_S L | S-phase compensate reactive power for SVG (low) | 0.1Var | |
| 223 | COMP_Q_T H | T-phase compensate reactive power for SVG (high) | 0.1Var | |
| 224 | COMP_Q_T L | T-phase compensate reactive power for SVG (low) | 0.1Var | |
| 225 | COMP HAR_I_R | R-phase compensate harmonic for SVG | 0.1A | |
| 226 | COMP HAR_I_S | S-phase compensate harmonic for SVG | 0.1A | |
| 227 | COMP HAR_I_T | T-phase compensate harmonic for SVG | 0.1A | |
| 228 | bRS232AgingTestOkFlag | RS232 aging test OK flag | — | 0–1 |
| 229 | bFanFaultBit | Fan fault bits | — | Bit0=Fan1,Bit1=Fan2,Bit2=Fan3,Bit3=Fan4 |
| 230 | Sac H | Output apparent power (high) | 0.1VA | 32-bit pair with reg 231 |
| 231 | Sac L | Output apparent power (low) | 0.1VA | |
| 232 | ReActPower H | Real output reactive power (high) | 0.1Var | Int32, 32-bit pair with reg 233 |
| 233 | ReActPower L | Real output reactive power (low) | 0.1Var | |
| 234 | ReActPowerMax H | Nominal output reactive power (high) | 0.1Var | 32-bit pair with reg 235 |
| 235 | ReActPowerMax L | Nominal output reactive power (low) | 0.1Var | |
| 236 | ReActPower_Total H | Reactive power generation (high) | 0.1kWh | 32-bit pair with reg 237 |
| 237 | ReActPower_Total L | Reactive power generation (low) | 0.1kWh | |
| 238 | bAfciStatus | AFCI status | — | 0=Waiting,1=Self-check,2=Detect arc,3=Fault,4=Update |
| 239 | uwPresentFFTValue [CHANNEL_A] | AFCI present FFT value channel A | — | |
| 240 | uwPresentFFTValue [CHANNEL_B] | AFCI present FFT value channel B | — | |
| 241 | DSP067 Debug Data1 | DSP067 debug data 1 (second group) | — | |
| 242 | DSP067 Debug Data2 | DSP067 debug data 2 | — | |
| 243 | DSP067 Debug Data3 | DSP067 debug data 3 | — | |
| 244 | DSP067 Debug Data4 | DSP067 debug data 4 | — | |
| 245 | DSP067 Debug Data5 | DSP067 debug data 5 | — | |
| 246 | DSP067 Debug Data6 | DSP067 debug data 6 | — | |
| 247 | DSP067 Debug Data7 | DSP067 debug data 7 | — | |
| 248 | DSP067 Debug Data8 | DSP067 debug data 8 | — | |
| 249 | Reserved | Reserved | — | |
| *Eighth group — PV9–PV16 (875–999)* | | | | |
| 875 | Vpv9 | PV9 voltage | 0.1V | |
| 876 | PV9Curr | PV9 input current | 0.1A | |
| 877 | Ppv9 H | PV9 input power (high) | 0.1W | 32-bit pair with reg 878 |
| 878 | Ppv9 L | PV9 input power (low) | 0.1W | |
| 879 | Vpv10 | PV10 voltage | 0.1V | |
| 880 | PV10Curr | PV10 input current | 0.1A | |
| 881 | Ppv10 H | PV10 input power (high) | 0.1W | 32-bit pair with reg 882 |
| 882 | Ppv10 L | PV10 input power (low) | 0.1W | |
| 883 | Vpv11 | PV11 voltage | 0.1V | |
| 884 | PV11Curr | PV11 input current | 0.1A | |
| 885 | Ppv11 H | PV11 input power (high) | 0.1W | 32-bit pair with reg 886 |
| 886 | Ppv11 L | PV11 input power (low) | 0.1W | |
| 887 | Vpv12 | PV12 voltage | 0.1V | |
| 888 | PV12Curr | PV12 input current | 0.1A | |
| 889 | Ppv12 H | PV12 input power (high) | 0.1W | 32-bit pair with reg 890 |
| 890 | Ppv12 L | PV12 input power (low) | 0.1W | |
| 891 | Vpv13 | PV13 voltage | 0.1V | |
| 892 | PV13Curr | PV13 input current | 0.1A | |
| 893 | Ppv13 H | PV13 input power (high) | 0.1W | 32-bit pair with reg 894 |
| 894 | Ppv13 L | PV13 input power (low) | 0.1W | |
| 895 | Vpv14 | PV14 voltage | 0.1V | |
| 896 | PV14Curr | PV14 input current | 0.1A | |
| 897 | Ppv14 H | PV14 input power (high) | 0.1W | 32-bit pair with reg 898 |
| 898 | Ppv14 L | PV14 input power (low) | 0.1W | |
| 899 | Vpv15 | PV15 voltage | 0.1V | |
| 900 | PV15Curr | PV15 input current | 0.1A | |
| 901 | Ppv15 H | PV15 input power (high) | 0.1W | 32-bit pair with reg 902 |
| 902 | Ppv15 L | PV15 input power (low) | 0.1W | |
| 903 | Vpv16 | PV16 voltage | 0.1V | |
| 904 | PV16Curr | PV16 input current | 0.1A | |
| 905 | Ppv16 H | PV16 input power (high) | 0.1W | 32-bit pair with reg 906 |
| 906 | Ppv16 L | PV16 input power (low) | 0.1W | |
| 907 | Epv9_today H | PV9 energy today (high) | 0.1kWh | |
| 908 | Epv9_today L | PV9 energy today (low) | 0.1kWh | |
| 909 | Epv9_total H | PV9 energy total (high) | 0.1kWh | |
| 910 | Epv9_total L | PV9 energy total (low) | 0.1kWh | |
| 911 | Epv10_today H | PV10 energy today (high) | 0.1kWh | |
| 912 | Epv10_today L | PV10 energy today (low) | 0.1kWh | |
| 913 | Epv10_total H | PV10 energy total (high) | 0.1kWh | |
| 914 | Epv10_total L | PV10 energy total (low) | 0.1kWh | |
| 915 | Epv11_today H | PV11 energy today (high) | 0.1kWh | |
| 916 | Epv11_today L | PV11 energy today (low) | 0.1kWh | |
| 917 | Epv11_total H | PV11 energy total (high) | 0.1kWh | |
| 918 | Epv11_total L | PV11 energy total (low) | 0.1kWh | |
| 919 | Epv12_today H | PV12 energy today (high) | 0.1kWh | |
| 920 | Epv12_today L | PV12 energy today (low) | 0.1kWh | |
| 921 | Epv12_total H | PV12 energy total (high) | 0.1kWh | |
| 922 | Epv12_total L | PV12 energy total (low) | 0.1kWh | |
| 923 | Epv13_today H | PV13 energy today (high) | 0.1kWh | |
| 924 | Epv13_today L | PV13 energy today (low) | 0.1kWh | |
| 925 | Epv13_total H | PV13 energy total (high) | 0.1kWh | |
| 926 | Epv13_total L | PV13 energy total (low) | 0.1kWh | |
| 927 | Epv14_today H | PV14 energy today (high) | 0.1kWh | |
| 928 | Epv14_today L | PV14 energy today (low) | 0.1kWh | |
| 929 | Epv14_total H | PV14 energy total (high) | 0.1kWh | |
| 930 | Epv14_total L | PV14 energy total (low) | 0.1kWh | |
| 931 | Epv15_today H | PV15 energy today (high) | 0.1kWh | |
| 932 | Epv15_today L | PV15 energy today (low) | 0.1kWh | |
| 933 | Epv15_total H | PV15 energy total (high) | 0.1kWh | |
| 934 | Epv15_total L | PV15 energy total (low) | 0.1kWh | |
| 935 | Epv16_today H | PV16 energy today (high) | 0.1kWh | |
| 936 | Epv16_today L | PV16 energy today (low) | 0.1kWh | |
| 937 | Epv16_total H | PV16 energy total (high) | 0.1kWh | |
| 938 | Epv16_total L | PV16 energy total (low) | 0.1kWh | |
| 939 | PID PV9+ Voltage | PID PV9PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 940 | PID PV9+ Current | PID PV9PE current | 0.1mA | |
| 941 | PID PV10+ Voltage | PID PV10PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 942 | PID PV10+ Current | PID PV10PE current | 0.1mA | |
| 943 | PID PV11+ Voltage | PID PV11PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 944 | PID PV11+ Current | PID PV11PE current | 0.1mA | |
| 945 | PID PV12+ Voltage | PID PV12PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 946 | PID PV12+ Current | PID PV12PE current | 0.1mA | |
| 947 | PID PV13+ Voltage | PID PV13PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 948 | PID PV13+ Current | PID PV13PE current | 0.1mA | |
| 949 | PID PV14+ Voltage | PID PV14PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 950 | PID PV14+ Current | PID PV14PE current | 0.1mA | |
| 951 | PID PV15+ Voltage | PID PV15PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 952 | PID PV15+ Current | PID PV15PE current | 0.1mA | |
| 953 | PID PV16+ Voltage | PID PV16PE volt / flyspan voltage (MAX HV) | 0.1V | |
| 954 | PID PV16+ Current | PID PV16PE current | 0.1mA | |
| 955 | V_String17 | PV string 17 voltage | 0.1V | |
| 956 | Curr_String17 | PV string 17 current | 0.1A | |
| 957 | V_String18 | PV string 18 voltage | 0.1V | |
| 958 | Curr_String18 | PV string 18 current | 0.1A | |
| 959 | V_String19 | PV string 19 voltage | 0.1V | |
| 960 | Curr_String19 | PV string 19 current | 0.1A | |
| 961 | V_String20 | PV string 20 voltage | 0.1V | |
| 962 | Curr_String20 | PV string 20 current | 0.1A | |
| 963 | V_String21 | PV string 21 voltage | 0.1V | |
| 964 | Curr_String21 | PV string 21 current | 0.1A | |
| 965 | V_String22 | PV string 22 voltage | 0.1V | |
| 966 | Curr_String22 | PV string 22 current | 0.1A | |
| 967 | V_String23 | PV string 23 voltage | 0.1V | |
| 968 | Curr_String23 | PV string 23 current | 0.1A | |
| 969 | V_String24 | PV string 24 voltage | 0.1V | |
| 970 | Curr_String24 | PV string 24 current | 0.1A | |
| 971 | V_String25 | PV string 25 voltage | 0.1V | |
| 972 | Curr_String25 | PV string 25 current | 0.1A | |
| 973 | V_String26 | PV string 26 voltage | 0.1V | |
| 974 | Curr_String26 | PV string 26 current | 0.1A | |
| 975 | V_String27 | PV string 27 voltage | 0.1V | |
| 976 | Curr_String27 | PV string 27 current | 0.1A | |
| 977 | V_String28 | PV string 28 voltage | 0.1V | |
| 978 | Curr_String28 | PV string 28 current | 0.1A | |
| 979 | V_String29 | PV string 29 voltage | 0.1V | |
| 980 | Curr_String29 | PV string 29 current | 0.1A | |
| 981 | V_String30 | PV string 30 voltage | 0.1V | |
| 982 | Curr_String30 | PV string 30 current | 0.1A | |
| 983 | V_String31 | PV string 31 voltage | 0.1V | |
| 984 | Curr_String31 | PV string 31 current | 0.1A | |
| 985 | V_String32 | PV string 32 voltage | 0.1V | |
| 986 | Curr_String32 | PV string 32 current | 0.1A | |
| 987 | StrUnmatch2 | String 17–32 unmatch flags | — | Bit0–15 |
| 988 | StrCurrentUnblance2 | String 17–32 current unbalance | — | Bit0–15 |
| 989 | StrDisconnect2 | String 17–32 disconnect flags | — | Bit0–15 |
| 990 | PV Warning Value | PV warning value (PV9–PV16) | — | |
| 991 | StrWaringvalue1 | String 1–16 abnormal | — | |
| 992 | StrWaringvalue2 | String 17–32 abnormal | — | |
| 993–998 | Reserved | Reserved | — | |
| 999 | SystemCmd | M3 to DSP system command | — | |
| *Ninth group — Storage power (1000–1249)* | | | | |
| 1000 | uwSysWorkMode | System work mode | — | 0x00=Waiting, 0x01=Self-test, 0x02=Reserved, 0x03=Fault, 0x04=Updating, 0x05=PV On-Grid, 0x06=Bat On-Grid, 0x07=PV+Bat Off-Grid, 0x08=Bat Off-Grid |
| 1001 | Systemfault word0 | System fault word 0 | — | See Hybrid fault table |
| 1002 | Systemfault word1 | System fault word 1 | — | |
| 1003 | Systemfault word2 | System fault word 2 | — | |
| 1004 | Systemfault word3 | System fault word 3 | — | |
| 1005 | Systemfault word4 | System fault word 4 | — | |
| 1006 | Systemfault word5 | System fault word 5 | — | |
| 1007 | Systemfault word6 | System fault word 6 | — | |
| 1008 | Systemfault word7 | System fault word 7 | — | |
| 1009 | Pdischarge1 H | Discharge power (high) | 0.1W | 32-bit pair with reg 1010 |
| 1010 | Pdischarge1 L | Discharge power (low) | 0.1W | |
| 1011 | Pcharge1 H | Charge power (high) | 0.1W | 32-bit pair with reg 1012 |
| 1012 | Pcharge1 L | Charge power (low) | 0.1W | |
| 1013 | Vbat | Battery voltage | 0.1V | |
| 1014 | SOC | State of charge | 1% | 0–100; lithium / lead-acid |
| 1015 | Pactouser R H | AC power to user R-phase (high) | 0.1W | |
| 1016 | Pactouser R L | AC power to user R-phase (low) | 0.1W | |
| 1017 | Pactouser S H | AC power to user S-phase (high) | 0.1W | |
| 1018 | Pactouser S L | AC power to user S-phase (low) | 0.1W | |
| 1019 | Pactouser T H | AC power to user T-phase (high) | 0.1W | |
| 1020 | Pactouser T L | AC power to user T-phase (low) | 0.1W | |
| 1021 | PactouserTotal H | AC power to user total (high) | 0.1W | |
| 1022 | PactouserTotal L | AC power to user total (low) | 0.1W | |
| 1023 | Pac to grid R H | AC power to grid R-phase (high) | 0.1W | |
| 1024 | Pac to grid R L | AC power to grid R-phase (low) | 0.1W | |
| 1025 | Pactogrid S H | AC power to grid S-phase (high) | 0.1W | |
| 1026 | Pactogrid S L | AC power to grid S-phase (low) | 0.1W | |
| 1027 | Pactogrid T H | AC power to grid T-phase (high) | 0.1W | |
| 1028 | Pactogrid T L | AC power to grid T-phase (low) | 0.1W | |
| 1029 | Pactogrid total H | AC power to grid total (high) | 0.1W | |
| 1030 | Pactogrid total L | AC power to grid total (low) | 0.1W | |
| 1031 | PLocalLoad R H | INV power to local load R-phase (high) | 0.1W | |
| 1032 | PLocalLoad R L | INV power to local load R-phase (low) | 0.1W | |
| 1033 | PLocalLoad S H | INV power to local load S-phase (high) | 0.1W | |
| 1034 | PLocalLoad S L | INV power to local load S-phase (low) | 0.1W | |
| 1035 | PLocalLoad T H | INV power to local load T-phase (high) | 0.1W | |
| 1036 | PLocalLoad T L | INV power to local load T-phase (low) | 0.1W | |
| 1037 | PLocalLoad total H | INV power to local load total (high) | 0.1W | |
| 1038 | PLocalLoad total L | INV power to local load total (low) | 0.1W | |
| 1039 | IP2M Temperature | REC temperature | 0.1C | Not used |
| 1040 | Battery Temperature | Battery temperature | 0.1C | Lead-acid / lithium |
| 1041 | SP DSP Status | SP state | — | CHG / DisCHG |
| 1042 | SP Bus Volt | SP BUS2 voltage | 0.1V | |
| 1043 | Reserved | Power generation data section start | — | |
| 1044 | Etouser_today H | Energy to user today (high) | 0.1kWh | |
| 1045 | Etouser_today L | Energy to user today (low) | 0.1kWh | |
| 1046 | Etouser_total H | Energy to user total (high) | 0.1kWh | |
| 1047 | Etouser_total L | Energy to user total (low) | 0.1kWh | |
| 1048 | Etogrid_today H | Energy to grid today (high) | 0.1kWh | |
| 1049 | Etogrid_today L | Energy to grid today (low) | 0.1kWh | |
| 1050 | Etogrid_total H | Energy to grid total (high) | 0.1kWh | |
| 1051 | Etogrid_total L | Energy to grid total (low) | 0.1kWh | |
| 1052 | Edischarge1_today H | Discharge energy 1 today (high) | 0.1kWh | |
| 1053 | Edischarge1_today L | Discharge energy 1 today (low) | 0.1kWh | |
| 1054 | Edischarge1_total H | Total discharge energy 1 (high) | 0.1kWh | |
| 1055 | Edischarge1_total L | Total discharge energy 1 (low) | 0.1kWh | |
| 1056 | Echarge1_today H | Charge energy 1 today (high) | 0.1kWh | |
| 1057 | Echarge1_today L | Charge energy 1 today (low) | 0.1kWh | |
| 1058 | Echarge1_total H | Charge energy 1 total (high) | 0.1kWh | |
| 1059 | Echarge1_total L | Charge energy 1 total (low) | 0.1kWh | |
| 1060 | ELocalLoad_Today H | Local load energy today (high) | 0.1kWh | |
| 1061 | ELocalLoad_Today L | Local load energy today (low) | 0.1kWh | |
| 1062 | ELocalLoad_Total H | Local load energy total (high) | 0.1kWh | |
| 1063 | ELocalLoad_Total L | Local load energy total (low) | 0.1kWh | |
| 1064 | dwExportLimitApparentPower H | Export limit apparent power (high) | 0.1VA | |
| 1065 | dwExportLimitApparentPower L | Export limit apparent power (low) | 0.1VA | |
| 1066 | Reserved | Reserved | — | |
| *UPS / EPS information (offline) — 1067–1081* | | | | |
| 1067 | EPS Fac | UPS frequency | 0.01Hz | 5000/6000 |
| 1068 | EPS Vac1 | UPS phase R output voltage | 0.1V | 2300 |
| 1069 | EPS Iac1 | UPS phase R output current | 0.1A | |
| 1070 | EPS Pac1 H | UPS phase R output power (high) | 0.1VA | |
| 1071 | EPS Pac1 L | UPS phase R output power (low) | 0.1VA | |
| 1072 | EPS Vac2 | UPS phase S output voltage | 0.1V | |
| 1073 | EPS Iac2 | UPS phase S output current | 0.1A | Not used |
| 1074 | EPS Pac2 H | UPS phase S output power (high) | 0.1VA | |
| 1075 | EPS Pac2 L | UPS phase S output power (low) | 0.1VA | |
| 1076 | EPS Vac3 | UPS phase T output voltage | 0.1V | |
| 1077 | EPS Iac3 | UPS phase T output current | 0.1A | Not used |
| 1078 | EPS Pac3 H | UPS phase T output power (high) | 0.1VA | |
| 1079 | EPS Pac3 L | UPS phase T output power (low) | 0.1VA | |
| 1080 | loadpercent | Load percent of UPS output | 1% | 0–100 |
| 1081 | PF | Power factor | 0.1 | Primary value + 1 |
| *BMS information — 1082–1124* | | | | |
| 1082 | BMS_StatusOld | Status old from BMS | — | |
| 1083 | BMS_Status | Status from BMS | — | W/R |
| 1084 | BMS_ErrorOld | Error info old from BMS | — | |
| 1085 | BMS_Error | Error info from BMS | — | |
| 1086 | BMS_SOC | SOC from BMS | — | R; SPH6K |
| 1087 | BMS_BatteryVolt | Battery voltage from BMS | — | R; SPH6K |
| 1088 | BMS_BatteryCurr | Battery current from BMS | — | |
| 1089 | BMS_BatteryTemp | Battery temperature from BMS | — | |
| 1090 | BMS_MaxCurr | Max charge/discharge current from BMS (Pylontech) | — | |
| 1091 | BMS_GaugeRM | Gauge RM from BMS | — | |
| 1092 | BMS_GaugeFCC | Gauge FCC from BMS | — | |
| 1093 | BMS_FW | BMS firmware version | — | |
| 1094 | BMS_DeltaVolt | Delta V from BMS | — | |
| 1095 | BMS_CycleCnt | Cycle count from BMS | — | |
| 1096 | BMS_SOH | SOH from BMS | — | |
| 1097 | BMS_ConstantVolt | CV voltage from BMS | — | |
| 1098 | BMS_WarnInfoOld | Warning info old from BMS | — | |
| 1099 | BMS_WarnInfo | Warning info from BMS | — | |
| 1100 | BMS_GaugeICCurr | Gauge IC current from BMS | — | |
| 1101 | BMS_MCUVersion | MCU software version from BMS | — | |
| 1102 | BMS_GaugeVersion | Gauge version from BMS | — | |
| 1103 | BMS_wGaugeFRVersion_L | Gauge FR version L16 from BMS | — | |
| 1104 | BMS_wGaugeFRVersion_H | Gauge FR version H16 from BMS | — | |
| 1105 | BMS_BMSInfo | BMS information from BMS | — | |
| 1106 | BMS_PackInfo | Pack information from BMS | — | |
| 1107 | BMS_UsingCap | Using cap from BMS | — | |
| 1108 | uwMaxCellVolt | Maximum single battery voltage | 0.001V | |
| 1109 | uwMinCellVolt | Minimum single battery voltage | 0.001V | |
| 1110 | bModuleNum | Battery parallel number | 1 | |
| 1111 | bBatNum | Number of batteries | 1 | |
| 1112 | uwMaxVoltCellNo | Max voltage cell number | 1 | |
| 1113 | uwMinVoltCellNo | Min voltage cell number | 1 | |
| 1114 | uwMaxTemprCell_10T | Max temperature cell (x10) | 0.1C | |
| 1115 | uwMinTemprCell_10T | Min temperature cell (x10) | 0.1C | |
| 1116 | uwMaxTemprCellNo | Max temperature cell number | 1 | |
| 1117 | uwMinTemprCellNo | Min temperature cell number | 1 | |
| 1118 | Protect pack ID | Faulty battery address | 1 | |
| 1119 | MaxSOC | Parallel maximum SOC | 1% | |
| 1120 | MinSOC | Parallel minimum SOC | 1% | |
| 1121 | BMS_Error2 | Battery protection 2 — CAN ID:0x323 Byte4-5 | — | |
| 1122 | BMS_Error3 | Battery protection 3 — CAN ID:0x323 Byte6 | — | |
| 1123 | BMS_WarnInfo2 | Battery warning 2 — CAN ID:0x323 Byte7 | — | |
| 1124 | AC Charge Energy Today H | AC charge energy today (high) | 0.1kWh | |
| 1125 | ACCharge Energy Today L | AC charge energy today (low) | 0.1kWh | |
| 1126 | ACCharge Energy Total H | AC charge energy total (high) | 0.1kWh | |
| 1127 | ACCharge Energy Total L | AC charge energy total (low) | 0.1kWh | |
| 1128 | AC Charge Power H | AC charge power (high) | W | |
| 1129 | AC Charge Power L | AC charge power (low) | W | |
| 1130 | 70% INV Power adjust | Grid power 70% adjust | W | uwGridPower_70_AdjEE_SP |
| 1131 | ExtraACPower to grid H | Extra inverter AC power to grid (high) | — | SPA only |
| 1132 | ExtraACPower to grid L | Extra inverter AC power to grid (low) | — | SPA only |
| 1133 | Eextra_today H | Extra inverter power to user today (high) | 0.1kWh | SPA only |
| 1134 | Eextra_today L | Extra inverter power to user today (low) | 0.1kWh | SPA only |
| 1135 | Eextra_total H | Extra inverter power to user total (high) | 0.1kWh | SPA only |
| 1136 | Eextra_total L | Extra inverter power to user total (low) | 0.1kWh | SPA only |
| 1137 | Esystem_today H | System electric energy today (high) | 0.1kWh | SPA only |
| 1138 | Esystem_today L | System electric energy today (low) | 0.1kWh | SPA only |
| 1139 | Esystem_total H | System electric energy total (high) | 0.1kWh | SPA only |
| 1140 | Esystem_total L | System electric energy total (low) | 0.1kWh | SPA only |
| 1141 | Eself_today H | Self electric energy today (high) | 0.1kWh | |
| 1142 | Eself_today L | Self electric energy today (low) | 0.1kWh | |
| 1143 | Eself_total H | Self electric energy total (high) | 0.1kWh | |
| 1144 | Eself_total L | Self electric energy total (low) | 0.1kWh | |
| 1145 | PSystem H | System power (high) | 0.1W | |
| 1146 | PSystem L | System power (low) | 0.1W | |
| 1147 | PSelf H | Self power (high) | 0.1W | |
| 1148 | PSelf L | Self power (low) | 0.1W | |
| 1149 | EPVAll_Today H | PV electric energy today (high) | 0.1kWh | |
| 1150 | EPVAll_Today L | PV electric energy today (low) | 0.1kWh | |
| 1151 | AcDischargePackSn | Discharge power pack serial number | — | R |
| 1152 | Acdischarge power H | Cumulative discharge power high 16-bit | 0.1kWh | R |
| 1153 | Acdischarge power L | Cumulative discharge power low 16-bit | 0.1kWh | R |
| 1154 | AcChargePackSn | Charge power pack serial number | — | R |
| 1155 | AcCharge power H | Cumulative charge power high 16-bit | 0.1kWh | R |
| 1156 | AcCharge power L | Cumulative charge power low 16-bit | 0.1kWh | R |
| 1157 | First Batt Fault Sn | First battery fault serial number | — | R |
| 1158 | Second Batt Fault Sn | Second battery fault serial number | — | R |
| 1159 | Third Batt Fault Sn | Third battery fault serial number | — | R |
| 1160 | Fourth Batt Fault Sn | Fourth battery fault serial number | — | R |
| 1161 | Battery history fault code 1 | Battery history fault code 1 | — | R |
| 1162 | Battery history fault code 2 | Battery history fault code 2 | — | R |
| 1163 | Battery history fault code 3 | Battery history fault code 3 | — | R |
| 1164 | Battery history fault code 4 | Battery history fault code 4 | — | R |
| 1165 | Battery history fault code 5 | Battery history fault code 5 | — | R |
| 1166 | Battery history fault code 6 | Battery history fault code 6 | — | R |
| 1167 | Battery history fault code 7 | Battery history fault code 7 | — | R |
| 1168 | Battery history fault code 8 | Battery history fault code 8 | — | R |
| 1169 | Number of battery codes | Battery fault code count (PACK + BIC) | — | R |
| 1170–1198 | Reserved | Reserved | — | |
| 1199 | NewEPowerCalcFlag | Energy calculation mode flag | — | 0=Old, 1=New |
| 1200 | MaxCellVolt | Maximum cell voltage | 0.001V | R |
| 1201 | MinCellVolt | Minimum cell voltage | 0.001V | R |
| 1202 | ModuleNum | Number of battery modules | — | R |
| 1203 | TotalCellNum | Total number of cells | — | R |
| 1204 | MaxVoltCellNo | Max voltage cell number | — | R |
| 1205 | MinVoltCellNo | Min voltage cell number | — | R |
| 1206 | MaxTemprCell_10T | Max temperature cell (x10) | 0.1C | R |
| 1207 | MinTemprCell_10T | Min temperature cell (x10) | 0.1C | R |
| 1208 | MaxTemprCellNo | Max temperature cell number | — | R |
| 1209 | MinTemprCellNo | Min temperature cell number | — | R |
| 1210 | ProtectPackID | Fault pack ID | — | R |
| 1211 | MaxSOC | Parallel maximum SOC | 1% | R |
| 1212 | MinSOC | Parallel minimum SOC | 1% | R |
| 1213 | BatProtect1Add | BatProtect1Add | — | R |
| 1214 | BatProtect2Add | BatProtect2Add | — | R |
| 1215 | BatWarn1Add | BatWarn1Add | — | R |
| 1216 | BMS_HighestSoftVersion | BMS highest software version | — | R |
| 1217 | BMS_HardwareVersion | BMS hardware version | — | R |
| 1218 | BMS_RequestType | BMS request type | — | R |
| 1219–1247 | Reserved | Reserved | — | |
| 1248 | bKeyAgingTestOkFlag | Key detection success flag | — | 0=Not completed, 1=Finished |
| 1249 | Reserved | Reserved | — | |
| *Thirteenth group — SPA storage (2000–2124)* | | | | |
| 2000 | Inverter Status | SPA inverter run state | — | 0=Waiting, 1=Normal, 3=Fault |
| 2001–2034 | Reserved | Reserved | — | |
| 2035 | Pac H | SPA output power (high) | 0.1W | |
| 2036 | Pac L | SPA output power (low) | 0.1W | |
| 2037 | Fac | SPA grid frequency | 0.01Hz | |
| 2038 | Vac1 | SPA R-phase grid voltage | 0.1V | |
| 2039 | Iac1 | SPA R-phase grid output current | 0.1A | |
| 2040 | Pac1 H | SPA R-phase grid output apparent power (high) | 0.1VA | |
| 2041 | Pac1 L | SPA R-phase grid output apparent power (low) | 0.1VA | |
| 2042–2052 | Reserved | Reserved | — | |
| 2053 | Eac today H | SPA today generate energy (high) | 0.1kWh | |
| 2054 | Eac today L | SPA today generate energy (low) | 0.1kWh | |
| 2055 | Eac total H | SPA total generate energy (high) | 0.1kWh | |
| 2056 | Eac total L | SPA total generate energy (low) | 0.1kWh | |
| 2057 | Time total H | SPA work time total (high) | 0.5s | |
| 2058 | Time total L | SPA work time total (low) | 0.5s | |
| 2059–2092 | Reserved | Reserved | — | |
| 2093 | Temp1 | SPA inverter temperature | 0.1C | |
| 2094 | Temp2 | SPA IPM temperature | 0.1C | |
| 2095 | Temp3 | SPA boost temperature | 0.1C | |
| 2096 | Temp4 | Reserved | — | |
| 2097 | uwBatVolt_DSP | BatVolt_DSP | 0.1V | |
| 2098 | P Bus Voltage | SPA P-Bus inside voltage | 0.1V | |
| 2099 | N Bus Voltage | SPA N-Bus inside voltage | 0.1V | |
| 2100 | RemoteCtrlEn | Remote control enable | — | 0=Load First, 1=Bat First, 2=Grid |
| 2101 | RemoteCtrlPower | Remotely set power | — | |
| 2102 | Extra AC Power to grid H | Extra inverter AC power to grid (high) | — | SPA |
| 2103 | Extra AC Power to grid L | Extra inverter AC power to grid (low) | — | SPA |
| 2104 | Eextra_today H | Extra inverter power to user today (high) | 0.1kWh | SPA |
| 2105 | Eextra_today L | Extra inverter power to user today (low) | 0.1kWh | SPA |
| 2106 | Eextra_total H | Extra inverter power to user total (high) | 0.1kWh | SPA |
| 2107 | Eextra_total L | Extra inverter power to user total (low) | 0.1kWh | SPA |
| 2108 | Esystem_today H | System electric energy today (high) | 0.1kWh | SPA |
| 2109 | Esystem_today L | System electric energy today (low) | 0.1kWh | SPA |
| 2110 | Esystem_total H | System electric energy total (high) | 0.1kWh | SPA |
| 2111 | Esystem_total L | System electric energy total (low) | 0.1kWh | SPA |
| 2112 | EACharge_Today_H | AC charge energy today (high) | 0.1kWh | Storage Power |
| 2113 | EACharge_Today_L | AC charge energy today (low) | 0.1kWh | Storage Power |
| 2114 | EACharge_Total_H | AC charge energy total (high) | 0.1kWh | Storage Power |
| 2115 | EACharge_Total_L | AC charge energy total (low) | 0.1kWh | Storage Power |
| 2116 | AC charge Power H | Grid power to local load (high) | 0.1kWh | Storage Power |
| 2117 | AC charge Power L | Grid power to local load (low) | 0.1kWh | Storage Power |
| 2118 | Priority | Charge/discharge priority | — | 0=Load First, 1=Battery First, 2=Grid First |
| 2119 | Battery Type | Battery type | — | 0=Lead-acid, 1=Lithium |
| 2120 | AutoProofreadCMD | Aging mode auto-calibration | — | Storage Power |
| 2121–2124 | Reserved | Reserved | — | |
| *TL-X and TL-XH group (3000–3417)* | | | | |
| 3000 | Inverter Status | Inverter run state | — | High 8-bit=mode (0=Wait,1=Self-test,3=Fault,4=Flash,5-8=Normal); Low 8-bit=display (0=Standby,1=Ongrid,2=Offgrid,3=Fault,4=Flash) |
| 3001 | Ppv H | PV total power (high) | 0.1W | |
| 3002 | Ppv L | PV total power (low) | 0.1W | |
| 3003 | Vpv1 | PV1 voltage | 0.1V | |
| 3004 | Ipv1 | PV1 input current | 0.1A | |
| 3005 | Ppv1 H | PV1 power (high) | 0.1W | |
| 3006 | Ppv1 L | PV1 power (low) | 0.1W | |
| 3007 | Vpv2 | PV2 voltage | 0.1V | |
| 3008 | Ipv2 | PV2 input current | 0.1A | |
| 3009 | Ppv2 H | PV2 power (high) | 0.1W | |
| 3010 | Ppv2 L | PV2 power (low) | 0.1W | |
| 3011 | Vpv3 | PV3 voltage | 0.1V | |
| 3012 | Ipv3 | PV3 input current | 0.1A | |
| 3013 | Ppv3 H | PV3 power (high) | 0.1W | |
| 3014 | Ppv3 L | PV3 power (low) | 0.1W | |
| 3015 | Vpv4 | PV4 voltage | 0.1V | |
| 3016 | Ipv4 | PV4 input current | 0.1A | |
| 3017 | Ppv4 H | PV4 power (high) | 0.1W | |
| 3018 | Ppv4 L | PV4 power (low) | 0.1W | |
| 3019 | Psys H | System output power (high) | 0.1W | |
| 3020 | Psys L | System output power (low) | 0.1W | |
| 3021 | Qac H | Reactive power (high) | 0.1Var | |
| 3022 | Qac L | Reactive power (low) | 0.1Var | |
| 3023 | Pac H | AC output power (high) | 0.1W | |
| 3024 | Pac L | AC output power (low) | 0.1W | |
| 3025 | Fac | Grid frequency | 0.01Hz | |
| 3026 | Vac1 | R-phase / single-phase grid voltage | 0.1V | |
| 3027 | Iac1 | R-phase / single-phase grid output current | 0.1A | |
| 3028 | Pac1 H | R-phase grid output apparent power (high) | 0.1VA | |
| 3029 | Pac1 L | R-phase grid output apparent power (low) | 0.1VA | |
| 3030 | Vac2 | S-phase grid voltage | 0.1V | |
| 3031 | Iac2 | S-phase grid output current | 0.1A | |
| 3032 | Pac2 H | S-phase grid output power (high) | 0.1VA | |
| 3033 | Pac2 L | S-phase grid output power (low) | 0.1VA | |
| 3034 | Vac3 | T-phase grid voltage | 0.1V | |
| 3035 | Iac3 | T-phase grid output current | 0.1A | |
| 3036 | Pac3 H | T-phase grid output power (high) | 0.1VA | |
| 3037 | Pac3 L | T-phase grid output power (low) | 0.1VA | |
| 3038 | Vac_RS | R-S line voltage | 0.1V | |
| 3039 | Vac_ST | S-T line voltage | 0.1V | |
| 3040 | Vac_TR | T-R line voltage | 0.1V | |
| 3041 | Ptouser total H | Total forward power (high) | 0.1W | |
| 3042 | Ptouser total L | Total forward power (low) | 0.1W | |
| 3043 | Ptogrid total H | Total reverse power (high) | 0.1W | |
| 3044 | Ptogrid total L | Total reverse power (low) | 0.1W | |
| 3045 | Ptoload total H | Total load power (high) | 0.1W | |
| 3046 | Ptoload total L | Total load power (low) | 0.1W | |
| 3047 | Time total H | Work time total (high) | 0.5s | |
| 3048 | Time total L | Work time total (low) | 0.5s | |
| 3049 | Eac today H | Today generate energy (high) | 0.1kWh | |
| 3050 | Eac today L | Today generate energy (low) | 0.1kWh | |
| 3051 | Eac total H | Total generate energy (high) | 0.1kWh | |
| 3052 | Eac total L | Total generate energy (low) | 0.1kWh | |
| 3053 | Epv_total H | PV energy total (high) | 0.1kWh | |
| 3054 | Epv_total L | PV energy total (low) | 0.1kWh | |
| 3055 | Epv1_today H | PV1 energy today (high) | 0.1kWh | |
| 3056 | Epv1_today L | PV1 energy today (low) | 0.1kWh | |
| 3057 | Epv1_total H | PV1 energy total (high) | 0.1kWh | |
| 3058 | Epv1_total L | PV1 energy total (low) | 0.1kWh | |
| 3059 | Epv2_today H | PV2 energy today (high) | 0.1kWh | |
| 3060 | Epv2_today L | PV2 energy today (low) | 0.1kWh | |
| 3061 | Epv2_total H | PV2 energy total (high) | 0.1kWh | |
| 3062 | Epv2_total L | PV2 energy total (low) | 0.1kWh | |
| 3063 | Epv3_today H | PV3 energy today (high) | 0.1kWh | |
| 3064 | Epv3_today L | PV3 energy today (low) | 0.1kWh | |
| 3065 | Epv3_total H | PV3 energy total (high) | 0.1kWh | |
| 3066 | Epv3_total L | PV3 energy total (low) | 0.1kWh | |
| 3067 | Etouser_today H | Today energy to user (high) | 0.1kWh | |
| 3068 | Etouser_today L | Today energy to user (low) | 0.1kWh | |
| 3069 | Etouser_total H | Total energy to user (high) | 0.1kWh | |
| 3070 | Etouser_total L | Total energy to user (low) | 0.1kWh | |
| 3071 | Etogrid_today H | Today energy to grid (high) | 0.1kWh | |
| 3072 | Etogrid_today L | Today energy to grid (low) | 0.1kWh | |
| 3073 | Etogrid_total H | Total energy to grid (high) | 0.1kWh | |
| 3074 | Etogrid_total L | Total energy to grid (low) | 0.1kWh | |
| 3075 | Eload_today H | Today energy of user load (high) | 0.1kWh | |
| 3076 | Eload_today L | Today energy of user load (low) | 0.1kWh | |
| 3077 | Eload_total H | Total energy of user load (high) | 0.1kWh | |
| 3078 | Eload_total L | Total energy of user load (low) | 0.1kWh | |
| 3079 | Epv4_today H | PV4 energy today (high) | 0.1kWh | |
| 3080 | Epv4_today L | PV4 energy today (low) | 0.1kWh | |
| 3081 | Epv4_total H | PV4 energy total (high) | 0.1kWh | |
| 3082 | Epv4_total L | PV4 energy total (low) | 0.1kWh | |
| 3083 | Epv_today H | PV energy today (high) | 0.1kWh | |
| 3084 | Epv_today L | PV energy today (low) | 0.1kWh | |
| 3085 | Reserved | Reserved | — | |
| 3086 | DeratingMode | Inverter derating mode | — | See appendix table 1 |
| 3087 | ISO | PV ISO value | 1kOhm | |
| 3088 | DCI_R | R-phase DCI current | 0.1mA | |
| 3089 | DCI_S | S-phase DCI current | 0.1mA | |
| 3090 | DCI_T | T-phase DCI current | 0.1mA | |
| 3091 | GFCI | GFCI current | 1mA | |
| 3092 | Bus Voltage | Total bus voltage | 0.1V | |
| 3093 | Temp1 | Inverter temperature | 0.1C | |
| 3094 | Temp2 | IPM temperature | 0.1C | |
| 3095 | Temp3 | Boost temperature | 0.1C | |
| 3096 | Temp4 | Reserved | 0.1C | |
| 3097 | Temp5 | Communication board temperature | 0.1C | |
| 3098 | P Bus Voltage | P-Bus inside voltage | 0.1V | |
| 3099 | N Bus Voltage | N-Bus inside voltage | 0.1V | |
| 3100 | IPF | Inverter output power factor | — | 0–20000 |
| 3101 | RealOPPercent | Real output power percent | 1% | 1–100 |
| 3102 | OPFullwatt H | Output max power limit (high) | 0.1W | |
| 3103 | OPFullwatt L | Output max power limit (low) | 0.1W | |
| 3104 | StandbyFlag | Inverter standby flag | — | Bit0=TurnOffOrder,Bit1=PVLow,Bit2=AC V/F out of scope |
| 3105 | Fault Maincode | Inverter fault main code | — | |
| 3106 | Warn Maincode | Inverter warning main code | — | |
| 3107 | Fault Subcode | Inverter fault sub code | — | bitfield |
| 3108 | Warn Subcode | Inverter warning sub code | — | bitfield |
| 3109 | Reserved | Reserved | — | bitfield |
| 3110 | Reserved | Reserved | — | bitfield |
| 3111 | uwPresentFFTValue [CHANNEL_A] | AFCI present FFT value channel A | — | bitfield |
| 3112 | bAfciStatus | AFCI status | — | 0=Waiting,1=Self-check,2=Detection,3=Fault,4=Update |
| 3113 | uwStrength [CHANNEL_A] | AFCI strength channel A | — | |
| 3114 | uwSelfCheckValue [CHANNEL_A] | AFCI self-check value channel A | — | |
| 3115 | inv start delay time | Inverter start delay time | 1s | |
| 3116 | Time total H | Work time total (high) | 0.5s | |
| 3117 | Time total L | Work time total (low) | 0.5s | |
| 3118 | BDC_OnOffState | BDC connection state | — | 0=No BDC, 1=BDC1, 2=BDC2, 3=BDC1+BDC2 |
| 3119 | DryContactState | Dry contact current status | — | 0=Off, 1=On |
| 3120 | Reserved | Reserved | — | |
| 3121 | Pself H | Self-use power (high) | 0.1W | |
| 3122 | Pself L | Self-use power (low) | 0.1W | |
| 3123 | Esys_today H | System energy today (high) | 0.1kWh | |
| 3124 | Esys_today L | System energy today (low) | 0.1kWh | |
| 3125 | Edischr_today H | Today discharge energy (high) | 0.1kWh | |
| 3126 | Edischr_today L | Today discharge energy (low) | 0.1kWh | |
| 3127 | Edischr_total H | Total discharge energy (high) | 0.1kWh | |
| 3128 | Edischr_total L | Total discharge energy (low) | 0.1kWh | |
| 3129 | Echr_today H | Charge energy today (high) | 0.1kWh | |
| 3130 | Echr_today L | Charge energy today (low) | 0.1kWh | |
| 3131 | Echr_total H | Charge energy total (high) | 0.1kWh | |
| 3132 | Echr_total L | Charge energy total (low) | 0.1kWh | |
| 3133 | Eacchr_today H | Today energy of AC charge (high) | 0.1kWh | |
| 3134 | Eacchr_today L | Today energy of AC charge (low) | 0.1kWh | |
| 3135 | Eacchr_total H | Total energy of AC charge (high) | 0.1kWh | |
| 3136 | Eacchr_total L | Total energy of AC charge (low) | 0.1kWh | |
| 3137 | Esys_total H | Total energy of system output (high) | 0.1kWh | |
| 3138 | Esys_total L | Total energy of system output (low) | 0.1kWh | |
| 3139 | Eself_today H | Today energy of self output (high) | 0.1kWh | |
| 3140 | Eself_today L | Today energy of self output (low) | 0.1kWh | |
| 3141 | Eself_total H | Total energy of self output (high) | 0.1kWh | |
| 3142 | Eself_total L | Total energy of self output (low) | 0.1kWh | |
| 3143 | Reserved | Reserved | — | |
| 3144 | Priority Word | Mode priority | — | 0=LoadFirst, 1=BatteryFirst, 2=GridFirst |
| 3145 | EPS Fac | UPS frequency | 0.01Hz | |
| 3146 | EPS Vac1 | UPS phase R output voltage | 0.1V | |
| 3147 | EPS Iac1 | UPS phase R output current | 0.1A | |
| 3148 | EPS Pac1 H | UPS phase R output power (high) | 0.1VA | |
| 3149 | EPS Pac1 L | UPS phase R output power (low) | 0.1VA | |
| 3150 | EPS Vac2 | UPS phase S output voltage | 0.1V | |
| 3151 | EPS Iac2 | UPS phase S output current | 0.1A | |
| 3152 | EPS Pac2 H | UPS phase S output power (high) | 0.1VA | |
| 3153 | EPS Pac2 L | UPS phase S output power (low) | 0.1VA | |
| 3154 | EPS Vac3 | UPS phase T output voltage | 0.1V | |
| 3155 | EPS Iac3 | UPS phase T output current | 0.1A | |
| 3156 | EPS Pac3 H | UPS phase T output power (high) | 0.1VA | |
| 3157 | EPS Pac3 L | UPS phase T output power (low) | 0.1VA | |
| 3158 | EPS Pac H | UPS total output power (high) | 0.1VA | |
| 3159 | EPS Pac L | UPS total output power (low) | 0.1VA | |
| 3160 | Loadpercent | Load percent of UPS output | 0.1% | |
| 3161 | PF | Power factor | 0.1 | |
| 3162 | DCV | DC voltage | 1mV | |
| 3163 | Reserved | Reserved | — | |
| 3164 | NewBdcFlag | Whether to parse BDC data separately | — | 0=No, 1=Yes |
| 3165 | BDCDeratingMode | Battery derating mode | — | See appendix table 2 |
| 3166 | SysState_Mode | System work state and mode | — | High 8-bit=mode (0=No CHG/DISCHG,1=Charge,2=Discharge); Low 8-bit=status (0=Standby,1=Normal,2=Fault,3=Flash) |
| *BDC1 battery data — 3167–3232* | | | | |
| 3167 | FaultCode | Storage device fault code | — | |
| 3168 | WarnCode | Storage device warning code | — | |
| 3169 | Vbat | Battery voltage | 0.01V | **Note:** spec says 0.01V; MOD TL3-XH hardware uses 0.1V scale (corrected in v0.8.0) |
| 3170 | Ibat | Battery current | 0.1A | |
| 3171 | SOC | State of charge | 1% | |
| 3172 | Vbus1 | Total BUS voltage | 0.1V | |
| 3173 | Vbus2 | Upper BUS voltage | 0.1V | |
| 3174 | Ibb | BUCK-BOOST current | 0.1A | |
| 3175 | Illc | LLC current | 0.1A | |
| 3176 | TempA | Temperature A | 0.1C | |
| 3177 | TempB | Temperature B | 0.1C | |
| 3178 | Pdischr H | Discharge power (high) | 0.1W | |
| 3179 | Pdischr L | Discharge power (low) | 0.1W | |
| 3180 | Pchr H | Charge power (high) | 0.1W | |
| 3181 | Pchr L | Charge power (low) | 0.1W | |
| 3182 | Edischr_total H | Discharge total energy of storage device (high) | 0.1kWh | |
| 3183 | Edischr_total L | Discharge total energy of storage device (low) | 0.1kWh | |
| 3184 | Echr_total H | Charge total energy of storage device (high) | 0.1kWh | |
| 3185 | Echr_total L | Charge total energy of storage device (low) | 0.1kWh | |
| 3186 | Reserved | Reserved | — | |
| 3187 | BDC1_Flag | BDC mark (charge/discharge/fault/alarm) | — | Bit0=ChargeEn, Bit1=DischargeEn, Bit8-11=WarnSubCode, Bit12-15=FaultSubCode |
| 3188 | Vbus2 | Lower BUS voltage | 0.1V | |
| 3189 | BmsMaxVoltCellNo | BMS max voltage cell number | — | |
| 3190 | BmsMinVoltCellNo | BMS min voltage cell number | — | |
| 3191 | BmsBatteryAvgTemp | BMS battery average temperature | — | |
| 3192 | BmsMaxCellTemp | BMS max cell temperature | 0.1C | |
| 3193 | BmsBatteryAvgTemp2 | BMS battery average temperature (2) | 0.1C | |
| 3194 | BmsMaxCellTemp2 | BMS max cell temperature (2) | — | |
| 3195 | BmsBatteryAvgTemp3 | BMS battery average temperature (3) | — | |
| 3196 | BmsMaxSOC | BMS max SOC | 1% | |
| 3197 | BmsMinSOC | BMS min SOC | 1% | |
| 3198 | ParallelBatteryNum | Parallel battery number | — | |
| 3199 | BmsDerateReason | BMS derate reason | — | |
| 3200 | BmsGaugeFCC | BMS gauge FCC (Ah) | — | |
| 3201 | BmsGaugeRM | BMS gauge RM (Ah) | — | |
| 3202 | BmsError | BMS protect 1 | — | |
| 3203 | BmsWarn | BMS warning 1 | — | |
| 3204 | BmsFault | BMS fault 1 | — | |
| 3205 | BmsFault2 | BMS fault 2 | — | |
| 3206 | Reserved | Reserved | — | |
| 3207 | Reserved | Reserved | — | |
| 3208 | Reserved | Reserved | — | |
| 3209 | Reserved | Reserved | — | |
| 3210 | BatIsoStatus | Battery ISO detection status | — | 0=Not detected, 1=Detection completed |
| 3211 | BattNeedChargeRequestFlag | Battery work request | — | Bit0=ProhibitCharging, Bit1=StrongCharge, Bit2=StrongCharge2, Bit8=ProhibitDischarge, Bit9=PowerReduction |
| 3212 | BMS_Status | Battery working status | — | 0=Dormancy,1=Charge,2=Discharge,3=Free,4=Standby,5=SoftStart,6=Fault,7=Update |
| 3213 | BmsError2 | BMS protect 2 | — | R |
| 3214 | BmsWarn2 | BMS warning 2 | — | R |
| 3215 | BMS_SOC | BMS SOC | 1% | R |
| 3216 | BMS_BatteryVolt | BMS battery voltage | 0.01V | R |
| 3217 | BMS_BatteryCurr | BMS battery current | 0.01A | R |
| 3218 | BMS_BatteryTemp | Battery cell maximum temperature | 0.1C | R |
| 3219 | BMS_MaxCurr | Maximum charging current | 0.01A | R |
| 3220 | BMS_MaxDischrCurr | Maximum discharge current | 0.01A | R |
| 3221 | BMS_CycleCnt | BMS cycle count | 1 | R |
| 3222 | BMS_SOH | BMS state of health | 1 | R |
| 3223 | BMS_ChargeVoltLimit | Battery charging voltage limit | 0.01V | R |
| 3224 | BMS_DischargeVoltLimit | Battery discharge voltage limit | 0.01V | R |
| 3225 | Bms Warn3 | BMS warning 3 | 1 | R |
| 3226 | Bms Error3 | BMS protect 3 | 1 | R |
| 3227 | Reserved | Reserved | — | |
| 3228 | Reserved | Reserved | — | |
| 3229 | Reserved | Reserved | — | |
| 3230 | BMSSingleVoltMax | BMS battery single volt max | 0.001V | R |
| 3231 | BMSSingleVoltMin | BMS battery single volt min | 0.001V | R |
| 3232 | BatLoadVolt | Battery load voltage | 0.01V | R; [0, 650.00V] |
| 3233 | Reserved | Reserved | — | |
| *Debug data — 3234–3249* | | | | |
| 3234 | Debug data1 | Debug data 1 | — | R |
| 3235 | Debug data2 | Debug data 2 | — | R |
| 3236 | Debug data3 | Debug data 3 | — | R |
| 3237 | Debug data4 | Debug data 4 | — | R |
| 3238 | Debug data5 | Debug data 5 | — | R |
| 3239 | Debug data6 | Debug data 6 | — | R |
| 3240 | Debug data7 | Debug data 7 | — | R |
| 3241 | Debug data8 | Debug data 8 | — | R |
| 3242 | Debug data9 | Debug data 9 | — | R |
| 3243 | Debug data10 | Debug data 10 | — | R |
| 3244 | Debug data11 | Debug data 11 | — | R |
| 3245 | Debug data12 | Debug data 12 | — | R |
| 3246 | Debug data13 | Debug data 13 | — | R |
| 3247 | Debug data14 | Debug data 14 | — | R |
| 3248 | Debug data15 | Debug data 15 | — | R |
| 3249 | Debug data16 | Debug data 16 | — | R |
| *Backup box / external inverter data — 3250–3342* | | | | |
| 3250 | Pex1H | PV inverter 1 output power (high) | 0.1W | R |
| 3251 | Pex1L | PV inverter 1 output power (low) | 0.1W | R |
| 3252 | Pex2H | PV inverter 2 output power (high) | 0.1W | R |
| 3253 | Pex2L | PV inverter 2 output power (low) | 0.1W | R |
| 3254 | Eex1TodayH | PV inverter 1 energy today (high) | 0.1kWh | R |
| 3255 | Eex1TodayL | PV inverter 1 energy today (low) | 0.1kWh | R |
| 3256 | Eex2TodayH | PV inverter 2 energy today (high) | 0.1kWh | R |
| 3257 | Eex2TodayL | PV inverter 2 energy today (low) | 0.1kWh | R |
| 3258 | Eex1TotalH | PV inverter 1 energy total (high) | 0.1kWh | R |
| 3259 | Eex1TotalL | PV inverter 1 energy total (low) | 0.1kWh | R |
| 3260 | Eex2TotalH | PV inverter 2 energy total (high) | 0.1kWh | R |
| 3261 | Eex2TotalL | PV inverter 2 energy total (low) | 0.1kWh | R |
| 3262 | uwBatNo | Battery pack number | — | R; updates every 15 min |
| 3263 | BatSerialNum1 | Battery pack serial SN[0]SN[1] | — | R |
| 3264 | BatSerialNum2 | Battery pack serial SN[2]SN[3] | — | R |
| 3265 | BatSerialNum3 | Battery pack serial SN[4]SN[5] | — | R |
| 3266 | BatSerialNum4 | Battery pack serial SN[6]SN[7] | — | R |
| 3267 | BatSerialNum5 | Battery pack serial SN[8]SN[9] | — | R |
| 3268 | BatSerialNum6 | Battery pack serial SN[10]SN[11] | — | R |
| 3269 | BatSerialNum7 | Battery pack serial SN[12]SN[13] | — | R |
| 3270 | BatSerialNum8 | Battery pack serial SN[14]SN[15] | — | R |
| 3271–3276 | Reserved | Reserved | — | |
| 3277 | bInvSnNumberFlag | Inverter SN number flag | — | R; 0=Other,1=10-bit,2=16-bit,3=21-bit |
| 3278 | bBatterySnNumberFlag | Battery SN number flag | — | R; Bit0-7=BDC1 type, Bit8-15=BDC2 type |
| 3279 | bBoxSnNumberFlag | Backup box SN number flag | — | R; 0=Other,1=10-bit,2=16-bit,3=21-bit |
| 3280 | bClrTodayDataFlag | Clear day data flag | — | R; 0=Not cleared, 1=Cleared |
| 3281 | ubBypassStatus | Backup box bypass switch status | — | R; 0=Off, 1=On |
| 3282 | ubWorkMode | Backup box work mode | — | R; 0=Offgrid, 1=Ongrid, 2=Generator |
| 3283 | ubFanStatus | Backup box fan status | — | R; 0=Off, 1=On |
| 3284 | uwErrorCode | Backup box error code | — | R; 700–800 range |
| 3285 | uwWarnCode | Backup box warning code | — | R; 700–800 range |
| 3286 | bNtcTemp | Backup box temperature | 1C | R; Int8; -40 to 100 |
| 3287 | uwGridVolt | Backup box grid voltage | 0.1V | R |
| 3288 | uwGridCurr | Backup box grid current | 0.1A | R |
| 3289 | dGridWatt_H | Backup box grid power (high) | 0.1W | R; Int32 |
| 3290 | dGridWatt_L | Backup box grid power (low) | 0.1W | R |
| 3291 | uwGridFreq | Backup box grid frequency | 0.01Hz | R |
| 3292 | uwGenVolt | Backup box generator voltage | 0.1V | R |
| 3293 | uwGenCurr | Backup box generator current | 0.1A | R |
| 3294 | DGenWatt_H | Backup box generator power (high) | 0.1W | R; Int32 |
| 3295 | DGenWatt_L | Backup box generator power (low) | 0.1W | R |
| 3296 | uwGenFreq | Backup box generator frequency | 0.01Hz | R |
| 3297 | dLoadWatt_H | Backup box load power (high) | 0.1W | R; Uint32 |
| 3298 | dLoadWatt_L | Backup box load power (low) | 0.1W | R |
| 3299 | uwFirmwareCode_H | Backup box firmware code (high) | — | R; 4 ASCII chars |
| 3300 | uwFirmwareCode_L | Backup box firmware code (low) | — | R |
| 3301 | ubFirmwareVersion | Backup box firmware version | — | R; Uint8 |
| 3302 | uwSerialNum0 | Backup box serial number word 0 | — | R; 30 ASCII chars total |
| 3303 | uwSerialNum1 | Backup box serial number word 1 | — | R |
| 3304 | uwSerialNum2 | Backup box serial number word 2 | — | R |
| 3305 | uwSerialNum3 | Backup box serial number word 3 | — | R |
| 3306 | uwSerialNum4 | Backup box serial number word 4 | — | R |
| 3307 | uwSerialNum5 | Backup box serial number word 5 | — | R |
| 3308 | uwSerialNum6 | Backup box serial number word 6 | — | R |
| 3309 | uwSerialNum7 | Backup box serial number word 7 | — | R |
| 3310 | uwSerialNum8 | Backup box serial number word 8 | — | R |
| 3311 | uwSerialNum9 | Backup box serial number word 9 | — | R |
| 3312 | uwSerialNum10 | Backup box serial number word 10 | — | R |
| 3313 | uwSerialNum11 | Backup box serial number word 11 | — | R |
| 3314 | uwSerialNum12 | Backup box serial number word 12 | — | R |
| 3315 | uwSerialNum13 | Backup box serial number word 13 | — | R |
| 3316 | uwSerialNum14 | Backup box serial number word 14 | — | R |
| 3317 | uwGridVoltS | Backup box S-phase grid voltage (XH models) | 0.1V | R |
| 3318 | uwGridVoltT | Backup box T-phase grid voltage (XH models) | 0.1V | R |
| 3319 | uwGridFreqS | Backup box S-phase grid frequency (XH models) | 0.01Hz | R |
| 3320 | bBoxConnectFlag | Backup box communication status | — | R; 0=Abnormal, 1=Normal |
| 3321 | bBoxDataUploadFlag | Backup box upload flag | — | R; 0=No, 1=Yes |
| 3322 | MeterConnectFlag | Ankeri meter connection status | — | R; 0=Invalid, 1=Normal |
| 3323 | SYNInstalledFlag | Backup box installation flag | — | R; 0=Not installed, 1=Installed |
| 3324 | BoxUnbalanceCurrent | Backup box unbalance current | 0.1A | R |
| 3325–3341 | Reserved | Reserved | — | |
| 3342 | InvRelayStatus | Backup box inv relay status | — | R; 0=Not supported/comm error, 1=Open, 2=Close |
| 3343 | GenvRelayStatus | Generator relay status | — | R; 0=Not supported/comm error, 1=Open, 2=Close |
| 3344–3409 | Reserved | Reserved | — | |
| *Error/warning bits — 3410–3417* | | | | |
| 3410 | ErrorBit1 | Error bit 1 | — | |
| 3411 | ErrorBit2 | Error bit 2 | — | |
| 3412 | ErrorBit3 | Error bit 3 | — | |
| 3413 | ErrorBit4 | Error bit 4 | — | |
| 3414 | WarningBit1 | Warning bit 1 | — | |
| 3415 | WarningBit2 | Warning bit 2 | — | |
| 3416 | WarningBit3 | Warning bit 3 | — | |
| 3417 | WarningBit4 | Warning bit 4 | — | |
| *BDC parallel — 10 BDCs (4000–5079)* | | | | |
| 4000–4107 | BDC1 | BDC1 data block | — | 8 regs SN + 69 regs same layout as 3165–3233 + 31 reserved |
| 4108–4215 | BDC2 | BDC2 data block | — | Same structure as BDC1 |
| 4216–4323 | BDC3 | BDC3 data block | — | Same structure |
| 4324–4431 | BDC4 | BDC4 data block | — | Same structure |
| 4432–4539 | BDC5 | BDC5 data block | — | Same structure |
| 4540–4647 | BDC6 | BDC6 data block | — | Same structure |
| 4648–4755 | BDC7 | BDC7 data block | — | Same structure |
| 4756–4863 | BDC8 | BDC8 data block | — | Same structure |
| 4864–4971 | BDC9 | BDC9 data block | — | Same structure |
| 4972–5079 | BDC10 | BDC10 data block | — | Same structure |
| *APX battery module — up to 64 parallel BDCs (5080+)* | | | | |
| 5080 | BatSysState | System working state | — | 0=Initialize,1=Standby,2=Charge,3=Discharge,4=Shutdown,5=Fault,6=Update |
| 5081 | BatSOC | Battery state of charge | 1% | Bit15-8=Mapping SOC[0,100]; Bit7-0=SOC[0,100] |
| 5082 | BatSOH | Battery state of health | 1% | Bit7=1:NeedScrap; Bit6-0=SOH[0,100] |
| 5083 | BatVolt | Total internal voltage of battery system | 0.1V | [0, 1500.0V] |
| 5084 | BatCurrent | Battery system current | 0.1A | [-1000.0, 1000.0A] |
| 5085 | BatPower | Charge and discharge power | 1W | [-32000, 32000W] |
| 5086 | BatTotalDischargeElectric H | Cumulative discharge energy (high) | 0.1kWh | [0, 2000000.0 kWh] |
| 5087 | BatTotalDischargeElectric L | Cumulative discharge energy (low) | 0.1kWh | |
| 5088 | BatMaxCellVolt | Maximum cell voltage | 0.001V | [0, 6.000V] |
| 5089 | BatMinCellVolt | Minimum cell voltage | 0.001V | [0, 6.000V] |
| 5090 | BatMaxTemp | Maximum battery temperature | 0.1C | [-40.0, 125.0C] |
| 5091 | BatMinTemp | Minimum battery temperature | 0.1C | [-40.0, 125.0C] |
| 5092 | BatMaxLimitChargeCurrent | Maximum allowable charging current | 0.1A | [0, 1000.0A] |
| 5093 | BatMaxLimitDischargeCurrent | Maximum allowable discharge current | 0.1A | (truncated in source) |
