import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Matriz Estratégica de Contenido", layout="wide")
st.title("🎯 Matriz de Viralidad vs. Calidad")
st.markdown("""
Esta herramienta clasifica tu contenido en 4 cuadrantes estratégicos.
**Instrucciones:** Ingresa los datos de tus últimos posts en la tabla de abajo.
""")

# --- BARRA LATERAL (PESOS) ---
with st.sidebar:
    st.header("⚙️ Configuración de Pesos")
    st.info("Ajusta la importancia de cada interacción para tu negocio.")
    w_like = st.number_input("Peso Like", value=1.0)
    w_save = st.number_input("Peso Guardado (Retención)", value=3.0)
    w_share = st.number_input("Peso Compartido (Viralidad)", value=4.0)
    w_comment = st.number_input("Peso Comentario", value=2.0)

# --- FUNCIÓN DE CÁLCULO ---
def calcular_metricas(df):
    # Asegurar que son números
    cols_numericas = ['Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios']
    for col in cols_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 1. Calcular Score Ponderado
    df['Score'] = (df['Likes'] * w_like) + \
                  (df['Guardados'] * w_save) + \
                  (df['Compartidos'] * w_share) + \
                  (df['Comentarios'] * w_comment)
    
    # 2. Calcular Engagement Rate (ER) sobre Alcance
    df['ER'] = df.apply(lambda row: (row['Score'] / row['Alcance']) * 100 if row['Alcance'] > 0 else 0, axis=1)
    
    # 3. ID para el gráfico
    df['Post_ID'] = ["Post " + str(i+1) for i in range(len(df))]
    return df

# --- INTERFAZ DE TABLA ---
col_input, col_graph = st.columns([1, 2])

with col_input:
    st.subheader("1. Carga de Datos")
    
    # Datos iniciales vacíos o de ejemplo para guiar al usuario
    data_inicial = {
        'Alcance': [12000, 15000, 8000, 25000, 10000],
        'Likes': [300, 450, 150, 800, 200],
        'Guardados': [20, 45, 10, 100, 15],
        'Compartidos': [5, 20, 2, 50, 3],
        'Comentarios': [8, 15, 3, 60, 5]
    }
    df_template = pd.DataFrame(data_inicial)
    
    # LA TABLA EDITABLE
    st.caption("Edita los valores, añade filas o pega desde Excel.")
    edited_df = st.data_editor(df_template, num_rows="dynamic", height=400)
    
    boton_analizar = st.button("🚀 GENERAR MATRIZ", type="primary")

# --- MOTOR DE ANÁLISIS ---
with col_graph:
    if boton_analizar:
        if edited_df.empty:
            st.error("⚠️ La tabla está vacía.")
        else:
            try:
                # Procesar dataframe editado
                df = calcular_metricas(edited_df.copy())
                
                # Calcular Medianas (Líneas de corte)
                mediana_alcance = df['Alcance'].median()
                mediana_er = df['ER'].median()

                # Clasificación de Cuadrantes
                def clasificar(row):
                    # Evitar errores si todo es cero
                    if row['Alcance'] == 0: return "🗑️ BASURA"
                    
                    if row['Alcance'] >= mediana_alcance and row['ER'] >= mediana_er:
                        return "💎 UNICORNIO (Viral + Calidad)"
                    elif row['Alcance'] < mediana_alcance and row['ER'] >= mediana_er:
                        return "🛡️ JOYA OCULTA (Alta Calidad)"
                    elif row['Alcance'] >= mediana_alcance and row['ER'] < mediana_er:
                        return "⚠️ CLICKBAIT (Viral, Baja Calidad)"
                    else:
                        return "🗑️ BASURA (Ni Viral ni Bueno)"

                df['Categoria'] = df.apply(clasificar, axis=1)

                # --- GRÁFICO ---
                st.subheader("2. Mapa Estratégico")
                
                # Base del gráfico
                base = alt.Chart(df).encode(
                    x=alt.X('Alcance', title='Viralidad (Alcance)'),
                    y=alt.Y('ER', title='Calidad (Engagement Rate %)'),
                    tooltip=['Post_ID', 'Categoria', 'Alcance', 'ER', 'Likes', 'Guardados']
                )

                # Puntos
                points = base.mark_circle(size=120).encode(
                    color=alt.Color('Categoria', legend=alt.Legend(orient='bottom', title="Tipo de Contenido")),
                    opacity=alt.value(0.9)
                )

                # Líneas de referencia (Medianas)
                rule_x = alt.Chart(
