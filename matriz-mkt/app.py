import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import io

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Matriz de Rendimiento", layout="wide")
st.title("🎯 Matriz de Impacto de Contenido")
st.markdown("Suba su archivo Excel para analizar Viralidad vs. Engagement.")

# --- 2. LÓGICA (Sin Pesos - Engagement Puro) ---
def calcular_metricas(df):
    # Estandarizar nombres de columnas (quita espacios extra, minúsculas)
    df.columns = df.columns.str.strip()
    
    # Validar que existan las columnas necesarias
    req_cols = ['Nombre del Post', 'Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios']
    missing = [c for c in req_cols if c not in df.columns]
    
    if missing:
        st.error(f"⚠️ Faltan columnas en el Excel: {missing}")
        st.stop()

    # Limpieza numérica
    cols_num = ['Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios']
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Cálculo Engagement Puro
    df['Interacciones'] = df['Likes'] + df['Guardados'] + df['Compartidos'] + df['Comentarios']
    df['ER'] = df.apply(lambda row: (row['Interacciones'] / row['Alcance']) * 100 if row['Alcance'] > 0 else 0, axis=1)
    
    return df

# --- 3. INTERFAZ DE CARGA (DRAG & DROP) ---
col_load, col_kpi = st.columns([2, 1])

with col_load:
    st.subheader("1. Cargar Datos")
    
    # Widget de subida de archivos
    uploaded_file = st.file_uploader("Arrastra tu Excel (.xlsx) o CSV aquí", type=['xlsx', 'csv'])

    # Botón para descargar plantilla (Ayuda al usuario)
    if not uploaded_file:
        st.info("¿No tienes el formato?")
        # Creamos un Excel vacío en memoria para que lo descargue
        df_template = pd.DataFrame(columns=['Nombre del Post', 'Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios'])
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_template.to_excel(writer, index=False, sheet_name='Datos')
            
        st.download_button(
            label="📥 Descargar Plantilla Excel Vacía",
            data=buffer,
            file_name="plantilla_metrics.xlsx",
            mime="application/vnd.ms-excel"
        )

# --- 4. MOTOR DE ANÁLISIS ---
if uploaded_file:
    try:
        # Detectar formato y leer
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        # Procesar
        df = calcular_metricas(df_raw)

        # Estadísticas Base
        mediana_alcance = df['Alcance'].median()
        mediana_er = df['ER'].median()

        # Clasificación
        def clasificar(row):
            if row['Alcance'] == 0: return "📉 Revisar Datos"
            
            # Zona Muerta (10%)
            margen_alcance = mediana_alcance * 0.10
            margen_er = mediana_er * 0.10

            # Si es Estándar
            if (abs(row['Alcance'] - mediana_alcance) <= margen_alcance) and \
               (abs(row['ER'] - mediana_er) <= margen_er):
                return "⚖️ Rendimiento Estándar"

            # Cuadrantes
            if row['Alcance'] > mediana_alcance and row['ER'] > mediana_er: return "💎 Éxito Total"
            elif row['Alcance'] < mediana_alcance and row['ER'] > mediana_er: return "🛡️ Alta Fidelización"
            elif row['Alcance'] > mediana_alcance and row['ER'] < mediana_er: return "⚠️ Viral Superficial"
            else: return "📉 Bajo Impacto"

        df['Categoria'] = df.apply(clasificar, axis=1)

        # --- 5. VISUALIZACIÓN ---
        st.divider()
        c_chart, c_summ = st.columns([3, 1])
        
        with c_chart:
            st.subheader("2. Mapa Estratégico")
            
            domain = ['💎 Éxito Total', '🛡️ Alta Fidelización', '⚠️ Viral Superficial', '📉 Bajo Impacto', '⚖️ Rendimiento Estándar', '📉 Revisar Datos']
            range_ = ['#2ecc71', '#3498db', '#f1c40f', '#e74c3c', '#bdc3c7', '#000000'] # ROJO APLICADO

            base = alt.Chart(df).encode(
                x=alt.X('Alcance', title='Viralidad (Alcance)'),
                y=alt.Y('ER', title='Engagement Rate (%)'),
                tooltip=['Nombre del Post', 'Categoria', 'Alcance', 'ER', 'Interacciones']
            )

            points = base.mark_circle(size=200).encode(
                color=alt.Color('Categoria', scale=alt.Scale(domain=domain, range=range_), legend=alt.Legend(orient='bottom')),
                opacity=alt.value(0.9)
            )

            text = base.mark_text(align='left', baseline='middle', dx=12).encode(text='Nombre del Post')
            
            # Líneas Promedio
            rule_x = alt.Chart(pd.DataFrame({'x': [mediana_alcance]})).mark_rule(color='gray', strokeDash=[3,3]).encode(x='x')
            rule_y = alt.Chart(pd.DataFrame({'y': [mediana_er]})).mark_rule(color='gray', strokeDash=[3,3]).encode(y='y')
            
            st.altair_chart(points + text + rule_x + rule_y, use_container_width=True)

        with c_summ:
            st.metric("Posts Analizados", len(df))
            st.metric("Promedio Alcance", f"{mediana_alcance:,.0f}")
            st.metric("Promedio ER", f"{mediana_er:.2f}%")
            
            # Tabla Resumen Pequeña
            st.caption("Top 3 por Engagement")
            st.dataframe(df.nlargest(3, 'ER')[['Nombre del Post', 'ER']], hide_index=True)

        # --- 6. DETALLE ---
        st.subheader("3. Detalle de Datos")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        st.info("Asegúrate de usar la plantilla descargable.")

else:
    # Mensaje de bienvenida cuando no hay archivo
    with col_kpi:
        st.info("👈 Sube un archivo para comenzar")



