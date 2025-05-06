
# Stock Index Viewer
Stock Index Viewer is a Flask-based interactive data visualization web application that allows users to explore, analyze, and compare the performance of various stock market indices over time. It provides a clean and responsive frontend combined with a robust Python backend to deliver real-time financial insights based on historical data.


## Features

- Interactive UI: A dark-themed, clean HTML interface with dropdowns to select one or two indices to visualize.

- Technical Analysis Tools:

  - RSI (Relative Strength Index): Measures the speed and change of price movements to identify overbought or oversold conditions.

  - SMI (Stochastic Momentum Index): A refined version of the stochastic oscillator that accounts for price momentum over time.

  - SMA (Simple Moving Average): Smoothens short-term fluctuations for trend analysis.

- Trend Detection: Automatically detects and displays whether a stock is in an upward, downward, or sideways trend based on recent data.

- Side-by-side Comparison: Normalize and compare the performance of two indices, with percentage change plots and overlayed indicators.

- Dynamic Chart Rendering: Uses matplotlib to generate PNG plots on-the-fly, displayed directly in the frontend.
## Tech Stack

- Backend: Python 3, Flask, Pandas, Matplotlib

- Frontend: HTML, CSS, JavaScript (Jinja templating)

- Data Handling: CSV parsing with Pandas, rolling window computations

- Chart Rendering: On-the-fly image generation with Matplotlib

- Deployment Ready: Can be deployed to local servers or cloud platforms like Heroku, Render, or even Docker.
## Run Locally

Clone the project

```bash
  git clone https://github.com/EmaadAkhter/Stock-Index-Viewer.git
```

Go to the project directory

```bash
  cd Peer-to-Peer-video-transfer
  cd code
```

Run the setup file

```bash
  sh setup.sh
```

Activate the virtual environment

```bash
 source venv/bin/activate
```

Start the Flask application

```bash
 python app.py
```

## Acknowledgements

 - [Flask](https://flask.palletsprojects.com/en/stable/)
 - [Dump file](https://github.com/shaktids/stock_app_test)


