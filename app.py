# app.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import feedparser

# Lightweight sentiment analyzer (replaces NLTK)
def simple_sentiment(text):
    """Simple rule-based sentiment analyzer - returns score between -1 and 1"""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Positive words
    positive_words = ['bullish', 'rise', 'up', 'gain', 'profit', 'growth', 'strong', 
                     'buy', 'positive', 'surge', 'rally', 'boom', 'success', 'win',
                     'beat', 'outperform', 'soar', 'jump', 'climb', 'advance']
    
    # Negative words
    negative_words = ['bearish', 'fall', 'down', 'loss', 'decline', 'weak', 'sell',
                     'negative', 'drop', 'crash', 'bust', 'fail', 'lose', 'miss',
                     'underperform', 'plunge', 'slide', 'dip', 'retreat', 'worry']
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    # Normalize to -1 to 1 range
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / max(total, 1)

# Simple linear regression using numpy (replaces scikit-learn)
class SimpleLinearRegression:
    def __init__(self):
        self.coef_ = None
        self.intercept_ = None
    
    def fit(self, X, y):
        """Fit linear regression model using least squares"""
        # Add intercept term
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
        
        # Solve using numpy's least squares
        try:
            coefs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse if lstsq fails
            coefs = np.linalg.pinv(X_with_intercept) @ y
        
        # Handle case where coefs might be 1D or 2D
        if coefs.ndim > 1:
            coefs = coefs.flatten()
        
        self.intercept_ = float(coefs[0])
        self.coef_ = coefs[1:].astype(float)
        return self
    
    def predict(self, X):
        """Make predictions"""
        if self.coef_ is None:
            raise ValueError("Model must be fitted before prediction")
        return self.intercept_ + np.dot(X, self.coef_)

def mean_squared_error(y_true, y_pred):
    """Calculate MSE"""
    return np.mean((y_true - y_pred) ** 2)

def r2_score(y_true, y_pred):
    """Calculate R² score"""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

