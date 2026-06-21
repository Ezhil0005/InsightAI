import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("QuickCart.Forecasting")

# Graceful import of scikit-learn
try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.info("scikit-learn not available. Falling back to mathematical least-squares regression.")


class TrendForecastingEngine:
    """
    Predicts future complaint volume, sentiment ratios, churn risks, and category spikes
    using Linear Regression, with a pure numpy/mathematical least-squares fallback.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._prepare_data()

    def _prepare_data(self):
        """
        Parses timestamps and sets up temporal variables for forecasting.
        """
        if self.df.empty:
            return

        # Ensure timestamp is parsed
        self.df['date_parsed'] = pd.to_datetime(self.df['timestamp'], errors='coerce')
        # Drop rows with invalid dates
        self.df = self.df.dropna(subset=['date_parsed'])
        
        # Extract only date (daily aggregation)
        self.df['date_only'] = self.df['date_parsed'].dt.date
        
        # Sort chronologically
        self.df = self.df.sort_values(by='date_parsed')

    def forecast_complaint_volume(self, days_to_forecast: int = 7) -> Dict[str, Any]:
        """
        Predicts total daily complaint counts over the next N days.
        Returns historical counts, predicted future counts, expected growth percentage, and trend line.
        """
        if self.df.empty:
            return self._empty_forecast()

        # Group by date
        daily_counts = self.df.groupby('date_only').size().reset_index(name='count')
        
        # Convert date to ordinal index (X variable)
        daily_counts['day_index'] = np.arange(len(daily_counts))
        
        X = daily_counts['day_index'].values.reshape(-1, 1)
        y = daily_counts['count'].values
        
        if len(y) < 2:
            # Not enough data points to fit a line, return flat projection
            last_val = y[0] if len(y) > 0 else 0
            future_days = [str(self.df['date_only'].max() + pd.Timedelta(days=i)) for i in range(1, days_to_forecast + 1)]
            return {
                "historical_dates": [str(d) for d in daily_counts['date_only']],
                "historical_counts": [int(c) for c in y],
                "forecast_dates": future_days,
                "forecast_counts": [int(last_val)] * days_to_forecast,
                "expected_growth_pct": 0.0,
                "slope": 0.0,
                "r_squared": 1.0
            }

        slope, intercept, r_sq = self._fit_linear_regression(X, y)
        
        # Generate future index
        last_index = daily_counts['day_index'].max()
        future_indices = np.arange(last_index + 1, last_index + 1 + days_to_forecast).reshape(-1, 1)
        
        # Predict future counts
        future_preds = (future_indices * slope + intercept).flatten()
        # Clamp negative values to zero
        future_preds = np.clip(future_preds, 0, None)
        
        # Calculate expected growth %
        avg_hist = np.mean(y[-5:]) if len(y) >= 5 else np.mean(y)
        avg_fut = np.mean(future_preds)
        growth_pct = ((avg_fut - avg_hist) / avg_hist * 100.0) if avg_hist > 0 else 0.0

        # Generate future dates
        last_date = daily_counts['date_only'].max()
        future_dates = [str(last_date + pd.Timedelta(days=int(i))) for i in range(1, days_to_forecast + 1)]
        
        return {
            "historical_dates": [str(d) for d in daily_counts['date_only']],
            "historical_counts": [int(c) for c in y],
            "forecast_dates": future_dates,
            "forecast_counts": [int(round(c)) for c in future_preds],
            "expected_growth_pct": float(round(growth_pct, 1)),
            "slope": float(slope),
            "r_squared": float(r_sq)
        }

    def forecast_category_spikes(self, days_to_forecast: int = 7) -> Dict[str, Any]:
        """
        Forecasts trends for each category and identifies potential spikes.
        Returns future predictions per category.
        """
        categories = ["Billing", "App Bug", "Delivery", "Staff/Support"]
        forecast_results = {}
        
        if self.df.empty:
            return {cat: [0] * days_to_forecast for cat in categories}
            
        for cat in categories:
            cat_df = self.df[self.df['category'] == cat]
            if cat_df.empty:
                forecast_results[cat] = [0] * days_to_forecast
                continue
                
            # Aggregate by day
            daily_cat = cat_df.groupby('date_only').size().reset_index(name='count')
            
            # Fill missing dates to keep a solid daily trend
            all_dates = pd.date_range(start=self.df['date_only'].min(), end=self.df['date_only'].max())
            daily_cat.index = pd.to_datetime(daily_cat['date_only'])
            daily_cat = daily_cat.reindex(all_dates, fill_value=0).reset_index()
            daily_cat['day_index'] = np.arange(len(daily_cat))
            
            X = daily_cat['day_index'].values.reshape(-1, 1)
            y = daily_cat['count'].values
            
            if len(y) < 2:
                forecast_results[cat] = [0] * days_to_forecast
                continue
                
            slope, intercept, _ = self._fit_linear_regression(X, y)
            
            last_index = daily_cat['day_index'].max()
            future_indices = np.arange(last_index + 1, last_index + 1 + days_to_forecast).reshape(-1, 1)
            preds = (future_indices * slope + intercept).flatten()
            preds = np.clip(preds, 0, None)
            
            forecast_results[cat] = [int(round(c)) for c in preds]
            
        return forecast_results

    def forecast_churn_risk(self, days_to_forecast: int = 7) -> Dict[str, Any]:
        """
        Forecasts the average customer churn risk trend.
        """
        if self.df.empty:
            return {"historical": [], "forecast": [], "growth_pct": 0.0}
            
        # Ensure churn risk column exists
        if 'churn_risk_percent' not in self.df.columns:
            return {"historical": [], "forecast": [], "growth_pct": 0.0}
            
        # Aggregate mean churn by day
        daily_churn = self.df.groupby('date_only')['churn_risk_percent'].mean().reset_index()
        daily_churn['day_index'] = np.arange(len(daily_churn))
        
        X = daily_churn['day_index'].values.reshape(-1, 1)
        y = daily_churn['churn_risk_percent'].values
        
        if len(y) < 2:
            return {
                "historical": [float(v) for v in y],
                "forecast": [float(y[0])] * days_to_forecast if len(y) > 0 else [],
                "growth_pct": 0.0
            }
            
        slope, intercept, _ = self._fit_linear_regression(X, y)
        
        last_index = daily_churn['day_index'].max()
        future_indices = np.arange(last_index + 1, last_index + 1 + days_to_forecast).reshape(-1, 1)
        preds = (future_indices * slope + intercept).flatten()
        preds = np.clip(preds, 0, 100)
        
        avg_hist = np.mean(y[-5:]) if len(y) >= 5 else np.mean(y)
        avg_fut = np.mean(preds)
        growth_pct = ((avg_fut - avg_hist) / avg_hist * 100.0) if avg_hist > 0 else 0.0
        
        return {
            "historical": [float(v) for v in y],
            "forecast": [float(round(v, 1)) for v in preds],
            "growth_pct": float(round(growth_pct, 1))
        }

    def forecast_sentiment_csat(self, days_to_forecast: int = 7) -> Dict[str, Any]:
        """
        Forecasts customer satisfaction (CSAT) rating trend (approximated from average rating).
        """
        if self.df.empty:
            return {"historical": [], "forecast": [], "growth_pct": 0.0}
            
        # Group average ratings by date
        daily_rating = self.df.groupby('date_only')['rating'].mean().reset_index()
        daily_rating['day_index'] = np.arange(len(daily_rating))
        
        # Fill missing ratings with mean
        mean_rating = self.df['rating'].mean() if not self.df['rating'].empty else 3.0
        daily_rating['rating'] = daily_rating['rating'].fillna(mean_rating)
        
        X = daily_rating['day_index'].values.reshape(-1, 1)
        y = daily_rating['rating'].values
        
        if len(y) < 2:
            return {
                "historical": [float(v) for v in y],
                "forecast": [float(y[0])] * days_to_forecast if len(y) > 0 else [],
                "growth_pct": 0.0
            }
            
        slope, intercept, _ = self._fit_linear_regression(X, y)
        
        last_index = daily_rating['day_index'].max()
        future_indices = np.arange(last_index + 1, last_index + 1 + days_to_forecast).reshape(-1, 1)
        preds = (future_indices * slope + intercept).flatten()
        preds = np.clip(preds, 1.0, 5.0)
        
        avg_hist = np.mean(y[-5:]) if len(y) >= 5 else np.mean(y)
        avg_fut = np.mean(preds)
        growth_pct = ((avg_fut - avg_hist) / avg_hist * 100.0) if avg_hist > 0 else 0.0
        
        return {
            "historical": [float(v) for v in y],
            "forecast": [float(round(v, 2)) for v in preds],
            "growth_pct": float(round(growth_pct, 1))
        }

    def _fit_linear_regression(self, X: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
        """
        Fits a linear regression model. Uses scikit-learn if available,
        otherwise falls back to mathematical least-squares formula.
        Returns: (slope, intercept, r_squared)
        """
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(X, y)
            slope = model.coef_[0]
            intercept = model.intercept_
            r_sq = model.score(X, y)
            return slope, intercept, r_sq
        else:
            # Mathematical least squares regression: y = m*x + c
            x_flat = X.flatten()
            n = len(x_flat)
            sum_x = np.sum(x_flat)
            sum_y = np.sum(y)
            sum_xy = np.sum(x_flat * y)
            sum_xx = np.sum(x_flat ** 2)
            
            denominator = (n * sum_xx - sum_x ** 2)
            if denominator == 0:
                return 0.0, float(np.mean(y)), 1.0
                
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n
            
            # Calculate r_squared
            y_pred = x_flat * slope + intercept
            y_mean = np.mean(y)
            ss_tot = np.sum((y - y_mean) ** 2)
            ss_res = np.sum((y - y_pred) ** 2)
            r_sq = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
            
            return slope, intercept, r_sq

    def _empty_forecast(self) -> Dict[str, Any]:
        return {
            "historical_dates": [],
            "historical_counts": [],
            "forecast_dates": [],
            "forecast_counts": [],
            "expected_growth_pct": 0.0,
            "slope": 0.0,
            "r_squared": 1.0
        }
