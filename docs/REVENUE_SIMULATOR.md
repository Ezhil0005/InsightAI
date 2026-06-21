# Revenue Impact Simulator Specification

The **Revenue Impact Simulator** in InsightAI models the financial recovery potential of addressing customer complaints in specific operational areas.

## Calculations & Formulas

### 1. Baseline Revenue at Risk
Each feedback record is assigned a baseline customer lifetime value (CLV) $V_c$ (defaulting to ₹2,500.0). The expected revenue loss/risk for a record $i$ is weighted by its churn probability $P_{churn}$:

$$R_i = V_c \times \frac{P_{churn}}{100}$$

The total baseline revenue at risk $R_{total}$ is the sum of risks across all records:

$$R_{total} = \sum_{i=1}^{N} R_i$$

### 2. Category Churn Mitigation
If complaints in a specific category (e.g., *Delivery*) are reduced by a target factor $F_{reduction}$ (e.g., 30%), the simulated churn probability for those records is scaled:

$$P'_{churn, i} = P_{churn, i} \times \left(1.0 - \frac{F_{reduction}}{100}\right)$$

### 3. Revenue Saved
The projected financial recovery $S_{recovered}$ represents the difference between baseline and simulated revenue risk:

$$S_{recovered} = R_{total} - R'_{total}$$

### 4. CSI Index Growth Estimation
Customer Satisfaction Index (CSI) growth is estimated proportionally to the category complaint volume ratio:

$$\Delta CSI = (100 - CSI_{baseline}) \times \left( \frac{N_{category}}{N_{total}} \right) \times \left( \frac{F_{reduction}}{100} \right) \times 0.6$$

### 5. Return on Investment (ROI)
We model the implementation cost $C$ at ₹15,000 per 10% reduction, scaled by the category's size ratio:

$$C = \left( \frac{F_{reduction}}{10} \times 15,000 \right) \times \left( 0.2 + 0.8 \times \frac{N_{category}}{N_{total}} \right)$$

$$ROI\% = \frac{S_{recovered}}{C} \times 100$$

## Data Flow
1. **Input**: Enriched DataFrame filtered by the chosen category.
2. **Execution**: The simulator runs on the subset, computing baseline and target-reduced churn states.
3. **Output**: Returns a summary statistics dictionary and Plotly-compatible chart data.
