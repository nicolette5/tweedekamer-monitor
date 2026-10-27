from pathlib import Path
 
import pandas as pd
import streamlit as st
import altair as alt
 
# ---------------------------------------------------------------------------
# Aannames: pas deze namen aan als jouw CSV's of kolommen anders heten
# ---------------------------------------------------------------------------
DATA = Path(__file__).parent / "data"
 
BESTAND_FEIT = "feit_inkomen.csv" 
BESTAND_PERSOON = "dim_persoon.csv"
BESTAND_NEVENFUNCTIE = "dim_nevenfunctie.csv"
BESTAND_FRACTIE = "dim_fractie.csv"
 
#PERSOON_NAAM = "voornamen" + " " + "achternaam"  # kolom in DIM_PERSOON met de naam van de persoon
 
st.set_page_config(page_title="Nevenfuncties en inkomsten", layout="wide")
st.title("Nevenfuncties inkomsten")
st.write("De gegevens zijn afkomstig van de Tweede Kamer en zijn openbaar beschikbaar." 
        " Nevenfunctie is dat ze naast hun werk als politicus ook een andere betaalde functie hebben."
        " In deze dashboard zijn alleen de gegevens weergeven van politici die een betaalde nevenfunctie hebben."
        " Links van het dashboard kun je het jaar en de fractie selecteren. De grafieken en tabellen worden automatisch aangepast op basis van de selectie." )

# ---------------------------------------------------------------------------
# Data inlezen
# ---------------------------------------------------------------------------
@st.cache_data
def laad(bestand):
    return pd.read_csv(DATA / bestand)
 
 
feit = laad(BESTAND_FEIT)
persoon = laad(BESTAND_PERSOON)
nevenfunctie = laad(BESTAND_NEVENFUNCTIE)
fractie = laad(BESTAND_FRACTIE)
 
feit["bedrag"] = pd.to_numeric(feit["bedrag"], errors="coerce")
 
# Feit en dimensies samenvoegen
df = (
    feit.merge(
        persoon[["persoon_id", "voornamen", "achternaam"]],
        on="persoon_id",
        how="left",
    )
    .merge(fractie[["fractie_id", "fractienaam"]], on="fractie_id", how="left")
    .rename(columns={"jaar_id": "jaar"})
)

df["politicus"] = (
    df["achternaam"].fillna("").str.strip()
    + ", "
    + df["voornamen"].fillna("").str.strip()
).str.strip()
 
# Eén kleurschaal voor alle grafieken, vastgelegd VOOR het filteren
# zodat een fractie altijd dezelfde kleur houdt.
alle_fracties = sorted(df["fractienaam"].dropna().unique())
kleur_schaal = alt.Scale(domain=alle_fracties, scheme="tableau20")
# ---------------------------------------------------------------------------
# Filters (zijbalk)
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")
# Filter op jaar
jaren = sorted(df["jaar"].dropna().unique())
jaar = st.sidebar.selectbox("Jaar", ["Alle"] + jaren)
if jaar != "Alle":
    df = df[df["jaar"] == jaar]
 
# Filter op fractie
with st.sidebar.expander("Fracties", expanded=False):
    gekozen_fracties = st.multiselect(
        "Kies fracties",
        alle_fracties,
        default=alle_fracties,
        label_visibility="collapsed",
    )
df = df[df["fractienaam"].isin(gekozen_fracties)]

if df.empty:
    st.warning("Geen gegevens voor deze selectie. Pas de filters aan.")
    st.stop()
 
# ---------------------------------------------------------------------------
# Kengetallen
# ---------------------------------------------------------------------------
per_persoon = df.groupby("persoon_id")["bedrag"].sum()

def euro(x):
    return f"€ {x:,.0f}".replace(",", ".")

kolom1, kolom2, kolom3 ,kolom4= st.columns(4)
totaal = df["bedrag"].sum()
kolom1.metric("Totaal bedrag", euro(df["bedrag"].sum()))
kolom2.metric("Gemiddeld per persoon", euro(per_persoon.mean()))
kolom3.metric("Mediaan per persoon", euro(per_persoon.median()))
kolom4.metric("Aantal politici met inkomsten", f"{df['persoon_id'].nunique()}")
st.caption(
    "Het gemiddelde ligt ruim boven de mediaan: een klein aantal politici verdient "
    "veel meer dan de meeste anderen."
)
st.divider()
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Rij 1: per fractie en per jaar
# ---------------------------------------------------------------------------
links, rechts = st.columns(2)

