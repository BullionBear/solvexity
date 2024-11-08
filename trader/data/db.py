from sqlalchemy import create_engine
import pandas as pd


def get_engine(url: str):
    return create_engine(url)

def get_klines(engine, symbol: str, granular: str, start: int, end: int):
    query = f"SELECT * FROM kline WHERE symbol = '{symbol}' AND open_time >= {start} AND open_time < {end}"
    return pd.read_sql(query, engine)


