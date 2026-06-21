# Executive Scorecard Specification

The **Executive Scorecard** provides high-level business indicator cards for the CEO Command Center, representing the ultimate platform health metrics.

## Key Performance Indicators

### 1. Business Health Score (0-100%)
Reflects overall operational integrity. Composed of:
- **Customer Satisfaction Index (CSI)** (30% weight)
- **Customer Loyalty/Retention Index** (25% weight)
- **Operational Safety** ($100 - \text{Operational Risk}$) (25% weight)
- **Churn Mitigation** ($100 - \text{Churn Average}$) (20% weight)

### 2. Customer Satisfaction Index (CSI) (0-100%)
Calculated as rating averages scaled linearly to 100:
- $Rating = 5 \rightarrow 100\%$
- $Rating = 4 \rightarrow 75\%$
- $Rating = 3 \rightarrow 50\%$
- $Rating = 2 \rightarrow 25\%$
- $Rating = 1 \rightarrow 0\%$
For records without ratings, sentiment mapping is utilized (Positive = 85%, Neutral = 50%, Negative = 15%).

### 3. Revenue at Risk
Sum of base transaction values (₹2,500.0) weighted by the churn probability of each customer complaint.

### 4. Operational Risk Index (0-100%)
Density of complaints calculated by weighting severity values:
- *Critical*: 1.0 weight
- *High*: 0.7 weight
- *Medium*: 0.4 weight
- *Low*: 0.1 weight

### 5. Confidence Intervals
- **Forecast Confidence**: Evaluated based on historical regression fit ($R^2$ proxy).
- **AI Confidence**: Aggregated token response statistics.
- **Provider Reliability**: Average uptime and success rates of API integrations.
