from flask import Flask, render_template, send_file, abort, redirect, url_for, request
import pandas as pd
import matplotlib.pyplot as plt
import io

# Initialize the Flask web application
app = Flask(__name__)

# Load the CSV file containing stock index data into a DataFrame
data = pd.read_csv("dump.csv")
# Clean column names by stripping any extra spaces
data.columns = data.columns.str.strip()
# Strip whitespace and convert 'index_name' to string for easier matching
data['index_name'] = data['index_name'].astype(str).str.strip()
# Create a lowercased version of 'index_name' for case-insensitive searches
data['index_name_lower'] = data['index_name'].str.lower()
# Convert 'index_date' to datetime format, assuming mixed date formats and day-first format
data['index_date'] = pd.to_datetime(data['index_date'], format='mixed', dayfirst=True)

# ----- Functions for Indicator Calculations -----

# Function to compute the Relative Strength Index (RSI)
def compute_rsi(series, period=14):
    delta = series.diff()  # Compute the difference between consecutive values
    gain = delta.where(delta > 0, 0).rolling(period).mean()  # Positive changes
    loss = -delta.where(delta < 0, 0).rolling(period).mean()  # Negative changes
    rs = gain / loss  # Relative strength
    return 100 - (100 / (1 + rs))  # RSI formula

# Function to compute the Smoothed Momentum Index (SMI)
def compute_smi(df, period=14, smooth=3):
    high = df['open_index_value'].rolling(period).max()  # Highest value in the period
    low = df['open_index_value'].rolling(period).min()  # Lowest value in the period
    median = (high + low) / 2  # Median value
    diff = df['open_index_value'] - median  # Difference from the median
    smi = diff.rolling(smooth).mean() / ((high - low).rolling(smooth).mean() / 2)  # SMI calculation
    return smi * 100  # Scale the result to be between -100 and 100

# Function to detect the trend based on recent price change
def detect_trend(df, window=30):
    recent = df.tail(window)  # Look at the most recent 'window' days of data
    if len(recent) < 2:  # If there's not enough data, return a default message
        return "Not enough data", 0.0
    start = recent['open_index_value'].iloc[0]  # Starting price
    end = recent['open_index_value'].iloc[-1]  # Ending price
    pct_change = ((end - start) / start) * 100  # Percentage change over the window
    if pct_change > 5:  # If price increased by more than 5%, consider it an upward trend
        return "Upwards trend", pct_change
    elif pct_change < -5:  # If price decreased by more than 5%, consider it a downward trend
        return "Downwards trend", pct_change
    return "Sideways trend", pct_change  # If price didn't change significantly, it's a sideways trend

# ----- Routes -----

# Route to the main page (index) showing a list of available companies (indices)
@app.route('/')
def index():
    index_names = data['index_name'].unique()  # Get unique index names
    return render_template('index.html', companies=index_names)  # Render the HTML template with index names

