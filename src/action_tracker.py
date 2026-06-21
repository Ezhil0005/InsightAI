import os
import pandas as pd
from typing import Dict, Any, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from revenue_simulator import RevenueSimulator

class ActionImpactTracker:
    """
    Evaluates and prioritizes recommended operational actions by implementation difficulty,
    time to value, and projected revenue/CSI benefits.
    """
    
    METADATA_CATALOG = {
        "Delivery": {
            "title": "Optimize Delivery Routing & Spill-Guards",
            "difficulty": "Medium",
            "time_to_value": "2 Weeks",
            "priority": "Critical",
            "description": "Recalibrate dispatch buffer limits, roll out spill-proof delivery boxes, and optimize routing."
        },
        "Billing": {
            "title": "Establish Secondary Gateway Fallback",
            "difficulty": "High",
            "time_to_value": "4 Weeks",
            "priority": "High",
            "description": "Configure automatic API retry handling and integrate backup broker gateway for instant payouts."
        },
        "App Bug": {
            "title": "Stabilize Checkout API Flow",
            "difficulty": "Low",
            "time_to_value": "1 Week",
            "priority": "Critical",
            "description": "Roll back recent frontend check-out release and correct location drift mapping checks."
        },
        "Staff/Support": {
            "title": "Deploy Support AI Autopilot",
            "difficulty": "Medium",
            "time_to_value": "3 Weeks",
            "priority": "Medium",
            "description": "Integrate AI agent to resolve refund/coupon issues in real-time, reducing agent hold loads."
        },
        "Other": {
            "title": "General Operations Assessment",
            "difficulty": "Low",
            "time_to_value": "1 Week",
            "priority": "Low",
            "description": "Establish weekly reviews for non-categorized feedbacks to identify new trends."
        }
    }

    @staticmethod
    def get_action_roadmap(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Calculates and maps operational recommendations with metrics.
        """
        roadmap = []
        if df.empty:
            return roadmap
            
        categories_present = df['category'].unique()
        
        for cat in categories_present:
            meta = ActionImpactTracker.METADATA_CATALOG.get(cat, ActionImpactTracker.METADATA_CATALOG["Other"])
            
            # Simulate the improvement for this category to get precise expected benefits
            # We assume we can reduce complaints by 35% with the recommended action
            sim_res = RevenueSimulator.simulate_improvement(df, cat, 35.0)
            
            roadmap.append({
                "category": cat,
                "action": meta["title"],
                "description": meta["description"],
                "difficulty": meta["difficulty"],
                "timeline": meta["time_to_value"],
                "priority": meta["priority"],
                "revenue_benefit": sim_res["revenue_saved"],
                "csi_benefit": sim_res["csi_increase"],
                "expected_impact": "High" if sim_res["revenue_saved"] > 10000.0 or sim_res["csi_increase"] > 2.0 else "Medium"
            })
            
        # Sort roadmap by priority (Critical > High > Medium > Low) and revenue benefit descending
        priority_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        return sorted(
            roadmap, 
            key=lambda x: (priority_order.get(x["priority"], 1), x["revenue_benefit"]), 
            reverse=True
        )
