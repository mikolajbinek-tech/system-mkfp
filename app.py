import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="System MKFP: Enea vs Tauron", layout="wide")
st.title("⚡ Monitoring Kondycji Finansowej: Enea vs Tauron")

uploaded_files = st.sidebar.file_uploader("Wgraj sprawozdania (XLSX/CSV)", accept_multiple_files=True)

def find_row_by_keyword(df, keyword):
    for idx in df.index:
        if isinstance(idx, str) and keyword.lower() in idx.lower():
            return idx
    return None

def process_data(file):
    try:
        # Odczytujemy plik
        df_raw = pd.read_csv(file, header=None) if file.name.endswith('.csv') else pd.read_excel(file, header=None)
        
        # 1. Szukamy wiersza z latami (szukamy 4-cyfrowych liczb)
        header_row_idx = None
        for i, row in df_raw.iterrows():
            potential_years = [str(x).strip() for x in row if str(x).strip().isdigit() and len(str(x).strip()) == 4]
            if len(potential_years) >= 2:
                header_row_idx = i
                break
        
        if header_row_idx is None:
            return pd.DataFrame() # Zwróć pusty jeśli nie znaleziono lat

        # 2. Naprawiamy tabelę
        df_raw.columns = [str(c).strip() for c in df_raw.iloc[header_row_idx]]
        df = df_raw.iloc[header_row_idx + 1:].copy()
        df.set_index(df.columns[0], inplace=True)
        
        # Wykrywamy lata w kolumnach
        years = [c for c in df.columns if str(c).isdigit() and len(str(c)) == 4]
        name = "Enea" if "enea" in file.name.lower() else "Tauron"

        extracted = []
        for yr in years:
            extracted.append({
                'Rok': str(yr), # KLUCZOWE: Tutaj tworzymy kolumnę 'Rok'
                'Spółka': name,
                'Przychody': pd.to_numeric(df.loc[find_row_by_keyword(df, "Przychody netto ze sprzedaży") or "", yr], errors='coerce') if find_row_by_keyword(df, "Przychody netto ze sprzedaży") else 0,
                'Zysk Netto': pd.to_numeric(df.loc[find_row_by_keyword(df, "Zysk netto (strata netto)") or "", yr], errors='coerce') if find_row_by_keyword(df, "Zysk netto (strata netto)") else 0,
                'Aktywa Obrotowe': pd.to_numeric(df.loc[find_row_by_keyword(df, "Aktywa obrotowe") or "", yr], errors='coerce') if find_row_by_keyword(df, "Aktywa obrotowe") else 0,
                'Zobowiazania KT': pd.to_numeric(df.loc[find_row_by_keyword(df, "Zobowiązania Krótkoterminowe") or "", yr], errors='coerce') if find_row_by_keyword(df, "Zobowiązania Krótkoterminowe") else 0,
                'Zapasy': pd.to_numeric(df.loc[find_row_by_keyword(df, "Zapasy") or "", yr], errors='coerce') if find_row_by_keyword(df, "Zapasy") else 0
            })
        return pd.DataFrame(extracted)
    except Exception as e:
        return pd.DataFrame()

if uploaded_files:
    results = []
    for f in uploaded_files:
        processed = process_data(f)
        if not processed.empty:
            results.append(processed)
    
    if results:
        full_df = pd.concat(results, ignore_index=True)
        
        # SPRAWDZENIE: Jeśli kolumna Rok istnieje, sortujemy
        if 'Rok' in full_df.columns:
            full_df = full_df.sort_values('Rok')
            
            # Obliczenia wskaźników (Harmonogram pkt 3 i 4) 
            full_df['CR'] = (full_df['Aktywa Obrotowe'] / full_df['Zobowiazania KT']).round(2)
            full_df['QR'] = ((full_df['Aktywa Obrotowe'] - full_df['Zapasy']) / full_df['Zobowiazania KT']).round(2)
            full_df['ROS (%)'] = (full_df['Zysk Netto'] / full_df['Przychody'] * 100).round(2)

            t1, t2 = st.tabs(["Płynność (16.III)", "Rentowność (23.III)"])
            with t1:
                st.header("Analiza Płynności")
                st.plotly_chart(px.line(full_df, x='Rok', y='CR', color='Spółka', markers=True, title="Wskaźnik Bieżący"))
            with t2:
                st.header("Analiza Rentowności")
                st.plotly_chart(px.bar(full_df, x='Rok', y='ROS (%)', color='Spółka', barmode='group', title="Marża Netto (%)"))
        else:
            st.error("Błąd: Nie udało się stworzyć kolumny 'Rok'. Sprawdź pliki.")
