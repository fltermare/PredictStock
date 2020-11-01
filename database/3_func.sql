CREATE FUNCTION get_stock_history(s VARCHAR)
    RETURNS TABLE (
        date DATE,
        close REAL,
        stock_code VARCHAR
    )
AS $$
BEGIN
    RETURN QUERY
        SELECT history.date, history.close, history.stock_code
        FROM history
        WHERE history.stock_code = s
        ORDER BY history.date;
END; $$
LANGUAGE 'plpgsql';