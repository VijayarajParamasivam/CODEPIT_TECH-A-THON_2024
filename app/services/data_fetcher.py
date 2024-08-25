import yfinance as yf
import pandas as pd
from typing import Optional

def fetch_stock_data(symbol: str, start_date: Optional[str], end_date: Optional[str], frequency: str) -> pd.DataFrame:
    stock = yf.Ticker(symbol)
    
    # Fetch full history if no start and end dates are provided
    if not start_date and not end_date:
        data = stock.history(period="max")
    else:
        data = stock.history(start=start_date, end=end_date)

    if data.empty:
        raise ValueError("No data available for the given symbol and date range.")
    
    # Resample data according to the frequency
    if frequency == 'daily':
        return data
    elif frequency == 'weekly':
        return data.resample('W').mean()
    elif frequency == 'monthly':
        return data.resample('M').mean()
    elif frequency == 'yearly':
        return data.resample('Y').mean()
    else:
        raise ValueError("Invalid frequency. Supported frequencies: daily, weekly, monthly, yearly.")

def fetch_current_stock_data(symbol: str) -> pd.Series:
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    
    if data.empty:
        raise ValueError("No current data available for the given symbol.")
    
    # Return the most recent row (current data)
    return data.iloc[-1]