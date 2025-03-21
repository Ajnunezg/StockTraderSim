import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from utils import get_intraday_data, validate_inputs
from arbitrage import simulate_trades, calculate_buy_hold_return, compare_frequencies

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
    trading_frequency = st.selectbox(
        "Trading Frequency", 
        options=["hourly", "30min", "15min", "10min", "5min", "1min"],
        index=3,  # Default to 10min
        help="How often to check for trading opportunities"
    )
    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 300px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -150px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    <div>Polygon.io API Key <span class="tooltip">*<span class="tooltiptext">You need a Polygon.io API key to fetch stock data. Visit <a href="https://polygon.io/" target="_blank" style="color: #00BFFF;">polygon.io</a> to create a free account and get your API key.</span></span></div>
    """, unsafe_allow_html=True)
    api_key = st.text_input("", type="password", label_visibility="collapsed")
    
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
                        with st.spinner(f'Simulating arbitrage trading strategy with {trading_frequency} frequency...'):
                            trades, ending_value, remaining_shares = simulate_trades(
                                intraday_data, 
                                initial_investment=investment_amount,
                                trading_frequency=trading_frequency
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
                        
                        # Create a strategy comparison chart
                        st.subheader("Strategy Performance Throughout the Day")
                        
                        # Calculate values over time for both strategies
                        # First, create a dataframe with timestamps
                        performance_df = pd.DataFrame(index=intraday_data['timestamp'])
                        
                        # Calculate buy and hold value over time
                        first_price = intraday_data.iloc[0]['open']
                        buy_hold_shares = investment_amount / first_price
                        performance_df['buy_hold_value'] = intraday_data['close'] * buy_hold_shares
                        
                        # Calculate arbitrage strategy value over time
                        # Start with initial investment
                        performance_df['arbitrage_value'] = investment_amount
                        
                        # Update value based on trades
                        if not trades.empty:
                            for idx, trade in trades.iterrows():
                                # Find all timestamps after this trade
                                mask = performance_df.index >= trade['timestamp']
                                
                                if trade['action'] == 'BUY':
                                    # When buying, cash decreases but share value increases
                                    performance_df.loc[mask, 'arbitrage_value'] = trade['shares'] * intraday_data.loc[intraday_data['timestamp'] >= trade['timestamp'], 'close'].values
                                elif trade['action'] == 'SELL':
                                    # When selling, we convert to cash
                                    performance_df.loc[mask, 'arbitrage_value'] = trade['shares'] * trade['price']
                        
                        # Create the comparison chart
                        fig = go.Figure()
                        
                        # Add lines for each strategy
                        fig.add_trace(go.Scatter(
                            x=performance_df.index,
                            y=performance_df['arbitrage_value'],
                            mode='lines',
                            name='Arbitrage Strategy',
                            line=dict(color='green', width=2)
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=performance_df.index,
                            y=performance_df['buy_hold_value'],
                            mode='lines',
                            name='Buy & Hold Strategy',
                            line=dict(color='blue', width=2)
                        ))
                        
                        # Add initial investment reference line
                        fig.add_trace(go.Scatter(
                            x=[performance_df.index.min(), performance_df.index.max()],
                            y=[investment_amount, investment_amount],
                            mode='lines',
                            name='Initial Investment',
                            line=dict(color='gray', width=1, dash='dash')
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f"Strategy Value Comparison Over Time",
                            xaxis_title="Time",
                            yaxis_title="Portfolio Value ($)",
                            height=400,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Performance conclusion
                        if ending_value > buy_hold_value:
                            st.success(f"The arbitrage strategy outperformed buy & hold by ${ending_value - buy_hold_value:,.2f} ({arbitrage_return_pct - buy_hold_return_pct:.2f}%).")
                        elif ending_value < buy_hold_value:
                            st.error(f"The arbitrage strategy underperformed buy & hold by ${buy_hold_value - ending_value:,.2f} ({buy_hold_return_pct - arbitrage_return_pct:.2f}%).")
                        else:
                            st.info("The arbitrage strategy performed exactly the same as buy & hold.")
                            
                        # Trading frequency comparison
                        st.subheader("Trading Frequency Comparison")
                        st.write("Compare how different trading frequencies affect performance:")
                        
                        # Run comparison across different frequencies
                        with st.spinner("Comparing performance across different trading frequencies..."):
                            frequency_comparison = compare_frequencies(intraday_data, investment_amount)
                        
                        # Format the DataFrame for display
                        formatted_comparison = frequency_comparison.style.format({
                            'Final Value': '${:,.2f}',
                            'Return (%)': '{:.2f}%'
                        })
                        
                        # Display the comparison table
                        st.dataframe(formatted_comparison, height=300)
                        
                        # Create a bar chart for visual comparison
                        fig = go.Figure()
                        
                        # Add bars for final values
                        fig.add_trace(go.Bar(
                            x=frequency_comparison['Trading Frequency'],
                            y=frequency_comparison['Final Value'],
                            name='Final Value',
                            marker_color='blue'
                        ))
                        
                        # Add reference line for initial investment
                        fig.add_trace(go.Scatter(
                            x=frequency_comparison['Trading Frequency'],
                            y=[investment_amount] * len(frequency_comparison),
                            mode='lines',
                            name='Initial Investment',
                            line=dict(color='red', width=2, dash='dash')
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title="Performance Comparison Across Trading Frequencies",
                            xaxis_title="Trading Frequency",
                            yaxis_title="Final Portfolio Value ($)",
                            height=400,
                            yaxis=dict(tickprefix="$")
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Find the best frequency
                        best_freq_idx = frequency_comparison['Final Value'].idxmax()
                        best_freq = frequency_comparison.iloc[best_freq_idx]
                        
                        st.write(f"**Best Trading Frequency:** {best_freq['Trading Frequency']} with a final value of ${best_freq['Final Value']:,.2f} ({best_freq['Return (%)']:.2f}%)")
                        
                        # Add a chart for number of trades by frequency
                        fig = go.Figure()
                        
                        # Add bars for number of trades
                        fig.add_trace(go.Bar(
                            x=frequency_comparison['Trading Frequency'],
                            y=frequency_comparison['Number of Trades'],
                            name='Number of Trades',
                            marker_color='green'
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title="Number of Trades by Frequency",
                            xaxis_title="Trading Frequency",
                            yaxis_title="Number of Trades",
                            height=350
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
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
- Analyze impact of different trading frequencies
""")
