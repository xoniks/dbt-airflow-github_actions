{{ config(materialized='table', schema='bronze') }}

SELECT
  id,
  name,
  cost,
  perishable,
  sku
FROM {{ source('ecom', 'raw_suppliers') }}