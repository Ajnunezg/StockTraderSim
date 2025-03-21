import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from polygon.rest import RESTClient
import time

def validate_inputs(ticker, date, investment_amount, api_key):
    """
    Validate user inputs.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    date : datetime.date
        Selected date for analysis
    investment_amount : float
        Initial investment amount
    api_key : str
        Polygon.io API key
    
    Returns:
    --------
    dict
        Validation result with success flag and message
    """
    # Check if API key is provided
    if not api_key:
        return {"success": False, "message": "Please provide your Polygon.io API key."}
    
    # Check if ticker is valid
    if not ticker or not ticker.strip():
        return {"success": False, "message": "Please provide a valid stock ticker symbol."}
    
    # Check if investment amount is valid
    if investment_amount <= 0:
        return {"success": False, "message": "Initial investment amount must be greater than zero."}
    
    # Check if date is valid (not a future date or weekend)
    if date > datetime.now().date():
        return {"success": False, "message": "Selected date cannot be in the future."}
    
    # Check if date is a weekend
    if date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return {"success": False, "message": "Selected date is a weekend. Stock markets are closed on weekends."}
    
    return {"success": True, "message": "Inputs validated successfully."}

def get_intraday_data(ticker, date, api_key):
    """
    Retrieve intraday stock data from Polygon.io API.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    date : datetime.date
        Date for which to retrieve data
    api_key : str
        Polygon.io API key
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing intraday stock data
    """
    # Initialize REST client
    client = RESTClient(api_key)
    
    # Format date string
    date_str = date.strftime('%Y-%m-%d')
    
    # Define time range for the day
    start_timestamp = pd.Timestamp(f"{date_str} 09:30:00", tz='America/New_York')
    end_timestamp = pd.Timestamp(f"{date_str} 16:00:00", tz='America/New_York')
    
    # Convert to milliseconds timestamp
    start_ms = int(start_timestamp.timestamp() * 1000)
    end_ms = int(end_timestamp.timestamp() * 1000)
    
    try:
        # Get aggregated bars for intraday data (1-minute intervals)
        aggs = []
        for a in client.list_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="minute",
            from_=start_ms,
            to=end_ms,
            limit=50000
        ):
            aggs.append({
                'timestamp': pd.to_datetime(a.timestamp, unit='ms', utc=True).tz_convert('America/New_York'),
                'open': a.open,
                'high': a.high,
                'low': a.low,
                'close': a.close,
                'volume': a.volume,
                'transactions': getattr(a, 'transactions', None),
            })
        
        # Create DataFrame
        df = pd.DataFrame(aggs)
        
        # Handle empty data
        if df.empty:
            return pd.DataFrame()
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Handle missing data using forward fill
        df = df.set_index('timestamp').resample('1min').ffill().reset_index()
        
        return df
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error retrieving data from Polygon.io: {str(e)}")
        
        # Return empty DataFrame on error
        return pd.DataFrame()

def format_trade_log(trades):
    """
    Format the trade log for display.
    
    Parameters:
    -----------
    trades : pandas.DataFrame
        DataFrame containing trade information
    
    Returns:
    --------
    pandas.DataFrame
        Formatted trade log
    """
    if trades.empty:
        return pd.DataFrame()
    
    # Format timestamps and trade details
    formatted_trades = trades.copy()
    formatted_trades['timestamp'] = formatted_trades['timestamp'].dt.strftime('%H:%M:%S')
    
    # Add formatted columns
    formatted_trades['price_fmt'] = formatted_trades['price'].map('${:.2f}'.format)
    formatted_trades['shares_fmt'] = formatted_trades['shares'].map('{:.4f}'.format)
    
    # Format gain/loss
    formatted_trades['gain_loss_fmt'] = formatted_trades['gain_loss'].map('${:.2f}'.format)
    formatted_trades.loc[formatted_trades['action'] == 'BUY', 'gain_loss_fmt'] = 'N/A'
    
    return formatted_trades[['timestamp', 'action', 'price_fmt', 'shares_fmt', 'gain_loss_fmt']]
