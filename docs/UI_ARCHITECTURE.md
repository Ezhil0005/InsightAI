# UI Architecture - InsightAI Platform

This document describes the design elements, UI architecture, visual layouts, and styling parameters used in the **InsightAI** platform.

---

## 🎨 Design Theme & Styles

InsightAI features a custom design tailored for corporate business users. Key elements include:
- **Typography**: Outfit font family (Google Fonts: 300, 400, 500, 600, 700, 800 weights) injected globally via CSS.
- **Header Gradient**: A clean blue gradient background text styling:
  `background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);`
- **Glassmorphism Metrics Cards**: Clean white container blocks with soft drop-shadow boundaries and border-top color-coding:
  `box-shadow: 0 4px 20px -2px rgba(50, 50, 93, 0.08), 0 2px 8px -1px rgba(0, 0, 0, 0.04);`
- **Hover Micro-Animations**: Card elements translate upward by `4px` with transition durations of `0.3s` to encourage interaction.
- **Enterprise Dark Theme Landing**: Ingestion hero blocks are styled with slate-dark parameters matching enterprise analytics platforms like Microsoft Fabric and Salesforce Tableau:
  `background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);`

---

## 📈 Visual Layouts & Charting Architecture

Interactive analytics dashboards leverage Plotly Express and Graph Objects for maximum details and custom styling:
1. **Donut Charts**: Render sentiment breakdown ratios with a color map:
   - *Positive*: Green (`#10B981`)
   - *Negative*: Red (`#EF4444`)
   - *Neutral*: Grey (`#6B7280`)
2. **Bar Projections**: Rating distributions and Churn Risk buckets use HSL color scales.
3. **Forecasting Charts**: Incorporate dual line traces (Solid Blue for actuals, Dashed Red for regression forecasts) to show mathematical trends.
4. **Hierarchical Treemaps**: Sized by average impact score and colored by mean customer churn risk, mapping operational root causes.
5. **Bubble priority grids**: Display category volume vs. churn risk vs. business impact.

---

## 📋 KPI Components

Unified metric containers displayed throughout the pages:
- **Business Health Score (0-100)**: Displayed on Landing, Sidebar, and Action centers. Status levels match color thresholds.
- **Total Ingested Volume**: Total rows count in active dataset session.
- **Avg Churn Risk %**: Predictive percentage metric.
- **Avg Business Impact Score**: Metric indexing service disruptions.
