import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Matriz Estratégica de Contenido", layout="wide")
st.title("🎯 Matriz de Viralidad vs. Calidad")
st.markdown("""
Esta herramienta clasifica tu contenido en 4 cuadrantes estratégicos.
**Instrucciones:** Escribe el nombre del post y sus métricas, o pega desde Excel.
""")

# --- BARRA LATERAL (PESOS) ---
with st.sidebar:
    st.header("⚙️ Configuración de Pesos")
    st.info("Ajusta la importancia de cada interacción.")
    w_like = st.number_input("Peso Like", value=1.0)
    w_save = st.number_input("Peso Guardado (Retención)", value=3.0)
    w_share = st.number_input("Peso Compartido (Viralidad)", value=4.0)
    w_comment = st.number_input("Peso Comentario", value=2.0)

# --- FUNCIÓN DE CÁLCULO ---
def calcular_metricas(df):
    # Asegurar que las columnas numéricas sean números (ignorar la columna Nombre)
    cols_numericas = ['Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios']
    
    for col in cols_numericas:
        # Si hay celdas vacías o texto erróneo en los números, se convierte a 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 1. Calcular Score Ponderado
    df['Score'] = (df['Likes'] * w_like) + \
                  (df['Guardados'] * w_save) + \
                  (df['Compartidos'] * w_share) + \
                  (df['Comentarios'] * w_comment)
    
    # 2. Calcular Engagement Rate (ER) sobre Alcance
    df['ER'] = df.apply(lambda row: (row['Score'] / row['Alcance']) * 100 if row['Alcance'] > 0 else 0, axis=1)
    
    return df

# --- INTERFAZ DE TABLA ---
col_input, col_graph = st.columns([1, 2])

with col_input:
    st.subheader("1. Carga de Datos")
    
    # Plantilla con columna de NOMBRE
    data_inicial = {
        'Nombre del Post': ['Reel Gatos', 'Carrusel Tips', 'Meme Oficina', 'Video Producto', 'Foto Equipo'],
        'Alcance': [12000, 15000, 8000, 25000, 10000],
        'Likes': [300, 450, 150, 800, 200],
        'Guardados': [20, 45, 10, 100, 15],
        'Compartidos': [5, 20, 2, 50, 3],
        'Comentarios': [8, 15, 3, 60, 5]
    }
    df_template = pd.DataFrame(data_inicial)
    
    # Configuración de columnas para la tabla editable
    column_config = {
        "Nombre del Post": st.column_config.TextColumn(
            "Nombre / Etiqueta",
            help="Escribe un nombre para identificar el post en el gráfico",
            required=True
        )
    }
    
    st.caption("Orden columnas: **Nombre** | Alcance | Likes | Guardados | Compartidos | Comentarios")
    edited_df = st.data_editor(
        df_template, 
        num_rows="dynamic", 
        height=400,
        column_config=column_config
    )
    
    boton_analizar = st.button("🚀 GENERAR MATRIZ", type="primary")

# --- MOTOR DE ANÁLISIS ---
with col_graph:
    if boton_analizar:
        if edited_df.empty:
            st.error("⚠️ La tabla está vacía.")
        else:
            try:
                # Procesar dataframe
                df = calcular_metricas(edited_df.copy())
                
                # Calcular Medianas (Líneas de corte)
                mediana_alcance = df['Alcance'].median()
                mediana_er = df['ER'].median()

                # Clasificación de Cuadrantes
                def clasificar(row):
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
                    # AHORA EL TOOLTIP INCLUYE EL NOMBRE
                    tooltip=['Nombre del Post', 'Categoria', 'Alcance', 'ER', 'Likes', 'Guardados']
                )

                # Puntos
                points = base.mark_circle(size=150).encode(
                    color=alt.Color('Categoria', legend=alt.Legend(orient='bottom', title="Clasificación")),
                    opacity=alt.value(0.9)
                )
                
                # Texto de los nombres sobre los puntos (opcional, puede saturar si son muchos)
                text = base.mark_text(
                    align='left',
                    baseline='middle',
                    dx=10,
                    fontSize=10,
                    color='white' # Oculto por defecto, visible si cambias color
                ).encode(text='Nombre del Post')

                # Líneas de referencia
                rule_x = alt.Chart(pd.DataFrame({'x': [mediana_alcance]})).mark_rule(color='red', strokeDash=[3,3]).encode(x='x')
                rule_y = alt.Chart(pd.DataFrame({'y': [mediana_er]})).mark_rule(color='red', strokeDash=[3,3]).encode(y='y')
                
                st.altair_chart(points + rule_x + rule_y, use_container_width=True)

                # --- TABLAS DE RESULTADOS ---
                st.divider()
                st.markdown("### 📋 Análisis Detallado")
                
                t1, t2 = st.tabs(["💎 Ganadores", "⚠️ A Corregir"])
                
                with t1:
                    st.success("Posts que funcionaron por encima de la media.")
                    ganadores = df[df['Categoria'].str.contains('UNICORNIO|JOYA')]
                    st.dataframe(ganadores[['Nombre del Post', 'Categoria', 'Alcance', 'ER']], hide_index=True)
                
                with t2:
                    st.warning("Posts que desgastaron a la audiencia

