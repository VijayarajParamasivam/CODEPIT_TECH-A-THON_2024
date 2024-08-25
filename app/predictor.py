import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from typing import Tuple, Optional

def fetch_and_prepare_data(symbol: str, period: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)
    
    if data.empty:
        raise ValueError("No data available for prediction")

    df = pd.DataFrame({
        'ds': data.index,
        'y': data['Close'],
        'open': data['Open'],
        'high': data['High'],
        'low': data['Low'],
        'volume': data['Volume']
    })

    df['ds'] = pd.to_datetime(df['ds'])
    df['day'] = df['ds'].dt.day
    df['month'] = df['ds'].dt.month
    df['year'] = df['ds'].dt.year
    df.drop('ds', axis=1, inplace=True)

    scaler = StandardScaler()
    df[['open', 'high', 'low', 'volume']] = scaler.fit_transform(df[['open', 'high', 'low', 'volume']])
    
    return df, data

def predict_stock_price_with_test_data(symbol: str, periods: int = 15) -> Optional[dict]:
    try:
        # Try with 2 years of data first
        df, data = fetch_and_prepare_data(symbol, '2y')
    except ValueError:
        return {"error": "Error fetching data for 2 years. Check the stock symbol or try again later."}

    # Get the most recent stock price
    #latest_date = data.index[-1]
    #if latest_date.date() != pd.Timestamp.today().normalize().date():
       # return {"error": "No stock market today"}

    # Split data into training and testing sets
    X = df.drop('y', axis=1)
    y = df['y']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Define and fit the model
    model = RandomForestRegressor(random_state=42)
    model.fit(X_train, y_train)

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Calculate performance metrics
    mse = mean_squared_error(y_test, y_pred)
    accuracy_percentage = 100 * (1 - mse / np.var(y_test))

    # If accuracy is negative, fetch more data (5 years) and retry
    if accuracy_percentage < 0:
        try:
            df, data = fetch_and_prepare_data(symbol, '5y')
        except ValueError:
            return {"error": "Error fetching data for 5 years. Check the stock symbol or try again later."}

        # Re-split data into training and testing sets
        X = df.drop('y', axis=1)
        y = df['y']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        # Re-define and fit the model
        model = RandomForestRegressor(random_state=42)
        model.fit(X_train, y_train)

        # Re-make predictions on the test set
        y_pred = model.predict(X_test)

        # Re-calculate performance metrics
        mse = mean_squared_error(y_test, y_pred)
        accuracy_percentage = 100 * (1 - mse / np.var(y_test))

    # Generate future dates
    last_date = df.index[-1]
    future_dates = [last_date + pd.DateOffset(days=i) for i in range(1, periods + 1)]

    # Prepare data for future predictions
    future_df = pd.DataFrame({
        'day': [d.day for d in future_dates],
        'month': [d.month for d in future_dates],
        'year': [d.year for d in future_dates],
        'open': [X.iloc[-1]['open']] * periods,
        'high': [X.iloc[-1]['high']] * periods,
        'low': [X.iloc[-1]['low']] * periods,
        'volume': [X.iloc[-1]['volume']] * periods
    })

    future_df = future_df[X.columns]

    # Predict future stock prices
    future_predictions = model.predict(future_df)

    # Create a DataFrame for future predictions
    future_df['Date'] = future_dates
    future_df['Predicted'] = future_predictions

    # Return predictions and metrics
    return {
        "predictions": future_df[['Date', 'Predicted']].to_dict(orient="records"),
        "mean_squared_error": mse,
        "accuracy_percentage": accuracy_percentage
    }
