-- Verify that securities join correctly to historical prices
-- by displaying Apple's 10 most recent records in the dataset.
SELECT
    s.symbol,
    s.security_name,
    p.trade_date,
    p.close,
    p.volume
FROM securities AS s
JOIN daily_prices AS p ON p.symbol = s.symbol
WHERE s.symbol = 'AAPL'
ORDER BY p.trade_date DESC
LIMIT 10;