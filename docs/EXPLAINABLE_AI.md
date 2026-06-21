# Explainable AI (XAI) Documentation

The **Explainable AI (XAI)** module provides transparency for customer predictions (e.g. churn risk).

## Explanation Breakdown

For any selected customer feedback record, the engine decomposes the churn risk into exact contributing driver percentages:

1. **Low Customer Rating**: Contributes up to +60 points for rating=1.
2. **Operational Category Issues**: Billing or App Bug issues contribute +15 points; Support issues contribute +8 points.
3. **Negative Sentiment Tone**: Contributes +15 points.
4. **Base Baseline**: Baseline default +5 points.

The percentages sum to exactly 100% and clearly explain to operators why a customer is classified as a churn risk.
