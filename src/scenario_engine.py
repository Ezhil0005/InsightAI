import os
import pandas as pd
from typing import Dict, Any, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from business_metrics import (
    calculate_csi, 
    calculate_revenue_risk, 
    calculate_business_health, 
    calculate_loyalty_score
)

class StrategicScenarioEngine:
    """
    Simulates what-if business decisions and projects future outcomes for core business KPIs.
    """
    PRESETS = {
        "Increase Support Team": {
            "name": "Increase Support Team by 15%",
            "category": "Staff/Support",
            "reduction_pct": 50.0,
            "description": "Deploy extra agents to handle peak hour support queues and lower hold-times."
        },
        "Improve Delivery Performance": {
            "name": "Improve Delivery Performance by 25%",
            "category": "Delivery",
            "reduction_pct": 40.0,
            "description": "Establish sealed spill-guards and optimize dispatch queue mapping."
        },
        "Reduce Payment Failures": {
            "name": "Reduce Payment Failures by 30%",
            "category": "Billing",
            "reduction_pct": 60.0,
            "description": "Establish backup dual-gateway integrations to bypass API timing delays."
        },
        "Improve App Stability": {
            "name": "Improve App Stability by 20%",
            "category": "App Bug",
            "reduction_pct": 50.0,
            "description": "Roll back recent checkout package releases and optimize static UI assets."
        }
    }

    @staticmethod
    def simulate_scenario(df: pd.DataFrame, scenario_key: str) -> Dict[str, Any]:
        """
        Simulates the selected scenario preset.
        Returns:
          - Baseline metrics vs Simulated metrics
          - Deltas (CSI, Churn, Revenue, Health)
        """
        preset = StrategicScenarioEngine.PRESETS.get(scenario_key)
        if df.empty or not preset:
            return {
                "name": preset["name"] if preset else scenario_key,
                "description": preset["description"] if preset else "",
                "baseline_health": 85.0, "simulated_health": 85.0, "health_delta": 0.0,
                "baseline_csi": 75.0, "simulated_csi": 75.0, "csi_delta": 0.0,
                "baseline_churn": 20.0, "simulated_churn": 20.0, "churn_delta": 0.0,
                "baseline_revenue_risk": 0.0, "simulated_revenue_risk": 0.0, "revenue_saved": 0.0
            }

        target_cat = preset["category"]
        reduction_pct = preset["reduction_pct"]
        
        # 1. Baseline Calculations
        baseline_health = calculate_business_health(df)
        baseline_csi = calculate_csi(df)
        baseline_churn = df['churn_risk_percent'].mean() if 'churn_risk_percent' in df.columns else 20.0
        baseline_rev_risk = calculate_revenue_risk(df)
        
        # 2. Simulated State
        # Copy data and apply reductions to records matching target category
        sim_df = df.copy()
        factor = 1.0 - (reduction_pct / 100.0)
        
        if target_cat in sim_df['category'].values:
            # Drop churn risk in category
            sim_df.loc[sim_df['category'] == target_cat, 'churn_risk_percent'] = (
                sim_df.loc[sim_df['category'] == target_cat, 'churn_risk_percent'] * factor
            )
            # Drop severity or raise rating values artificially (simulating user satisfaction growth)
            sim_df.loc[sim_df['category'] == target_cat, 'business_impact_score'] = (
                sim_df.loc[sim_df['category'] == target_cat, 'business_impact_score'] * factor
            )
            # Artificially shift rating higher for category complaints
            if 'rating' in sim_df.columns:
                sim_df.loc[(sim_df['category'] == target_cat) & (sim_df['rating'] < 5), 'rating'] = (
                    sim_df.loc[(sim_df['category'] == target_cat) & (sim_df['rating'] < 5), 'rating'] + 1
                )
                sim_df['rating'] = sim_df['rating'].clip(1, 5)
                
            # Shift sentiment from Negative to Neutral/Positive
            if 'sentiment' in sim_df.columns:
                neg_indices = sim_df[(sim_df['category'] == target_cat) & (sim_df['sentiment'] == 'Negative')].index
                # Convert half of the negative complaints in this category to neutral/positive
                convert_count = int(len(neg_indices) * (reduction_pct / 100.0))
                if convert_count > 0:
                    sim_df.loc[neg_indices[:convert_count], 'sentiment'] = 'Neutral'
                    
        # Recalculate simulated metrics
        simulated_health = calculate_business_health(sim_df)
        simulated_csi = calculate_csi(sim_df)
        simulated_churn = sim_df['churn_risk_percent'].mean()
        simulated_rev_risk = calculate_revenue_risk(sim_df)
        
        # Calculate Deltas
        health_delta = simulated_health - baseline_health
        csi_delta = simulated_csi - baseline_csi
        churn_delta = simulated_churn - baseline_churn
        revenue_saved = max(baseline_rev_risk - simulated_rev_risk, 0.0)
        
        return {
            "name": preset["name"],
            "category": target_cat,
            "description": preset["description"],
            "baseline_health": round(baseline_health, 2),
            "simulated_health": round(simulated_health, 2),
            "health_delta": round(health_delta, 2),
            "baseline_csi": round(baseline_csi, 2),
            "simulated_csi": round(simulated_csi, 2),
            "csi_delta": round(csi_delta, 2),
            "baseline_churn": round(baseline_churn, 2),
            "simulated_churn": round(simulated_churn, 2),
            "churn_delta": round(churn_delta, 2),
            "baseline_revenue_risk": round(baseline_rev_risk, 2),
            "simulated_revenue_risk": round(simulated_rev_risk, 2),
            "revenue_saved": round(revenue_saved, 2)
        }
        
    @staticmethod
    def get_comparison_matrix(df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs simulations on all presets and compiles them in a single table for comparison.
        """
        rows = []
        for key in StrategicScenarioEngine.PRESETS.keys():
            res = StrategicScenarioEngine.simulate_scenario(df, key)
            rows.append({
                "Scenario Preset": res["name"],
                "Business Health": f"{res['simulated_health']}% ({'+' if res['health_delta'] >= 0 else ''}{res['health_delta']:.1f}%)",
                "Satisfaction (CSI)": f"{res['simulated_csi']}% ({'+' if res['csi_delta'] >= 0 else ''}{res['csi_delta']:.1f}%)",
                "Churn Level": f"{res['simulated_churn']:.1f}% ({res['churn_delta']:.1f}%)",
                "Churn Reduction": f"{abs(res['churn_delta']):.1f}% absolute"
            })
            
        return pd.DataFrame(rows)
