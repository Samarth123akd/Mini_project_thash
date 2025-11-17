-- Create a view with ML model features from processed orders
-- This provides the same 6 features used in training:
-- items_count, total_price, total_freight, avg_item_price, payment_value, payment_installments

CREATE OR REPLACE VIEW etl.model_features AS
SELECT
  order_id,
  CAST(item_count AS INTEGER) AS items_count,
  CAST(total_amount AS NUMERIC) AS total_price,
  -- Placeholder for total_freight (not in processed CSV, set to 0)
  0.0 AS total_freight,
  -- avg_item_price = total_amount / item_count
  CASE 
    WHEN CAST(item_count AS INTEGER) > 0 THEN CAST(total_amount AS NUMERIC) / CAST(item_count AS INTEGER)
    ELSE 0.0
  END AS avg_item_price,
  -- Placeholder for payment_value (assume same as total_amount for now)
  CAST(total_amount AS NUMERIC) AS payment_value,
  -- Placeholder for payment_installments (default to 1)
  1 AS payment_installments,
  -- Additional useful columns
  customer_id,
  order_status,
  order_purchase_timestamp,
  CAST(customer_lifetime_value AS NUMERIC) AS customer_lifetime_value,
  CAST(avg_order_value AS NUMERIC) AS avg_order_value,
  CAST(order_frequency AS NUMERIC) AS order_frequency
FROM etl.orders_processed
WHERE order_status = 'delivered';  -- Only use completed orders for modeling
