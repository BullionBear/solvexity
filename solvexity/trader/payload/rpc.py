from solvexity.connector.types import Trade, Symbol, InstrumentType, OrderSide, Exchange
from pydantic import BaseModel, Field
from decimal import Decimal, ROUND_HALF_UP
from influxdb_client import Point, WritePrecision
from influxdb_client.client.flux_table import FluxRecord
from typing import Union


class InfluxTradeQuery(BaseModel):
    exchange: str
    symbol: str
    duration: str



