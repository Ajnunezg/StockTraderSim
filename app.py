import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from utils import get_intraday_data, validate_inputs
from arbitrage import simulate_trades, calculate_buy_hold_return

# Set page title and layout
st.set_page_config(
    page_title="Stock Market Arbitrage Simulator",
    layout="wide"
)

# Main title
st.title("Intraday Stock Market Arbitrage Simulator")
st.markdown("""
This application simulates intraday arbitrage trading strategies. It identifies optimal buying and selling
opportunities throughout a trading day to maximize returns on your investment.
""")

# Sidebar for inputs
st.sidebar.header("Input Parameters")

# Input fields
with st.sidebar.form("input_form"):
    ticker = st.text_input("Stock Ticker Symbol (e.g., AAPL)", value="AAPL")
    date = st.date_input("Select Date", value=datetime.now() - timedelta(days=7))
    investment_amount = st.number_input("Initial Investment Amount ($)", value=10000.0, min_value=100.0)
    api_key = st.text_input("Polygon.io API Key", type="password")
    
    submit_button = st.form_submit_button("Analyze Stock")

# Main content area
if submit_button:
    # Validate inputs
    validation_result = validate_inputs(ticker, date, investment_amount, api_key)
    
    if validation_result["success"]:
        try:
            with st.spinner('Retrieving intraday data from Polygon.io...'):
                # Get intraday data
                intraday_data = get_intraday_data(ticker, date, api_key)
                
                if intraday_data.empty:
                    st.error(f"No intraday data available for {ticker} on {date}. Please try another date or stock.")
                else:
                    # Display success message
                    st.success(f"Successfully retrieved {len(intraday_data)} data points for {ticker} on {date.strftime('%Y-%m-%d')}")
                    
                    # Display tabs for different sections
                    tab1, tab2, tab3 = st.tabs(["Data & Chart", "Trade Simulation", "Performance"])
                    
                    with tab1:
                        col1, col2 = st.columns([2, 3])
                        
                        with col1:
                            st.subheader("Raw Intraday Data")
                            st.dataframe(intraday_data[["timestamp", "open", "high", "low", "close", "volume"]], 
                                        height=400)
                        
                        with col2:
                            st.subheader("Intraday Price Chart")
                            # Create candlestick chart
                            fig = go.Figure(data=[go.Candlestick(
                                x=intraday_data['timestamp'],
                                open=intraday_data['open'],
                                high=intraday_data['high'],
                                low=intraday_data['low'],
                                close=intraday_data['close'],
                                name="Price"
                            )])
                            
                            fig.update_layout(
                                title=f"{ticker} Intraday Price on {date.strftime('%Y-%m-%d')}",
                                xaxis_title="Time",
                                yaxis_title="Price ($)",
                                xaxis_rangeslider_visible=False,
                                height=450
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        st.subheader("Arbitrage Trading Simulation")
                        
                        # Simulate trades
                        with st.spinner('Simulating arbitrage trading strategy...'):
                            trades, ending_value, remaining_shares = simulate_trades(
                                intraday_data, 
                                initial_investment=investment_amount
                            )
                        
                        if not trades.empty:
                            # Display trades
                            st.write(f"**Trading Activity**: Executed {len(trades)} trades")
                            st.dataframe(trades, height=300)
                            
                            # Create trade visualization
                            fig = go.Figure()
                            
                            # Add candlestick for price data
                            fig.add_trace(go.Candlestick(
                                x=intraday_data['timestamp'],
                                open=intraday_data['open'],
                                high=intraday_data['high'],
                                low=intraday_data['low'],
                                close=intraday_data['close'],
                                name="Price"
                            ))
                            
                            # Add buy points
                            buy_trades = trades[trades['action'] == 'BUY']
                            if not buy_trades.empty:
                                fig.add_trace(go.Scatter(
                                    x=buy_trades['timestamp'],
                                    y=buy_trades['price'],
                                    mode='markers',
                                    marker=dict(color='green', size=10, symbol='triangle-up'),
                                    name='Buy'
                                ))
                            
                            # Add sell points
                            sell_trades = trades[trades['action'] == 'SELL']
                            if not sell_trades.empty:
                                fig.add_trace(go.Scatter(
                                    x=sell_trades['timestamp'],
                                    y=sell_trades['price'],
                                    mode='markers',
                                    marker=dict(color='red', size=10, symbol='triangle-down'),
                                    name='Sell'
                                ))
                            
                            fig.update_layout(
                                title=f"{ticker} Trading Activity on {date.strftime('%Y-%m-%d')}",
                                xaxis_title="Time",
                                yaxis_title="Price ($)",
                                xaxis_rangeslider_visible=False,
                                height=450
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No profitable trades were identified for this stock on the selected date.")
                    
                    with tab3:
                        st.subheader("Performance Metrics")
                        
                        # Calculate buy and hold return
                        buy_hold_value = calculate_buy_hold_return(intraday_data, investment_amount)
                        
                        # Calculate returns
                        arbitrage_return_pct = ((ending_value - investment_amount) / investment_amount) * 100
                        buy_hold_return_pct = ((buy_hold_value - investment_amount) / investment_amount) * 100
                        
                        # Create metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                label="Initial Investment",
                                value=f"${investment_amount:,.2f}"
                            )
                        
                        with col2:
                            st.metric(
                                label="Final Portfolio Value",
                                value=f"${ending_value:,.2f}",
                                delta=f"{arbitrage_return_pct:.2f}%"
                            )
                        
                        with col3:
                            st.metric(
                                label="Buy & Hold Value",
                                value=f"${buy_hold_value:,.2f}",
                                delta=f"{buy_hold_return_pct:.2f}%"
                            )
                        
                        # Display portfolio composition
                        st.subheader("Final Portfolio Composition")
                        
                        last_price = intraday_data.iloc[-1]['close']
                        shares_value = remaining_shares * last_price
                        cash_value = ending_value - shares_value
                        
                        # Create pie chart for portfolio composition
                        labels = ['Cash', f'{ticker} Shares']
                        values = [cash_value, shares_value]
                        
                        fig = go.Figure(data=[go.Pie(
                            labels=labels,
                            values=values,
                            hole=.4,
                            marker_colors=['#636EFA', '#EF553B']
                        )])
                        
                        fig.update_layout(
                            title="Final Portfolio Breakdown",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show detailed breakdown
                        st.write(f"**Cash**: ${cash_value:,.2f}")
                        st.write(f"**Shares**: {remaining_shares:.4f} shares of {ticker} (${shares_value:,.2f})")
                        
                        # Show strategy comparison
                        st.subheader("Strategy Comparison")
                        
                        comparison_df = pd.DataFrame({
                            'Strategy': ['Arbitrage Trading', 'Buy & Hold'],
                            'Final Value': [ending_value, buy_hold_value],
                            'Return (%)': [arbitrage_return_pct, buy_hold_return_pct],
                            'Difference from Buy & Hold': [ending_value - buy_hold_value, 0],
                        })
                        
                        st.dataframe(comparison_df.style.format({
                            'Final Value': '${:,.2f}',
                            'Return (%)': '{:.2f}%',
                            'Difference from Buy & Hold': '${:,.2f}'
                        }))
                        
                        # Performance conclusion
                        if ending_value > buy_hold_value:
                            st.success(f"The arbitrage strategy outperformed buy & hold by ${ending_value - buy_hold_value:,.2f} ({arbitrage_return_pct - buy_hold_return_pct:.2f}%).")
                        elif ending_value < buy_hold_value:
                            st.error(f"The arbitrage strategy underperformed buy & hold by ${buy_hold_value - ending_value:,.2f} ({buy_hold_return_pct - arbitrage_return_pct:.2f}%).")
                        else:
                            st.info("The arbitrage strategy performed exactly the same as buy & hold.")
                        
        except Exception as e:
            st.error(f"An error occurred during data processing: {str(e)}")
    else:
        st.error(validation_result["message"])

# App footer information
st.sidebar.markdown("---")
st.sidebar.info("""
### About This App
This application simulates an intraday arbitrage trading strategy using historical stock data from Polygon.io.

**Features:**
- Retrieve intraday stock data for any ticker
- Identify profitable arbitrage opportunities
- Simulate trading with perfect execution
- Compare performance against buy & hold
""")
