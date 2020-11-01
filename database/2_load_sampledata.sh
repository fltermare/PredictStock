#/usr/bin/bash
sleep 5;
for code in $(ls ./data);
do
    echo [$code.TW]
    for filename in $(ls /data/$code/*.csv);
    do
        psql -U $POSTGRES_USER -d $POSTGRES_DB -c "COPY tmp FROM '$filename' DELIMITER ',' CSV HEADER;" ;
        psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER TABLE tmp ADD COLUMN stock_code VARCHAR(20) NOT NULL DEFAULT '$code.TW';" ;
        psql -U $POSTGRES_USER -d $POSTGRES_DB -c "INSERT INTO stock(stock_code) SELECT DISTINCT stock_code FROM tmp on conflict (stock_code) do nothing;";
        psql -U $POSTGRES_USER -d $POSTGRES_DB -c "INSERT INTO history SELECT * FROM tmp;";
        psql -U $POSTGRES_USER -d $POSTGRES_DB -c "TRUNCATE TABLE tmp;";
        psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER TABLE tmp DROP COLUMN stock_code;";
        echo $filename
    done
done
