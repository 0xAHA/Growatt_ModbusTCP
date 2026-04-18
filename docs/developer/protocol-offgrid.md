# Off-Grid Protocol V0.26

> **Source document:** Growatt OffGrid Modbus RS485/RS232 RTU Protocol V0.26
> (`OffGrid-Modbus-RS485-RS232-RTU-Protocol-V0-26.xlsx`)
>
> This is the protocol used by Growatt's off-grid and AC-coupled inverter families.
> Holding registers cover settings and control; input registers cover real-time data.
>
> **Applicable models:**
> - **SPF 3000-6000 ES PLUS**  -  off-grid with battery, no grid export
> - **SPE 8000-12000 ES**  -  higher-capacity off-grid / AC-coupled storage

---

## Register Ranges

| Range | Purpose |
| --- | --- |
| 0-426 | Holding registers (settings and control) |
| 0-111 | Input registers (real-time data) |

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
| 28 | Moudle H | Inverter Moudle (high) | W | 0: model can be modify |
| 29 | Moudle L | Inverter Moudle (low) | W | eg: 50 for 5.0KW model |
| 30 | Com Address | Communicate addr ess | W | 1~254 ， but 253 only for debug |
| 31 | FlashStart | Update firmware | W | 0x0001: own 0X0100: control broad |
| 32 | Reset User Info | Reset User Information | W | 0x0001 |
| 33 | Reset to factory | Reset to factory | W | 0x0001 |
| 34 | MaxChargeCurr | Max Charge Current | W | 0~ |
| 35 | BulkChargeVolt | Bulk Charge Volt | W | 500~640- |
| 36 | FloatChargeVolt | Float Charge Volt | W | 500~560 |
| 37 | BatLowToUtiVolt | Bat Low Volt Switch To Uti | W |  |
| 38 | ACChargeCurr | AC Charge Current | W |  |
| 39 | Battery Type | Battery Type | W |  |
| 40 | Aging Mode | Aging Mode | W |  |
| 41 | Function Mask |  | W | bit0=Etl check enable |
| 42 | Safety Type |  | W |  |
| 43 | DTC | Device Type Code |  | &*6 |
| 44 | reg_44 |  |  |  |
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
| 58 | reg_58 |  |  |  |
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
| 71 | reg_71 |  |  |  |
| 72 | Sys Weekly | Sys Weekly | W | 0-6 |
| 73 | ModbusVersion | Modbus Version |  | Eg：207 is V2.07 |
| 74 | reg_74 |  |  |  |
| 75 | SCC_ComMode | SCC Communication Mode |  |  |
| 76 | Rate Watt H | Rate active power(high) |  |  |
| 77 | Rate Watt L | Rate active power(low) |  |  |
| 78 | Rate VA H | Rata apparent power (high) |  |  |
| 79 | Rate VA L | Rate apparent power (low) |  |  |
| 80 | ComboardVer | Communicaiton board Version |  |  |
| 81 | uwBatPieceNum |  |  |  |
| 82 | wBatLowCutOff | Bat cutoff |  |  |
| 83 | MaxGenChgCurr | maximum generator charge current |  |  |
| 84 | NomGridVolt |  |  |  |
| 85 | NomGridFreq |  |  |  |
| 86 | NomBatVolt |  |  |  |
| 87 | NomPvCurr |  |  |  |
| 88 | NomAcChgCurr |  |  |  |
| 89 | NomOpVolt |  |  |  |
| 90 | NomOpFreq |  |  |  |
| 91 | NomOpPow |  |  |  |
| 92 | reg_92 |  |  |  |
| 93 | reg_93 |  |  |  |
| 94 | reg_94 |  |  |  |
| 95 | uwAC2BatVolt | AC switch to Battery |  |  |
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
| 310 | uwPfModelSet | Set PF function mode |  | 0: Reactive power generation is prohibited 1: Constant (Fixed PF mode) 2: Watt/Var (Active and reactive modes) 3: Constant Var (Fixed reactive power percentage) 4: Volt/Var (volt reactive power mode) |
| 311 | wPfSet | Power factor set |  | -1000~1000 (cannot be 0) |
| 312 | wGridVoltLowStar t | Grid volt low at startup |  | 0~3000 |
| 313 | wGridVoltHighStar t | Grid volt high at startup |  | 0~3000 |
| 314 | wGridFreqLowSta rt | Grid freq low at startup |  | 0~6600 |
| 315 | wGridFreqHighSta rt | Grid freq high at startup |  | 0~6600 |
| 316 | uwVoltLLPercent1 | Volt Low Loss Percent1 |  | 1-130 |
| 317 | uwVoltLLPercent2 | Volt Low Loss Percent2 |  | 1-130 |
| 318 | uwVoltLLPercent3 | Volt Low Loss Percent3 |  | 1-130 |
| 319 | reg_319 |  |  |  |
| 320 | uwVoltHLPercent1 | Volt High Loss Percent1 |  | 1-130 |
| 321 | uwVoltHLPercent2 | Volt High Loss Percent2 |  | 1-130 |
| 322 | uwVoltHLPercent3 | Volt High Loss Percent3 |  | 1-130 |
| 323 | reg_323 |  |  |  |
| 324 | uwFreqLL1 | Freq Low Loss1 |  | 4500~6600 |
| 325 | uwFreqLL2 | Freq Low Loss2 |  | 4500~6600 |
| 326 | uwFreqLL3 | Freq Low Loss3 |  | 4500~6600 |
| 327 | uwFreqLL4 | Freq Low Loss4 |  | 4500~6600 |
| 328 | uwFreqHL1 | Freq High Loss1 |  | 4500~6600 |
| 329 | uwFreqHL2 | Freq High Loss2 |  | 4500~6600 |
| 330 | uwFreqHL3 | Freq High Loss3 |  | 4500~6600 |
| 331 | reg_331 |  |  |  |
| 332 | uwVoltLLTime1 | Volt Low Loss Time1 |  | 0~6000 |
| 333 | uwVoltLLTime2 | Volt Low Loss Time2 |  | 0~6000 |
| 334 | uwVoltLLTime3 | Volt Low Loss Time3 |  | 0~6000 |
| 335 | reg_335 |  |  |  |
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
| 351 | reg_351 |  |  |  |
| 352 | uwHVRT1 | High volt ride through stage 1 |  | 0-3000 |
| 353 | uwHVRT2 | High volt ride through stage 2 |  | 0-3000 |
| 354 | uwHVRT3 | High volt ride through stage3 |  | 0-3000 |
| 355 | reg_355 |  |  |  |
| 356 | uwLVRTTime1 | Low volt ride through stage 1 Time |  | 0~60000 |
| 357 | uwLVRTTime2 | Low volt ride through stage 1 Time |  | 0~60000 |
| 358 | uwLVRTTime3 | Low volt ride through stage 1 Time |  | 0~60000 |
| 359 | uwHLVRTRecvTim e | High and Low volt ride through Reconnect Time |  | 0~6000 |
| 360 | uwHVRTTime1 | High volt ride through stage 1 Time |  | 0~60000 |
| 361 | uwHVRTTime2 | High volt ride through stage 2 Time |  | 0~60000 |
| 362 | uwHVRTTime3 | High volt ride through stage 3 Time |  | 0~60000 |
| 363 | reg_363 |  |  |  |
| 364 | uwLFRT1 | Low Freq ride through stage 1 |  | 4500~6600 |
| 365 | uwLFRT2 | Low Freq ride through stage 2 |  | 4500~6600 |
| 366 | uwLFRT3 | Low Freq ride through stage 3 |  | 4500~6600 |
| 367 | reg_367 |  |  |  |
| 368 | uwHFRT1 | High Freq ride through stage 1 |  | 4500~6600 |
| 369 | uwHFRT2 | High Freq ride through stage2 |  | 4500~6600 |
| 370 | uwHFRT3 | High Freq ride through stage3 |  | 4500~6600 |
| 371 | reg_371 |  |  |  |
| 372 | uwLFRTTime1 | Low Freq ride through stage 1 Time |  | 0~60000 |
| 373 | uwLFRTTime2 | Low Freq ride through stage 2 Time |  | 0~60000 |
| 374 | uwLFRTTime3 | Low Freq ride through stage 3 Time |  | 0~60000 |
| 375 | reg_375 |  |  |  |
| 376 | uwHFRTTime1 | High Freq ride through stage 1 Time |  | 0~60000 |
| 377 | uwHFRTTime2 | High Freq ride through stage 2 Time |  | 0~60000 |
| 378 | uwHFRTTime3 | High Freq ride through stage 3 Time |  | 0~60000 |
| 379 | reg_379 |  |  |  |
| 380 | wLoadP_Out1 | Active power P1 percent |  | 0~100 |
| 381 | wLoadP_Out2 | Active power P2 percent |  | 20~100 |
| 382 | wLoadP_Out3 | Active power P3 percent |  | 0~20 |
| 383 | reg_383 |  |  |  |
| 384 | wLoadQ_Out1 | Reactive power Q1 percen |  | -60~60 |
| 385 | wLoadQ_Out2 | Reactive power Q2 percen |  | -60~60 |
| 386 | wLoadQ_Out3 | Reactive power Q3 percen |  | -60~60 |
| 387 | reg_387 |  |  |  |
| 388 | uwLoadP_Absorp 1 | Active power PP1 percent |  | 0~100 |
| 389 | uwLoadP_Absorp 2 | Active power PP2 percent |  | 0~100 |
| 390 | uwLoadP_Absorp 3 | Active power PP3 percent |  | 0~100 |
| 391 | reg_391 |  |  |  |
| 392 | wLoadQ_Absorp1 | Reactive power QP1 percen |  | -60~60 |
| 393 | wLoadQ_Absorp2 | Reactive power QP2 percen |  | -60~60 |
| 394 | wLoadQ_Absorp3 | Reactive power QP3 percen |  | -60~60 |
| 395 | reg_395 |  |  |  |
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
| 413 | reg_413 |  |  |  |
| 414 | reg_414 |  |  |  |
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

