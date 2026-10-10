"""DLMS/COSEM meter test vectors and fixtures collected from physical meter."""

from __future__ import annotations

from typing import Any, Final

METER_MODEL: Final = "Mercury 234"
METER_MANUFACTURER: Final = "Incotex"
METER_SERIAL_NUMBER: Final = "41920942"
METER_FIRMWARE: Final = "09.00.00"
SERVER_PHYSICAL_ADDRESS: Final = 42
SERVER_LOGICAL_ADDRESS: Final = 1
CLIENT_LOGICAL_ADDRESS: Final = 32

# Individual frame constants for direct import in tests:
# Establish HDLC connection (SNRM -> UA)
SNRM_CONNECT_REQ_HDLC: Final = bytes.fromhex("7ea00802554193e9577e")
SNRM_CONNECT_RESP_HDLC: Final = bytes.fromhex(
    "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
)

# LowLevelSecurity Application Association (AARQ -> AARE Accepted)
AARQ_ASSOCIATE_SUCCESS_REQ_HDLC: Final = bytes.fromhex(
    "7ea04f025541108410e6e6006040a109060760857405080101a60a04087574691cc56a72648a0207808b0760857405080201ac088006313131313131be10040e01000000065f1f040020525fffff705c7e"
)
AARQ_ASSOCIATE_SUCCESS_RESP_HDLC: Final = bytes.fromhex(
    "7ea03841025530c4dae6e7006129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007828b7e"
)
AARQ_ASSOCIATE_SUCCESS_REQ_APDU: Final = bytes.fromhex(
    "6040a109060760857405080101a60a04087574691cc56a72648a0207808b0760857405080201ac088006313131313131be10040e01000000065f1f040020525fffff"
)
AARQ_ASSOCIATE_SUCCESS_RESP_APDU: Final = bytes.fromhex(
    "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
)

# GET Logical Device Name (Obis(a=0, b=0, c=42, d=0, e=0, f=255), attr 2)
GET_LOGICAL_DEVICE_NAME_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554132a241e6e600c001c0000100002a0000ff020083d57e"
)
GET_LOGICAL_DEVICE_NAME_RESP_HDLC: Final = bytes.fromhex(
    "7ea023410255527c69e6e700c401c0000910494e433233343030343139323039343214ab7e"
)
GET_LOGICAL_DEVICE_NAME_REQ_APDU: Final = bytes.fromhex("c001c0000100002a0000ff0200")
GET_LOGICAL_DEVICE_NAME_RESP_APDU: Final = bytes.fromhex(
    "c401c0000910494e4332333430303431393230393432"
)

# GET Meter Serial Number (Obis(a=0, b=0, c=96, d=1, e=0, f=255), attr 2)
GET_EQUIPMENT_ID_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541549247e6e600c001c100010000600100ff020089a07e"
)
GET_EQUIPMENT_ID_RESP_HDLC: Final = bytes.fromhex(
    "7ea01b41025574b9a3e6e700c401c1000a083431393230393432d4217e"
)
GET_EQUIPMENT_ID_REQ_APDU: Final = bytes.fromhex("c001c100010000600100ff0200")
GET_EQUIPMENT_ID_RESP_APDU: Final = bytes.fromhex("c401c1000a083431393230393432")

# GET Software Package / Firmware Version (Obis(a=0, b=0, c=96, d=1, e=2, f=255), attr 2)
GET_SOFTWARE_PACKAGE_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541768245e6e600c001c200010000600102ff02004c677e"
)
GET_SOFTWARE_PACKAGE_RESP_HDLC: Final = bytes.fromhex(
    "7ea01b41025596a567e6e700c401c2000a0830392e30302e3030036b7e"
)
GET_SOFTWARE_PACKAGE_REQ_APDU: Final = bytes.fromhex("c001c200010000600102ff0200")
GET_SOFTWARE_PACKAGE_RESP_APDU: Final = bytes.fromhex("c401c2000a0830392e30302e3030")

# GET Current Phase L1 (mA) (Obis(a=1, b=0, c=31, d=7, e=0, f=255), attr 2)
GET_CURRENT_L1_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554198f24be6e600c001c3000301001f0700ff0200fed27e"
)
GET_CURRENT_L1_RESP_HDLC: Final = bytes.fromhex("7ea016410255b8add3e6e700c401c30006000008110ee07e")
GET_CURRENT_L1_REQ_APDU: Final = bytes.fromhex("c001c3000301001f0700ff0200")
GET_CURRENT_L1_RESP_APDU: Final = bytes.fromhex("c401c3000600000811")

# GET Current Phase L2 (mA) (Obis(a=1, b=0, c=51, d=7, e=0, f=255), attr 2)
GET_CURRENT_L2_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541bae249e6e600c001c400030100330700ff02008cc67e"
)
GET_CURRENT_L2_RESP_HDLC: Final = bytes.fromhex("7ea016410255dab993e6e700c401c40006000004da69f67e")
GET_CURRENT_L2_REQ_APDU: Final = bytes.fromhex("c001c400030100330700ff0200")
GET_CURRENT_L2_RESP_APDU: Final = bytes.fromhex("c401c40006000004da")

# GET Current Phase L3 (mA) (Obis(a=1, b=0, c=71, d=7, e=0, f=255), attr 2)
GET_CURRENT_L3_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541dcd24fe6e600c001c500030100470700ff0200b0467e"
)
GET_CURRENT_L3_RESP_HDLC: Final = bytes.fromhex("7ea016410255fc8dd7e6e700c401c500060000018b08547e")
GET_CURRENT_L3_REQ_APDU: Final = bytes.fromhex("c001c500030100470700ff0200")
GET_CURRENT_L3_RESP_APDU: Final = bytes.fromhex("c401c500060000018b")

# GET Voltage Phase L1 (0.01 V) (Obis(a=1, b=0, c=32, d=7, e=0, f=255), attr 2)
GET_VOLTAGE_L1_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541fec24de6e600c001c600030100200700ff020063237e"
)
GET_VOLTAGE_L1_RESP_HDLC: Final = bytes.fromhex("7ea0144102551e1905e6e700c401c6001255cf6b127e")
GET_VOLTAGE_L1_REQ_APDU: Final = bytes.fromhex("c001c600030100200700ff0200")
GET_VOLTAGE_L1_RESP_APDU: Final = bytes.fromhex("c401c6001255cf")

# GET Voltage Phase L2 (0.01 V) (Obis(a=1, b=0, c=52, d=7, e=0, f=255), attr 2)
GET_VOLTAGE_L2_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554110b243e6e600c001c700030100340700ff0200ee247e"
)
GET_VOLTAGE_L2_RESP_HDLC: Final = bytes.fromhex("7ea0144102553065cde6e700c401c70012511598077e")
GET_VOLTAGE_L2_REQ_APDU: Final = bytes.fromhex("c001c700030100340700ff0200")
GET_VOLTAGE_L2_RESP_APDU: Final = bytes.fromhex("c401c700125115")

# GET Voltage Phase L3 (0.01 V) (Obis(a=1, b=0, c=72, d=7, e=0, f=255), attr 2)
GET_VOLTAGE_L3_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554132a241e6e600c001c800030100480700ff020057cc7e"
)
GET_VOLTAGE_L3_RESP_HDLC: Final = bytes.fromhex("7ea01441025552718de6e700c401c8001257b388f97e")
GET_VOLTAGE_L3_REQ_APDU: Final = bytes.fromhex("c001c800030100480700ff0200")
GET_VOLTAGE_L3_RESP_APDU: Final = bytes.fromhex("c401c8001257b3")

