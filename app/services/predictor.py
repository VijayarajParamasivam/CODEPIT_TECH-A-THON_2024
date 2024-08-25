import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import numpy as np

def predict_stock_price(symbol: str, periods: int):
    stock = yf.Ticker(symbol)
    data = stock.history(period='1y')
    if data.empty:
        raise ValueError("No data available for prediction")

    # Prepare the data
    data = data['Close']
    model = ARIMA(data, order=(5, 1, 0))
    model_fit = model.fit()
    
    # Forecast
    forecast = model_fit.forecast(steps=periods)
    
    # Handle NaN values
    forecast = np.nan_to_num(forecast)  # Replace NaN with 0 or use another method to handle NaNs
    
    # Generate forecast dates
    last_date = data.index[-1]
    forecast_dates = pd.date_range(start=last_date, periods=periods + 1, freq='B')[1:]  # Skip the first date
    
    forecast_df = pd.DataFrame(forecast, index=forecast_dates, columns=['Forecast'])
    return forecast_df.to_dict()
