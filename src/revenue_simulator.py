import os
import pandas as pd
from typing import Dict, Any, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from business_metrics import calculate_revenue_risk, calculate_csi

class RevenueSimulator:
    """
    Simulates the financial impact of business decisions and customer retention improvements.
    """
    @staticmethod
    def simulate_improvement(df: pd.DataFrame, category: str, reduction_pct: float) -> Dict[str, Any]:
        """
        Simulates the effect of reducing complaints in a specific category by a given percentage.
        Calculates:
          - Revenue saved (₹)
          - Overall churn reduction (%)
          - CSI growth (%)
          - ROI estimation
        """
        if df.empty:
            return {
                "category": category,
                "reduction_pct": reduction_pct,
                "baseline_revenue_risk": 0.0,
                "simulated_revenue_risk": 0.0,
                "revenue_saved": 0.0,
                "baseline_churn_avg": 0.0,
                "simulated_churn_avg": 0.0,
                "churn_reduction_abs": 0.0,
                "baseline_csi": 75.0,
                "simulated_csi": 75.0,
                "csi_increase": 0.0,
                "estimated_implementation_cost": 0.0,
                "roi_pct": 0.0
            }

        total_count = len(df)
        cat_df = df[df['category'] == category]
        cat_count = len(cat_df)
        
        # 1. Baseline calculations
        baseline_revenue_risk = calculate_revenue_risk(df)
        baseline_churn_avg = df['churn_risk_percent'].mean() if 'churn_risk_percent' in df.columns else 20.0
        baseline_csi = calculate_csi(df)
        
        if cat_count == 0:
            # Category has no complaints, no improvement possible
            return {
                "category": category,
                "reduction_pct": reduction_pct,
                "baseline_revenue_risk": baseline_revenue_risk,
                "simulated_revenue_risk": baseline_revenue_risk,
                "revenue_saved": 0.0,
                "baseline_churn_avg": round(baseline_churn_avg, 2),
                "simulated_churn_avg": round(baseline_churn_avg, 2),
                "churn_reduction_abs": 0.0,
                "baseline_csi": round(baseline_csi, 2),
                "simulated_csi": round(baseline_csi, 2),
                "csi_increase": 0.0,
                "estimated_implementation_cost": 0.0,
                "roi_pct": 0.0
            }

        # Calculate category specific risk
        cat_baseline_risk = calculate_revenue_risk(cat_df)
        
        # 2. Simulated calculations
        # Complaint reduction in category means churn risk for those complaints drops
        sim_df = df.copy()
        factor = 1.0 - (reduction_pct / 100.0)
        
        # We apply the reduction factor to the churn risk of the target category
        sim_df.loc[sim_df['category'] == category, 'churn_risk_percent'] = (
            sim_df.loc[sim_df['category'] == category, 'churn_risk_percent'] * factor
        )
        
        simulated_revenue_risk = calculate_revenue_risk(sim_df)
        revenue_saved = max(baseline_revenue_risk - simulated_revenue_risk, 0.0)
        
        # Churn reduction
        simulated_churn_avg = sim_df['churn_risk_percent'].mean()
        churn_reduction_abs = max(baseline_churn_avg - simulated_churn_avg, 0.0)
        
        # CSI increase estimation:
        # Scale improvement of CSI linearly by the ratio of complaints resolved
        csi_cat_factor = (cat_count / total_count) * (reduction_pct / 100.0)
        csi_increase = (100.0 - baseline_csi) * csi_cat_factor * 0.6  # Scale coefficient
        simulated_csi = min(baseline_csi + csi_increase, 100.0)
        
        # 3. ROI Estimation
        # Assume an implementation cost of ₹15,000 for every 10% of complaint reduction
        estimated_implementation_cost = (reduction_pct / 10.0) * 15000.0
        # For small categories, scale down cost
        cat_ratio = cat_count / total_count
        estimated_implementation_cost = estimated_implementation_cost * (0.2 + 0.8 * cat_ratio)
        
        if estimated_implementation_cost > 0:
            roi_pct = (revenue_saved / estimated_implementation_cost) * 100.0
        else:
            roi_pct = 0.0
            
        return {
            "category": category,
            "reduction_pct": reduction_pct,
            "baseline_revenue_risk": round(baseline_revenue_risk, 2),
            "simulated_revenue_risk": round(simulated_revenue_risk, 2),
            "revenue_saved": round(revenue_saved, 2),
            "baseline_churn_avg": round(baseline_churn_avg, 2),
            "simulated_churn_avg": round(simulated_churn_avg, 2),
            "churn_reduction_abs": round(churn_reduction_abs, 2),
            "baseline_csi": round(baseline_csi, 2),
            "simulated_csi": round(simulated_csi, 2),
            "csi_increase": round(csi_increase, 2),
            "estimated_implementation_cost": round(estimated_implementation_cost, 2),
            "roi_pct": round(roi_pct, 2)
        }
        
    @staticmethod
    def get_simulation_chart_data(df: pd.DataFrame, category: str, reduction_pct: float) -> pd.DataFrame:
        """
        Formats a DataFrame suitable for plotting baseline vs target recovery.
        """
        results = RevenueSimulator.simulate_improvement(df, category, reduction_pct)
        chart_df = pd.DataFrame({
            "Metrics": ["Baseline Churn Risk", "Simulated Churn Risk", "Churn Prevented"],
            "Value (%)": [
                results["baseline_churn_avg"],
                results["simulated_churn_avg"],
                results["churn_reduction_abs"]
            ],
            "Color": ["#fb7185", "#cbd5e1", "#34d399"]
        })
        return chart_df
