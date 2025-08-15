{{ config(materialized='table', schema='silver') }}

SELECT
  id AS customer_id,
  TRIM(name) AS customer_name
FROM {{ ref('bronze_customers') }}
WHERE id IS NOT NULL
  AND name IS NOT NULL