## Input Registers (201 registers)

> Source: Off-Grid Protocol V0.26 PDF (register data extracted directly  -  the Excel
> input register section uses an inconsistent layout with merged cells).

| Address | Variable Name | Description | Scale | Unit | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 | System Status | System run state | - | - | 0:Standby, 1:PV&Grid Supporting Loads, 2:Battery Discharging, 3:Fault, 4:Flash, 5:PV Charging, 6:Grid Charging, 7:PV&Grid Charging, 8:PV&Grid Charging+Grid Bypass, 9:PV Charging+Grid Bypass, 10:Grid Charging+Grid Bypass, 11:Grid Bypass, 12:PV Charging+Loads Supporting, 13:PV Discharging, 14:PV&Battery Discharging, 15:Gen Charging, 16:Gen Charging+Gen Bypass, 17:PV&Gen Charging, 18:PV&Gen Charging+Gen Bypass, 19:PV Charging+Gen Bypass, 20:Gen Bypass, 21:PV Export to Grid, 22:PV Export to Grid+Loads Supporting, 23:PV Charging+Export to Grid, 24:PV Charging+Export to Grid+Loads Supporting, 25:Battery Export to Grid, 26:Battery Export to Grid+Loads Supporting, 27:Battery&PV Export to Grid, 28:Battery&PV Export to Grid+Loads Supporting |
| 1 | Vpv1 | PV1 voltage | 0.1 | V |  |
| 2 | Vpv2 | PV2 voltage | 0.1 | V |  |
| 3 | Ppv1 H | PV1 charge power (high) | 0.1 | W |  |
| 4 | Ppv1 L | PV1 charge power (low) | 0.1 | W |  |
| 5 | Ppv2 H | PV2 charge power (high) | 0.1 | W |  |
| 6 | Ppv2 L | PV2 charge power (low) | 0.1 | W |  |
| 7 | Buck1Curr/Pv1Curr | Buck1 current or PV1 current | 0.1 | A |  |
| 8 | Buck2Curr/Pv2Curr | Buck2 current or PV2 current | 0.1 | A |  |
| 9 | OP_Watt H | Output active power (high) | 0.1 | W |  |
| 10 | OP_Watt L | Output active power (low) | 0.1 | W |  |
| 11 | OP_VA H | Output apparent power (high) | 0.1 | VA |  |
| 12 | OP_VA L | Output apparent power (low) | 0.1 | VA |  |
| 13 | ACChr_Watt H | AC charge watt (high) | 0.1 | W |  |
| 14 | ACChr_Watt L | AC charge watt (low) | 0.1 | W |  |
| 15 | ACChr_VA H | AC charge apparent power (high) | 0.1 | VA |  |
| 16 | ACChr_VA L | AC charge apparent power (low) | 0.1 | VA |  |
| 17 | Bat Volt | Battery voltage (M3) | 0.01 | V |  |
| 18 | BatterySOC | Battery SOC | 1 | % | 0~100 |
| 19 | Bus Volt | INV bus total voltage | 0.1 | V |  |
| 20 | Grid Volt | AC input voltage | 0.1 | V |  |
| 21 | Line Freq | AC input frequency | 0.01 | Hz |  |
| 22 | OutputVolt | AC output voltage | 0.1 | V |  |
| 23 | OutputFreq | AC output frequency | 0.01 | Hz |  |
| 24 | Ouput DCV | Output DC voltage | 0.1 | V |  |
| 25 | InvTemp | Inverter temperature | 0.1 | °C | -30~200.0 |
| 26 | DcDc Temp | DC-DC temperature | 0.1 | °C | -30~200.0 |
| 27 | LoadPercent | Load percentage | 0.1 | % | 0~1000 |
| 28 | Bat_s_Volt | Battery-port voltage (DSP) | 0.01 | V |  |
| 29 | Bat_Volt_DSP | Battery-bus voltage (DSP) | 0.01 | V |  |
| 30 | Time total H | Work time total (high) | 0.5 | S |  |
| 31 | Time total L | Work time total (low) | 0.5 | S |  |
| 32 | Buck1_NTC | Buck1 temperature | 0.1 | °C | -30~200.0 |
| 33 | Buck2_NTC | Buck2 temperature | 0.1 | °C | -30~200.0 |
| 34 | OP_Curr | Output current | 0.1 | A |  |
| 35 | Inv_Curr | Inverter current | 0.1 | A |  |
| 36 | AC_InWatt H | AC input watt (high) | 0.1 | W | signed int32; >0: get energy from grid, <0: export to grid |
| 37 | AC_InWatt L | AC input watt (low) | 0.1 | W |  |
| 38 | AC_InVA H | AC input apparent power (high) | 0.1 | VA |  |
| 39 | AC_InVA L | AC input apparent power (low) | 0.1 | VA |  |
| 40 | Fault bit | Fault bit | - | - |  |
| 41 | Warning bit | Warning bit | - | - |  |
| 42 | Warning bit high | Warning bit high | - | - |  |
| 43 | warning value | Warning value | - | - |  |
| 44 | DTC | Device Type Code | - | - |  |
| 45 | Export to Grid Today | Today's energy fed to grid | 0.1 | kWh |  |
| 46 | Export to Grid Total H | Total energy fed to grid (high) | 0.1 | kWh |  |
| 47 | Export to Grid Total L | Total energy fed to grid (low) | 0.1 | kWh |  |
| 48 | Epv1_today H | PV1 energy today (high) | 0.1 | kWh |  |
| 49 | Epv1_today L | PV1 energy today (low) | 0.1 | kWh |  |
| 50 | Epv1_total H | PV1 energy total (high) | 0.1 | kWh |  |
| 51 | Epv1_total L | PV1 energy total (low) | 0.1 | kWh |  |
| 52 | Epv2_today H | PV2 energy today (high) | 0.1 | kWh |  |
| 53 | Epv2_today L | PV2 energy today (low) | 0.1 | kWh |  |
| 54 | Epv2_total H | PV2 energy total (high) | 0.1 | kWh |  |
| 55 | Epv2_total L | PV2 energy total (low) | 0.1 | kWh |  |
| 56 | Eac_chrToday H | AC charge energy today (high) | 0.1 | kWh |  |
| 57 | Eac_chrToday L | AC charge energy today (low) | 0.1 | kWh |  |
| 58 | Eac_chrTotal H | AC charge energy total (high) | 0.1 | kWh |  |
| 59 | Eac_chrTotal L | AC charge energy total (low) | 0.1 | kWh |  |
| 60 | Ebat_dischrToday H | Battery discharge energy today (high) | 0.1 | kWh |  |
| 61 | Ebat_dischrToday L | Battery discharge energy today (low) | 0.1 | kWh |  |
| 62 | Ebat_dischrTotal H | Battery discharge energy total (high) | 0.1 | kWh |  |
| 63 | Ebat_dischrTotal L | Battery discharge energy total (low) | 0.1 | kWh |  |
| 64 | Eac_dischrToday H | AC discharge energy today (high) | 0.1 | kWh |  |
| 65 | Eac_dischrToday L | AC discharge energy today (low) | 0.1 | kWh |  |
| 66 | Eac_dischrTotal H | AC discharge energy total (high) | 0.1 | kWh |  |
| 67 | Eac_dischrTotal L | AC discharge energy total (low) | 0.1 | kWh |  |
| 68 | ACChrCurr | AC charge battery current | 0.1 | A |  |
| 69 | AC_DisChrWatt H | AC discharge watt (high) | 0.1 | W |  |
| 70 | AC_DisChrWatt L | AC discharge watt (low) | 0.1 | W |  |
| 71 | AC_DisChrVA H | AC discharge apparent power (high) | 0.1 | VA |  |
| 72 | AC_DisChrVA L | AC discharge apparent power (low) | 0.1 | VA |  |
| 73 | Bat_DisChrWatt H | Battery discharge watt (high) | 0.1 | W |  |
| 74 | Bat_DisChrWatt L | Battery discharge watt (low) | 0.1 | W |  |
| 75 | Bat_DisChrVA H | Battery discharge apparent power (high) | 0.1 | VA |  |
| 76 | Bat_DisChrVA L | Battery discharge apparent power (low) | 0.1 | VA |  |
| 77 | Bat_Watt H | Battery watt (high) | 0.1 | W | signed int32; positive=discharge, negative=charge |
| 78 | Bat_Watt L | Battery watt (low) | 0.1 | W |  |
| 79 | uwSlaveExistCnt | Number of parallel slave units | - | - |  |
| 81 | MpptFanSpeed | MPPT charger fan speed | 1 | % | 0~100 |
| 82 | InvFanSpeed | Inverter fan speed | 1 | % | 0~100 |
| 83 | TotalChgCur | Total charge current | 0.1 | A |  |
| 84 | TotalDisChgCur | Total discharge current | 0.1 | A |  |
| 85 | Eop_dischrToday_H | Output discharge energy today (high) | 0.1 | kWh |  |
| 86 | Eop_dischrToday_L | Output discharge energy today (low) | 0.1 | kWh |  |
| 87 | Eop_dischrTotal_H | Output discharge energy total (high) | 0.1 | kWh |  |
| 88 | Eop_dischrTotal_L | Output discharge energy total (low) | 0.1 | kWh |  |
| 90 | ParaChgCurr | Parallel system charge current | 0.1 | A |  |
| 91 | ParStatus | Parallel status | - | - | 0:New module, 1:Master, 2:Slave (single parallel), 3:Slave1 (three phase R), 4:Slave2 (three phase S), 5:Slave3 (three phase T), 6:Slave4 (two phase R), 7:Slave5 (two phase/120° S), 8:Slave6 (two phase/180° S) |
| 92 | EGen_dischrToday_H | Generator energy today (high) | 0.1 | kWh |  |
| 93 | EGen_dischrToday_L | Generator energy today (low) | 0.1 | kWh |  |
| 94 | EGen_dischrTotal_H | Generator energy total (high) | 0.1 | kWh |  |
| 95 | EGen_dischrTotal_L | Generator energy total (low) | 0.1 | kWh |  |
| 96 | EGen_dischrPower | Generator power | 1 | W |  |
| 97 | EGen_voltage | Generator voltage | 0.1 | V |  |
| 98 | EBatChgToday_H | Battery charge energy today (high) | 0.1 | kWh |  |
| 99 | EBatChgToday_L | Battery charge energy today (low) | 0.1 | kWh |  |
| 100 | EBatChgTotal_H | Battery charge energy total (high) | 0.1 | kWh |  |
| 101 | EBatChgTotal_L | Battery charge energy total (low) | 0.1 | kWh |  |
| 102 | CT_InWatt H | CT input watt (high) | 0.1 | W |  |
| 103 | CT_InWatt L | CT input watt (low) | 0.1 | W |  |
| 104 | CtLoadWatt H | CT load active power (high) | 0.1 | W |  |
| 105 | CtLoadWatt L | CT load active power (low) | 0.1 | W |  |
| 106 | CtLoadPer | CT load percentage | 0.1 | % | 0~1000 |
| 107 | TxTemp | Transformer temperature | 0.1 | °C | -30~200.0 |
| 108 | LLCTemp | LLC temperature | 0.1 | °C | -30~200.0 |
| 109 | LLCBusVolt | LLC bus total voltage | 0.1 | V |  |
| 110 | LLCBatVolt | LLC battery voltage | 0.01 | V |  |
| 111 | EnvTemp | Environment temperature | 0.1 | °C | -30~200.0 |
| 200 | BMS_Status | BMS status | - | - | Bit field, see note *9 |
| 201 | BMS_Error_old | BMS error (legacy) | - | - | Bit field, see note *10 |
| 202 | BMS_WarnInfo_old | BMS warning info (legacy) | - | - | Bit field, see note *11 |
| 203 | BMS_SOC | BMS state of charge | 1 | % | 1~100 |
| 204 | BMS_BatteryVolt | BMS average voltage | 0.01 | V |  |
| 205 | BMS_BatteryCurr | BMS average current | 0.1 | A | signed int16; see note *12 |
| 206 | BMS_BatteryTemp | BMS average temperature | 0.1 | °C | signed int16 |
| 207 | BMS_MaxCurrChg | BMS maximum charge current | 0.1 | A |  |
| 208 | BMS_CVolt | BMS float charge voltage | 0.01 | V | see note *13 |
| 209 | BMS_BMSInfo | BMS board info | - | - | see note *14 |
| 210 | BMS_PackInfo | Battery module info | - | - | see note *15 |
| 211 | BMS_UsingCap | Battery used capacity | - | - |  |
| 212 | BMS_Cell_Volt1 | Cell voltage 1 | 0.001 | V | Individual cell data  -  identifies different battery packs under same BMS |
| 213 | BMS_Cell_Volt2 | Cell voltage 2 | 0.001 | V |  |
| 214 | BMS_Cell_Volt3 | Cell voltage 3 | 0.001 | V |  |
| 215 | BMS_Cell_Volt4 | Cell voltage 4 | 0.001 | V |  |
| 216 | BMS_Cell_Volt5 | Cell voltage 5 | 0.001 | V |  |
| 217 | BMS_Cell_Volt6 | Cell voltage 6 | 0.001 | V |  |
| 218 | BMS_Cell_Volt7 | Cell voltage 7 | 0.001 | V |  |
| 219 | BMS_Cell_Volt8 | Cell voltage 8 | 0.001 | V |  |
| 220 | BMS_Cell_Volt9 | Cell voltage 9 | 0.001 | V |  |
| 221 | BMS_Cell_Volt10 | Cell voltage 10 | 0.001 | V |  |
| 222 | BMS_Cell_Volt11 | Cell voltage 11 | 0.001 | V |  |
| 223 | BMS_Cell_Volt12 | Cell voltage 12 | 0.001 | V |  |
| 224 | BMS_Cell_Volt13 | Cell voltage 13 | 0.001 | V |  |
| 225 | BMS_Cell_Volt14 | Cell voltage 14 | 0.001 | V |  |
| 226 | BMS_Cell_Volt15 | Cell voltage 15 | 0.001 | V |  |
| 227 | BMS_Cell_Volt16 | Cell voltage 16 | 0.001 | V |  |
| 228 | ModuleID | Module ID | - | - | 1~12 |
| 229 | ModuleTotalVolt | Module total voltage | 0.01 | V | signed int16 |
| 230 | ModuleTotalCurrent | Module total current | 0.1 | A | signed int16 |
| 231 | ModuleSoc | Module state of charge | 1 | % | 1~100 |
| 232 | ModuleStatus | Module status | - | - | see note *16 |
| 233 | BatProtect1_2 | Battery protection flags 1-2 | - | - | see note *17 |
| 234 | BatWarnInfo1_2 | Battery warning flags 1-2 | - | - | see note *18 |
| 235 | PackNumber | Number of parallel battery packs | - | - | 1~254 |
| 236 | BatDePowerReason | Battery power derating reason | - | - | see note *19 |
| 237 | SOH | Battery state of health | - | % | Bit0~Bit6: SOH value; Bit7: battery end-of-life warning flag |
| 238 | GaugeRM | Remaining capacity | 10 | mAh |  |
| 239 | GaugeFCC | Full charge capacity (nominal) | 10 | mAh |  |
| 240 | DeltaV | Cell voltage delta | 1 | mV |  |
| 241 | CycleCount | Charge/discharge cycle count | - | - |  |
| 242 | RequestOrBatteryType | Charge request or battery type | - | - | see note *20 |
| 243 | MaximumCellVoltage | Maximum cell voltage | 1 | mV |  |
| 244 | MinimumCellVoltage | Minimum cell voltage | 1 | mV |  |
| 245 | MaxMinCellVoltageNumber | Max/min cell voltage numbers | - | - | Bit0~Bit7: min voltage cell number; Bit8~Bit15: max voltage cell number |
| 246 | ProtectPackID | Faulted battery pack address | - | - |  |
| 247 | ManufacturerName | Manufacturer name | - | - |  |
| 248 | HardwareVersion | Hardware version | - | - | 1~9 |
| 249 | SoftwareVersion01 | Software version (bytes 0-1) | - | - |  |
| 250 | ParallelHightSoftwarVer | Highest software version in parallel system | - | - |  |
| 251 | MaxCellTemp | Maximum cell temperature | 0.1 | °C | signed int16 |
| 252 | MinCellTemp | Minimum cell temperature | 0.1 | °C | signed int16 |
| 253 | MaxMinCellTempSerialNum | Max/min temperature cell numbers | - | - | Bit0~Bit7: MinCellTempNum; Bit8~Bit15: MaxCellTempNum |
| 254 | MaxMinSOC | Max/min SOC | - | % | 0~100; Bit0~Bit7: MinSOC; Bit8~Bit15: MaxSOC |
| 255 | TotalCellNumber | Total cell count | - | - | 1~254 |
| 256 | BatProtect3_4 | Battery protection flags 3-4 | - | - | see note *21 |
| 257 | BatProtect5 | Battery protection flags 5 | - | - | see note *22 |
| 258 | BatWarnInfo3 | Battery warning flags 3 | - | - | see note *23 |
| 259 | UpdateStatus | Firmware upgrade status | - | - | Bit0~1: 0=normal, 1=programming, 2=upgrade successful |
| 260 | SoftwareVersion23 | Software version (bytes 2-3) | - | - | ASCII encoded |
| 261 | SoftwareVersion45 | Software version (bytes 4-5) | - | - | ASCII encoded |
| 262 | BatSerialNumber_ID | Battery serial number ID | - | - |  |
| 263 | BatSerialNumber0_1 | Battery serial number (chars 0-1) | - | - | ASCII encoded |
| 264 | BatSerialNumber2_3 | Battery serial number (chars 2-3) | - | - | ASCII encoded |
| 265 | BatSerialNumber4_5 | Battery serial number (chars 4-5) | - | - | ASCII encoded |
| 266 | BatSerialNumber6_7 | Battery serial number (chars 6-7) | - | - | ASCII encoded |
| 267 | BatSerialNumber8_9 | Battery serial number (chars 8-9) | - | - | ASCII encoded |
| 268 | BatSerialNumber10_11 | Battery serial number (chars 10-11) | - | - | ASCII encoded |
| 269 | BatSerialNumber12_13 | Battery serial number (chars 12-13) | - | - | ASCII encoded |
| 270 | BatSerialNumber14_15 | Battery serial number (chars 14-15) | - | - | ASCII encoded |
| 271 | BatSerialNumber16_17 | Battery serial number (chars 16-17) | - | - | ASCII encoded |
| 272 | BatSerialNumber18_19 | Battery serial number (chars 18-19) | - | - | ASCII encoded |
| 273 | ModuleID2 | Module ID 2 | - | - | 1~12 |
| 274 | Module2MaxVol | Module 2 maximum cell voltage | 0.01 | V |  |
| 275 | Module2MimVol | Module 2 minimum cell voltage | 0.01 | V |  |
| 276 | Module2MaxTemp | Module 2 maximum temperature | 1 | °C | offset +40 |
| 277 | Module2MimTemp | Module 2 minimum temperature | 1 | °C | offset +40 |
| 278 | DoStatus | Output dry contact status | - | - |  |
| 279 | DsgBatNumber | Discharge energy statistics - battery ID | 1 | kWh |  |
| 280 | DsgEnergyKWH_H | Discharge energy (high 16 bits) | 1 | kWh |  |
| 281 | DsgEnergyKWH_L | Discharge energy (low 16 bits) | 1 | kWh |  |
| 282 | ChgBatNumber | Charge energy statistics - battery ID | - | - |  |
| 283 | ChgEnergyKWH_H | Charge energy (high 16 bits) | 1 | kWh |  |
| 284 | ChgEnergyKWH_L | Charge energy (low 16 bits) | 1 | kWh |  |
| 285 | reserve285 | Reserved | - | - |  |
| 286 | reserve286 | Reserved | - | - |  |
| 287 | reserve287 | Reserved | - | - |  |
| 288 | reserve288 | Reserved | - | - |  |
| 289 | reserve289 | Reserved | - | - |  |
| 290 | reserve290 | Reserved | - | - |  |
