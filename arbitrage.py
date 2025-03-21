import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def simulate_trades(intraday_data, initial_investment, trading_frequency='10min'):
    """
    Simulate intraday arbitrage trades to maximize profit.

    Parameters:
    -----------
    intraday_data : pandas.DataFrame
        DataFrame containing intraday stock data
    initial_investment : float
        Initial investment amount
    trading_frequency : str
        Frequency of trading ('hourly', '30min', '15min', '10min', '5min', '1min')

    Returns:
    --------
    tuple
        (trades DataFrame, ending_value, remaining_shares)
    """
    # Initialize variables
    cash = initial_investment
    shares = 0.0
    trades = []

    # Make a copy of the DataFrame to avoid modifying the original
    df = intraday_data.copy()

    # Create intervals throughout the trading day based on trading frequency
    trading_intervals = []
    
    if trading_frequency == 'hourly':
        for hour in range(9, 16):  # 9 AM to 3 PM
            trading_intervals.append((hour, 0))
    elif trading_frequency == '30min':
        for hour in range(9, 16):  # 9 AM to 3 PM
            for minute in range(0, 60, 30):
                trading_intervals.append((hour, minute))
    elif trading_frequency == '15min':
        for hour in range(9, 16):  # 9 AM to 3 PM
            for minute in range(0, 60, 15):
                trading_intervals.append((hour, minute))
    elif trading_frequency == '10min':
        for hour in range(9, 16):  # 9 AM to 3 PM
            for minute in range(0, 60, 10):
                trading_intervals.append((hour, minute))
    elif trading_frequency == '5min':
        for hour in range(9, 16):  # 9 AM to 3 PM
            for minute in range(0, 60, 5):
                trading_intervals.append((hour, minute))
    elif trading_frequency == '1min':
        for hour in range(9, 16):  # 9 AM to 3 PM
            for minute in range(0, 60):
                trading_intervals.append((hour, minute))
    else:
        # Default to 10min if invalid frequency
        for hour in range(9, 16):  # 9 AM to 3 PM
            for minute in range(0, 60, 10):
                trading_intervals.append((hour, minute))

    for interval in trading_intervals:
        hour, minute = interval
        
        # Calculate interval duration in minutes
        if trading_frequency == 'hourly':
            interval_duration = 60
        elif trading_frequency == '30min':
            interval_duration = 30
        elif trading_frequency == '15min':
            interval_duration = 15
        elif trading_frequency == '10min':
            interval_duration = 10
        elif trading_frequency == '5min':
            interval_duration = 5
        elif trading_frequency == '1min':
            interval_duration = 1
        else:
            interval_duration = 10
        
        # Filter data for the current interval
        interval_data = df[
            (df['timestamp'].dt.hour == hour) & 
            (df['timestamp'].dt.minute >= minute) & 
            (df['timestamp'].dt.minute < minute + interval_duration)
        ]

        if interval_data.empty:
            continue

        # Find the lowest and highest prices within this interval
        lowest_idx = interval_data['low'].idxmin()
        highest_idx = interval_data['high'].idxmax()

        # Check if the lowest price comes before the highest (opportunity for profit)
        if lowest_idx < highest_idx:
            buy_data = df.loc[lowest_idx]
            sell_data = df.loc[highest_idx]

            # Calculate the number of shares to buy (all available cash)
            buy_price = buy_data['low']
            shares_to_buy = cash / buy_price

            # Record the buy trade
            trades.append({
                'timestamp': buy_data['timestamp'],
                'action': 'BUY',
                'price': buy_price,
                'shares': shares_to_buy,
                'gain_loss': 0  # No gain/loss on buy
            })

            # Update portfolio
            cash = 0
            shares += shares_to_buy

            # Calculate the selling proceeds
            sell_price = sell_data['high']
            sell_value = shares * sell_price
            gain_loss = sell_value - (buy_price * shares_to_buy)

            # Record the sell trade
            trades.append({
                'timestamp': sell_data['timestamp'],
                'action': 'SELL',
                'price': sell_price,
                'shares': shares,
                'gain_loss': gain_loss
            })

            # Update portfolio
            cash = sell_value
            shares = 0

    # Convert trades to DataFrame
    trades_df = pd.DataFrame(trades)

    # Calculate ending value (cash + value of remaining shares)
    if shares > 0:
        last_price = df.iloc[-1]['close']
        remaining_value = shares * last_price
    else:
        remaining_value = 0

    ending_value = cash + remaining_value

    # Return trades, ending value, and remaining shares
    return trades_df, ending_value, shares

def calculate_buy_hold_return(intraday_data, initial_investment):
    """
    Calculate return for a simple buy and hold strategy.

    Parameters:
    -----------
    intraday_data : pandas.DataFrame
        DataFrame containing intraday stock data
    initial_investment : float
        Initial investment amount

    Returns:
    --------
    float
        Final value of the investment using buy and hold strategy
    """
    # Get the first and last prices of the day
    first_price = intraday_data.iloc[0]['open']
    last_price = intraday_data.iloc[-1]['close']

    # Calculate the number of shares that could be purchased at the beginning of the day
    shares = initial_investment / first_price

    # Calculate the ending value
    ending_value = shares * last_price

    return ending_value

def identify_hourly_opportunities(intraday_data):
    """
    Identify the best trading opportunity for each hour of the trading day.

    Parameters:
    -----------
    intraday_data : pandas.DataFrame
        DataFrame containing intraday stock data

    Returns:
    --------
    pandas.DataFrame
        DataFrame containing hourly opportunities
    """
    # Make a copy of the DataFrame
    df = intraday_data.copy()

    # Initialize list to store opportunities
    opportunities = []

    # Split trading day into hourly segments
    trading_hours = [9, 10, 11, 12, 13, 14, 15]

    for hour in trading_hours:
        # Filter data for the current hour
        hour_data = df[df['timestamp'].dt.hour == hour]

        if hour_data.empty:
            continue

        # Find the lowest and highest prices within this hour
        min_price = hour_data['low'].min()
        max_price = hour_data['high'].max()

        # Calculate potential profit percentage
        profit_pct = ((max_price - min_price) / min_price) * 100

        # Record the opportunity
        opportunities.append({
            'hour': hour,
            'min_price': min_price,
            'max_price': max_price,
            'profit_potential_pct': profit_pct
        })

    # Convert to DataFrame
    return pd.DataFrame(opportunities)


def compare_frequencies(intraday_data, initial_investment):
    """
    Compare arbitrage strategy performance across different trading frequencies.
    
    Parameters:
    -----------
    intraday_data : pandas.DataFrame
        DataFrame containing intraday stock data
    initial_investment : float
        Initial investment amount
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame comparing performance across frequencies
    """
    # List of frequencies to compare
    frequencies = ['hourly', '30min', '15min', '10min', '5min', '1min']
    
    # Dictionary to store results
    results = []
    
    for freq in frequencies:
        # Run simulation for this frequency
        trades, ending_value, remaining_shares = simulate_trades(
            intraday_data, 
            initial_investment, 
            trading_frequency=freq
        )
        
        # Calculate number of trades
        num_trades = len(trades)
        
        # Calculate return percentage
        return_pct = ((ending_value - initial_investment) / initial_investment) * 100
        
        # Add to results
        results.append({
            'Trading Frequency': freq,
            'Final Value': ending_value,
            'Return (%)': return_pct,
            'Number of Trades': num_trades
        })
    
    # Convert to DataFrame
    return pd.DataFrame(results)