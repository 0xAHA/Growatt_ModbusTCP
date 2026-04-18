# Off-Grid Protocol V0.26

> **Source document:** Growatt OffGrid Modbus RS485/RS232 RTU Protocol V0.26
>
> This is the protocol used by Growatt's off-grid and AC-coupled inverter families.
> It covers registers 0–97 only; VPP registers are never used with these models.
>
> **Applicable models:**
> - **SPF 3000-6000 ES PLUS** — off-grid with battery, no grid export
> - **SPE 8000-12000 ES** — higher-capacity off-grid / AC-coupled storage

---

## Register Ranges

| Range | Purpose |
| --- | --- |
| 0–97 | All registers (holding and input share the same base range) |

---

## Holding Registers (311 registers)

| Address | Name | Description | Access | Range |
| --- | --- | --- | --- | --- |
| 0 | On/Off | The Standby On/Off state and the AC output DisEN/EN state; The low byte is the Standby on/off(1/0), the high byte is the AC output disable/enable (1/0). |  | 0x0000: Output enable; 0x0100: Output disable; |
| 1 | OutputConfig | AC output set | W | 0: BAT First; 1: PV First; 2: UTI First; 3: PV&UTI First |
| 2 | ChargeConfig | Charge source set | W | 0: PV first; 1: PV&UTI; 2: PV Only; |
| 3 | UtiOutStart | Uti Time | W | bit0~bit7 |
| 4 | UtiOutEnd | Uti Output End Time | W | bit0~bit7 |
| 5 | UtiChargeStart | Uti Time | W | bit0~bit7 |
| 6 | UtiChargeEnd | Uti Charge End Time | W | bit0~bit7 |
| 7 | PVModel | PV Input Mode | W | 0:Independent; 1: Parallel; |
| 8 | ACInModel | AC Input Mode | W | 0: 1: 2: |
| 9 | Fw version H | Firmware version (high) |  |  |
| 10 | Fw version M | Firmware version (middle) |  |  |
| 11 | Fw version L | Firmware version (low) |  |  |
| 12 | Fw version2 H | Control Firmware version (high) |  |  |
| 13 | Fw version2 M | Control Firmware version (middle) |  |  |
| 14 | Fw version2 L | Control Firmware version (low) |  |  |
| 15 | LCD language | LCD language | W | 0-1 |
| 16 | GridV_Adj |  |  |  |
| 17 | InvV_Adj |  |  |  |
| 18 | OutputVoltType | Output Volt Type | W | 0: 208VAC; 1: 230VAC |
| 19 | OutputFreqType | Output Freq Type | W | 0: 50Hz; 1: 60Hz |
| 20 | OverLoadRestart | Over Load Restart | W | 0:Yes; 1:No; 2: Swith to UTI; |
| 21 | OverTempRestart | Over Temperature Restart | W | 0:Yes; 1:No; |
| 22 | BuzzerEN | Buzzer on/off enable | W | 1:Enable; 0:Disable; |
| 23 | Serial NO. 5 | Serial number 5 | W |  |
| 24 | Serial No. 4 | Serial number 4 | W |  |
| 25 | Serial No. 3 | Serial number 3 | W |  |
| 26 | Serial No. 2 | Serial number 2 | W |  |
| 27 | Serial No. 1 | Serial number 1 | W |  |
| 28 | Module H | Inverter Module (high) | W | 0: model can be modify |
| 29 | Module L | Inverter Module (low) | W | eg: 50 for 5.0KW model |
| 30 | Com Address | Communicate addr ess | W | 1~254 ， but 253 only for debug |
| 31 | FlashStart | Update firmware | W | 0x0001: own 0X0100: control broad |
| 32 | Reset User Info | Reset User Information | W | 0x0001 |
| 33 | Reset to factory | Reset to factory | W | 0x0001 |
| 34 | MaxChargeCurr | Max Charge Current | W | 0~400 |
| 35 | BulkChargeVolt | Bulk Charge Volt | W | 500~640- |
| 36 | FloatChargeVolt | Float Charge Volt | W | 500~560 |
| 37 | BatLowToUtiVolt | Bat Low Volt Switch To Uti | W |  |
| 38 | ACChargeCurr | AC Charge Current | W | 0~400 |
| 39 | Battery Type | Battery Type | W | 0: AGM / 1: FLD / 2: USE / 3: Lithium / 4: USE2 |
| 40 | Aging Mode | Aging Mode | W | 0: Normal Mode / 1: Aging Mode |
| 41 | Function Mask |  | W | bit0=Etl check enable |
| 42 | Safety Type |  | W |  |
| 43 | DTC | Device Type Code |  | See DTC Table |
| 44 | --- |  |  |  |
| 45 | Sys Year | System time-year | W | Year offset is 2000 |
| 46 | Sys Month | System time- Month | W |  |
| 47 | Sys Day | System time- Day | W |  |
| 48 | Sys Hour | System time- Hour | W |  |
| 49 | Sys Min | System time- Min | W |  |
| 50 | Sys Sec | System time- Second | W |  |
| 51 | Chip Select |  |  | 01 for Master 02 for Slave 03 for Arm |
| 52 | Var1 Value |  |  |  |
| 53 | Var2 Value |  |  |  |
| 54 | Var1 address |  |  |  |
| 55 | Var2 address |  |  |  |
| 56 | Var1 Setting |  |  |  |
| 57 | DebugModeEn | Debug mode enable |  | 0:disable; 1:Enable; |
| 58 | --- |  |  |  |
| 59 | Manufacturer Info 8 | Manufacturer information (high) |  |  |
| 60 | Manufacturer Info 7 | Manufacturer information (middle) |  |  |
| 61 | Manufacturer Info 6 | Manufacturer information (low) |  |  |
| 62 | Manufacturer Info 5 | Manufacturer information (high) |  |  |
| 63 | Manufacturer Info 4 | Manufacturer information (middle) |  |  |
| 64 | Manufacturer Info3 | Manufacturer information (low) |  |  |
| 65 | Manufacturer Info 2 | Manufacturer information (low) |  |  |
| 66 | Manufacturer Info 1 | Manufacturer information (high) |  |  |
| 67 | FW Build No. 4 | Control FW Build No. 2 |  |  |
| 68 | FW Build No. 3 | Control FW Build No. 1 |  |  |
| 69 | FW Build No. 2 | COM FW Build No. 2 |  |  |
| 70 | FW Build No. 1 | COM FW Build No. 1 |  |  |
| 71 | --- |  |  |  |
| 72 | Sys Weekly | Sys Weekly | W | 0-6 |
| 73 | ModbusVersion | Modbus Version |  | Eg：207 is V2.07 |
| 74 | --- |  |  |  |
| 75 | SCC_ComMode | SCC Communication Mode |  |  |
| 76 | Rate Watt H | Rate active power(high) |  |  |
| 77 | Rate Watt L | Rate active power(low) |  |  |
| 78 | Rate VA H | Rata apparent power (high) |  |  |
| 79 | Rate VA L | Rate apparent power (low) |  |  |
| 80 | ComboardVer | Communicaiton board Version |  |  |
| 81 | uwBatPieceNum |  |  |  |
| 82 | wBatLowCutOff | Bat cutoff |  |  |
| 83 | MaxGenChgCurr | maximum generator charge current |  | 0~400 |
| 84 | NomGridVolt |  |  |  |
| 85 | NomGridFreq |  |  |  |
| 86 | NomBatVolt |  |  |  |
| 87 | NomPvCurr |  |  |  |
| 88 | NomAcChgCurr |  |  |  |
| 89 | NomOpVolt |  |  |  |
| 90 | NomOpFreq |  |  |  |
| 91 | NomOpPow |  |  |  |
| 92 | --- |  |  |  |
| 93 | --- |  |  |  |
| 94 | --- |  |  |  |
| 95 | uwAC2BatVolt | AC switch to Battery |  | 200 - 640 (non Lithium) <br> 5 - 100 (Lithium) |
| 96 | BypEnable |  |  |  |
| 97 | PowSavingEn |  |  |  |
| 98 | SpowBalEn |  |  |  |
| 99 | ClrEnergyToday |  |  |  |
| 100 | clrEnergyAll |  |  |  |
| 101 | BurnInTestEn |  |  |  |
| 102 | ManualStartEn |  |  |  |
| 103 | SciLossChkEn |  |  |  |
| 104 | BlightEn |  |  |  |
| 105 | ParaMaxChgCurr | Parallel System Maximum charge current |  |  |
| 106 | LiProtocolType | Protocol type for battery |  |  |
| 107 | AudioAlarmEn |  |  |  |
| 108 | uwEqEn |  |  |  |
| 109 | uwEqChgVolt |  |  |  |
| 110 | uwEqTime |  |  |  |
| 111 | uwEqTimeOut |  |  |  |
| 112 | uwEqInterval |  |  |  |
| 113 | uwMaxDisChgCurr |  |  |  |
| 114 | uwFaultResartEn | Fault restart enable |  | 0:disable; 1:Enable; |
| 115 | uwFeedEn | grid feed enable |  | 0:disable; 1:Enable; |
| 116 | uwLoadFirst | Load first or Charge first |  | 0:charge first; 1:load first; 2:Feed first; |
| 117 | uwFeedRange | feed range |  | 0:Asia; 1:Europe; 2:South american; 3:South africa |
| 118 | uwBatFeedEn | battery feed enable |  | 0:disable; 1:Enable; |
| 119 | uwFeedPow | feed power limit |  | 0-120 |
| 120 | uwBatFeedCurr | battery feed current |  | 0-400 |
| 121 | uwBatFeedVLoss | battery feed voltage loss point |  | 420-540 |
| 122 | uwBatFeedVBack | battery feed voltage back point |  | 440-560 |
| 123 | uwBatFeedSocLos s | battery feed Soc loss point |  | 5-90 |
| 124 | uwBatFeedSocBac k | battery feed Soc back point |  | 15-100 |
| 125 | uwBatFeedTimeSt art1 | battery feed time1 start |  | bit0~bit7 |
| 126 | uwBatFeedTimeE | battery feed time1 end |  | bit0~bit7 |
| 127 | uwBatFeedTimeSt art2 | battery feed time2 start |  | bit0~bit7 |
| 128 | uwBatFeedTimeE nd2 | battery feed time2 end |  | bit0~bit7 |
| 129 | uwBatFeedTimeSt art3 | battery feed time3 start |  | bit0~bit7 |
| 130 | uwBatFeedTimeE nd3 | battery feed time3 end |  | bit0~bit7 |
| 131 | uwGridChgTimeSt art1 | grid charge time1 start |  | bit0~bit7 |
| 132 | uwGridChgTimeEn d1 | grid charge time1 end |  | bit0~bit7 |
| 133 | uwGridChgTimeSt art2 | grid charge time2 start |  | bit0~bit7 |
| 134 | uwGridChgTimeEn d2 | grid charge time2 end |  | bit0~bit7 |
| 135 | uwGridChgTimeSt art3 | grid charge time3 start |  | bit0~bit7 |
| 136 | uwGridChgTimeEn d3 | grid charge time3 end |  | bit0~bit7 |
| 137 | MaxGenRunTime | Maximum Generator Running Time |  | 0-23 |
| 138 | LiBatChgIntervalE n | Li Bat Charge interval Enable |  | 0:disable; 1:Enable; |
| 139 | LiBatChgInterval | Li Bat Charge interval |  | 1~90 |
| 140 | NgRlyEn | Ng Relay enable |  | 0:disable; 1:Enable; |
| 141 | GridAlwaysOnEn | Gird mode allows the second output to be always on |  | 0:disable; 1:Enable; |
| 142 | Op2TimeStart1 | Second output time1 Start |  | bit0~bit7 |
| 143 | Op2TimeEnd1 | Second output time1 end |  | bit0~bit7 |
| 144 | Op2TimeStart2 | Second output time2 Start |  | bit0~bit7 |
| 145 | Op2TimeEnd2 | Second output time2 end |  | bit0~bit7 |
| 146 | Op2TimeStart3 | Second output time3 Start |  | bit0~bit7 |
| 147 | Op2TimeEnd3 | Second output time3 end |  | bit0~bit7 |
| 148 | Op2VoltLoss | Second output volt loss point |  | 400~580 |
| 149 | Op2SocLoss | Second output soc loss point |  | 10~100 |
| 150 | Op2VoltBack | Second output volt back point |  | 440~600 |
| 151 | Op2SocBack | Second output soc back point |  | 10~100 |
| 152 | PvLowLimWatt | Pv low limit watt for the second output start |  | 0-120 |
| 153 | MenuBackEn | Menu back main interface enable |  | 0:disable; 1:Enable; |
| 154 | BmsErrWorkEn | Bms comm errer work enable |  | 0:disable; 1:Enable; |
| 155 | ExternalCtEn | External Ct enable |  | 0:disable; 1:Enable; |
| 156 | ExtCtSampleRate | External Ct sample rate |  | 1000-9999 |
| 157 | ShavingPow | Grid peak-shaving power |  | 0-240 |
| 158 | ExpLimPow | export limit power |  | 0-120 |
| 159 | TypicalSet | Typical setup |  | 0:User defined; 1:On Grid; 2:Zero Export Limit; 3:Off Grid; |
| 160 | EtlEn | Etl check enable |  | 0:disable; 1:Enable; |
| 161 | PvIsoEn | Pv Iso check enable |  | 0:disable; 1:Enable; |
| 162 | GfciFastProtEn | Gfci fast protect enabel |  | 0:disable; 1:Enable; |
| 163 | FeedVoltHighLoss | Feed grid high volt loss |  | 240~280Vac |
| 164 | FeedVoltLowLoss | Feed grid low volt loss |  | 170~200Vac |
| 165 | FeedFreqHighLoss | Feed grid high freq loss |  | 50 Hz system: 510~550 Hz 60 Hz system: 610~650 Hz |
| 166 | FeedFreqLowLoss | Feed grid low freq loss |  | 50 Hz system: 450~490 Hz |
| 167 | PvDcSourceEn | Pv dc source enable |  | 0:disable; 1:Enable; |
| 168 | ShavingEn | Shaving enble |  | 0:disable; 1:Enable; |
| 169 | DryContactEn | Dry contact enble |  | 0:Auto; 1:Enable; 2:disable; |
| 209 | uwNewSerNum15 | New Serial Num15 |  |  |
| 210 | uwNewSerNum14 | New Serial Num14 |  |  |
| 211 | uwNewSerNum13 | New Serial Num13 |  |  |
| 212 | uwNewSerNum12 | New Serial Num12 |  |  |
| 213 | uwNewSerNum11 | New Serial Num11 |  |  |
| 214 | uwNewSerNum10 | New Serial Num10 |  |  |
| 215 | uwNewSerNum9 | New Serial Num9 |  |  |
| 216 | uwNewSerNum8 | New Serial Num8 |  |  |
| 217 | uwNewSerNum7 | New Serial Num7 |  |  |
| 218 | uwNewSerNum6 | New Serial Num6 |  |  |
| 219 | uwNewSerNum5 | New Serial Num5 |  |  |
| 220 | uwNewSerNum4 | New Serial Num4 |  |  |
| 221 | uwNewSerNum3 | New Serial Num3 |  |  |
| 222 | uwNewSerNum2 | New Serial Num2 |  |  |
| 223 | uwNewSerNum1 | New Serial Num1 |  |  |
| 300 | uwHVDecLoadStar t | Grid high volt load reduction start value |  | 0~2800 |
| 301 | uwHVDecLoadEnd | Grid high volt load reduction end value |  | 0~2800 |
| 302 | uwHFreqDecLoad Start | Grid high Freq load reduction start value |  | 0~65000 |
| 303 | uwHFreqDecLoad End | Grid high Freq load reduction end value |  | 0~65000 |
| 304 | uwLFreqDecLoadS tart | Grid low Freq load reduction start value |  | 56000~60000 |
| 305 | uwLFreqDecLoadE nd | Grid low Freq load reduction end value |  | 56000~60000 |
| 306 | uwFreqSlope1 | Underfrequency loading slope |  | 20~70 |
| 307 | uwFreqSlope2 | Over frequency loading slope |  | 20~70 |
| 308 | wHVDecWatt1 | Grid high volt load reduction Watt 1 |  | 0~100 |
| 309 | wHVDecWatt2 | Grid high volt load reduction Watt 2 |  | -100~100 |
| 310 | uwPfModelSet | Set PF function mode |  | 0: Reactive power generation is prohibited<br>1: Constant (Fixed PF mode)<br>2: Watt/Var (Active and reactive modes)<br>3: Constant Var (Fixed reactive power percentage)<br>4: Volt/Var (volt reactive power mode) |
| 311 | wPfSet | Power factor set |  | -1000~1000 (cannot be 0) |
| 312 | wGridVoltLowStar t | Grid volt low at startup |  | 0~3000 |
| 313 | wGridVoltHighStar t | Grid volt high at startup |  | 0~3000 |
| 314 | wGridFreqLowSta rt | Grid freq low at startup |  | 0~6600 |
| 315 | wGridFreqHighSta rt | Grid freq high at startup |  | 0~6600 |
| 316 | uwVoltLLPercent1 | Volt Low Loss Percent1 |  | 1-130 |
| 317 | uwVoltLLPercent2 | Volt Low Loss Percent2 |  | 1-130 |
| 318 | uwVoltLLPercent3 | Volt Low Loss Percent3 |  | 1-130 |
| 319 | --- |  |  |  |
| 320 | uwVoltHLPercent1 | Volt High Loss Percent1 |  | 1-130 |
| 321 | uwVoltHLPercent2 | Volt High Loss Percent2 |  | 1-130 |
| 322 | uwVoltHLPercent3 | Volt High Loss Percent3 |  | 1-130 |
| 323 | --- |  |  |  |
| 324 | uwFreqLL1 | Freq Low Loss1 |  | 4500~6600 |
| 325 | uwFreqLL2 | Freq Low Loss2 |  | 4500~6600 |
| 326 | uwFreqLL3 | Freq Low Loss3 |  | 4500~6600 |
| 327 | uwFreqLL4 | Freq Low Loss4 |  | 4500~6600 |
| 328 | uwFreqHL1 | Freq High Loss1 |  | 4500~6600 |
| 329 | uwFreqHL2 | Freq High Loss2 |  | 4500~6600 |
| 330 | uwFreqHL3 | Freq High Loss3 |  | 4500~6600 |
| 331 | --- |  |  |  |
| 332 | uwVoltLLTime1 | Volt Low Loss Time1 |  | 0~6000 |
| 333 | uwVoltLLTime2 | Volt Low Loss Time2 |  | 0~6000 |
| 334 | uwVoltLLTime3 | Volt Low Loss Time3 |  | 0~6000 |
| 335 | --- |  |  |  |
| 336 | uwVoltHLTime1 | Volt High Loss Time1 |  | 0~6000 |
| 337 | uwVoltHLTime2 | Volt High Loss Time2 |  | 0~6000 |
| 338 | uwVoltHLTime3 | Volt High Loss Time3 |  | 0~6000 |
| 339 | uwVoltRecvTime | Volt Reconnect Time |  | 0~6000 |
| 340 | uwFreqLLTime1 | Freq Low Loss Time1 |  | 0~6000 |
| 341 | uwFreqLLTime2 | Freq Low Loss Time2 |  | 0~6000 |
| 342 | uwFreqLLTime3 | Freq Low Loss Time3 |  | 0~6000 |
| 343 | uwFreqLLTime4 | Freq Low Loss Time4 |  | 0~6000 |
| 344 | uwFreqHLTime1 | Freq High Loss Time1 |  | 0~6000 |
| 345 | uwFreqHLTime2 | Freq High Loss Time2 |  | 0~6000 |
| 346 | uwFreqHLTime3 | Freq High Loss Time3 |  | 0~6000 |
| 347 | uwFreqRecvTime | High Freq or low Freq Loss Reconnect Time |  | 0~6000 |
| 348 | uwLVRT1 | Low volt ride through stage 1 |  | 0-3000 |
| 349 | uwLVRT2 | Low volt ride through stage 2 |  | 0-3000 |
| 350 | uwLVRT3 | Low volt ride through stage 3 |  | 0-3000 |
| 351 | --- |  |  |  |
| 352 | uwHVRT1 | High volt ride through stage 1 |  | 0-3000 |
| 353 | uwHVRT2 | High volt ride through stage 2 |  | 0-3000 |
| 354 | uwHVRT3 | High volt ride through stage3 |  | 0-3000 |
| 355 | --- |  |  |  |
| 356 | uwLVRTTime1 | Low volt ride through stage 1 Time |  | 0~60000 |
| 357 | uwLVRTTime2 | Low volt ride through stage 1 Time |  | 0~60000 |
| 358 | uwLVRTTime3 | Low volt ride through stage 1 Time |  | 0~60000 |
| 359 | uwHLVRTRecvTim e | High and Low volt ride through Reconnect Time |  | 0~6000 |
| 360 | uwHVRTTime1 | High volt ride through stage 1 Time |  | 0~60000 |
| 361 | uwHVRTTime2 | High volt ride through stage 2 Time |  | 0~60000 |
| 362 | uwHVRTTime3 | High volt ride through stage 3 Time |  | 0~60000 |
| 363 | --- |  |  |  |
| 364 | uwLFRT1 | Low Freq ride through stage 1 |  | 4500~6600 |
| 365 | uwLFRT2 | Low Freq ride through stage 2 |  | 4500~6600 |
| 366 | uwLFRT3 | Low Freq ride through stage 3 |  | 4500~6600 |
| 367 | --- |  |  |  |
| 368 | uwHFRT1 | High Freq ride through stage 1 |  | 4500~6600 |
| 369 | uwHFRT2 | High Freq ride through stage2 |  | 4500~6600 |
| 370 | uwHFRT3 | High Freq ride through stage3 |  | 4500~6600 |
| 371 | --- |  |  |  |
| 372 | uwLFRTTime1 | Low Freq ride through stage 1 Time |  | 0~60000 |
| 373 | uwLFRTTime2 | Low Freq ride through stage 2 Time |  | 0~60000 |
| 374 | uwLFRTTime3 | Low Freq ride through stage 3 Time |  | 0~60000 |
| 375 | --- |  |  |  |
| 376 | uwHFRTTime1 | High Freq ride through stage 1 Time |  | 0~60000 |
| 377 | uwHFRTTime2 | High Freq ride through stage 2 Time |  | 0~60000 |
| 378 | uwHFRTTime3 | High Freq ride through stage 3 Time |  | 0~60000 |
| 379 | --- |  |  |  |
| 380 | wLoadP_Out1 | Active power P1 percent |  | 0~100 |
| 381 | wLoadP_Out2 | Active power P2 percent |  | 20~100 |
| 382 | wLoadP_Out3 | Active power P3 percent |  | 0~20 |
| 383 | --- |  |  |  |
| 384 | wLoadQ_Out1 | Reactive power Q1 percen |  | -60~60 |
| 385 | wLoadQ_Out2 | Reactive power Q2 percen |  | -60~60 |
| 386 | wLoadQ_Out3 | Reactive power Q3 percen |  | -60~60 |
| 387 | --- |  |  |  |
| 388 | uwLoadP_Absorp 1 | Active power PP1 percent |  | 0~100 |
| 389 | uwLoadP_Absorp 2 | Active power PP2 percent |  | 0~100 |
| 390 | uwLoadP_Absorp 3 | Active power PP3 percent |  | 0~100 |
| 391 | --- |  |  |  |
| 392 | wLoadQ_Absorp1 | Reactive power QP1 percen |  | -60~60 |
| 393 | wLoadQ_Absorp2 | Reactive power QP2 percen |  | -60~60 |
| 394 | wLoadQ_Absorp3 | Reactive power QP3 percen |  | -60~60 |
| 395 | --- |  |  |  |
| 396 | uwReactV1 | Volt reactive mode V1 |  | 0~3000 |
| 397 | uwReactV2 | Volt reactive mode V2 |  | 0~3000 |
| 398 | uwReactV3 | Volt reactive mode V3 |  | 0~3000 |
| 399 | uwReactV4 | Volt reactive mode V4 |  | 0~3000 |
| 400 | wReactQ1_Percen t | volt reactive Q1 corresponding to Reactive power percen (Capacitive Qmax) |  | -60~60 |
| 401 | wReactQ2_Percen t | volt reactive Q2 corresponding to Reactive power percen |  | -60~60 |
| 402 | wReactQ3_Percen t | volt reactive Q3 corresponding to Reactive power percen |  | -60~60 |
| 403 | wReactQ4_Percen t | volt reactive Q4 corresponding to Reactive power percen ( inductive Qmax) |  | -60~60 |
| 404 | uwPowSlopeTime | Power Slop Time |  | 1~1000 |
| 405 | wModVoltVarOLR Set | Volt reactive power open loop response time |  | 10~900 |
| 406 | uwVrefModelFilte rTime | Vref Model Filter Time |  | 3000-50000 |
| 407 | wModVoltWattOL RSet | Volt active power open loop response time |  | 5~600 |
| 408 | wModFreqDroop OLRSet | Freq active power open loop response time |  | 2~100 |
| 409 | uwStartDelayTime | System countdown time |  | 0~600 |
| 410 | wReconnectTime | Power-on reconnection time |  | 0~600 |
| 411 | wDciDetect | DCI DC component detection |  | 0~600 |
| 412 | wIslandProtectTi me | Island Protect Time |  | 0~600 |
| 413 | --- |  |  |  |
| 414 | --- |  |  |  |
| 415 | HlvrtEn | High and low crossover enable |  | 0:disable; 1:Enable; |
| 416 | HvDecLoadEn | High volt load reduction enable |  | 0:disable; |
| 417 | FreqDecLoadEn | Over frequency load reduction enable |  | 0:disable; 1:Enable; |
| 418 | AntiIslandEn | Island detection enabled |  | 0:disable; 1:Enable; |
| 420 | AutoVRefEn | Reactive power auto Ref enable |  | 0:disable; 1:Enable; |
| 421 | MeterOrCtSw | Meter CT selection |  | 0:wired CT 1: wireless 2:meter |
| 422 | DCIAdjEN | DCI regulation |  | 0:disable; 1:Enable; |
| 423 | IslandPWMEN | Island PWM enable |  | 0:disable; 1:Enable; |
| 424 | SpectypevalueEn | Safety value protection enable |  | 0:disable; 1:Enable; |
| 425 | VrefModelEn | Vref mode enabled |  | 0: Vref mode of QV curve is not activated 1: Vref mode of QV curve activated |
| 426 | RoCoFEn | RoCoF enable |  | 0:disable; 1:Enable; |