def predict_stock(user_input):
    try:
        if not user_input or not isinstance(user_input, str):
            return {"error": "Invalid input"}
        
        if "." not in user_input:
            TICKER = user_input.upper() + ".NS"
        else:
            TICKER = user_input.upper()

        start = "2025-03-01"
        # Train up to Oct 10, 2025; fetch data up to Nov 09, 2025 for backtesting/forecast window
        train_cutoff_str = "2025-10-10"
        forecast_end_str = "2025-11-09"
        end   = forecast_end_str

        try:
            price = yf.download(TICKER, start=start, end=end, progress=False, auto_adjust=False)
        except Exception as e:
            return {"error": f"Failed to download data: {str(e)}"}
        
        if price is None or len(price)==0:
            return {"error":"no data"}

        if isinstance(price.columns, pd.MultiIndex):
            price.columns = price.columns.droplevel(1)

        price = price.reset_index()
        price['Date'] = pd.to_datetime(price['Date'])
        price = price[['Date','Open','High','Low','Close','Volume']]

        rss_urls = [
            f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={TICKER}&region=IN&lang=en-IN",
            "https://www.thehindu.com/business/feeder/default.rss",
            "https://feeds.feedburner.com/NDTV-Business",
            "https://www.moneycontrol.com/rss/latestnews.xml"
        ]

        news_list=[]
        start_date = datetime(2025,3,1)
        end_date   = datetime(2025,11,9)

        for url in rss_urls:
            try:
                rss = feedparser.parse(url)
                for entry in rss.entries:
                    if hasattr(entry,"published_parsed") and entry.published_parsed:
                        try:
                            dt = datetime(*entry.published_parsed[:6])
                            if start_date.date() <= dt.date() <= end_date.date():
                                sentiment = simple_sentiment(entry.title)
                                news_list.append([dt.date(),sentiment])
                        except (ValueError, TypeError, IndexError):
                            continue
            except Exception:
                # Continue if RSS feed fails
                continue

        news_daily = pd.DataFrame(news_list, columns=['DateOnly','Sentiment'])
        news_daily = news_daily.groupby("DateOnly")['Sentiment'].mean().reset_index()

        price['DateOnly'] = price['Date'].dt.date
        df = price.merge(news_daily,on="DateOnly",how="left")
        df['Sentiment'] = df['Sentiment'].fillna(0)

        df['PrevClose'] = df['Close'].shift(1)
        df['Return%'] = ((df['Close'] - df['PrevClose'])/df['PrevClose'])*100
        df = df.dropna()

        # Domain-informed interaction features:
        # - Positive sentiment with rising price => strong bullish
        # - Positive sentiment with falling price => weak
        # Implement by interacting sentiment with returns (and volume)
        df['Sent_x_Return'] = df['Sentiment'] * df['Return%']
        df['Sent_x_PosRet'] = df['Sentiment'] * df['Return%'].clip(lower=0)
        df['Sent_x_Volume'] = df['Sentiment'] * df['Volume']

        # Remove raw Sentiment as standalone feature; keep interactions only
        features = [
            'Open','High','Low','Close','Volume','Return%',
            'Sent_x_Return','Sent_x_PosRet','Sent_x_Volume'
        ]
        X = df[features]
        y = df['Close'].shift(-1).dropna()
        X = X.iloc[:-1]

        # Train strictly up to the cutoff date
        train_cutoff = pd.to_datetime(train_cutoff_str)
        train_idx = df['Date'].iloc[:-1] <= train_cutoff
        X_train = X[train_idx]
        y_train = y[train_idx.values]
        # Hold out the remainder (after cutoff) for evaluation/backtest alignment
        X_test = X[~train_idx]
        y_test = y[~train_idx.values]

        model = SimpleLinearRegression()
        model.fit(X_train.values, y_train.values)

        pred_test = model.predict(X_test.values)
        mse = mean_squared_error(y_test.values, pred_test)
        rmse = mse**0.5
        confidence = r2_score(y_test.values, pred_test)*100

        curr = df.iloc[-1]['Close']
        latest_time = df.iloc[-1]['Date']

        pred_next = model.predict(df.iloc[-1:][features].values)[0]

        # -------- CHART DATA FOR CLIENT-SIDE RENDERING (Plotly.js) --------
        hist_dates = df['Date'].astype(str).tolist()
        hist_close = df['Close'].astype(float).tolist()
        pred_point_date = (df['Date'].iloc[-1] + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        # ----------------------------------------------------------------

        # ===== Task 1: Generate daily predictions from Oct 11 to Nov 09 (walk-forward using previous-day features) =====
        forecast_start = pd.to_datetime(train_cutoff_str) + pd.Timedelta(days=1)
        forecast_end = pd.to_datetime(forecast_end_str)
        # Align to available trading days present in df
        available_dates = df['Date']
        target_dates = available_dates[(available_dates >= forecast_start) & (available_dates <= forecast_end)].sort_values()

        pred_series_dates = []
        pred_series_values = []
        actual_series_values = []
        directional_flags = []  # Will be computed after sequences are built (within-series day-over-day moves)

        # Our model predicts Close_t using features from day t-1, consistent with y = Close.shift(-1)
        for target_date in target_dates:
            prev_day_mask = df['Date'] == (target_date - pd.Timedelta(days=1))
            if not prev_day_mask.any():
                # If previous trading day not found, skip
                continue
            prev_features = df.loc[prev_day_mask, features].values
            pred_val = float(model.predict(prev_features)[0])
            pred_series_dates.append(target_date.strftime("%Y-%m-%d"))
            pred_series_values.append(pred_val)
            # Actual close for target day (for backtest/comparison)
            act_mask = df['Date'] == target_date
            if act_mask.any():
                act_val = float(df.loc[act_mask, 'Close'].values[0])
                actual_series_values.append(act_val)
            else:
                actual_series_values.append(None)

        # Compute directional flags based on within-series day-over-day movement
        # For index 0, we cannot compute a direction (needs previous day in series)
        for i in range(len(pred_series_values)):
            if i == 0:
                directional_flags.append(None)
                continue
            prev_pred = pred_series_values[i-1]
            curr_pred = pred_series_values[i]
            prev_act  = actual_series_values[i-1]
            curr_act  = actual_series_values[i]
            # Need actual values available for both consecutive days
            if prev_act is None or curr_act is None:
                directional_flags.append(None)
                continue
            pred_dir = np.sign(curr_pred - prev_pred)
            act_dir  = np.sign(curr_act - prev_act)
            if pred_dir == 0 and act_dir == 0:
                directional_flags.append(True)
            elif pred_dir == 0 or act_dir == 0:
                directional_flags.append(False)
            else:
                directional_flags.append(bool(pred_dir == act_dir))

        # Compute comparison metrics over overlapping non-null pairs
        comp_df = pd.DataFrame({
            'date': pred_series_dates,
            'pred': pred_series_values,
            'act': actual_series_values,
            'dir_ok': directional_flags
        })
        comp_df = comp_df.dropna()
        if not comp_df.empty:
            comp_rmse = float(np.sqrt(np.mean((comp_df['pred'] - comp_df['act'])**2)))
            comp_mape = float(np.mean(np.abs((comp_df['act'] - comp_df['pred']) / comp_df['act'])) * 100.0)
            # Directional accuracy based on within-series flags (exclude None)
            valid_flags = [flag for flag in directional_flags if flag is not None]
            dir_accuracy = float(100.0 * np.mean(valid_flags)) if len(valid_flags) > 0 else None
        else:
            comp_rmse = None
            comp_mape = None
            dir_accuracy = None

        # Comparison chart data is sent as JSON, rendered client-side with Plotly.js
        # ===== End Task 1/2/3 =====

        return {
            "ticker":TICKER,
            "current_price":float(curr),
            "current_time": latest_time.strftime("%Y-%m-%d %H:%M:%S"),
            "predicted_next":float(pred_next),
            "accuracy":float(confidence),
            "rmse":float(rmse),

            # Chart data for client-side rendering (Plotly.js):
            "hist_dates": hist_dates,
            "hist_close": hist_close,
            "pred_date": pred_point_date,
            "pred_value": float(pred_next),

            # Task 1 outputs: one-month daily predictions up to Nov 09, 2025
            "month_pred_dates": pred_series_dates,
            "month_pred_values": pred_series_values,

            # Task 2 outputs: backtesting for provided period (for generic ticker; user requested TCS.NS)
            "backtest_dates": pred_series_dates,   # same target dates
            "backtest_actuals": actual_series_values,

            # Task 3: comparison + metrics (charts rendered client-side)
            "comparison_rmse": comp_rmse,
            "comparison_mape": comp_mape,

            # Directional accuracy over the backtest window
            "directional_accuracy": dir_accuracy,
            "directional_flags": [bool(x) if x is not None else None for x in directional_flags]
        }
    except Exception as e:
        import traceback
        return {"error": f"Prediction failed: {str(e)}", "traceback": traceback.format_exc()}
