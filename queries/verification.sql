-- queries/verification.sql
-- Checks used to verify the chatbot's answers against the real database.
-- Run them all:  sqlite3 -header -column delivery.db < queries/verification.sql
-- 1. Total number of orders
SELECT '1. Total orders' AS check_name;
SELECT *
FROM orders;
-- 2. Restaurant with the slowest average delivery time (delivered orders only)
-- JOIN links each order to its restaurant by matching restaurant_id with the restaurant's id
SELECT '2. Slowest restaurant' AS check_name;
SELECT r.name,
    ROUND(AVG(o.delivery_minutes), 1) AS avg_minutes
FROM orders o
    JOIN restaurants r ON r.id = o.restaurant_id
WHERE o.status = 'delivered'
GROUP BY r.name -- one result row per restaurant
ORDER BY avg_minutes DESC -- slowest first
LIMIT 1;
-- keep only the top row
-- 3. Cancellation rate by city, as a percentage
-- (o.status = 'cancelled') is 1 for cancelled orders and 0 otherwise, so SUM counts them
SELECT '3. Cancellation rate by city' AS check_name;
SELECT r.city,
    ROUND(
        100.0 * SUM(o.status = 'cancelled') / COUNT(*),
        1
    ) AS cancel_percent
FROM orders o
    JOIN restaurants r ON r.id = o.restaurant_id
GROUP BY r.city;
-- 4. Driver with the highest total tips
SELECT '4. Top driver by tips' AS check_name;
SELECT d.name,
    SUM(o.tip) AS total_tips
FROM orders o
    JOIN drivers d ON d.id = o.driver_id
GROUP BY d.name
ORDER BY total_tips DESC
LIMIT 1;
-- 5. Average order value for delivered orders
SELECT '5. Average order value' AS check_name;
SELECT ROUND(AVG(order_value), 2) AS avg_order_value
FROM orders
WHERE status = 'delivered';
-- 6. Follow-up check: slowest restaurant in Leeds only
SELECT '6. Slowest restaurant in Leeds' AS check_name;
SELECT r.name,
    ROUND(AVG(o.delivery_minutes), 1) AS avg_minutes
FROM orders o
    JOIN restaurants r ON r.id = o.restaurant_id
WHERE o.status = 'delivered'
    AND r.city = 'Leeds'
GROUP BY r.name
ORDER BY avg_minutes DESC
LIMIT 1;