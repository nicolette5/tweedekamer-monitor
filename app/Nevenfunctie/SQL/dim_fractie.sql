SELECT id AS fractie_id, naam_nl AS fractienaam, datum_actief AS opgericht_datum,
    CASE
        WHEN LOWER(f.naam_nl) LIKE '%groenlinks%'
        OR LOWER (f.naam_nl) LIKE '%partij van de arbeid%'
        OR LOWER(f.naam_nl) LIKE '%progressief nederland%' THEN 'GroenLinks / Progressief Nederland'
    ELSE f.naam_nl
    END AS fractienaam
FROM silver.fractie f

