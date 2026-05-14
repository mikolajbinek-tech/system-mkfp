import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="System MKFP: Enea vs Tauron", layout="wide")
st.title("⚡ Monitoring Kondycji Finansowej: Enea vs Tauron")

uploaded_files = st.sidebar.file_uploader("Wgraj sprawozdania (XLSX/CSV)", accept_multiple_files=True)

# Funkcja pomocnicza do szukania wierszy po słowach kluczowych
def find_row_by_keyword(df, keyword):
    for idx in df.index:
        if isinstance(idx, str) and keyword.lower() in idx.lower():
            return idx
    return None

def process_data(file):
    try:
        df = pd.read_csv(file, index_col=0) if file.name.endswith('.csv') else pd.read_excel(file, index_col=0)
        name = "Enea" if "enea" in file.name.lower() else "Tauron"
        
        # Dynamiczne szukanie wierszy w Twoich plikach
        row_przychody = find_row_by_keyword(df, "Przychody netto ze sprzedaży")
        row_zysk = find_row_by_keyword(df, "Zysk netto (strata netto)")
        row_aktywa = find_row_by_keyword(df, "Aktywa obrotowe")
        row_zobowiazania = find_row_by_keyword(df, "Zobowiązania Krótkoterminowe")
        row_zapasy = find_row_by_keyword(df, "Zapasy")

        if not row_przychody:
            st.error(f"Nie znaleziono wiersza z Przychodami w {file.name}")
            return None

        # Wybieramy tylko kolumny z latami
        years = [col for col in df.columns if str(col).isdigit() or '20' in str(col)]
        
        extracted = []
        for year in years:
            extracted.append({
                'Rok': year,
                'Spółka': name,
                'Przychody': pd.to_numeric(df.loc[row_przychody, year], errors='coerce'),
                'Zysk Netto': pd.to_numeric(df.loc[row_zysk, year], errors='coerce') if row_zysk else 0,
                'Aktywa Obrotowe': pd.to_numeric(df.loc[row_aktywa, year], errors='coerce') if row_aktywa else 0,
                'Zobowiazania KT': pd.to_numeric(df.loc[row_zobowiazania, year], errors='coerce') if row_zobowiazania else 0,
                'Zapasy': pd.to_numeric(df.loc[row_zapasy, year], errors='coerce') if row_zapasy else 0
            })
        return pd.DataFrame(extracted)
    except Exception as e:
        st.error(f"Błąd krytyczny w {file.name}: {e}")
        return None

if uploaded_files:
    results = []
    for f in uploaded_files:
        df_p = process_data(f)
        if df_p is not None: results.append(df_p)
    
    if results:
        full_df = pd.concat(results).sort_values('Rok')
        full_df['CR'] = (full_df['Aktywa Obrotowe'] / full_df['Zobowiazania KT']).round(2)
        full_df['QR'] = ((full_df['Aktywa Obrotowe'] - full_df['Zapasy']) / full_df['Zobowiazania KT']).round(2)
        full_df['ROS (%)'] = (full_df['Zysk Netto'] / full_df['Przychody'] * 100).round(2)

        t1, t2 = st.tabs(["Płynność (16.III)", "Rentowność (23.III)"])
        with t1:
            st.header("Płynność: Enea vs Tauron")
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.line(full_df, x='Rok', y='CR', color='Spółka', markers=True, title="Wskaźnik Bieżący"))
            c2.plotly_chart(px.line(full_df, x='Rok', y='QR', color='Spółka', markers=True, title="Wskaźnik Szybki"))
        with t2:
            st.header("Rentowność Sprzedaży (ROS)")
            st.plotly_chart(px.bar(full_df, x='Rok', y='ROS (%)', color='Spółka', barmode='group'))