# GET Total Active Power (0.01 W) (Obis(a=1, b=0, c=1, d=7, e=0, f=255), attr 2)
GET_ACTIVE_POWER_TOTAL_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541549247e6e600c001c900030100010700ff020064be7e"
)
GET_ACTIVE_POWER_TOTAL_RESP_HDLC: Final = bytes.fromhex(
    "7ea01641025574cddfe6e700c401c900050000e98eaa887e"
)
GET_ACTIVE_POWER_TOTAL_REQ_APDU: Final = bytes.fromhex("c001c900030100010700ff0200")
GET_ACTIVE_POWER_TOTAL_RESP_APDU: Final = bytes.fromhex("c401c900050000e98e")

# GET Active Power Phase L1 (0.01 W) (Obis(a=1, b=0, c=21, d=7, e=0, f=255), attr 2)
GET_ACTIVE_POWER_L1_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541768245e6e600c001ca00030100150700ff0200cb127e"
)
GET_ACTIVE_POWER_L1_RESP_HDLC: Final = bytes.fromhex(
    "7ea01641025596d11be6e700c401ca000500007610a6c77e"
)
GET_ACTIVE_POWER_L1_REQ_APDU: Final = bytes.fromhex("c001ca00030100150700ff0200")
GET_ACTIVE_POWER_L1_RESP_APDU: Final = bytes.fromhex("c401ca000500007610")

# GET Active Power Phase L2 (0.01 W) (Obis(a=1, b=0, c=41, d=7, e=0, f=255), attr 2)
GET_ACTIVE_POWER_L2_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554198f24be6e600c001cb00030100290700ff02007eb17e"
)
GET_ACTIVE_POWER_L2_RESP_HDLC: Final = bytes.fromhex(
    "7ea016410255b8add3e6e700c401cb0005000055d024977e"
)
GET_ACTIVE_POWER_L2_REQ_APDU: Final = bytes.fromhex("c001cb00030100290700ff0200")
GET_ACTIVE_POWER_L2_RESP_APDU: Final = bytes.fromhex("c401cb0005000055d0")

# GET Active Power Phase L3 (0.01 W) (Obis(a=1, b=0, c=61, d=7, e=0, f=255), attr 2)
GET_ACTIVE_POWER_L3_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541bae249e6e600c001cc000301003d0700ff020084437e"
)
GET_ACTIVE_POWER_L3_RESP_HDLC: Final = bytes.fromhex(
    "7ea016410255dab993e6e700c401cc000500001d5f65a47e"
)
GET_ACTIVE_POWER_L3_REQ_APDU: Final = bytes.fromhex("c001cc000301003d0700ff0200")
GET_ACTIVE_POWER_L3_RESP_APDU: Final = bytes.fromhex("c401cc000500001d5f")

# GET Apparent Power Phase L1 (0.01 VA) (Obis(a=1, b=0, c=29, d=7, e=0, f=255), attr 2)
GET_APPARENT_POWER_L1_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541dcd24fe6e600c001cd000301001d0700ff020075937e"
)
GET_APPARENT_POWER_L1_RESP_HDLC: Final = bytes.fromhex(
    "7ea016410255fc8dd7e6e700c401cd00060000b1e817e17e"
)
GET_APPARENT_POWER_L1_REQ_APDU: Final = bytes.fromhex("c001cd000301001d0700ff0200")
GET_APPARENT_POWER_L1_RESP_APDU: Final = bytes.fromhex("c401cd00060000b1e8")

# GET Apparent Power Phase L2 (0.01 VA) (Obis(a=1, b=0, c=49, d=7, e=0, f=255), attr 2)
GET_APPARENT_POWER_L2_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541fec24de6e600c001ce00030100310700ff020052d97e"
)
GET_APPARENT_POWER_L2_RESP_HDLC: Final = bytes.fromhex(
    "7ea0164102551e9113e6e700c401ce0006000055bc21d37e"
)
GET_APPARENT_POWER_L2_REQ_APDU: Final = bytes.fromhex("c001ce00030100310700ff0200")
GET_APPARENT_POWER_L2_RESP_APDU: Final = bytes.fromhex("c401ce0006000055bc")

# GET Apparent Power Phase L3 (0.01 VA) (Obis(a=1, b=0, c=69, d=7, e=0, f=255), attr 2)
GET_APPARENT_POWER_L3_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554110b243e6e600c001cf00030100450700ff02006e597e"
)
GET_APPARENT_POWER_L3_RESP_HDLC: Final = bytes.fromhex(
    "7ea01641025530eddbe6e700c401cf000600002271d1ec7e"
)
GET_APPARENT_POWER_L3_REQ_APDU: Final = bytes.fromhex("c001cf00030100450700ff0200")
GET_APPARENT_POWER_L3_RESP_APDU: Final = bytes.fromhex("c401cf000600002271")

# GET Total Apparent Power (0.01 VA) (Obis(a=1, b=0, c=9, d=7, e=0, f=255), attr 2)
GET_APPARENT_POWER_TOTAL_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554132a241e6e600c001c000030100090700ff020007767e"
)
GET_APPARENT_POWER_TOTAL_RESP_HDLC: Final = bytes.fromhex(
    "7ea01641025552f99be6e700c401c0000600012f542e697e"
)
GET_APPARENT_POWER_TOTAL_REQ_APDU: Final = bytes.fromhex("c001c000030100090700ff0200")
GET_APPARENT_POWER_TOTAL_RESP_APDU: Final = bytes.fromhex("c401c0000600012f54")

# GET Total Power Factor (0.001) (Obis(a=1, b=0, c=13, d=7, e=0, f=255), attr 2)
GET_POWER_FACTOR_TOTAL_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541549247e6e600c001c1000301000d0700ff02003a337e"
)
GET_POWER_FACTOR_TOTAL_RESP_HDLC: Final = bytes.fromhex(
    "7ea0144102557445c9e6e700c401c1001002d9477c7e"
)
GET_POWER_FACTOR_TOTAL_REQ_APDU: Final = bytes.fromhex("c001c1000301000d0700ff0200")
GET_POWER_FACTOR_TOTAL_RESP_APDU: Final = bytes.fromhex("c401c1001002d9")

# GET Power Factor Phase L1 (0.001) (Obis(a=1, b=0, c=33, d=7, e=0, f=255), attr 2)
GET_POWER_FACTOR_L1_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541768245e6e600c001c200030100210700ff02001d797e"
)
GET_POWER_FACTOR_L1_RESP_HDLC: Final = bytes.fromhex("7ea01441025596590de6e700c401c20010028ca3647e")
GET_POWER_FACTOR_L1_REQ_APDU: Final = bytes.fromhex("c001c200030100210700ff0200")
GET_POWER_FACTOR_L1_RESP_APDU: Final = bytes.fromhex("c401c20010028c")

# GET Power Factor Phase L2 (0.001) (Obis(a=1, b=0, c=53, d=7, e=0, f=255), attr 2)
GET_POWER_FACTOR_L2_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554198f24be6e600c001c300030100350700ff0200907e7e"
)
GET_POWER_FACTOR_L2_RESP_HDLC: Final = bytes.fromhex("7ea014410255b825c5e6e700c401c3001003405f7a7e")
GET_POWER_FACTOR_L2_REQ_APDU: Final = bytes.fromhex("c001c300030100350700ff0200")
GET_POWER_FACTOR_L2_RESP_APDU: Final = bytes.fromhex("c401c300100340")