# Route to generate and display a plot for a specific index
@app.route('/plot/<name>')
def plot_index(name):
    # Convert the index name to lowercase for case-insensitive matching
    name_lower = name.strip().lower()
    # Filter the data for the selected index and sort by date
    df_plot = data[data['index_name_lower'] == name_lower].sort_values('index_date').copy()

    # If no data is found for the selected index, return a 404 error
    if df_plot.empty:
        abort(404, "Index not found")

    # Detect the trend and percentage change for the selected index
    trend, pct_change = detect_trend(df_plot)
    # Calculate the 14-day simple moving average (SMA) for the index
    df_plot['sma_14'] = df_plot['open_index_value'].rolling(14).mean()
    # Calculate the RSI for the index
    df_plot['rsi'] = compute_rsi(df_plot['open_index_value'])
    # Calculate the SMI for the index
    df_plot['smi'] = compute_smi(df_plot)

    # Check if the user wants to display RSI and/or SMI on the plot (via query parameters)
    show_rsi = request.args.get('rsi', '1') == '1'
    show_smi = request.args.get('smi', '1') == '1'

    # Determine the number of rows in the plot based on whether RSI and/or SMI will be shown
    num_rows = 1 + show_rsi + show_smi
    # Create a figure with multiple subplots (one for the main price chart and additional ones for RSI/SMI)
    fig, axes = plt.subplots(num_rows, 1, figsize=(12, 4 * num_rows), sharex=True)
    axes = [axes] if num_rows == 1 else axes  # Ensure axes is always iterable
    fig.patch.set_facecolor('#1e1e1e')  # Set dark background for the plot
    for ax in axes:
        ax.set_facecolor('#0e1a2f')  # Set dark background for each subplot

    # Main price chart: plot the open index value and the SMA
    axes[0].plot(df_plot['index_date'], df_plot['open_index_value'], label='Open', color='#00bff1')
    axes[0].plot(df_plot['index_date'], df_plot['sma_14'], label='Simple Moving Average', color='gold')
    axes[0].set_title(f'{name.upper()} - {trend} ({pct_change:.2f}%)', color='white')  # Title with trend info
    axes[0].set_ylabel('Value', color='white')  # Label for the y-axis
    axes[0].tick_params(colors='white')  # Set tick marks to white for visibility
    axes[0].grid(True, color='#444444')  # Enable grid with a subtle color
    axes[0].legend()  # Show legend for the plot

    row = 1  # Start plotting from the second row (after the main price chart)
    if show_rsi:  # If RSI is enabled, plot the RSI chart
        axes[row].plot(df_plot['index_date'], df_plot['rsi'], label='RSI', color='pink')
        axes[row].axhline(70, color='red', linestyle='--')  # Overbought line at 70
        axes[row].axhline(30, color='green', linestyle='--')  # Oversold line at 30
        axes[row].fill_between(df_plot['index_date'], df_plot['rsi'], 70, where=(df_plot['rsi'] > 70), color='red', alpha=0.3)  # Red fill for overbought
        axes[row].fill_between(df_plot['index_date'], df_plot['rsi'], 30, where=(df_plot['rsi'] < 30), color='green', alpha=0.3)  # Green fill for oversold
        axes[row].set_ylabel('Relative Strength Index', color='white')  # Label for RSI y-axis
        axes[row].tick_params(colors='white')
        axes[row].set_ylim(0, 100)  # Set y-axis limits for RSI
        axes[row].grid(True, color='#444444')
        axes[row].legend()
        row += 1

    if show_smi:  # If SMI is enabled, plot the SMI chart
        axes[row].plot(df_plot['index_date'], df_plot['smi'], label='SMI', color='yellow')
        axes[row].axhline(40, color='red', linestyle='--')  # Overbought line at 40
        axes[row].axhline(-40, color='green', linestyle='--')  # Oversold line at -40
        axes[row].set_ylabel('Stochastic Momentum Index', color='white')
        axes[row].set_xlabel('Date', color='white')  # Label for x-axis
        axes[row].set_ylim(-100, 100)  # Set y-axis limits for SMI
        axes[row].tick_params(colors='white')
        axes[row].grid(True, color='#444444')
        axes[row].legend()

    # Save the plot to a BytesIO buffer
    buf = io.BytesIO()
    plt.tight_layout()  # Adjust layout to prevent overlapping elements
    plt.savefig(buf, format='png')  # Save the plot as a PNG image in the buffer
    plt.close(fig)  # Close the plot to free up resources
    buf.seek(0)  # Rewind the buffer to the start
    return send_file(buf, mimetype='image/png')  # Send the plot as an image response

