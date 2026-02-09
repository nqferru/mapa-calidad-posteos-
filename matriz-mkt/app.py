import streamlit as st
import pandas as pd
import numpy as np
import io
import altair as alt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Matriz Estratégica de Contenido", layout="wide")
st.title("🎯 Matriz de Viralidad vs. Calidad")
st.markdown("""
Esta herramienta clasifica tu contenido en 4 cuadrantes estratégicos para la toma de decisiones.
* **Eje X:** Alcance (¿Cuánta gente lo vio?)
* **Eje Y:** Engagement Rate Ponderado (¿Qué tan bueno es el contenido?)
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
    # 1. Calcular Score Ponderado
    df['Score'] = (df['Likes'] * w_like) + \
                  (df['Guardados'] * w_save) + \
                  (df['Compartidos'] * w_share) + \
                  (df['Comentarios'] * w_comment)
    
    # 2. Calcular Engagement Rate (ER) sobre Alcance
    # Evitamos división por cero
    df['ER'] = df.apply(lambda row: (row['Score'] / row['Alcance']) * 100 if row['Alcance'] > 0 else 0, axis=1)
    
    # 3. Crear etiqueta de identificación (Post 1, Post 2...)
    df['Post_ID'] = ["Post " + str(i+1) for i in range(len(df))]
    return df

# --- INTERFAZ DE CARGA ---
col_input, col_graph = st.columns([1, 3])

with col_input:
    st.subheader("1. Datos (Excel)")
    st.markdown("**Columnas:** `Alcance` `Likes` `Guardados` `Compartidos` `Comentarios`")
    st.caption("Copia solo los números desde Excel.")
    
    texto_pegado = st.text_area("Pega aquí (Ctrl+V):", height=300,
                                placeholder="12000\t300\t20\t5\t8\n13500\t320\t25\t8\t10...")
    
    boton_analizar = st.button("🚀 GENERAR MATRIZ", type="primary")

# --- MOTOR DE ANÁLISIS ---
if boton_analizar and texto_pegado:
    try:
        # Procesar datos (robusto a espacios/tabs)
        df = pd.read_csv(io.StringIO(texto_pegado), sep=r'\s+', header=None, engine='python')
        
        # Validar columnas
        if df.shape[1] < 5:
            st.error("⚠️ Error: Faltan columnas. Asegúrate de copiar las 5 métricas.")
            st.stop()
            
        df = df.iloc[:, :5]
        df.columns = ['Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios']
        
        # Limpiar números
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('.', '')
                df[col] = pd.to_numeric(df[col])

        # Calcular todo
        df = calcular_metricas(df)
        
        # Estadísticas clave para los cuadrantes (Medianas)
        mediana_alcance = df['Alcance'].median()
        mediana_er = df['ER'].median()

        # Clasificación de Cuadrantes
        def clasificar(row):
            if row['Alcance'] >= mediana_alcance and row['ER'] >= mediana_er:
                return "💎 UNICORNIO (Viral + Calidad)"
            elif row['Alcance'] < mediana_alcance and row['ER'] >= mediana_er:
                return "🛡️ JOYA OCULTA (Alta Calidad, Bajo Alcance)"
            elif row['Alcance'] >= mediana_alcance and row['ER'] < mediana_er:
                return "⚠️ CLICKBAIT (Viral, Baja Calidad)"
            else:
                return "🗑️ BASURA (Ni Viral ni Bueno)"

        df['Categoria'] = df.apply(clasificar, axis=1)

        # --- VISUALIZACIÓN ---
        with col_graph:
            st.subheader("2. Mapa Estratégico")
            
            # Gráfico interactivo con Altair
            base = alt.Chart(df).encode(
                x=alt.X('Alcance', title='Viralidad (Alcance)'),
                y=alt.Y('ER', title='Calidad (Engagement Rate %)'),
                tooltip=['Post_ID', 'Categoria', 'Alcance', 'ER', 'Likes', 'Guardados']
            )

            # Puntos
            points = base.mark_circle(size=100).encode(
                color=alt.Color('Categoria', legend=alt.Legend(orient='bottom')),
                opacity=alt.value(0.8)
            )

            # Líneas de cuadrantes (Medianas)
            rule_x = alt.Chart(pd.DataFrame({'x': [mediana_alcance]})).mark_rule(color='gray', strokeDash=[5,5]).encode(x='x')
            rule_y = alt.Chart(pd.DataFrame({'y': [mediana_er]})).mark_rule(color='gray', strokeDash=[5,5]).encode(y='y')
            
            # Texto en los cuadrantes
            text_q1 = alt.Chart(pd.DataFrame({'x': [df['Alcance'].max()], 'y': [df['ER'].max()], 'text': ['UNICORNIOS']})).mark_text(align='right', baseline='top', color='gray', dx=-10).encode(x='x', y='y', text='text')

            st.altair_chart(points + rule_x + rule_y + text_q1, use_container_width=True)

        # --- INFORME TÁCTICO ---
        st.divider()
        c1, c2 = st.columns(2)
        
        with c1:
            st.success(f"💎 **UNICORNIOS ({len(df[df['Categoria'].str.contains('UNICORNIO')])} posts)**")
            st.markdown("Post que funcionaron perfecto. **ACCIÓN:** Repetir formato y tema tal cual.")
            st.dataframe(df[df['Categoria'].str.contains('UNICORNIO')][['Post_ID', 'Alcance', 'ER']], hide_index=True)
            
            st.warning(f"⚠️ **DESGASTE ({len(df[df['Categoria'].str.contains('CLICKBAIT')])} posts)**")
            st.markdown("Tienen mucho alcance pero la gente no interactúa. **ACCIÓN:** Mejorar el 'Call to Action' o el contenido final.")
            st.dataframe(df[df['Categoria'].str.contains('CLICKBAIT')][['Post_ID', 'Alcance', 'ER']], hide_index=True)

        with c2:
            st.info(f"🛡️ **JOYAS OCULTAS ({len(df[df['Categoria'].str.contains('JOYA')])} posts)**")
            st.markdown("El algoritmo los ignoró, pero a la audiencia fiel le encantaron. **ACCIÓN:** Repostear en Stories o cambiar la portada.")
            st.dataframe(df[df['Categoria'].str.contains('JOYA')][['Post_ID', 'Alcance', 'ER']], hide_index=True)
            
            st.error(f"🗑️ **BAJO RENDIMIENTO ({len(df[df['Categoria'].str.contains('BASURA')])} posts)**")
            st.markdown("No gastar más energía en esto.")
            st.dataframe(df[df['Categoria'].str.contains('BASURA')][['Post_ID', 'Alcance', 'ER']], hide_index=True)

    except Exception as e:
        st.error(f"Error procesando datos: {e}")