# GET Power Factor Phase L3 (0.001) (Obis(a=1, b=0, c=73, d=7, e=0, f=255), attr 2)
GET_POWER_FACTOR_L3_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541bae249e6e600c001c400030100490700ff0200832a7e"
)
GET_POWER_FACTOR_L3_RESP_HDLC: Final = bytes.fromhex("7ea014410255da3185e6e700c401c400100354261c7e")
GET_POWER_FACTOR_L3_REQ_APDU: Final = bytes.fromhex("c001c400030100490700ff0200")
GET_POWER_FACTOR_L3_RESP_APDU: Final = bytes.fromhex("c401c400100354")

# GET Grid Frequency (0.01 Hz) (Obis(a=1, b=0, c=14, d=7, e=0, f=255), attr 2)
GET_FREQUENCY_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541dcd24fe6e600c001c5000301000e0700ff020012617e"
)
GET_FREQUENCY_RESP_HDLC: Final = bytes.fromhex("7ea014410255fc05c1e6e700c401c50012138b31197e")
GET_FREQUENCY_REQ_APDU: Final = bytes.fromhex("c001c5000301000e0700ff0200")
GET_FREQUENCY_RESP_APDU: Final = bytes.fromhex("c401c50012138b")

# GET Voltage L1 Scaler and Unit (Obis(a=1, b=0, c=32, d=7, e=0, f=255), attr 3)
GET_VOLTAGE_L1_SCALER_UNIT_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541fec24de6e600c001c600030100200700ff0300bb3a7e"
)
GET_VOLTAGE_L1_SCALER_UNIT_RESP_HDLC: Final = bytes.fromhex(
    "7ea0174102551ed518e6e700c401c60002020ffe1623263e7e"
)
GET_VOLTAGE_L1_SCALER_UNIT_REQ_APDU: Final = bytes.fromhex("c001c600030100200700ff0300")
GET_VOLTAGE_L1_SCALER_UNIT_RESP_APDU: Final = bytes.fromhex("c401c60002020ffe1623")

# GET Current L1 Scaler and Unit (Obis(a=1, b=0, c=31, d=7, e=0, f=255), attr 3)
GET_CURRENT_L1_SCALER_UNIT_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554110b243e6e600c001c7000301001f0700ff030073957e"
)
GET_CURRENT_L1_SCALER_UNIT_RESP_HDLC: Final = bytes.fromhex(
    "7ea01741025530a9d0e6e700c401c70002020ffd1621ef737e"
)
GET_CURRENT_L1_SCALER_UNIT_REQ_APDU: Final = bytes.fromhex("c001c7000301001f0700ff0300")
GET_CURRENT_L1_SCALER_UNIT_RESP_APDU: Final = bytes.fromhex("c401c70002020ffd1621")

# GET Active Power Scaler and Unit (Obis(a=1, b=0, c=1, d=7, e=0, f=255), attr 3)
GET_ACTIVE_POWER_TOTAL_SCALER_UNIT_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554132a241e6e600c001c800030100010700ff03002df27e"
)
GET_ACTIVE_POWER_TOTAL_SCALER_UNIT_RESP_HDLC: Final = bytes.fromhex(
    "7ea01741025552bd90e6e700c401c80002020ffe161be0b37e"
)
GET_ACTIVE_POWER_TOTAL_SCALER_UNIT_REQ_APDU: Final = bytes.fromhex("c001c800030100010700ff0300")
GET_ACTIVE_POWER_TOTAL_SCALER_UNIT_RESP_APDU: Final = bytes.fromhex("c401c80002020ffe161b")

# GET Active Energy Scaler and Unit (Obis(a=1, b=0, c=1, d=8, e=0, f=255), attr 3)
GET_ACTIVE_ENERGY_TOTAL_SCALER_UNIT_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541549247e6e600c001c900030100010800ff030040cd7e"
)
GET_ACTIVE_ENERGY_TOTAL_SCALER_UNIT_RESP_HDLC: Final = bytes.fromhex(
    "7ea0174102557489d4e6e700c401c90002020f00161eddf97e"
)
GET_ACTIVE_ENERGY_TOTAL_SCALER_UNIT_REQ_APDU: Final = bytes.fromhex("c001c900030100010800ff0300")
GET_ACTIVE_ENERGY_TOTAL_SCALER_UNIT_RESP_APDU: Final = bytes.fromhex("c401c90002020f00161e")

# GET Total Active Energy (Wh) (Obis(a=1, b=0, c=1, d=8, e=0, f=255), attr 2)
GET_ACTIVE_ENERGY_TOTAL_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541768245e6e600c001ca00030100010800ff02002b2a7e"
)
GET_ACTIVE_ENERGY_TOTAL_RESP_HDLC: Final = bytes.fromhex(
    "7ea01641025596d11be6e700c401ca0006022920de6cd47e"
)
GET_ACTIVE_ENERGY_TOTAL_REQ_APDU: Final = bytes.fromhex("c001ca00030100010800ff0200")
GET_ACTIVE_ENERGY_TOTAL_RESP_APDU: Final = bytes.fromhex("c401ca0006022920de")

# GET Active Energy Tariff 1 (Wh) (Obis(a=1, b=0, c=1, d=8, e=1, f=255), attr 2)
GET_ACTIVE_ENERGY_TARIFF1_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554198f24be6e600c001cb00030100010801ff020001637e"
)
GET_ACTIVE_ENERGY_TARIFF1_RESP_HDLC: Final = bytes.fromhex(
    "7ea016410255b8add3e6e700c401cb0006010128122d697e"
)
GET_ACTIVE_ENERGY_TARIFF1_REQ_APDU: Final = bytes.fromhex("c001cb00030100010801ff0200")
GET_ACTIVE_ENERGY_TARIFF1_RESP_APDU: Final = bytes.fromhex("c401cb000601012812")

# GET Active Energy Tariff 2 (Wh) (Obis(a=1, b=0, c=1, d=8, e=2, f=255), attr 2)
GET_ACTIVE_ENERGY_TARIFF2_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541bae249e6e600c001cc00030100010802ff02002ae67e"
)
GET_ACTIVE_ENERGY_TARIFF2_RESP_HDLC: Final = bytes.fromhex(
    "7ea016410255dab993e6e700c401cc00060127f8cc1f1b7e"
)
GET_ACTIVE_ENERGY_TARIFF2_REQ_APDU: Final = bytes.fromhex("c001cc00030100010802ff0200")
GET_ACTIVE_ENERGY_TARIFF2_RESP_APDU: Final = bytes.fromhex("c401cc00060127f8cc")

# GET Current Active Tariff (Obis(a=0, b=0, c=96, d=14, e=0, f=255), attr 2)
GET_ACTIVE_TARIFF_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541dcd24fe6e600c001cd00010000600e00ff02008a287e"
)
GET_ACTIVE_TARIFF_RESP_HDLC: Final = bytes.fromhex("7ea013410255fcd9f1e6e700c401cd001101a6cb7e")
GET_ACTIVE_TARIFF_REQ_APDU: Final = bytes.fromhex("c001cd00010000600e00ff0200")
GET_ACTIVE_TARIFF_RESP_APDU: Final = bytes.fromhex("c401cd001101")

# GET Internal Meter Temperature (C) (Obis(a=0, b=0, c=96, d=9, e=0, f=255), attr 2)
GET_INTERNAL_TEMPERATURE_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541fec24de6e600c001ce00030000600900ff02001f7d7e"
)
GET_INTERNAL_TEMPERATURE_RESP_HDLC: Final = bytes.fromhex(
    "7ea0144102551e1905e6e700c401ce00100012d45d7e"
)
GET_INTERNAL_TEMPERATURE_REQ_APDU: Final = bytes.fromhex("c001ce00030000600900ff0200")
GET_INTERNAL_TEMPERATURE_RESP_APDU: Final = bytes.fromhex("c401ce00100012")

