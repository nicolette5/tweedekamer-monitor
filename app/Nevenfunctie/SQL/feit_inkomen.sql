SELECT
    nf.id AS nevenfunctie_id,
    nf.persoon_id,
    fz.fractie_id,
    ink.jaar as jaar_id,
    CASE
        WHEN LOWER(ink.frequentie) LIKE '%maand%' THEN ink.bedrag * 12
        WHEN LOWER(ink.frequentie) LIKE '%dag%'
          OR LOWER(ink.frequentie) LIKE '%Vrije invoer%'  THEN ink.bedrag * 4
        ELSE ink.bedrag
    END AS bedrag
FROM silver.persoon_nevenfunctie_inkomsten ink
JOIN silver.persoon_nevenfunctie nf
  ON nf.id = ink.persoon_nevenfunctie_id
LEFT JOIN silver.fractie_zetel_persoon zp
  ON zp.persoon_id = nf.persoon_id
 AND ink.jaar BETWEEN YEAR(zp.van) AND COALESCE(YEAR(zp.tot_en_met), 9999)
LEFT JOIN silver.fractie_zetel fz
  ON fz.id = zp.fractie_zetel_id
WHERE ink.bedrag > 0
  AND ink.jaar >= 2015 AND ink.jaar <= 2026


