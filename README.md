# Stock Price Predictor

A Next.js frontend with Python backend for predicting stock prices using machine learning and sentiment analysis. Deployable on Vercel.

## Features

- Stock price prediction using linear regression (Python backend)
- Sentiment analysis from RSS feeds
- Interactive charts using Plotly.js
- Backtesting and comparison metrics
- Directional accuracy analysis
- Same beautiful UI as the original Flask app

## Project Structure

```
stock/
├── app.py              # Python prediction logic
├── web.py              # Original Flask app (for reference)
├── api/
│   └── predict.py      # Vercel serverless function
├── pages/
│   └── index.js        # Next.js frontend
├── package.json        # Node.js dependencies
├── requirements.txt    # Python dependencies
└── vercel.json         # Vercel configuration
```

## Setup

1. Install Node.js dependencies:
```bash
npm install
```

2. Install Python dependencies (for local testing):
```bash
pip install -r requirements.txt
```

3. Run development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

## Deployment on Vercel

1. Push your code to GitHub
2. Import the repository in Vercel
3. Vercel will automatically detect:
   - Next.js frontend
   - Python serverless functions in `api/` directory
4. The Python API route will be available at `/api/predict`

The API route has a 60-second timeout configured for longer-running predictions.

## Usage

Enter a stock symbol (e.g., "TCS" for TCS.NS) and click "Predict" to get:
- Current stock price
- Predicted next day price
- Historical price chart
- Backtesting results (Oct 11 - Nov 09, 2025)
- Comparison metrics (RMSE, MAPE, Directional Accuracy)
- Daily values table with directional flags

## Notes

- The Python backend (`app.py`) remains unchanged and is used by the serverless function
- The frontend is a React/Next.js application with the same UI as the Flask version
- All Python dependencies are specified in `requirements.txt` for Vercel to install

