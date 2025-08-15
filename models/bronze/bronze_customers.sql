{{ config(materialized='table', schema='bronze') }}

SELECT
  id,
  name
FROM {{ source('ecom', 'raw_customers') }}