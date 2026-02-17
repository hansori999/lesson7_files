"""
Business Metrics Module for E-Commerce Analytics
=================================================

This module provides documented, reusable functions for computing the key
business metrics used in the sales analysis notebook.

Metric categories:
    Revenue       : Total revenue, YoY growth, monthly trend, AOV
    Orders        : Order count, order count growth
    Product       : Revenue breakdown by product category
    Geographic    : Revenue breakdown by US state
    Customer      : Review score distribution, delivery-review correlation,
                    average delivery time, order status distribution
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Revenue metrics
# ---------------------------------------------------------------------------


def calculate_total_revenue(sales_data):
    """Sum the 'price' column to get total revenue.

    Args:
        sales_data (pd.DataFrame): Sales data with a 'price' column.

    Returns:
        float: Total revenue in USD.
    """
    return sales_data["price"].sum()


def calculate_revenue_growth(current_revenue, previous_revenue):
    """Compute the percentage change in revenue between two periods.

    Args:
        current_revenue (float) : Revenue for the period being analysed.
        previous_revenue (float): Revenue for the comparison period.

    Returns:
        float: Growth rate as a decimal (e.g., 0.05 means +5%).
               Returns float('nan') if previous_revenue is zero.
    """
    if previous_revenue == 0:
        return float("nan")
    return (current_revenue - previous_revenue) / previous_revenue


def calculate_monthly_revenue(sales_data):
    """Aggregate revenue by calendar month.

    Args:
        sales_data (pd.DataFrame): Sales data with 'price' and 'month' columns.

    Returns:
        pd.Series: Revenue per month, indexed by month number (1-12).
    """
    return sales_data.groupby("month")["price"].sum()


def calculate_monthly_growth(sales_data):
    """Compute month-over-month revenue growth for the given dataset.

    Uses pct_change() on the monthly revenue series, so the first month
    will always have NaN.

    Args:
        sales_data (pd.DataFrame): Sales data with 'price' and 'month' columns.

    Returns:
        pd.Series: MoM growth rates (as decimals) indexed by month number.
    """
    monthly_rev = calculate_monthly_revenue(sales_data)
    return monthly_rev.pct_change()


# ---------------------------------------------------------------------------
# Order metrics
# ---------------------------------------------------------------------------


def calculate_average_order_value(sales_data):
    """Calculate the average total value per unique order.

    Items belonging to the same order are summed before averaging.

    Args:
        sales_data (pd.DataFrame): Sales data with 'order_id' and 'price'.

    Returns:
        float: Average order value in USD.
    """
    return sales_data.groupby("order_id")["price"].sum().mean()


def calculate_order_count(sales_data):
    """Count the number of distinct orders in the dataset.

    Args:
        sales_data (pd.DataFrame): Sales data with an 'order_id' column.

    Returns:
        int: Number of unique orders.
    """
    return sales_data["order_id"].nunique()


# ---------------------------------------------------------------------------
# Product metrics
# ---------------------------------------------------------------------------


def calculate_category_revenue(sales_data, products):
    """Compute total revenue per product category, sorted descending.

    Args:
        sales_data (pd.DataFrame): Sales data with 'product_id' and 'price'.
        products (pd.DataFrame)  : Products catalog with 'product_id' and
                                   'product_category_name'.

    Returns:
        pd.Series: Revenue per category, sorted from highest to lowest.
    """
    merged = pd.merge(
        left=products[["product_id", "product_category_name"]],
        right=sales_data[["product_id", "price"]],
        on="product_id",
    )
    return (
        merged.groupby("product_category_name")["price"]
        .sum()
        .sort_values(ascending=False)
    )


# ---------------------------------------------------------------------------
# Geographic metrics
# ---------------------------------------------------------------------------


def calculate_state_revenue(sales_data, orders, customers):
    """Compute total revenue per US state, sorted descending.

    Joins sales_data -> orders -> customers to obtain the customer state
    for each order item.

    Args:
        sales_data (pd.DataFrame): Sales data with 'order_id' and 'price'.
        orders (pd.DataFrame)    : Orders data with 'order_id' and 'customer_id'.
        customers (pd.DataFrame) : Customers data with 'customer_id' and
                                   'customer_state'.

    Returns:
        pd.DataFrame: Columns ['customer_state', 'price'], sorted descending
                      by revenue.
    """
    with_customer = pd.merge(
        left=sales_data[["order_id", "price"]],
        right=orders[["order_id", "customer_id"]],
        on="order_id",
    )
    with_state = pd.merge(
        left=with_customer,
        right=customers[["customer_id", "customer_state"]],
        on="customer_id",
    )
    return (
        with_state.groupby("customer_state")["price"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


# ---------------------------------------------------------------------------
# Customer experience metrics
# ---------------------------------------------------------------------------


def calculate_review_score_distribution(sales_data, reviews):
    """Calculate the proportion of each review score for the given orders.

    Only reviews that belong to orders present in sales_data are included.

    Args:
        sales_data (pd.DataFrame): Sales data with 'order_id' column.
        reviews (pd.DataFrame)   : Reviews data with 'order_id' and
                                   'review_score' columns.

    Returns:
        pd.Series: Proportion of each score (1-5), indexed by score,
                   sorted ascending.
    """
    order_ids = sales_data["order_id"].unique()
    relevant = reviews[reviews["order_id"].isin(order_ids)]
    return relevant["review_score"].value_counts(normalize=True).sort_index()


def calculate_average_review_score(sales_data, reviews):
    """Calculate the mean review score for the given orders.

    Args:
        sales_data (pd.DataFrame): Sales data with 'order_id' column.
        reviews (pd.DataFrame)   : Reviews data with 'order_id' and
                                   'review_score' columns.

    Returns:
        float: Mean review score on a 1-5 scale.
    """
    order_ids = sales_data["order_id"].unique()
    relevant = reviews[reviews["order_id"].isin(order_ids)]
    return relevant["review_score"].mean()


def calculate_delivery_review_correlation(sales_data_with_speed, reviews):
    """Calculate average review score grouped by delivery speed category.

    Requires 'delivery_speed_days' and 'delivery_time' columns in
    sales_data_with_speed (add them with add_delivery_speed() and
    categorize_delivery_speed() from data_loader).

    Args:
        sales_data_with_speed (pd.DataFrame): Sales data containing
            'order_id', 'delivery_speed_days', and 'delivery_time'.
        reviews (pd.DataFrame): Reviews data with 'order_id' and
            'review_score'.

    Returns:
        pd.DataFrame: Columns ['delivery_time', 'review_score'] with one
                      row per delivery category.
    """
    merged = sales_data_with_speed.merge(reviews[["order_id", "review_score"]])
    per_order = merged[
        ["order_id", "delivery_speed_days", "delivery_time", "review_score"]
    ].drop_duplicates()
    return (
        per_order.groupby("delivery_time")["review_score"].mean().reset_index()
    )


def calculate_average_delivery_time(sales_data_with_speed):
    """Calculate the mean delivery time in days.

    Args:
        sales_data_with_speed (pd.DataFrame): Sales data with a
            'delivery_speed_days' column (added by add_delivery_speed()).

    Returns:
        float: Mean delivery time in days.
    """
    return sales_data_with_speed["delivery_speed_days"].mean()


def calculate_order_status_distribution(orders, year):
    """Calculate the proportion of each order status for a given year.

    Args:
        orders (pd.DataFrame): Orders data with 'order_purchase_timestamp'
                               and 'order_status'.
        year (int)           : Year to filter by.

    Returns:
        pd.Series: Proportion of each order status, sorted descending.
    """
    orders_year = orders[orders["order_purchase_timestamp"].dt.year == year]
    return orders_year["order_status"].value_counts(normalize=True)


# ---------------------------------------------------------------------------
# Composite summary
# ---------------------------------------------------------------------------


def summarize_period_metrics(sales_data, year, month=None):
    """Return a dictionary with top-level KPIs for a given period.

    Args:
        sales_data (pd.DataFrame): Filtered delivered sales data for the
                                   target period.
        year (int)               : Year of the analysis period.
        month (int, optional)    : Month of the analysis period, or None
                                   for a full-year summary.

    Returns:
        dict: Keys:
            'period'          : Human-readable period label
            'total_revenue'   : Total revenue (float)
            'order_count'     : Number of unique orders (int)
            'avg_order_value' : Average order value (float)
    """
    if month is None:
        period_label = str(year)
    else:
        period_label = f"{year}-{month:02d}"

    return {
        "period": period_label,
        "total_revenue": calculate_total_revenue(sales_data),
        "order_count": calculate_order_count(sales_data),
        "avg_order_value": calculate_average_order_value(sales_data),
    }
