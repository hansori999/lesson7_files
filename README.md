# E-Commerce Sales Analysis

A refactored exploratory data analysis framework for e-commerce sales data.
Provides a configurable notebook analysis with reusable Python modules, and a
Streamlit dashboard for interactive exploration.

## Project Structure

```
lesson7_files/
├── dashboard.py              # Interactive Streamlit dashboard
├── EDA_Refactored.ipynb      # Main analysis notebook
├── data_loader.py            # Data loading and processing module
├── business_metrics.py       # Business metrics calculation module
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── ecommerce_data/           # Data directory
    ├── orders_dataset.csv
    ├── order_items_dataset.csv
    ├── products_dataset.csv
    ├── customers_dataset.csv
    ├── order_reviews_dataset.csv
    └── order_payments_dataset.csv
```

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify all CSV files are present in the `ecommerce_data/` directory.

## Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard opens at `http://localhost:8501` and includes:

- **Header** — title and a global date-range filter (defaults to full year 2023)
- **KPI Row** — Total Revenue, Monthly Growth, Avg Order Value, Total Orders with
  year-over-year trend indicators (green = positive, red = negative)
- **Charts (2 × 2)**
  - Revenue Trend — current period (solid) vs prior year (dashed), grid lines,
    compact Y-axis labels ($300K / $2M)
  - Top 10 Categories — horizontal bar chart with blue gradient, sorted descending
  - Revenue by State — US choropleth map, blue gradient
  - Review Score by Delivery Time — average score per delivery-speed bucket
- **Bottom Row** — Average Delivery Time with trend indicator; Review Score with
  star rating and subtitle

All charts update automatically when the date range filter changes.

## Running the Notebook

```bash
jupyter notebook EDA_Refactored.ipynb
```

### Configuring the Analysis

Open `EDA_Refactored.ipynb` and edit the configuration cell near the top:

```python
ANALYSIS_YEAR    = 2023   # Primary year to analyze
COMPARISON_YEAR  = 2022   # Year to compare against
ANALYSIS_MONTH   = None   # None for full year, or 1-12 for a specific month
DATA_DIR         = 'ecommerce_data'
```

Run all cells to regenerate the full analysis for the chosen period.

## Module Reference

### data_loader.py

Functions for loading and processing the raw CSV data.

```python
from data_loader import (
    load_all_datasets,
    build_sales_data,
    filter_delivered_orders,
    filter_by_period,
    add_delivery_speed,
    categorize_delivery_speed,
)

datasets  = load_all_datasets('ecommerce_data')
sales     = build_sales_data(datasets['orders'], datasets['order_items'])
delivered = filter_delivered_orders(sales)
period    = filter_by_period(delivered, year=2023, month=None)
```

### business_metrics.py

Functions for computing business KPIs from a sales DataFrame.

```python
from business_metrics import (
    calculate_total_revenue,
    calculate_revenue_growth,
    calculate_monthly_revenue,
    calculate_monthly_growth,
    calculate_average_order_value,
    calculate_order_count,
    calculate_category_revenue,
    calculate_state_revenue,
    calculate_review_score_distribution,
    calculate_average_review_score,
    calculate_delivery_review_correlation,
    calculate_average_delivery_time,
    calculate_order_status_distribution,
    summarize_period_metrics,
)

revenue = calculate_total_revenue(period_sales)
growth  = calculate_revenue_growth(revenue_2023, revenue_2022)
summary = summarize_period_metrics(period_sales, year=2023)
```

## Key Metrics

| Metric | Description |
|--------|-------------|
| Total Revenue | Sum of item prices for delivered orders |
| Revenue Growth | Year-over-year percentage change |
| Average Order Value (AOV) | Mean total value per unique order |
| Monthly Growth | Month-over-month revenue percentage change |
| Category Revenue | Revenue breakdown by product category |
| State Revenue | Revenue breakdown by US state |
| Review Score | Average customer rating (1-5) |
| Delivery Time | Average days from order placement to delivery |
