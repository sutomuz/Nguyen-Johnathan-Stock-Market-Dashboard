CREATE TABLE securities (
    symbol TEXT PRIMARY KEY,
    security_name TEXT NOT NULL,
    listing_exchange TEXT,
    market_category TEXT,
    etf TEXT,
    test_issue TEXT,
    financial_status TEXT,
    asset_type TEXT NOT NULL
        CHECK (asset_type IN ('stock', 'etf')),
    has_price_file BOOLEAN NOT NULL
);

CREATE TABLE daily_prices (
    symbol TEXT NOT NULL REFERENCES securities(symbol),
    trade_date DATE NOT NULL,
    open DOUBLE PRECISION CHECK (open > 0),
    high DOUBLE PRECISION CHECK (high > 0),
    low DOUBLE PRECISION CHECK (low > 0),
    close DOUBLE PRECISION CHECK (close > 0),
    adj_close DOUBLE PRECISION CHECK (adj_close > 0),
    volume BIGINT CHECK (volume >= 0),
    source_row INTEGER NOT NULL,
    flag_missing_numeric BOOLEAN NOT NULL,
    flag_nonpositive_price BOOLEAN NOT NULL,
    flag_invalid_adj_close BOOLEAN NOT NULL,
    flag_zero_volume BOOLEAN NOT NULL,
    flag_negative_volume BOOLEAN NOT NULL,
    valid_ohlc BOOLEAN NOT NULL,
    valid_adj_close BOOLEAN NOT NULL,
    PRIMARY KEY (symbol, trade_date)
);