---

## Input Registers (305 registers)

| Address | Name | Description | Access | Range |
| --- | --- | --- | --- | --- |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 8 | reg_8 |  |  |  |
| 9 | reg_9 |  |  |  |
| 10 | reg_10 |  |  |  |
| 11 | reg_11 |  |  |  |
| 12 | reg_12 |  |  |  |
| 13 | reg_13 |  |  |  |
| 14 | reg_14 |  |  |  |
| 15 | reg_15 |  |  |  |
| 16 | reg_16 |  |  |  |
| 17 | reg_17 |  |  |  |
| 18 | reg_18 |  |  |  |
| 19 | reg_19 |  |  |  |
| 20 | reg_20 |  |  |  |
| 21 | reg_21 |  |  |  |
| 22 | reg_22 |  |  |  |
| 23 | reg_23 |  |  |  |
| 24 | reg_24 |  |  |  |
| 25 | reg_25 |  |  |  |
| 26 | reg_26 |  |  |  |
| 27 | reg_27 |  |  |  |
| 28 | reg_28 |  |  |  |
| 29 | reg_29 |  |  |  |
| 30 | reg_30 |  |  |  |
| 31 | reg_31 |  |  |  |
| 32 | reg_32 |  |  |  |
| 33 | reg_33 |  |  |  |
| 34 | reg_34 |  |  |  |
| 35 | reg_35 |  |  |  |
| 36 | reg_36 |  |  |  |
| 37 | reg_37 |  |  |  |
| 38 | reg_38 |  |  |  |
| 39 | reg_39 |  |  |  |
| 40 | reg_40 |  |  |  |
| 41 | reg_41 |  |  |  |
| 42 | reg_42 |  |  |  |
| 43 | reg_43 |  |  |  |
| 44 | reg_44 | Export to Grid Today Export to Grid Total H . 1 K W H Total energy feed to grid L 0 . 1 K W H PV Energy today |  |  |
| 70 | reg_70 |  |  |  |
| 71 | reg_71 |  |  |  |
| 72 | reg_72 |  |  |  |
| 73 | reg_73 |  |  |  |
| 74 | reg_74 | Bat_DisChrVA H Bat_DisChrVA L |  |  |
| 77 | reg_77 |  |  |  |
| 78 | Bat_Watt L |  |  |  |
| 79 | reg_79 |  |  |  |
| 80 | reg_80 |  |  |  |
| 81 | reg_81 |  |  |  |
| 82 | reg_82 |  |  |  |
| 83 | reg_83 |  |  |  |
| 84 | reg_84 |  |  |  |
| 85 | reg_85 |  |  |  |
| 86 | reg_86 |  |  |  |
| 87 | reg_87 | Eop_dischrTotal_L |  |  |
| 90 | reg_90 |  |  |  |
| 91 | reg_91 |  |  |  |
| 92 | reg_92 |  |  |  |
| 93 | reg_93 |  |  |  |
| 94 | reg_94 |  |  |  |
| 95 | reg_95 |  |  |  |
| 96 | reg_96 |  |  |  |
| 97 | reg_97 |  |  |  |
| 98 | reg_98 |  |  |  |
| 99 | reg_99 |  |  |  |
| 100 | reg_100 |  |  |  |
| 101 | reg_101 |  |  |  |
| 102 | reg_102 |  |  |  |
| 103 | reg_103 |  |  |  |
| 104 | reg_104 |  |  |  |
| 105 | reg_105 |  |  |  |
| 106 | reg_106 |  |  |  |
| 107 | reg_107 |  |  |  |
| 108 | reg_108 |  |  |  |
| 109 | reg_109 |  |  |  |
| 110 | reg_110 |  |  |  |
| 111 | reg_111 |  |  |  |
| 209 | reg_209 |  |  |  |
| 210 | reg_210 |  |  |  |
| 211 | reg_211 |  |  |  |
| 212 | reg_212 |  |  |  |
| 213 | reg_213 |  |  |  |
| 214 | reg_214 |  |  |  |
| 215 | reg_215 |  |  |  |
| 216 | reg_216 |  |  |  |
| 217 | reg_217 |  |  |  |
| 218 | reg_218 |  |  |  |
| 219 | reg_219 |  |  |  |
| 220 | reg_220 |  |  |  |
| 221 | reg_221 |  |  |  |
| 222 | reg_222 |  |  |  |
| 223 | reg_223 |  |  |  |
| 224 | reg_224 |  |  |  |
| 225 | reg_225 |  |  |  |
| 226 | reg_226 |  |  |  |
| 227 | reg_227 |  |  |  |
| 228 | reg_228 |  |  |  |
| 229 | reg_229 |  |  |  |
| 230 | reg_230 |  |  |  |
| 231 | reg_231 |  |  |  |
| 232 | reg_232 |  |  |  |
| 233 | reg_233 |  |  |  |
| 234 | reg_234 |  |  |  |
| 235 | reg_235 |  |  |  |
| 236 | reg_236 |  |  |  |
| 237 | reg_237 |  |  |  |
| 238 | reg_238 |  |  |  |
| 239 | reg_239 |  |  |  |
| 240 | reg_240 |  |  |  |
| 241 | reg_241 |  |  |  |
| 242 | reg_242 |  |  |  |
| 243 | reg_243 |  |  |  |
| 244 | reg_244 |  |  |  |
| 245 | reg_245 |  |  |  |
| 246 | reg_246 |  |  |  |
| 247 | reg_247 |  |  |  |
| 248 | reg_248 |  |  |  |
| 249 | reg_249 |  |  |  |
| 250 | reg_250 |  |  |  |
| 251 | reg_251 |  |  |  |
| 252 | reg_252 |  |  |  |
| 253 | reg_253 |  |  |  |
| 254 | reg_254 |  |  |  |
| 255 | reg_255 |  |  |  |
| 256 | reg_256 |  |  |  |
| 257 | reg_257 |  |  |  |
| 258 | reg_258 |  |  |  |
| 259 | reg_259 |  |  |  |
| 260 | reg_260 |  |  |  |
| 261 | reg_261 |  |  |  |
| 262 | reg_262 |  |  |  |
| 263 | reg_263 |  |  |  |
| 264 | reg_264 |  |  |  |
| 265 | reg_265 |  |  |  |
| 266 | reg_266 |  |  |  |
| 267 | reg_267 |  |  |  |
| 268 | reg_268 |  |  |  |
| 269 | reg_269 |  |  |  |
| 270 | reg_270 |  |  |  |
| 271 | reg_271 |  |  |  |
| 272 | reg_272 |  |  |  |
| 273 | reg_273 |  |  |  |
| 274 | reg_274 |  |  |  |
| 275 | reg_275 |  |  |  |
| 276 | reg_276 |  |  |  |
| 277 | reg_277 |  |  |  |
| 278 | reg_278 |  |  |  |
| 279 | reg_279 |  |  |  |
| 280 | reg_280 |  |  |  |
| 281 | reg_281 |  |  |  |
| 282 | reg_282 |  |  |  |
| 283 | reg_283 |  |  |  |
| 284 | reg_284 |  |  |  |
| 285 | reg_285 |  |  |  |
| 286 | reg_286 |  |  |  |
| 287 | reg_287 |  |  |  |
| 288 | reg_288 |  |  |  |
| 289 | reg_289 |  |  |  |
| 290 | reg_290 |  |  |  |
| *Fault type value* |  |  |  |  |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 8 | reg_8 |  |  |  |
| 9 | reg_9 |  |  |  |
| 11 | reg_11 |  |  |  |
| 51 | reg_51 |  |  |  |
| 52 | reg_52 |  |  |  |
| 53 | reg_53 |  |  |  |
| 56 | reg_56 |  |  |  |
| 58 | reg_58 |  |  |  |
| 60 | reg_60 |  |  |  |
| 61 | reg_61 |  |  |  |
| 62 | reg_62 |  |  |  |
| 80 | reg_80 |  |  |  |
| 81 | reg_81 |  |  |  |
| *&*9: BMS_Status code* |  |  |  |  |
| 0 | reg_0 |  |  | 00 : soft_starting |
| 1 | reg_1 |  |  | 11 : discharging |
| 2 | reg_2 |  |  | 1 : “Error” byte valid |
| 3 | reg_3 |  |  | 0 : unbalance PF |
| 4 | reg_4 |  |  | 0 : disable |
| 5 | reg_5 |  |  | 0 : disable |
| 6 | reg_6 |  |  | 0 : disable |
| 7 | reg_7 |  |  | 0 : terminal |
| 8 | reg_8 |  |  | 00:单机 |
| 9 | reg_9 |  |  | 10:并联准备 |
| 10 | reg_10 |  |  | 00:none |
| 11 | reg_11 |  |  | 11 : discharging |
| 12 | reg_12 |  |  | 0 : disable |
| *&*14: BMS_BMSInfo code* |  |  |  |  |
| 0 | reg_0 |  |  |  |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 8 | reg_8 |  |  |  |
| 9 | reg_9 |  |  |  |
| 10 | reg_10 |  |  |  |
| 11 | reg_11 |  |  |  |
| 12 | reg_12 |  |  |  |
| 13 | reg_13 |  |  |  |
| 14 | reg_14 |  |  |  |
| 15 | reg_15 |  |  |  |
| *&*15: BMS_PackInfo code* |  |  |  |  |
| 0 | reg_0 |  |  |  |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 8 | reg_8 |  |  |  |
| 9 | reg_9 |  |  |  |
| 10 | reg_10 |  |  |  |
| 11 | reg_11 |  |  |  |
| 12 | reg_12 |  |  |  |
| 13 | reg_13 |  |  |  |
| 14 | reg_14 |  |  |  |
| 15 | reg_15 |  |  |  |
| *&*16: ModuleStatus code* |  |  |  |  |
| 0 | reg_0 |  |  |  |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 8 | reg_8 |  |  |  |
| 9 | reg_9 |  |  |  |
| 10 | reg_10 |  |  |  |
| 11 | reg_11 |  |  |  |
| 0 | reg_0 |  |  |  |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 8 | reg_8 |  |  |  |
| 9 | reg_9 |  |  |  |
| 10 | reg_10 |  |  |  |
| 11 | reg_11 |  |  |  |
| 12 | reg_12 |  |  |  |
| 13 | reg_13 |  |  |  |
| 14 | reg_14 |  |  |  |
| 15 | reg_15 |  |  |  |
| 0 | reg_0 |  |  |  |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 8 | reg_8 |  |  |  |
| 9 | reg_9 |  |  |  |
| 10 | reg_10 |  |  |  |
| 11 | reg_11 |  |  |  |
| 12 | reg_12 |  |  |  |
| 13 | reg_13 |  |  |  |
| 14 | reg_14 |  |  |  |
| 15 | reg_15 |  |  |  |
| *&*20: RequestOrBatteryType code* |  |  |  |  |
| 0 | reg_0 |  | 充电过功率 |  |
| 1 | reg_1 |  | 放电过功率 |  |
| 2 | reg_2 |  | 并机重号故障 |  |
| 3 | reg_3 |  | 预充失败 |  |
| 4 | reg_4 |  | 预充短路 |  |
| 5 | reg_5 |  | Communication error between AFE and MCU |  |
| 6 | reg_6 |  | 单体异常故障（单体失效） |  |
| 7 | reg_7 |  | 单体温度异常故障（单体失效） |  |
| 8 | reg_8 |  | 总压采样故障 |  |
| 9 | reg_9 |  | 温度短路 |  |
| 10 | reg_10 |  | 负载侧总压采样故障 |  |
| 11 | reg_11 |  | 载入标定参数故障 |  |
| 12 | reg_12 |  | 硬件过压（AFE OV） |  |
| 13 | reg_13 |  | 硬件欠压（AFE UV） |  |
| 14 | reg_14 |  | 硬件过流（硬件保护反馈） |  |
| 15 | reg_15 |  | 硬件放电过流故障 |  |
| 0 | reg_0 |  | 从主机电池压差较大 |  |
| 1 | reg_1 |  | 充电限流失败故障 |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
| 0 | reg_0 |  |  |  |
| 1 | reg_1 |  |  |  |
| 2 | reg_2 |  |  |  |
| 3 | reg_3 |  |  |  |
| 4 | reg_4 |  |  |  |
| 5 | reg_5 |  |  |  |
| 6 | reg_6 |  |  |  |
| 7 | reg_7 |  |  |  |
