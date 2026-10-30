select
    order_id,
    customer_id,
    amount,
    cast(created_at as date) as order_date
from {{ source('raw', 'orders') }}
where status != 'cancelled'
