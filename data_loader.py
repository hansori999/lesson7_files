"""
Data Loader Module for E-Commerce Analytics
============================================

This module handles loading, processing, and cleaning the e-commerce datasets.
It provides reusable functions for building analysis-ready DataFrames.

Datasets:
    - orders_dataset.csv         : Order-level information
    - order_items_dataset.csv    : Item-level order details
    - products_dataset.csv       : Product catalog
    - customers_dataset.csv      : Customer information
    - order_reviews_dataset.csv  : Customer reviews
    - order_payments_dataset.csv : Payment information
"""

import os
import pandas as pd

DATA_DIR = "ecommerce_data"


# ---------------------------------------------------------------------------
# Individual dataset loaders
# ---------------------------------------------------------------------------


def load_orders(data_dir=DATA_DIR):
    """Load and parse the orders dataset.

    Args:
        data_dir (str): Path to the directory containing CSV files.

    Returns:
        pd.DataFrame: Orders with all timestamp columns parsed as datetime.

    Columns:
        order_id                      : Unique order identifier
        customer_id                   : Customer identifier (per order)
        order_status                  : Fulfillment status (delivered, canceled, ...)
        order_purchase_timestamp      : Timestamp when the order was placed
        order_approved_at             : Timestamp when payment was approved
        order_delivered_carrier_date  : Timestamp when handed to carrier
        order_delivered_customer_date : Timestamp when delivered to customer
        order_estimated_delivery_date : Estimated delivery timestamp
    """
    filepath = os.path.join(data_dir, "orders_dataset.csv")
    datetime_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    df = pd.read_csv(filepath)
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])
    return df


def load_order_items(data_dir=DATA_DIR):
    """Load and parse the order items dataset.

    Args:
        data_dir (str): Path to the directory containing CSV files.

    Returns:
        pd.DataFrame: Order items with shipping_limit_date parsed as datetime.

    Columns:
        order_id            : Unique order identifier
        order_item_id       : Sequence number of the item within the order
        product_id          : Product identifier
        seller_id           : Seller identifier
        shipping_limit_date : Deadline by which seller must ship
        price               : Item price in USD
        freight_value       : Shipping cost in USD
    """
    filepath = os.path.join(data_dir, "order_items_dataset.csv")
    df = pd.read_csv(filepath)
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"])
    return df


def load_products(data_dir=DATA_DIR):
    """Load the products dataset.

    Args:
        data_dir (str): Path to the directory containing CSV files.

    Returns:
        pd.DataFrame: Products catalog.

    Columns:
        product_id                 : Unique product identifier
        product_category_name      : Category the product belongs to
        product_name_length        : Character length of the product name
        product_description_length : Character length of the description
        product_photos_qty         : Number of product photos
        product_weight_g           : Weight in grams
        product_length_cm          : Length in centimeters
        product_height_cm          : Height in centimeters
        product_width_cm           : Width in centimeters
    """
    filepath = os.path.join(data_dir, "products_dataset.csv")
    return pd.read_csv(filepath)


def load_customers(data_dir=DATA_DIR):
    """Load the customers dataset.

    Args:
        data_dir (str): Path to the directory containing CSV files.

    Returns:
        pd.DataFrame: Customers.

    Columns:
        customer_id              : Order-level customer identifier (changes per order)
        customer_unique_id       : Persistent identifier for the same person
        customer_zip_code_prefix : 5-digit ZIP code prefix
        customer_city            : City name
        customer_state           : US state abbreviation (e.g., 'CA', 'TX')
    """
    filepath = os.path.join(data_dir, "customers_dataset.csv")
    return pd.read_csv(filepath)


def load_reviews(data_dir=DATA_DIR):
    """Load and parse the order reviews dataset.

    Args:
        data_dir (str): Path to the directory containing CSV files.

    Returns:
        pd.DataFrame: Reviews with review_creation_date parsed as datetime.

    Columns:
        review_id               : Unique review identifier
        order_id                : Order this review belongs to
        review_score            : Customer rating from 1 (worst) to 5 (best)
        review_comment_title    : Short title of the review
        review_comment_message  : Full review text (may be NaN)
        review_creation_date    : Timestamp when the review was submitted
        review_answer_timestamp : Timestamp when the review was answered (may be NaN)
    """
    filepath = os.path.join(data_dir, "order_reviews_dataset.csv")
    df = pd.read_csv(filepath)
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"])
    return df