# Route to compare two indices by plotting their normalized values, RSI, and SMI
@app.route('/compare/<main>/<other>')
def compare_indices(main, other):
    # Check if the user wants to show RSI and/or SMI (via query parameters)
    show_rsi = request.args.get('rsi', '1') == '1'
    show_smi = request.args.get('smi', '1') == '1'

    # Convert index names to lowercase for case-insensitive matching
    main_name = main.strip().lower()
    other_name = other.strip().lower()

    # If both indices are the same, redirect to a single index plot
    if main_name == other_name:
        return redirect(url_for('plot_index', name=main_name))

    # Filter the data for both selected indices and sort by date
    df_main = data[data['index_name_lower'] == main_name].sort_values('index_date').copy()
    df_other = data[data['index_name_lower'] == other_name].sort_values('index_date').copy()

    # If either index is not found, return a 404 error
    if df_main.empty or df_other.empty:
        abort(404, "One or both indices not found")

    # Align the data by the common date range
    start_date = max(df_main['index_date'].min(), df_other['index_date'].min())  # Use the latest starting date
    end_date = min(df_main['index_date'].max(), df_other['index_date'].max())  # Use the earliest ending date
    df_main = df_main[(df_main['index_date'] >= start_date) & (df_main['index_date'] <= end_date)]
    df_other = df_other[(df_other['index_date'] >= start_date) & (df_other['index_date'] <= end_date)]

    # Normalize the data to show percentage change from the first available value for each index
    df_main['norm'] = (df_main['open_index_value'] / df_main['open_index_value'].iloc[0] - 1) * 100
    df_other['norm'] = (df_other['open_index_value'] / df_other['open_index_value'].iloc[0] - 1) * 100

    # Calculate the indicators (SMA, RSI, SMI) for both indices
    for df_tmp in [df_main, df_other]:
        df_tmp['sma_14'] = df_tmp['open_index_value'].rolling(14).mean()
        df_tmp['rsi'] = compute_rsi(df_tmp['open_index_value'])
        df_tmp['smi'] = compute_smi(df_tmp)

    # Detect trends for both indices
    trend_main, change_main = detect_trend(df_main)
    trend_other, change_other = detect_trend(df_other)

    # Determine the number of rows in the plot based on which indicators will be shown
    num_rows = 1 + show_rsi + show_smi
    fig, axes = plt.subplots(num_rows, 1, figsize=(14, 4 * num_rows), sharex=True)
    axes = [axes] if num_rows == 1 else axes  # Ensure axes is always iterable
    fig.patch.set_facecolor('#1e1e1e')
    for ax in axes:
        ax.set_facecolor('#0e1a2b')

    # Plot the normalized price change for both indices
    axes[0].plot(df_main['index_date'], df_main['norm'], label=f'{main.upper()} ({change_main:.2f}%)', color='blue')
    axes[0].plot(df_other['index_date'], df_other['norm'], label=f'{other.upper()} ({change_other:.2f}%)', color='yellow')
    axes[0].set_title(f'{main.upper()} vs {other.upper()}', color='white')
    axes[0].set_ylabel('% Change', color='white')
    axes[0].tick_params(colors='white')
    axes[0].grid(True, color='#444444')
    axes[0].legend()

    row = 1
    if show_rsi:  # Plot the RSI for both indices
        axes[row].plot(df_main['index_date'], df_main['rsi'], label=f'{main.upper()} RSI', color='cyan')
        axes[row].plot(df_other['index_date'], df_other['rsi'], label=f'{other.upper()} RSI', color='orange', linestyle='--')
        axes[row].axhline(70, color='red', linestyle='-.')  # Overbought line at 70
        axes[row].axhline(30, color='green', linestyle='-.')  # Oversold line at 30
        axes[row].set_ylabel('Relative Strength Index', color='white')
        axes[row].set_ylim(0, 100)  # Set y-axis limits for RSI
        axes[row].tick_params(colors='white')
        axes[row].grid(True, color='#444444')
        axes[row].legend()
        row += 1

    if show_smi:  # Plot the SMI for both indices
        axes[row].plot(df_main['index_date'], df_main['smi'], label=f'{main.upper()} SMI', color='red')
        axes[row].plot(df_other['index_date'], df_other['smi'], label=f'{other.upper()} SMI', color='pink', linestyle='--')
        axes[row].axhline(40, color='red', linestyle='-.')  # Overbought line at 40
        axes[row].axhline(-40, color='green', linestyle='-.')  # Oversold line at -40
        axes[row].set_ylabel('Stochastic Momentum Index', color='white')
        axes[row].set_xlabel('Date', color='white')
        axes[row].set_ylim(-100, 100)  # Set y-axis limits for SMI
        axes[row].tick_params(colors='white')
        axes[row].grid(True, color='#444444')
        axes[row].legend()

    # Save the comparison plot to a BytesIO buffer
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')  # Return the comparison plot as an image

# Run the Flask web app
if __name__ == "__main__":
    app.run(debug=True)
