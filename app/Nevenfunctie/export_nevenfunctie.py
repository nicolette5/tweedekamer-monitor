from pathlib import Path
import duckdb

map_hier = Path(__file__).resolve().parent                     # de map van dit script (eda)
database = Path(r"C:\Users\henkl\tweedekamer.duckdb")          # het echte pad van de database
connection = duckdb.connect(str(database), read_only=True)

data_map = map_hier / "data"
data_map.mkdir(exist_ok=True)

sql_map = map_hier / "sql"
bestanden = sorted(sql_map.glob("*.sql"))
print("Database:", database, "| bestaat:", database.exists())
print(f"{len(bestanden)} SQL-bestanden gevonden in {sql_map}")

for sql_bestand in bestanden:
    df = connection.execute(sql_bestand.read_text(encoding="utf-8")).fetchdf()
    df.to_csv(data_map / f"{sql_bestand.stem}.csv", index=False)
    print(f"{sql_bestand.stem}: {len(df)} rijen opgeslagen")