def load_all_datasets(data_dir=DATA_DIR):
    """Load all e-commerce datasets at once.

    Args:
        data_dir (str): Path to the directory containing CSV files.

    Returns:
        dict: Dictionary with keys:
            'orders'      : pd.DataFrame from load_orders()
            'order_items' : pd.DataFrame from load_order_items()
            'products'    : pd.DataFrame from load_products()
            'customers'   : pd.DataFrame from load_customers()
            'reviews'     : pd.DataFrame from load_reviews()
    """
    return {
        "orders": load_orders(data_dir),
        "order_items": load_order_items(data_dir),
        "products": load_products(data_dir),
        "customers": load_customers(data_dir),
        "reviews": load_reviews(data_dir),
    }


# ---------------------------------------------------------------------------
# Data transformation helpers
# ---------------------------------------------------------------------------


def build_sales_data(orders, order_items):
    """Merge order items with order details to create a flat sales dataset.

    Adds 'month' and 'year' columns derived from order_purchase_timestamp
    for convenient time-based filtering and grouping.

    Args:
        orders (pd.DataFrame)     : Output of load_orders().
        order_items (pd.DataFrame): Output of load_order_items().

    Returns:
        pd.DataFrame: Merged sales data with columns:
            order_id, order_item_id, product_id, price,
            order_status, order_purchase_timestamp,
            order_delivered_customer_date, month, year
    """
    sales = pd.merge(
        left=order_items[["order_id", "order_item_id", "product_id", "price"]],
        right=orders[
            [
                "order_id",
                "order_status",
                "order_purchase_timestamp",
                "order_delivered_customer_date",
            ]
        ],
        on="order_id",
    )
    sales["order_purchase_timestamp"] = pd.to_datetime(
        sales["order_purchase_timestamp"]
    )
    sales["order_delivered_customer_date"] = pd.to_datetime(
        sales["order_delivered_customer_date"]
    )
    sales["month"] = sales["order_purchase_timestamp"].dt.month
    sales["year"] = sales["order_purchase_timestamp"].dt.year
    return sales


def filter_delivered_orders(sales_data):
    """Return only rows where the order status is 'delivered'.

    Args:
        sales_data (pd.DataFrame): Output of build_sales_data().

    Returns:
        pd.DataFrame: Subset of sales_data for delivered orders (copy).
    """
    return sales_data[sales_data["order_status"] == "delivered"].copy()


def filter_by_period(sales_data, year, month=None):
    """Filter sales data to a specific year and optional month.

    Args:
        sales_data (pd.DataFrame): Sales data with 'year' and 'month' columns.
        year (int)                : Target year (e.g., 2023).
        month (int, optional)     : Target month 1-12. Pass None to include
                                    the full year.

    Returns:
        pd.DataFrame: Filtered subset (copy).
    """
    mask = sales_data["year"] == year
    if month is not None:
        mask = mask & (sales_data["month"] == month)
    return sales_data[mask].copy()


def add_delivery_speed(sales_data):
    """Add a 'delivery_speed_days' column with the number of days from
    order placement to customer delivery.

    Rows where order_delivered_customer_date is NaN will have NaN in the
    new column.

    Args:
        sales_data (pd.DataFrame): Sales data with
            'order_purchase_timestamp' and 'order_delivered_customer_date'.

    Returns:
        pd.DataFrame: Copy of sales_data with 'delivery_speed_days' added.
    """
    df = sales_data.copy()
    df["delivery_speed_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days
    return df


def categorize_delivery_speed(days):
    """Assign a human-readable delivery speed category based on elapsed days.

    Buckets:
        '1-3 days' : up to 3 days
        '4-7 days' : 4 to 7 days
        '8+ days'  : 8 days or more

    Args:
        days (int or float): Delivery time in days.

    Returns:
        str: Category label.
    """
    if days <= 3:
        return "1-3 days"
    if days <= 7:
        return "4-7 days"
    return "8+ days"