# GET Meter Operating Time (seconds) (Obis(a=0, b=0, c=96, d=8, e=0, f=255), attr 2)
GET_UPTIME_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554110b243e6e600c001cf00030000600800ff0200ca237e"
)
GET_UPTIME_RESP_HDLC: Final = bytes.fromhex("7ea01641025530eddbe6e700c401cf0006078c216b0c877e")
GET_UPTIME_REQ_APDU: Final = bytes.fromhex("c001cf00030000600800ff0200")
GET_UPTIME_RESP_APDU: Final = bytes.fromhex("c401cf0006078c216b")

# GET Meter Internal Clock (DLMS datetime) (Obis(a=0, b=0, c=1, d=0, e=0, f=255), attr 2)
GET_LOCAL_TIME_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554132a241e6e600c001c000080000010000ff0200f14f7e"
)
GET_LOCAL_TIME_RESP_HDLC: Final = bytes.fromhex(
    "7ea01f410255529dcae6e700c401c000090c07ea0a0a061317230000b400e08d7e"
)
GET_LOCAL_TIME_REQ_APDU: Final = bytes.fromhex("c001c000080000010000ff0200")
GET_LOCAL_TIME_RESP_APDU: Final = bytes.fromhex("c401c000090c07ea0a0a061317230000b400")

# GET Last Clock Sync Timestamp (Obis(a=0, b=0, c=96, d=2, e=12, f=255), attr 2)
GET_CLOCK_SYNCED_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541549247e6e600c001c10001000060020cff0200712a7e"
)
GET_CLOCK_SYNCED_RESP_HDLC: Final = bytes.fromhex(
    "7ea01f41025574a98ee6e700c401c100090c07ea0a060200310b0000b4008def7e"
)
GET_CLOCK_SYNCED_REQ_APDU: Final = bytes.fromhex("c001c10001000060020cff0200")
GET_CLOCK_SYNCED_RESP_APDU: Final = bytes.fromhex("c401c100090c07ea0a060200310b0000b400")

# GET Last Front Cover Opened Timestamp (Obis(a=0, b=0, c=96, d=20, e=1, f=255), attr 2)
GET_FRONT_COVER_OPENED_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541768245e6e600c001c200010000601401ff020095d07e"
)
GET_FRONT_COVER_OPENED_RESP_HDLC: Final = bytes.fromhex(
    "7ea01f41025596b54ae6e700c401c200090c07e40717040b31110000b40051e87e"
)
GET_FRONT_COVER_OPENED_REQ_APDU: Final = bytes.fromhex("c001c200010000601401ff0200")
GET_FRONT_COVER_OPENED_RESP_APDU: Final = bytes.fromhex("c401c200090c07e40717040b31110000b400")

# GET Last Terminals Cover Opened Timestamp (Obis(a=0, b=0, c=96, d=20, e=6, f=255), attr 2)
GET_TERMINALS_COVER_OPENED_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554198f24be6e600c001c300010000601406ff020025d27e"
)
GET_TERMINALS_COVER_OPENED_RESP_HDLC: Final = bytes.fromhex(
    "7ea01f410255b8c982e6e700c401c300090c07e60915030e172c0000b400f08e7e"
)
GET_TERMINALS_COVER_OPENED_REQ_APDU: Final = bytes.fromhex("c001c300010000601406ff0200")
GET_TERMINALS_COVER_OPENED_RESP_APDU: Final = bytes.fromhex("c401c300090c07e60915030e172c0000b400")

# GET Last Magnetic Field Detection Timestamp (Obis(a=0, b=0, c=96, d=20, e=16, f=255), attr 2)
GET_MAGNETIC_FIELD_DETECTED_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541bae249e6e600c001c400010000601410ff0200f8fa7e"
)
GET_MAGNETIC_FIELD_DETECTED_RESP_HDLC: Final = bytes.fromhex(
    "7ea01f410255daddc2e6e700c401c400090c07e40717040b310f0000b400fa017e"
)
GET_MAGNETIC_FIELD_DETECTED_REQ_APDU: Final = bytes.fromhex("c001c400010000601410ff0200")
GET_MAGNETIC_FIELD_DETECTED_RESP_APDU: Final = bytes.fromhex("c401c400090c07e40717040b310f0000b400")

# GET Meter Self-Test Error Flags (Obis(a=0, b=0, c=97, d=97, e=0, f=255), attr 2)
GET_SELF_TEST_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541dcd24fe6e600c001c500010000616100ff0200445b7e"
)
GET_SELF_TEST_RESP_HDLC: Final = bytes.fromhex(
    "7ea019410255fc71bde6e700c401c5000906000000000000d9bb7e"
)
GET_SELF_TEST_REQ_APDU: Final = bytes.fromhex("c001c500010000616100ff0200")
GET_SELF_TEST_RESP_APDU: Final = bytes.fromhex("c401c5000906000000000000")

# GET request for non-existent OBIS (0.0.99.99.99.255) -> OBJECT_UNDEFINED
GET_ERROR_NONEXISTENT_OBIS_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a025541fec24de6e600c001c600010000636363ff020000077e"
)
GET_ERROR_NONEXISTENT_OBIS_RESP_HDLC: Final = bytes.fromhex(
    "7ea0124102551e813ee6e700c401c60104c97a7e"
)
GET_ERROR_NONEXISTENT_OBIS_REQ_APDU: Final = bytes.fromhex("c001c600010000636363ff0200")
GET_ERROR_NONEXISTENT_OBIS_RESP_APDU: Final = bytes.fromhex("c401c60104")

# GET request for non-existent attribute (attr 99) -> OBJECT_UNDEFINED
GET_ERROR_NONEXISTENT_ATTRIBUTE_REQ_HDLC: Final = bytes.fromhex(
    "7ea01a02554110b243e6e600c001c7000100002a0000ff6300e8097e"
)
GET_ERROR_NONEXISTENT_ATTRIBUTE_RESP_HDLC: Final = bytes.fromhex(
    "7ea01241025530fdf6e6e700c401c7010415207e"
)
GET_ERROR_NONEXISTENT_ATTRIBUTE_REQ_APDU: Final = bytes.fromhex("c001c7000100002a0000ff6300")
GET_ERROR_NONEXISTENT_ATTRIBUTE_RESP_APDU: Final = bytes.fromhex("c401c70104")

# HDLC Disconnect (DISC -> UA)
DISC_DISCONNECT_REQ_HDLC: Final = bytes.fromhex("7ea00802554153e5917e")
DISC_DISCONNECT_RESP_HDLC: Final = bytes.fromhex(
    "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
)

# Establish HDLC connection for auth failure test (SNRM -> UA)
SNRM_CONNECT_AUTH_SESSION_REQ_HDLC: Final = bytes.fromhex("7ea00802554193e9577e")
SNRM_CONNECT_AUTH_SESSION_RESP_HDLC: Final = bytes.fromhex(
    "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
)

