import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Matriz de Rendimiento", layout="wide")
st.title("🎯 Matriz de Impacto de Contenido")
st.markdown("""
Esta herramienta analiza el equilibrio entre **Viralidad** (Alcance) y **Calidad** (Engagement).
Ayuda a identificar qué formatos replicar y cuáles ajustar.
""")

# --- BARRA LATERAL (PESOS) ---
with st.sidebar:
    st.header("⚙️ Estrategia")
    st.info("Define el valor de cada interacción para tu marca.")
    w_like = st.number_input("Peso Me Gusta", value=1.0)
    w_save = st.number_input("Peso Guardado (Retención)", value=3.0)
    w_share = st.number_input("Peso Compartido (Viralidad)", value=4.0)
    w_comment = st.number_input("Peso Comentario", value=2.0)

# --- FUNCIÓN DE CÁLCULO ---
def calcular_metricas(df):
    cols_numericas = ['Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios']
    for col in cols_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 1. Score Ponderado
    df['Score'] = (df['Likes'] * w_like) + \
                  (df['Guardados'] * w_save) + \
                  (df['Compartidos'] * w_share) + \
                  (df['Comentarios'] * w_comment)
    
    # 2. Engagement Rate (ER)
    df['ER'] = df.apply(lambda row: (row['Score'] / row['Alcance']) * 100 if row['Alcance'] > 0 else 0, axis=1)
    
    return df

# --- INTERFAZ DE TABLA ---
st.subheader("1. Ingreso de Datos")

# Plantilla de ejemplo
data_inicial = {
    'Nombre del Post': ['Reel Tendencia', 'Carrusel Educativo', 'Meme Viernes', 'Video Promo', 'Foto Equipo'],
    'Alcance': [12000, 15000, 8000, 25000, 10000],
    'Likes': [300, 450, 150, 800, 200],
    'Guardados': [20, 45, 10, 100, 15],
    'Compartidos': [5, 20, 2, 50, 3],
    'Comentarios': [8, 15, 3, 60, 5]
}
df_template = pd.DataFrame(data_inicial)

column_config = {
    "Nombre del Post": st.column_config.TextColumn("Nombre / Etiqueta", required=True),
    "Alcance": st.column_config.NumberColumn("Alcance", format="%d"),
    "Likes": st.column_config.NumberColumn("Likes", format="%d"),
    "Guardados": st.column_config.NumberColumn("Guardados", format="%d"),
    "Compartidos": st.column_config.NumberColumn("Compartidos", format="%d"),
    "Comentarios": st.column_config.NumberColumn("Comentarios", format="%d"),
}

# TABLA EXPANDIDA (use_container_width=True arregla el ancho)
edited_df = st.data_editor(
    df_template, 
    num_rows="dynamic", 
    height=300,
    use_container_width=True, 
    column_config=column_config
)

boton_analizar = st.button("🚀 ANALIZAR RENDIMIENTO", type="primary")

# --- MOTOR DE ANÁLISIS ---
if boton_analizar:
    if edited_df.empty:
        st.error("⚠️ La tabla está vacía.")
    else:
        try:
            df = calcular_metricas(edited_df.copy())
            
            # Cálculo de Medianas
            mediana_alcance = df['Alcance'].median()
            mediana_er = df['ER'].median()

            # --- NUEVA CLASIFICACIÓN (NOMBRES AMABLES) ---
            def clasificar(row):
                if row['Alcance'] == 0: return "📉 Revisar Datos"
                
                # Cuadrante 1: Alto Alcance / Alto Engagement
                if row['Alcance'] >= mediana_alcance and row['ER'] >= mediana_er:
                    return "💎 Éxito Total"
                
                # Cuadrante 2: Bajo Alcance / Alto Engagement
                elif row['Alcance'] < mediana_alcance and row['ER'] >= mediana_er:
                    return "🛡️ Alta Fidelización"
                
                # Cuadrante 3: Alto Alcance / Bajo Engagement
                elif row['Alcance'] >= mediana_alcance and row['ER'] < mediana_er:
                    return "⚠️ Viral Superficial"
                
                # Cuadrante 4: Bajo Alcance / Bajo Engagement
                else:
                    return "📉 Bajo Impacto"

            df['Categoria'] = df.apply(clasificar, axis=1)

            st.divider()
            
            # --- GRÁFICO ---
            col_graph, col_kpi = st.columns([3, 1])
            
            with col_graph:
                st.subheader("2. Mapa Estratégico")
                
                base = alt.Chart(df).encode(
                    x=alt.X('Alcance', title='Viralidad (Alcance)'),
                    y=alt.Y('ER', title='Calidad (Engagement Rate %)'),
                    tooltip=['Nombre del Post', 'Categoria', 'Alcance', 'ER', 'Likes', 'Guardados']
                )

                points = base.mark_circle(size=200).encode(
                    color=alt.Color('Categoria', 
                                    scale=alt.Scale(domain=['💎 Éxito Total', '🛡️ Alta Fidelización', '⚠️ Viral Superficial', '📉 Bajo Impacto'],
                                                    range=['#2ecc71', '#3498db', '#f1c40f', '#95a5a6']),
                                    legend=alt.Legend(orient='bottom', title="Categoría")),
                    opacity=alt.value(0.9)
                )

                # Etiquetas de texto
                text = base.mark_text(align='left', baseline='middle', dx=12).encode(text='Nombre del Post')

                # Líneas promedio
                rule_x = alt.Chart(pd.DataFrame({'x': [mediana_alcance]})).mark_rule(color='gray', strokeDash=[3,3]).encode(x='x')
                rule_y = alt.Chart(pd.DataFrame({'y': [mediana_er]})).mark_rule(color='gray', strokeDash=[3,3]).encode(y='y')
                
                st.altair_chart(points + text + rule_x + rule_y, use_container_width=True)

            with col_kpi:
                st.subheader("Resumen")
                st.metric("Promedio Alcance", f"{mediana_alcance:,.0f}")
                st.metric("Promedio Engagement", f"{mediana_er:.2f}%")
                best_post = df.loc[df['ER'].idxmax()]
                st.info(f"🏆 **Mejor Post:**\n\n{best_post['Nombre del Post']}")

            # --- TABLAS DE ACCIÓN ---
            st.divider()
            st.subheader("3. Acciones Recomendadas")
            
            t1, t2, t3 = st.tabs(["💎 Replicar (Éxitos)", "🛡️ Potenciar (Fieles)", "🛠️ Optimizar (Mejoras)"])
            
            with t1:
                st.success("**Estos contenidos funcionan perfecto.** Mantener línea editorial.")
                st.dataframe(df[df['Categoria'] == '💎 Éxito Total'][['Nombre del Post', 'Alcance', 'ER']], hide_index=True, use_container_width=True)
            
            with t2:
                st.info("**Contenido de nicho muy valioso.** Intentar nuevas portadas o resubir en Stories para dar más alcance.")
                st.dataframe(df[df['Categoria'] == '🛡️ Alta Fidelización'][['Nombre del Post', 'Alcance', 'ER']], hide_index=True, use_container_width=True)
                
            with t3:
                st.warning("**Contenidos que requieren revisión de formato o estrategia.**")
                mejora = df[df['Categoria'].isin(['⚠️ Viral Superficial', '📉 Bajo Impacto'])]
                st.dataframe(mejora[['Nombre del Post', 'Categoria', 'Alcance', 'ER']], hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"Error en el cálculo: {e}")
else:
    st.info("💡 Tip: Copia y pega tus datos de Excel directamente en la tabla de arriba.")

