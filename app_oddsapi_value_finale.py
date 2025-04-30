
import streamlit as st
import requests
import pandas as pd
from config_oddsapi import API_KEY, REGION

st.title("Value Bet Finder – The Odds API (1X2 e Over/Under)")

MARKETS = {
    "1X2": "h2h",
    "Over/Under 2.5": "totals"
}

def equalizza_quota(quota, mercato):
    return round(quota * 0.94, 2) if mercato == "h2h" else round(quota * 0.93, 2)

def calcola_ev(prob, quota):
    return round(prob * quota - 1, 3)

def scarica_quote(market="h2h", sport="soccer_epl"):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?regions={REGION}&markets={market}&oddsFormat=decimal&apiKey={API_KEY}"
    res = requests.get(url)
    if res.status_code != 200:
        return [], res.status_code
    return res.json(), 200

def trova_value_bet(sport, market):
    data, code = scarica_quote(market, sport)
    risultato = []
    if code != 200 or not data:
        return risultato

    for match in data:
        try:
            bookmaker = match['bookmakers'][0]
            outcomes = bookmaker['markets'][0]['outcomes']
            for outcome in outcomes:
                quota = equalizza_quota(outcome['price'], market)
                prob_stimata = 1 / quota if quota > 0 else 0
                ev = calcola_ev(prob_stimata, quota)
                value_label = "Sì" if ev > 0 else "No"
                risultato.append({
                    "Data": match["commence_time"][:10],
                    "Casa": match["home_team"],
                    "Ospite": [t for t in match["teams"] if t != match["home_team"]][0],
                    "Mercato": market,
                    "Giocata": outcome["name"],
                    "Quota eq": quota,
                    "Probabilità stimata": round(prob_stimata, 2),
                    "Value Bet (EV)": ev,
                    "Value Bet?": value_label
                })
        except:
            continue
    return risultato

campionati = {
    "Premier League": "soccer_epl",
    "Serie A": "soccer_italy_serie_a"
}
campionato = st.selectbox("Seleziona campionato", list(campionati.keys()))
sport_key = campionati[campionato]

tipo_mercato = st.radio("Tipo di mercato", list(MARKETS.keys()))
dati = trova_value_bet(sport_key, MARKETS[tipo_mercato])

if dati:
    st.success(f"{len(dati)} quote trovate.")
    df = pd.DataFrame(dati).sort_values("Value Bet (EV)", ascending=False)
    st.dataframe(df.head(25))
else:
    st.warning("Nessuna value bet trovata nel campionato selezionato.")

# Bottone globale per tutte le leghe
if st.button("Scopri le 25 migliori value bet su tutti i campionati"):
    tutti_sport = ["soccer_epl", "soccer_italy_serie_a", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_france_ligue_one"]
    risultato_globale = []
    for sport in tutti_sport:
        for market in MARKETS.values():
            risultato_globale.extend(trova_value_bet(sport, market))
    if risultato_globale:
        df_top = pd.DataFrame(risultato_globale).sort_values("Value Bet (EV)", ascending=False).head(25)
        st.subheader("Top 25 Value Bet Globali (anche EV < 0)")
        st.dataframe(df_top)
    else:
        st.warning("Nessuna quota disponibile.")
