import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Analiza MKFP: Enea vs Tauron", layout="wide")
st.title("⚡ Monitoring Kondycji Finansowej: Enea vs Tauron")
st.markdown("Projekt MKFP 2025/2026 - Analiza Porównawcza Sektora Energetycznego")

uploaded_files = st.sidebar.file_uploader("Wgraj sprawozdania Enei i Tauronu (XLSX/CSV)", accept_multiple_files=True)

def process_data(file):
    try:
        # Odczyt danych z uwzględnieniem struktury Twoich plików
        df = pd.read_csv(file, index_col=0) if file.name.endswith('.csv') else pd.read_excel(file, index_col=0)
        
        # Wykrywanie spółki
        name = "Enea" if "enea" in file.name.lower() else "Tauron"
        
        # Mapowanie konkretnych nazw wierszy z Twoich plików
        data_map = {
            'Przychody': '    Przychody netto ze sprzedaży ',
            'Zysk Netto': '    Zysk netto (strata netto)',
            'Aktywa Obrotowe': '        Aktywa obrotowe',
            'Zobowiazania KT': '            Zobowiązania Krótkoterminowe',
            'Zapasy': '            Zapasy'
        }
        
        years = [col for col in df.columns if str(col).isdigit() or '20' in str(col)]
        
        extracted = []
        for year in years:
            extracted.append({
                'Rok': year,
                'Spółka': name,
                'Przychody': pd.to_numeric(df.loc[data_map['Przychody'], year], errors='coerce'),
                'Zysk Netto': pd.to_numeric(df.loc[data_map['Zysk Netto'], year], errors='coerce'),
                'Aktywa Obrotowe': pd.to_numeric(df.loc[data_map['Aktywa Obrotowe'], year], errors='coerce'),
                'Zobowiazania KT': pd.to_numeric(df.loc[data_map['Zobowiazania KT'], year], errors='coerce'),
                'Zapasy': pd.to_numeric(df.loc[data_map['Zapasy'], year], errors='coerce')
            })
        
        return pd.DataFrame(extracted)
    except Exception as e:
        st.error(f"Problem z plikiem {file.name}: {e}")
        return None

if uploaded_files:
    results = []
    for f in uploaded_files:
        df_p = process_data(f)
        if df_p is not None: results.append(df_p)
    
    if results:
        full_df = pd.concat(results).sort_values('Rok')
        
        # Obliczenia wskaźników
        full_df['CR'] = (full_df['Aktywa Obrotowe'] / full_df['Zobowiazania KT']).round(2)
        full_df['QR'] = ((full_df['Aktywa Obrotowe'] - full_df['Zapasy']) / full_df['Zobowiazania KT']).round(2)
        full_df['ROS (%)'] = (full_df['Zysk Netto'] / full_df['Przychody'] * 100).round(2)

        t1, t2, t3 = st.tabs(["Płynność (16.III)", "Rentowność (23.III)", "Upadłość (27.IV)"])

        with t1:
            st.header("Wskaźniki Płynności")
            c1, c2 = st.columns(2)
            c1.plotly_chart(px.line(full_df, x='Rok', y='CR', color='Spółka', markers=True, title="Bieżąca (CR)"))
            c2.plotly_chart(px.line(full_df, x='Rok', y='QR', color='Spółka', markers=True, title="Szybka (QR)"))

        with t2:
            st.header("Rentowność Sprzedaży")
            st.plotly_chart(px.bar(full_df, x='Rok', y='ROS (%)', color='Spółka', barmode='group'))
            
        with t3:
            st.header("Analiza Zagrożenia Upadłością")
            st.info("Zgodnie z harmonogramem (27.IV), modele zostaną zaimplementowane po konsultacjach.")
