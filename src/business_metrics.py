import os
import pandas as pd
from typing import Dict, Any, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def calculate_csi(df: pd.DataFrame) -> float:
    """
    Computes Customer Satisfaction Index (CSI) from 0 to 100.
    CSI = Average of mapped scores:
      - Ratings 1-5 are scaled linearly to 0-100: (rating - 1) * 25
      - If rating is missing, sentiment is mapped: Positive=85, Neutral=50, Negative=15
    """
    if df.empty:
        return 75.0  # Default baseline
        
    scores = []
    for _, row in df.iterrows():
        rating = row.get('rating')
        sentiment = row.get('sentiment')
        
        if pd.notnull(rating):
            # Scale 1-5 to 0-100
            rating_score = (int(rating) - 1) * 25.0
            scores.append(min(max(rating_score, 0.0), 100.0))
        elif pd.notnull(sentiment):
            # Fallback to sentiment
            sent_str = str(sentiment).title()
            if sent_str == "Positive":
                scores.append(85.0)
            elif sent_str == "Negative":
                scores.append(15.0)
            else:
                scores.append(50.0)
                
    if not scores:
        return 75.0
        
    return round(sum(scores) / len(scores), 2)

def calculate_revenue_risk(df: pd.DataFrame) -> float:
    """
    Calculates total expected Revenue at Risk in INR (₹).
    Expected Loss = Sum of (Base Customer Value * Churn Risk %) per customer.
    """
    if df.empty:
        return 0.0
        
    churn_cols = [c for c in ['churn_risk_percent', 'churn_risk'] if c in df.columns]
    if not churn_cols:
        return 0.0
        
    churn_col = churn_cols[0]
    
    # Base calculation
    total_risk = 0.0
    for _, row in df.iterrows():
        churn_pct = row.get(churn_col)
        # Handle cases where churn_risk_percent is missing or null
        churn_val = float(churn_pct) if pd.notnull(churn_pct) else 10.0
        
        # Calculate risk based on customer lifetime value
        val_risk = config.DEFAULT_REVENUE_PER_CUSTOMER * (churn_val / 100.0)
        total_risk += val_risk
        
    return round(total_risk, 2)

def calculate_loyalty_score(df: pd.DataFrame) -> float:
    """
    Computes Customer Loyalty Score (0 to 100).
    A function of customer satisfaction (CSI) and low churn probability.
    """
    if df.empty:
        return 80.0
        
    csi = calculate_csi(df)
    
    # Calculate average retention rate (100 - churn_risk)
    churn_cols = [c for c in ['churn_risk_percent', 'churn_risk'] if c in df.columns]
    if churn_cols:
        churn_col = churn_cols[0]
        avg_churn = df[churn_col].mean()
        retention = 100.0 - (avg_churn if pd.notnull(avg_churn) else 20.0)
    else:
        retention = 80.0
        
    # Loyalty is a weighted combination of current satisfaction and retention likelihood
    loyalty = (csi * 0.5) + (retention * 0.5)
    return round(min(max(loyalty, 0.0), 100.0), 2)

def calculate_operational_risk(df: pd.DataFrame) -> float:
    """
    Computes Operational Risk Score (0 to 100) based on severity distributions.
    Critical = 1.0 weight
    High = 0.7 weight
    Medium = 0.4 weight
    Low = 0.1 weight
    """
    if df.empty:
        return 20.0
        
    severity_col = 'severity'
    if severity_col not in df.columns:
        return 20.0
        
    weights = []
    for _, row in df.iterrows():
        sev = str(row.get(severity_col, 'Low')).title()
        if sev == "Critical":
            weights.append(1.0)
        elif sev == "High":
            weights.append(0.7)
        elif sev == "Medium":
            weights.append(0.4)
        else:
            weights.append(0.1)
            
    if not weights:
        return 20.0
        
    avg_weight = sum(weights) / len(weights)
    return round(avg_weight * 100.0, 2)

def calculate_business_health(df: pd.DataFrame) -> float:
    """
    Computes overall Business Health Score (0-100).
    Weighted average:
      - CSI (30%)
      - Loyalty Score (25%)
      - Operational Health (100 - Operational Risk) (25%)
      - Churn mitigation (100 - Churn Average) (20%)
    """
    if df.empty:
        return 85.0
        
    csi = calculate_csi(df)
    loyalty = calculate_loyalty_score(df)
    op_risk = calculate_operational_risk(df)
    
    churn_cols = [c for c in ['churn_risk_percent', 'churn_risk'] if c in df.columns]
    if churn_cols:
        avg_churn = df[churn_cols[0]].mean()
        churn_factor = 100.0 - (avg_churn if pd.notnull(avg_churn) else 20.0)
    else:
        churn_factor = 80.0
        
    health = (csi * 0.3) + (loyalty * 0.25) + ((100.0 - op_risk) * 0.25) + (churn_factor * 0.2)
    return round(min(max(health, 5.0), 100.0), 2)

def calculate_category_risk_index(df: pd.DataFrame) -> Dict[str, float]:
    """
    Computes separate risk indices (0-100) for each category.
    Category Risk = Average Priority Score in that category.
    """
    categories = ["Delivery", "Billing", "App Bug", "Staff/Support", "Other"]
    risk_indices = {cat: 0.0 for cat in categories}
    
    if df.empty:
        return risk_indices
        
    for cat in categories:
        cat_df = df[df['category'] == cat]
        if cat_df.empty:
            risk_indices[cat] = 15.0 # Low baseline if no complaints
            continue
            
        # Average priority score
        p_col = 'priority_score' if 'priority_score' in df.columns else 'business_impact_score'
        avg_p = cat_df[p_col].mean() if p_col in cat_df.columns else 30.0
        risk_indices[cat] = round(min(max(avg_p, 0.0), 100.0), 2)
        
    return risk_indices