# AARQ with wrong secret -> AARE REJECTED_PERMANENT (AUTHENTICATION_FAILED 13)
AARQ_ASSOCIATE_AUTH_FAILURE_REQ_HDLC: Final = bytes.fromhex(
    "7ea04f025541108410e6e6006040a109060760857405080101a60a0408757469b6a30b12588a0207808b0760857405080201ac08800677726f6e6721be10040e01000000065f1f040020525fffffcd7f7e"
)
AARQ_ASSOCIATE_AUTH_FAILURE_RESP_HDLC: Final = bytes.fromhex(
    "7ea02e410255301c55e6e700611fa109060760857405080101a203020101a305a10302010dbe0604040e0106016c717e"
)
AARQ_ASSOCIATE_AUTH_FAILURE_REQ_APDU: Final = bytes.fromhex(
    "6040a109060760857405080101a60a0408757469b6a30b12588a0207808b0760857405080201ac08800677726f6e6721be10040e01000000065f1f040020525fffff"
)
AARQ_ASSOCIATE_AUTH_FAILURE_RESP_APDU: Final = bytes.fromhex(
    "611fa109060760857405080101a203020101a305a10302010dbe0604040e010601"
)

# HDLC Disconnect after auth fail (DISC -> UA)
DISC_DISCONNECT_AUTH_SESSION_REQ_HDLC: Final = bytes.fromhex("7ea00802554153e5917e")
DISC_DISCONNECT_AUTH_SESSION_RESP_HDLC: Final = bytes.fromhex(
    "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
)

