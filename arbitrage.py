import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def simulate_trades(intraday_data, initial_investment):
    """
    Simulate intraday arbitrage trades to maximize profit.
    
    Parameters:
    -----------
    intraday_data : pandas.DataFrame
        DataFrame containing intraday stock data
    initial_investment : float
        Initial investment amount
    
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
    
    # Split trading day into hourly segments
    trading_hours = [9, 10, 11, 12, 13, 14, 15]
    
    for hour in trading_hours:
        # Filter data for the current hour
        hour_data = df[df['timestamp'].dt.hour == hour]
        
        if hour_data.empty:
            continue
        
        # Find the lowest and highest prices within this hour
        lowest_idx = hour_data['low'].idxmin()
        highest_idx = hour_data['high'].idxmax()
        
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
