{{ config(materialized='table', schema='silver') }}

SELECT
  id AS supplier_id,
  TRIM(name) AS supplier_name,
  cost AS supplier_cost,
  perishable AS is_perishable,
  sku AS product_sku
FROM {{ ref('bronze_suppliers') }}
WHERE id IS NOT NULL
  AND sku IS NOT NULL