# Full exchange dictionary list
EXCHANGES: Final[list[dict[str, Any]]] = [
    {
        "id": "snrm_connect",
        "category": "session_management",
        "description": "Establish HDLC connection (SNRM -> UA)",
        "req_hdlc": bytes.fromhex("7ea00802554193e9577e"),
        "resp_hdlc": bytes.fromhex(
            "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
        ),
        "decoded_value": None,
    },
    {
        "id": "aarq_associate_success",
        "category": "session_management",
        "description": "LowLevelSecurity Application Association (AARQ -> AARE Accepted)",
        "req_hdlc": bytes.fromhex(
            "7ea04f025541108410e6e6006040a109060760857405080101a60a04087574691cc56a72648a0207808b0760857405080201ac088006313131313131be10040e01000000065f1f040020525fffff705c7e"
        ),
        "resp_hdlc": bytes.fromhex(
            "7ea03841025530c4dae6e7006129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007828b7e"
        ),
        "req_apdu": bytes.fromhex(
            "6040a109060760857405080101a60a04087574691cc56a72648a0207808b0760857405080201ac088006313131313131be10040e01000000065f1f040020525fffff"
        ),
        "resp_apdu": bytes.fromhex(
            "6129a109060760857405080101a203020100a305a103020100be10040e0800065f1f040000101d00640007"
        ),
        "decoded_value": "AssociationResult.ACCEPTED",
    },
    {
        "id": "get_logical_device_name",
        "category": "identification",
        "description": "GET Logical Device Name (Obis(a=0, b=0, c=42, d=0, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554132a241e6e600c001c0000100002a0000ff020083d57e"),
        "resp_hdlc": bytes.fromhex(
            "7ea023410255527c69e6e700c401c0000910494e433233343030343139323039343214ab7e"
        ),
        "req_apdu": bytes.fromhex("c001c0000100002a0000ff0200"),
        "resp_apdu": bytes.fromhex("c401c0000910494e4332333430303431393230393432"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=42, d=0, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": {
            "type": "bytes",
            "hex": "494e4332333430303431393230393432",
            "str": "INC2340041920942",
        },
    },
    {
        "id": "get_equipment_id",
        "category": "identification",
        "description": "GET Meter Serial Number (Obis(a=0, b=0, c=96, d=1, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541549247e6e600c001c100010000600100ff020089a07e"),
        "resp_hdlc": bytes.fromhex("7ea01b41025574b9a3e6e700c401c1000a083431393230393432d4217e"),
        "req_apdu": bytes.fromhex("c001c100010000600100ff0200"),
        "resp_apdu": bytes.fromhex("c401c1000a083431393230393432"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=96, d=1, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": "41920942",
    },
    {
        "id": "get_software_package",
        "category": "identification",
        "description": "GET Software Package / Firmware Version (Obis(a=0, b=0, c=96, d=1, e=2, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541768245e6e600c001c200010000600102ff02004c677e"),
        "resp_hdlc": bytes.fromhex("7ea01b41025596a567e6e700c401c2000a0830392e30302e3030036b7e"),
        "req_apdu": bytes.fromhex("c001c200010000600102ff0200"),
        "resp_apdu": bytes.fromhex("c401c2000a0830392e30302e3030"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=96, d=1, e=2, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": "09.00.00",
    },
    {
        "id": "get_current_l1",
        "category": "instantaneous",
        "description": "GET Current Phase L1 (mA) (Obis(a=1, b=0, c=31, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554198f24be6e600c001c3000301001f0700ff0200fed27e"),
        "resp_hdlc": bytes.fromhex("7ea016410255b8add3e6e700c401c30006000008110ee07e"),
        "req_apdu": bytes.fromhex("c001c3000301001f0700ff0200"),
        "resp_apdu": bytes.fromhex("c401c3000600000811"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=31, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 2065,
    },
    {
        "id": "get_current_l2",
        "category": "instantaneous",
        "description": "GET Current Phase L2 (mA) (Obis(a=1, b=0, c=51, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541bae249e6e600c001c400030100330700ff02008cc67e"),
        "resp_hdlc": bytes.fromhex("7ea016410255dab993e6e700c401c40006000004da69f67e"),
        "req_apdu": bytes.fromhex("c001c400030100330700ff0200"),
        "resp_apdu": bytes.fromhex("c401c40006000004da"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=51, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 1242,
    },
    {
        "id": "get_current_l3",
        "category": "instantaneous",
        "description": "GET Current Phase L3 (mA) (Obis(a=1, b=0, c=71, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541dcd24fe6e600c001c500030100470700ff0200b0467e"),
        "resp_hdlc": bytes.fromhex("7ea016410255fc8dd7e6e700c401c500060000018b08547e"),
        "req_apdu": bytes.fromhex("c001c500030100470700ff0200"),
        "resp_apdu": bytes.fromhex("c401c500060000018b"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=71, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 395,
    },
    {
        "id": "get_voltage_l1",
        "category": "instantaneous",
        "description": "GET Voltage Phase L1 (0.01 V) (Obis(a=1, b=0, c=32, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541fec24de6e600c001c600030100200700ff020063237e"),
        "resp_hdlc": bytes.fromhex("7ea0144102551e1905e6e700c401c6001255cf6b127e"),
        "req_apdu": bytes.fromhex("c001c600030100200700ff0200"),
        "resp_apdu": bytes.fromhex("c401c6001255cf"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=32, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 21967,
    },
    {
        "id": "get_voltage_l2",
        "category": "instantaneous",
        "description": "GET Voltage Phase L2 (0.01 V) (Obis(a=1, b=0, c=52, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554110b243e6e600c001c700030100340700ff0200ee247e"),
        "resp_hdlc": bytes.fromhex("7ea0144102553065cde6e700c401c70012511598077e"),
        "req_apdu": bytes.fromhex("c001c700030100340700ff0200"),
        "resp_apdu": bytes.fromhex("c401c700125115"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=52, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 20757,
    },
    {
        "id": "get_voltage_l3",
        "category": "instantaneous",
        "description": "GET Voltage Phase L3 (0.01 V) (Obis(a=1, b=0, c=72, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554132a241e6e600c001c800030100480700ff020057cc7e"),
        "resp_hdlc": bytes.fromhex("7ea01441025552718de6e700c401c8001257b388f97e"),
        "req_apdu": bytes.fromhex("c001c800030100480700ff0200"),
        "resp_apdu": bytes.fromhex("c401c8001257b3"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=72, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 22451,
    },
    {
        "id": "get_active_power_total",
        "category": "instantaneous",
        "description": "GET Total Active Power (0.01 W) (Obis(a=1, b=0, c=1, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541549247e6e600c001c900030100010700ff020064be7e"),
        "resp_hdlc": bytes.fromhex("7ea01641025574cddfe6e700c401c900050000e98eaa887e"),
        "req_apdu": bytes.fromhex("c001c900030100010700ff0200"),
        "resp_apdu": bytes.fromhex("c401c900050000e98e"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=1, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 59790,
    },
    {
        "id": "get_active_power_l1",
        "category": "instantaneous",
        "description": "GET Active Power Phase L1 (0.01 W) (Obis(a=1, b=0, c=21, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541768245e6e600c001ca00030100150700ff0200cb127e"),
        "resp_hdlc": bytes.fromhex("7ea01641025596d11be6e700c401ca000500007610a6c77e"),
        "req_apdu": bytes.fromhex("c001ca00030100150700ff0200"),
        "resp_apdu": bytes.fromhex("c401ca000500007610"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=21, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 30224,
    },
    {
        "id": "get_active_power_l2",
        "category": "instantaneous",
        "description": "GET Active Power Phase L2 (0.01 W) (Obis(a=1, b=0, c=41, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554198f24be6e600c001cb00030100290700ff02007eb17e"),
        "resp_hdlc": bytes.fromhex("7ea016410255b8add3e6e700c401cb0005000055d024977e"),
        "req_apdu": bytes.fromhex("c001cb00030100290700ff0200"),
        "resp_apdu": bytes.fromhex("c401cb0005000055d0"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=41, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 21968,
    },
    {
        "id": "get_active_power_l3",
        "category": "instantaneous",
        "description": "GET Active Power Phase L3 (0.01 W) (Obis(a=1, b=0, c=61, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541bae249e6e600c001cc000301003d0700ff020084437e"),
        "resp_hdlc": bytes.fromhex("7ea016410255dab993e6e700c401cc000500001d5f65a47e"),
        "req_apdu": bytes.fromhex("c001cc000301003d0700ff0200"),
        "resp_apdu": bytes.fromhex("c401cc000500001d5f"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=61, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 7519,
    },
    {
        "id": "get_apparent_power_l1",
        "category": "instantaneous",
        "description": "GET Apparent Power Phase L1 (0.01 VA) (Obis(a=1, b=0, c=29, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541dcd24fe6e600c001cd000301001d0700ff020075937e"),
        "resp_hdlc": bytes.fromhex("7ea016410255fc8dd7e6e700c401cd00060000b1e817e17e"),
        "req_apdu": bytes.fromhex("c001cd000301001d0700ff0200"),
        "resp_apdu": bytes.fromhex("c401cd00060000b1e8"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=29, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 45544,
    },
    {
        "id": "get_apparent_power_l2",
        "category": "instantaneous",
        "description": "GET Apparent Power Phase L2 (0.01 VA) (Obis(a=1, b=0, c=49, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541fec24de6e600c001ce00030100310700ff020052d97e"),
        "resp_hdlc": bytes.fromhex("7ea0164102551e9113e6e700c401ce0006000055bc21d37e"),
        "req_apdu": bytes.fromhex("c001ce00030100310700ff0200"),
        "resp_apdu": bytes.fromhex("c401ce0006000055bc"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=49, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 21948,
    },
    {
        "id": "get_apparent_power_l3",
        "category": "instantaneous",
        "description": "GET Apparent Power Phase L3 (0.01 VA) (Obis(a=1, b=0, c=69, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554110b243e6e600c001cf00030100450700ff02006e597e"),
        "resp_hdlc": bytes.fromhex("7ea01641025530eddbe6e700c401cf000600002271d1ec7e"),
        "req_apdu": bytes.fromhex("c001cf00030100450700ff0200"),
        "resp_apdu": bytes.fromhex("c401cf000600002271"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=69, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 8817,
    },
    {
        "id": "get_apparent_power_total",
        "category": "instantaneous",
        "description": "GET Total Apparent Power (0.01 VA) (Obis(a=1, b=0, c=9, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554132a241e6e600c001c000030100090700ff020007767e"),
        "resp_hdlc": bytes.fromhex("7ea01641025552f99be6e700c401c0000600012f542e697e"),
        "req_apdu": bytes.fromhex("c001c000030100090700ff0200"),
        "resp_apdu": bytes.fromhex("c401c0000600012f54"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=9, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 77652,
    },
    {
        "id": "get_power_factor_total",
        "category": "instantaneous",
        "description": "GET Total Power Factor (0.001) (Obis(a=1, b=0, c=13, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541549247e6e600c001c1000301000d0700ff02003a337e"),
        "resp_hdlc": bytes.fromhex("7ea0144102557445c9e6e700c401c1001002d9477c7e"),
        "req_apdu": bytes.fromhex("c001c1000301000d0700ff0200"),
        "resp_apdu": bytes.fromhex("c401c1001002d9"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=13, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 729,
    },
    {
        "id": "get_power_factor_l1",
        "category": "instantaneous",
        "description": "GET Power Factor Phase L1 (0.001) (Obis(a=1, b=0, c=33, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541768245e6e600c001c200030100210700ff02001d797e"),
        "resp_hdlc": bytes.fromhex("7ea01441025596590de6e700c401c20010028ca3647e"),
        "req_apdu": bytes.fromhex("c001c200030100210700ff0200"),
        "resp_apdu": bytes.fromhex("c401c20010028c"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=33, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 652,
    },
    {
        "id": "get_power_factor_l2",
        "category": "instantaneous",
        "description": "GET Power Factor Phase L2 (0.001) (Obis(a=1, b=0, c=53, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554198f24be6e600c001c300030100350700ff0200907e7e"),
        "resp_hdlc": bytes.fromhex("7ea014410255b825c5e6e700c401c3001003405f7a7e"),
        "req_apdu": bytes.fromhex("c001c300030100350700ff0200"),
        "resp_apdu": bytes.fromhex("c401c300100340"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=53, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 832,
    },
    {
        "id": "get_power_factor_l3",
        "category": "instantaneous",
        "description": "GET Power Factor Phase L3 (0.001) (Obis(a=1, b=0, c=73, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541bae249e6e600c001c400030100490700ff0200832a7e"),
        "resp_hdlc": bytes.fromhex("7ea014410255da3185e6e700c401c400100354261c7e"),
        "req_apdu": bytes.fromhex("c001c400030100490700ff0200"),
        "resp_apdu": bytes.fromhex("c401c400100354"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=73, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 852,
    },
    {
        "id": "get_frequency",
        "category": "instantaneous",
        "description": "GET Grid Frequency (0.01 Hz) (Obis(a=1, b=0, c=14, d=7, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541dcd24fe6e600c001c5000301000e0700ff020012617e"),
        "resp_hdlc": bytes.fromhex("7ea014410255fc05c1e6e700c401c50012138b31197e"),
        "req_apdu": bytes.fromhex("c001c5000301000e0700ff0200"),
        "resp_apdu": bytes.fromhex("c401c50012138b"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=14, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 5003,
    },
    {
        "id": "get_voltage_l1_scaler_unit",
        "category": "scaler_unit",
        "description": "GET Voltage L1 Scaler and Unit (Obis(a=1, b=0, c=32, d=7, e=0, f=255), attr 3)",
        "req_hdlc": bytes.fromhex("7ea01a025541fec24de6e600c001c600030100200700ff0300bb3a7e"),
        "resp_hdlc": bytes.fromhex("7ea0174102551ed518e6e700c401c60002020ffe1623263e7e"),
        "req_apdu": bytes.fromhex("c001c600030100200700ff0300"),
        "resp_apdu": bytes.fromhex("c401c60002020ffe1623"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=32, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 3,
        },
        "decoded_value": [-2, 35],
    },
    {
        "id": "get_current_l1_scaler_unit",
        "category": "scaler_unit",
        "description": "GET Current L1 Scaler and Unit (Obis(a=1, b=0, c=31, d=7, e=0, f=255), attr 3)",
        "req_hdlc": bytes.fromhex("7ea01a02554110b243e6e600c001c7000301001f0700ff030073957e"),
        "resp_hdlc": bytes.fromhex("7ea01741025530a9d0e6e700c401c70002020ffd1621ef737e"),
        "req_apdu": bytes.fromhex("c001c7000301001f0700ff0300"),
        "resp_apdu": bytes.fromhex("c401c70002020ffd1621"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=31, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 3,
        },
        "decoded_value": [-3, 33],
    },
    {
        "id": "get_active_power_total_scaler_unit",
        "category": "scaler_unit",
        "description": "GET Active Power Scaler and Unit (Obis(a=1, b=0, c=1, d=7, e=0, f=255), attr 3)",
        "req_hdlc": bytes.fromhex("7ea01a02554132a241e6e600c001c800030100010700ff03002df27e"),
        "resp_hdlc": bytes.fromhex("7ea01741025552bd90e6e700c401c80002020ffe161be0b37e"),
        "req_apdu": bytes.fromhex("c001c800030100010700ff0300"),
        "resp_apdu": bytes.fromhex("c401c80002020ffe161b"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=1, d=7, e=0, f=255)",
            "obis_hex": "",
            "attribute": 3,
        },
        "decoded_value": [-2, 27],
    },
    {
        "id": "get_active_energy_total_scaler_unit",
        "category": "scaler_unit",
        "description": "GET Active Energy Scaler and Unit (Obis(a=1, b=0, c=1, d=8, e=0, f=255), attr 3)",
        "req_hdlc": bytes.fromhex("7ea01a025541549247e6e600c001c900030100010800ff030040cd7e"),
        "resp_hdlc": bytes.fromhex("7ea0174102557489d4e6e700c401c90002020f00161eddf97e"),
        "req_apdu": bytes.fromhex("c001c900030100010800ff0300"),
        "resp_apdu": bytes.fromhex("c401c90002020f00161e"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=1, d=8, e=0, f=255)",
            "obis_hex": "",
            "attribute": 3,
        },
        "decoded_value": [0, 30],
    },
    {
        "id": "get_active_energy_total",
        "category": "energy",
        "description": "GET Total Active Energy (Wh) (Obis(a=1, b=0, c=1, d=8, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541768245e6e600c001ca00030100010800ff02002b2a7e"),
        "resp_hdlc": bytes.fromhex("7ea01641025596d11be6e700c401ca0006022920de6cd47e"),
        "req_apdu": bytes.fromhex("c001ca00030100010800ff0200"),
        "resp_apdu": bytes.fromhex("c401ca0006022920de"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=1, d=8, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 36249822,
    },
    {
        "id": "get_active_energy_tariff1",
        "category": "energy",
        "description": "GET Active Energy Tariff 1 (Wh) (Obis(a=1, b=0, c=1, d=8, e=1, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554198f24be6e600c001cb00030100010801ff020001637e"),
        "resp_hdlc": bytes.fromhex("7ea016410255b8add3e6e700c401cb0006010128122d697e"),
        "req_apdu": bytes.fromhex("c001cb00030100010801ff0200"),
        "resp_apdu": bytes.fromhex("c401cb000601012812"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=1, d=8, e=1, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 16853010,
    },
    {
        "id": "get_active_energy_tariff2",
        "category": "energy",
        "description": "GET Active Energy Tariff 2 (Wh) (Obis(a=1, b=0, c=1, d=8, e=2, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541bae249e6e600c001cc00030100010802ff02002ae67e"),
        "resp_hdlc": bytes.fromhex("7ea016410255dab993e6e700c401cc00060127f8cc1f1b7e"),
        "req_apdu": bytes.fromhex("c001cc00030100010802ff0200"),
        "resp_apdu": bytes.fromhex("c401cc00060127f8cc"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=1, b=0, c=1, d=8, e=2, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 19396812,
    },
    {
        "id": "get_active_tariff",
        "category": "energy",
        "description": "GET Current Active Tariff (Obis(a=0, b=0, c=96, d=14, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541dcd24fe6e600c001cd00010000600e00ff02008a287e"),
        "resp_hdlc": bytes.fromhex("7ea013410255fcd9f1e6e700c401cd001101a6cb7e"),
        "req_apdu": bytes.fromhex("c001cd00010000600e00ff0200"),
        "resp_apdu": bytes.fromhex("c401cd001101"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=96, d=14, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 1,
    },
    {
        "id": "get_internal_temperature",
        "category": "diagnostic",
        "description": "GET Internal Meter Temperature (C) (Obis(a=0, b=0, c=96, d=9, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541fec24de6e600c001ce00030000600900ff02001f7d7e"),
        "resp_hdlc": bytes.fromhex("7ea0144102551e1905e6e700c401ce00100012d45d7e"),
        "req_apdu": bytes.fromhex("c001ce00030000600900ff0200"),
        "resp_apdu": bytes.fromhex("c401ce00100012"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=0, b=0, c=96, d=9, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 18,
    },
    {
        "id": "get_uptime",
        "category": "diagnostic",
        "description": "GET Meter Operating Time (seconds) (Obis(a=0, b=0, c=96, d=8, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554110b243e6e600c001cf00030000600800ff0200ca237e"),
        "resp_hdlc": bytes.fromhex("7ea01641025530eddbe6e700c401cf0006078c216b0c877e"),
        "req_apdu": bytes.fromhex("c001cf00030000600800ff0200"),
        "resp_apdu": bytes.fromhex("c401cf0006078c216b"),
        "cosem": {
            "interface_id": 3,
            "interface_name": "REGISTER",
            "obis": "Obis(a=0, b=0, c=96, d=8, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": 126624107,
    },
    {
        "id": "get_local_time",
        "category": "diagnostic",
        "description": "GET Meter Internal Clock (DLMS datetime) (Obis(a=0, b=0, c=1, d=0, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554132a241e6e600c001c000080000010000ff0200f14f7e"),
        "resp_hdlc": bytes.fromhex(
            "7ea01f410255529dcae6e700c401c000090c07ea0a0a061317230000b400e08d7e"
        ),
        "req_apdu": bytes.fromhex("c001c000080000010000ff0200"),
        "resp_apdu": bytes.fromhex("c401c000090c07ea0a0a061317230000b400"),
        "cosem": {
            "interface_id": 8,
            "interface_name": "CLOCK",
            "obis": "Obis(a=0, b=0, c=1, d=0, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": {
            "type": "bytes",
            "hex": "07ea0a0a061317230000b400",
            "str": "\x07�\n\n\x06\x13\x17#\x00\x00�\x00",
        },
    },
    {
        "id": "get_clock_synced",
        "category": "diagnostic",
        "description": "GET Last Clock Sync Timestamp (Obis(a=0, b=0, c=96, d=2, e=12, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541549247e6e600c001c10001000060020cff0200712a7e"),
        "resp_hdlc": bytes.fromhex(
            "7ea01f41025574a98ee6e700c401c100090c07ea0a060200310b0000b4008def7e"
        ),
        "req_apdu": bytes.fromhex("c001c10001000060020cff0200"),
        "resp_apdu": bytes.fromhex("c401c100090c07ea0a060200310b0000b400"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=96, d=2, e=12, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": {
            "type": "bytes",
            "hex": "07ea0a060200310b0000b400",
            "str": "\x07�\n\x06\x02\x001\x0b\x00\x00�\x00",
        },
    },
    {
        "id": "get_front_cover_opened",
        "category": "diagnostic",
        "description": "GET Last Front Cover Opened Timestamp (Obis(a=0, b=0, c=96, d=20, e=1, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541768245e6e600c001c200010000601401ff020095d07e"),
        "resp_hdlc": bytes.fromhex(
            "7ea01f41025596b54ae6e700c401c200090c07e40717040b31110000b40051e87e"
        ),
        "req_apdu": bytes.fromhex("c001c200010000601401ff0200"),
        "resp_apdu": bytes.fromhex("c401c200090c07e40717040b31110000b400"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=96, d=20, e=1, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": {
            "type": "bytes",
            "hex": "07e40717040b31110000b400",
            "str": "\x07�\x07\x17\x04\x0b1\x11\x00\x00�\x00",
        },
    },
    {
        "id": "get_terminals_cover_opened",
        "category": "diagnostic",
        "description": "GET Last Terminals Cover Opened Timestamp (Obis(a=0, b=0, c=96, d=20, e=6, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a02554198f24be6e600c001c300010000601406ff020025d27e"),
        "resp_hdlc": bytes.fromhex(
            "7ea01f410255b8c982e6e700c401c300090c07e60915030e172c0000b400f08e7e"
        ),
        "req_apdu": bytes.fromhex("c001c300010000601406ff0200"),
        "resp_apdu": bytes.fromhex("c401c300090c07e60915030e172c0000b400"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=96, d=20, e=6, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": {
            "type": "bytes",
            "hex": "07e60915030e172c0000b400",
            "str": "\x07�\t\x15\x03\x0e\x17,\x00\x00�\x00",
        },
    },
    {
        "id": "get_magnetic_field_detected",
        "category": "diagnostic",
        "description": "GET Last Magnetic Field Detection Timestamp (Obis(a=0, b=0, c=96, d=20, e=16, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541bae249e6e600c001c400010000601410ff0200f8fa7e"),
        "resp_hdlc": bytes.fromhex(
            "7ea01f410255daddc2e6e700c401c400090c07e40717040b310f0000b400fa017e"
        ),
        "req_apdu": bytes.fromhex("c001c400010000601410ff0200"),
        "resp_apdu": bytes.fromhex("c401c400090c07e40717040b310f0000b400"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=96, d=20, e=16, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": {
            "type": "bytes",
            "hex": "07e40717040b310f0000b400",
            "str": "\x07�\x07\x17\x04\x0b1\x0f\x00\x00�\x00",
        },
    },
    {
        "id": "get_self_test",
        "category": "diagnostic",
        "description": "GET Meter Self-Test Error Flags (Obis(a=0, b=0, c=97, d=97, e=0, f=255), attr 2)",
        "req_hdlc": bytes.fromhex("7ea01a025541dcd24fe6e600c001c500010000616100ff0200445b7e"),
        "resp_hdlc": bytes.fromhex("7ea019410255fc71bde6e700c401c5000906000000000000d9bb7e"),
        "req_apdu": bytes.fromhex("c001c500010000616100ff0200"),
        "resp_apdu": bytes.fromhex("c401c5000906000000000000"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=97, d=97, e=0, f=255)",
            "obis_hex": "",
            "attribute": 2,
        },
        "decoded_value": {
            "type": "bytes",
            "hex": "000000000000",
            "str": "\x00\x00\x00\x00\x00\x00",
        },
    },
    {
        "id": "get_error_nonexistent_obis",
        "category": "negative_test",
        "description": "GET request for non-existent OBIS (0.0.99.99.99.255) -> OBJECT_UNDEFINED",
        "req_hdlc": bytes.fromhex("7ea01a025541fec24de6e600c001c600010000636363ff020000077e"),
        "resp_hdlc": bytes.fromhex("7ea0124102551e813ee6e700c401c60104c97a7e"),
        "req_apdu": bytes.fromhex("c001c600010000636363ff0200"),
        "resp_apdu": bytes.fromhex("c401c60104"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "Obis(a=0, b=0, c=99, d=99, e=99, f=255)",
            "attribute": 2,
        },
        "decoded_value": "DataAccessResult.OBJECT_UNDEFINED (4)",
    },
    {
        "id": "get_error_nonexistent_attribute",
        "category": "negative_test",
        "description": "GET request for non-existent attribute (attr 99) -> OBJECT_UNDEFINED",
        "req_hdlc": bytes.fromhex("7ea01a02554110b243e6e600c001c7000100002a0000ff6300e8097e"),
        "resp_hdlc": bytes.fromhex("7ea01241025530fdf6e6e700c401c7010415207e"),
        "req_apdu": bytes.fromhex("c001c7000100002a0000ff6300"),
        "resp_apdu": bytes.fromhex("c401c70104"),
        "cosem": {
            "interface_id": 1,
            "interface_name": "DATA",
            "obis": "0.0.42.0.0.255",
            "attribute": 99,
        },
        "decoded_value": "DataAccessResult.OBJECT_UNDEFINED (4)",
    },
    {
        "id": "disc_disconnect",
        "category": "session_management",
        "description": "HDLC Disconnect (DISC -> UA)",
        "req_hdlc": bytes.fromhex("7ea00802554153e5917e"),
        "resp_hdlc": bytes.fromhex(
            "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
        ),
        "decoded_value": None,
    },
    {
        "id": "snrm_connect_auth_session",
        "category": "session_management",
        "description": "Establish HDLC connection for auth failure test (SNRM -> UA)",
        "req_hdlc": bytes.fromhex("7ea00802554193e9577e"),
        "resp_hdlc": bytes.fromhex(
            "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
        ),
        "decoded_value": None,
    },
    {
        "id": "aarq_associate_auth_failure",
        "category": "negative_test",
        "description": "AARQ with wrong secret -> AARE REJECTED_PERMANENT (AUTHENTICATION_FAILED 13)",
        "req_hdlc": bytes.fromhex(
            "7ea04f025541108410e6e6006040a109060760857405080101a60a0408757469b6a30b12588a0207808b0760857405080201ac08800677726f6e6721be10040e01000000065f1f040020525fffffcd7f7e"
        ),
        "resp_hdlc": bytes.fromhex(
            "7ea02e410255301c55e6e700611fa109060760857405080101a203020101a305a10302010dbe0604040e0106016c717e"
        ),
        "req_apdu": bytes.fromhex(
            "6040a109060760857405080101a60a0408757469b6a30b12588a0207808b0760857405080201ac08800677726f6e6721be10040e01000000065f1f040020525fffff"
        ),
        "resp_apdu": bytes.fromhex(
            "611fa109060760857405080101a203020101a305a10302010dbe0604040e010601"
        ),
        "decoded_value": "AssociationResult.REJECTED_PERMANENT (1) / AUTHENTICATION_FAILED (13)",
    },
    {
        "id": "disc_disconnect_auth_session",
        "category": "session_management",
        "description": "HDLC Disconnect after auth fail (DISC -> UA)",
        "req_hdlc": bytes.fromhex("7ea00802554153e5917e"),
        "resp_hdlc": bytes.fromhex(
            "7ea021410255737f4f8180140502008006020080070400000001080400000001ce6a7e"
        ),
        "decoded_value": None,
    },
]