with links:
    st.subheader("Totaal bedrag per fractie")
    per_fractie = (
        df.groupby("fractienaam", as_index=False)["bedrag"].sum()
        .sort_values("bedrag", ascending=False)
    )
    grafiek_fractie = (
        alt.Chart(per_fractie)
        .mark_bar()
        .encode(
            y=alt.Y("fractienaam:N", sort="-x", title=None, axis=alt.Axis(labelLimit=300)),
            x=alt.X("bedrag:Q", title="Totaal bedrag (€)"),
            color=alt.Color("fractienaam:N", scale=kleur_schaal, legend=None),
            tooltip=[
                alt.Tooltip("fractienaam:N", title="Fractie"),
                alt.Tooltip("bedrag:Q", title="Totaal (€)", format=",.0f"),
            ],
        )
        .properties(height=alt.Step(22))
    )
    st.altair_chart(grafiek_fractie, use_container_width=True)
    st.caption("Gesorteerd op totaalbedrag: de som van alle nevenfunctie-inkomsten van de politici in de fractie.")

with rechts:
    st.subheader("Totaal bedrag per jaar")
    per_jaar = df.groupby("jaar", as_index=False)["bedrag"].sum()
    grafiek_jaar = (
        alt.Chart(per_jaar)
        .mark_bar(color="#E63946")
        .encode(
            x=alt.X("jaar:O", title="Jaar", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("bedrag:Q", title="Totaal bedrag (€)"),
            tooltip=[
                alt.Tooltip("jaar:O", title="Jaar"),
                alt.Tooltip("bedrag:Q", title="Totaal (€)", format=",.0f"),
            ],
        )
    )
    st.altair_chart(grafiek_jaar, use_container_width=True)
    st.caption("Het laatste jaar kan onvolledig zijn, omdat inkomsten pas achteraf worden gemeld.")

st.divider()

# ---------------------------------------------------------------------------
# Rij 2: per politicus en top 10
# ---------------------------------------------------------------------------
inkomen = (
    df.groupby(["persoon_id", "politicus"], as_index=False)["bedrag"].sum()
    .rename(columns={"bedrag": "totaal_bedrag"})
    .sort_values("totaal_bedrag", ascending=False)
)

# Eén fractie per politicus: de fractie met het hoogste bedrag
dominante = (
    df.groupby(["persoon_id", "fractienaam"], as_index=False)["bedrag"].sum()
    .sort_values("bedrag", ascending=False)
    .drop_duplicates("persoon_id")[["persoon_id", "fractienaam"]]
)
inkomen = inkomen.merge(dominante, on="persoon_id", how="left")

links, rechts = st.columns([2, 2])

with links:
    st.subheader("Inkomen per politicus")
    top_n = st.slider("Aantal politici in de grafiek", 5, 30, 15)

    grafiek_inkomen = (
        alt.Chart(inkomen.head(top_n))
        .mark_bar()
        .encode(
            y=alt.Y("politicus:N", sort="-x", title=None, axis=alt.Axis(labelLimit=300)),
            x=alt.X("totaal_bedrag:Q", title="Totaal bedrag (€)", axis=alt.Axis(tickCount=5)),
            color=alt.Color(
                "fractienaam:N",
                scale=kleur_schaal,
                legend=alt.Legend(title="Fractie"),
            ),
            tooltip=[
                alt.Tooltip("politicus:N", title="Politicus"),
                alt.Tooltip("fractienaam:N", title="Fractie"),
                alt.Tooltip("totaal_bedrag:Q", title="Totaal (€)", format=",.0f"),
            ],
        )
        .properties(height=alt.Step(24))
    )
    st.altair_chart(grafiek_inkomen, use_container_width=True)
    st.caption("Gekleurd op fractie. Politici met meerdere fracties staan bij de fractie met het hoogste bedrag.")

with rechts:
    st.subheader("Top 10 hoogste inkomsten")
    st.write("De top 10 politici met de hoogste nevenfunctie-inkomsten. Het staat op volgorde van het totaalbedrag")
    top = inkomen.head(10).reset_index(drop=True)

    st.dataframe(
        top[[ "politicus", "fractienaam", "totaal_bedrag"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "politicus": st.column_config.TextColumn("Politicus", width="large"),
            "fractienaam": st.column_config.TextColumn("Fractie", width="medium"),
            "totaal_bedrag": st.column_config.NumberColumn("Totaal bedrag", format="€ %.0f"),
        },
    )

# ---------------------------------------------------------------------------
# Toelichting
# ---------------------------------------------------------------------------
with st.expander("Over deze data"):
    st.write(
        "Bedragen zijn omgerekend naar (geschatte) jaarbedragen: maandbedragen × 12 en "
        "dag- of vrije-invoerbedragen × 4. Inkomsten zijn gekoppeld aan de fractie waar de "
        "persoon in dat jaar lid van was. Alleen betaalde nevenfuncties zijn meegenomen. "
        "GroenLinks, de Partij van de Arbeid en Progressief Nederland zijn samengevoegd tot "
        "één fractie, omdat deze partijen gefuseerd zijn."
    )

