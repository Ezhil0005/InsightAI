# Business Intelligence Layer Documentation

The **Business Intelligence (BI) Layer** in InsightAI acts as the central engine for computing customer experience and operational performance metrics.

## Key Calculations

1. **Customer Satisfaction Index (CSI)**: Mapped from rating averages (linear scale to 100) or sentiment fallback categories.
2. **Revenue Risk**: Base transactional value ₹2,500 multiplied by churn risk percentage.
3. **Customer Loyalty Score**: Weighted combination of current satisfaction (CSI) and retention probability.
4. **Operational Risk Score**: Severity weight density index.
5. **Category Risk Index**: Normalizes risk exposure specifically for Delivery, Billing, App Bug, and Support.

## Architecture & Data Flow
1. **Source Data**: SQLite feedback records.
2. **Transformation**: Computed dynamically via `src/business_metrics.py`.
3. **Downstream Consumables**: CEO dashboard metrics, executive recommendations, and Plotly visualization charts.
