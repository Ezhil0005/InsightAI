import os
import pandas as pd
from typing import Dict, Any, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class ExecutiveAdvisor:
    """
    Translates analytics and metrics into strategic, executive-level business advice.
    """
    @staticmethod
    def generate_advice(df: pd.DataFrame, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates high-level business risk assessments and recommended actions.
        """
        if df.empty:
            return {
                "top_business_risk": "No active issues detected.",
                "highest_priority_issue": "None",
                "affected_customers": 0,
                "revenue_risk": 0.0,
                "priority_level": "Low",
                "recommended_action": "No actions needed. System reports healthy baseline.",
                "expected_outcome": "Maintain current operational parameters.",
                "recommendations_list": []
            }

        # 1. Determine top risk category (by sum of priority_score or count of negative reviews)
        cat_stats = df.groupby('category').agg(
            count=('id', 'count'),
            avg_priority=('priority_score', 'mean'),
            neg_count=('sentiment', lambda s: (s == 'Negative').sum())
        )
        
        if not cat_stats.empty:
            # Sort by negative count first, then avg priority
            top_risk_cat = cat_stats.sort_values(by=['neg_count', 'avg_priority'], ascending=False).index[0]
            neg_count = int(cat_stats.loc[top_risk_cat, 'neg_count'])
            total_cat_count = int(cat_stats.loc[top_risk_cat, 'count'])
        else:
            top_risk_cat = "Other"
            neg_count = 0
            total_cat_count = 0

        # Calculate specific revenue risk for this category
        from business_metrics import calculate_revenue_risk
        cat_df = df[df['category'] == top_risk_cat]
        cat_revenue_risk = calculate_revenue_risk(cat_df)

        # 2. Determine highest priority root cause
        rc_stats = df.groupby('root_cause').agg(
            avg_priority=('priority_score', 'mean'),
            count=('id', 'count')
        )
        if not rc_stats.empty:
            top_rc = rc_stats.sort_values(by='avg_priority', ascending=False).index[0]
        else:
            top_rc = "General Operations"

        # 3. Determine overall priority level
        overall_health = metrics.get("business_health_score", 100.0)
        if overall_health < 50.0:
            priority_level = "Critical"
        elif overall_health < 75.0:
            priority_level = "High"
        elif overall_health < 90.0:
            priority_level = "Medium"
        else:
            priority_level = "Low"

        # 4. Map recommendations based on the top category
        rec_catalog = {
            "Delivery": {
                "action": "Audit delivery bag specifications, deploy sealed packaging spill-guards, and optimize route-planning dispatch windows.",
                "improvement": "Reduce delivery delay complaints by 35% and completely resolve packaging leakage instances.",
                "outcome": "CSI recovery by +12% and reduction of delivery churn by 15%.",
                "title": "Logistics & Dispatch Calibration"
            },
            "Billing": {
                "action": "Establish dual-gateway fallback routing with our secondary payment gateway, and automate customer credit settlements for billing disputes immediately.",
                "improvement": "Reduce transaction failure complaints by 45% and shorten refund dispute resolution cycles to under 2 hours.",
                "outcome": "CSI recovery by +15% and decrease double-charging churn risk.",
                "title": "Payment Settlement Gateways Optimization"
            },
            "App Bug": {
                "action": "Roll back recent checkout API release, optimize static UI elements, and expand mobile device testing parameters for checkout session handling.",
                "improvement": "Eliminate checkout screen crashes and reduce app freezes by 50% across Android/iOS platforms.",
                "outcome": "Minimize transaction checkout drops, increasing sales conversion by +6%.",
                "title": "Checkout Flow API Stabilization"
            },
            "Staff/Support": {
                "action": "Launch automated AI customer service agent to handle repetitive refund/FAQ inquiries and resolve peak-hour hold-time spikes.",
                "improvement": "Decrease average support response wait times by 60% and lower support escalation ratios.",
                "outcome": "Improve customer satisfaction metrics and relieve staffing load.",
                "title": "Customer Service AI-Augmentation"
            },
            "Other": {
                "action": "Establish customer experience review board to track non-categorized reviews, and improve product description parameters.",
                "improvement": "Reduce unclassified reviews and clarify user purchase details.",
                "outcome": "Broad customer retention uplift.",
                "title": "General Operations Review"
            }
        }

        rec = rec_catalog.get(top_risk_cat, rec_catalog["Other"])

        # Create structured recommendations list
        recommendations_list = []
        for cat, item in rec_catalog.items():
            # Check if category has issues in the dataset
            cat_count = len(df[df['category'] == cat])
            if cat_count > 0:
                recommendations_list.append({
                    "title": item["title"],
                    "category": cat,
                    "recommended_action": item["action"],
                    "expected_improvement": item["improvement"],
                    "expected_outcome": item["outcome"],
                    "priority": "High" if cat == top_risk_cat else "Medium",
                    "impact": "High" if cat in ["Delivery", "Billing", "App Bug"] else "Medium"
                })

        return {
            "top_business_risk": f"{top_risk_cat} Issues ({neg_count} negative reviews)",
            "highest_priority_issue": f"{top_rc} (Root Cause)",
            "affected_customers": total_cat_count,
            "revenue_risk": cat_revenue_risk,
            "priority_level": priority_level,
            "recommended_action": rec["action"],
            "expected_improvement": rec["improvement"],
            "expected_outcome": rec["outcome"],
            "recommendations_list": sorted(recommendations_list, key=lambda x: x["priority"] == "High", reverse=True)
        }
