CREATE TABLE stock (
    stock_code          VARCHAR(20) PRIMARY KEY,
    name                VARCHAR(30),
    first_record_date   DATE,
    last_record_date    DATE
);

CREATE TABLE history (
    date                DATE NOT NULL,
    volume              BIGINT NOT NULL,
    turnover            BIGINT,
    open                REAL NOT NULL,
    high                REAL NOT NULL,
    low                 REAL NOT NULL,
    close               REAL NOT NULL,
    change              REAL,
    transactions        BIGINT,
    stock_code          VARCHAR(20) REFERENCES stock(stock_code),
    PRIMARY KEY         (stock_code, date)
);

CREATE TABLE tmp (
    date                DATE NOT NULL,
    volume              BIGINT NOT NULL,
    turnover            BIGINT,
    open                REAL NOT NULL,
    high                REAL NOT NULL,
    low                 REAL NOT NULL,
    close               REAL NOT NULL,
    change              REAL,
    transactions        BIGINT
);
