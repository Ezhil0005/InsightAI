# Strategic Scenario Engine Specification

The **Strategic Scenario Engine** allows business leaders to model simulated outcomes of key operational decisions.

## Presets & Multipliers

The engine provides four standard business strategy simulations:

1. **Increase Support Team by 15%**
   - *Target Category*: Staff/Support
   - *Complaint Reduction*: 50%
   - *Impact*: Lowers Support churn, increases response speed, and mitigates Support priority indexes.

2. **Improve Delivery Performance by 25%**
   - *Target Category*: Delivery
   - *Complaint Reduction*: 40%
   - *Impact*: Uplifts Delivery satisfaction, mitigates leakage issues, and recovers logistics revenue.

3. **Reduce Payment Failures by 30%**
   - *Target Category*: Billing
   - *Complaint Reduction*: 60%
   - *Impact*: Reduces checkout billing failures and bypasses payment timeouts.

4. **Improve App Stability by 20%**
   - *Target Category*: App Bug
   - *Complaint Reduction*: 50%
   - *Impact*: Resolves checkout crashes and UI loading lag.

## Logic & Projections

For the selected scenario:
- **Rating Uplift**: Mapped category complaints having ratings $< 5$ are artificially shifted by $+1$ (capped at 5) to model customer satisfaction recovery.
- **Sentiment Conversions**: A percentage of negative reviews matching the category is converted to `Neutral` or `Positive`.
- **KPI Recalculation**: The engine re-runs the calculations for CSI, Churn, Revenue Risk, and Business Health on the modified dataset to output deltas.
