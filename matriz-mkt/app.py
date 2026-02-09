import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Matriz de Rendimiento", layout="wide")
st.title("🎯 Matriz de Impacto de Contenido")
st.markdown("""
Esta herramienta clasifica tus posts basándose en **Viralidad** (Alcance) y **Calidad** (Engagement).
**Nota:** El gráfico penaliza el rendimiento promedio para resaltar solo el éxito real.
""")

# --- 2. BARRA LATERAL (PESOS ESTRATÉGICOS) ---
with st.sidebar:
    st.header("⚙️ Estrategia")
    st.info("Define cuánto vale cada interacción para tu marca.")
    w_like = st.number_input("Peso Me Gusta", value=1.0)
    w_save = st.number_input("Peso Guardado (Retención)", value=3.0)
    w_share = st.number_input("Peso Compartido (Viralidad)", value=4.0)
    w_comment = st.number_input("Peso Comentario", value=2.0)

# --- 3. FUNCIONES DE CÁLCULO ---
def calcular_metricas(df):
    # Limpieza: Asegurar que todo sea número (convierte errores a 0)
    cols_numericas = ['Alcance', 'Likes', 'Guardados', 'Compartidos', 'Comentarios']
    for col in cols_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Cálculo del Score Ponderado
    df['Score'] = (df['Likes'] * w_like) + \
                  (df['Guardados'] * w_save) + \
                  (df['Compartidos'] * w_share) + \
                  (df['Comentarios'] * w_comment)
    
    # Cálculo del Engagement Rate (ER) sobre Alcance
    df['ER'] = df.apply(lambda row: (row['Score'] / row['Alcance']) * 100 if row['Alcance'] > 0 else 0, axis=1)
    
    return df

# --- 4. INTERFAZ DE INGRESO DE DATOS ---
st.subheader("1. Datos de Origen")

# Plantilla inicial (Ejemplo)
data_inicial = {
    'Nombre del Post': ['Reel Tendencia', 'Carrusel Educativo', 'Meme Viernes', 'Video Promo', 'Foto Equipo', 'Post Promedio 1', 'Post Promedio 2'],
    'Alcance': [12000, 15000, 8000, 25000, 10000, 11500, 11800],
    'Likes': [300, 450, 150, 800, 200, 280, 290],
    'Guardados': [20, 45, 10, 100, 15, 18, 19],
    'Compartidos': [5, 20, 2, 50, 3, 4, 5],
    'Comentarios': [8, 15, 3, 60, 5, 7, 7]
}
df_template = pd.DataFrame(data_inicial)

# Configuración visual de la tabla
column_config = {
    "Nombre del Post": st.column_config.TextColumn("Nombre / Etiqueta", required=True, width="medium"),
    "Alcance": st.column_config.NumberColumn("Alcance", format="%d"),
    "Likes": st.column_config.NumberColumn("Likes", format="%d"),
    "Guardados": st.column_config.NumberColumn("Guardados", format="%d"),
    "Compartidos": st.column_config.NumberColumn("Compartidos", format="%d"),
    "Comentarios": st.column_config.NumberColumn("Comentarios", format="%d"),
}

# La Tabla Editable
edited_df = st.data_editor(
    df_template, 
    num_rows="dynamic", 
    height=300,
    use_container_width=True, 
    column_config=column_config
)

boton_analizar = st.button("🚀 ANALIZAR RENDIMIENTO", type="primary")

# --- 5. MOTOR DE ANÁLISIS ---
if boton_analizar:
    if edited_df.empty:
        st.error("⚠️ La tabla está vacía.")
    else:
        try:
            # 5.1 Procesar Datos
            df = calcular_metricas(edited_df.copy())
            
            # 5.2 Calcular Estadísticas Base (Medianas)
            mediana_alcance = df['Alcance'].median()
            mediana_er = df['ER'].median()

            # 5.3 Lógica de Clasificación (Con Zona Muerta)
            def clasificar(row):
                if row['Alcance'] == 0: return "📉 Revisar Datos"
                
                # Definir Zona Muerta (10% alrededor de la mediana)
                # Si el post está muy cerca del promedio, es "Estándar", no "Éxito".
                margen_alcance = mediana_alcance * 0.10
                margen_er = mediana_er * 0.10

                distancia_alcance = abs(row['Alcance'] - mediana_alcance)
                distancia_er = abs(row['ER'] - mediana_er)

                # Si cae dentro del margen del 10%, es Estándar
                if distancia_alcance <= margen_alcance and distancia_er <= margen_er:
                    return "⚖️ Rendimiento Estándar"

                # Si escapa del margen, clasificamos en cuadrantes:
                if row['Alcance'] > mediana_alcance and row['ER'] > mediana_er:
                    return "💎 Éxito Total"
                
                elif row['Alcance'] < mediana_alcance and row['ER'] > mediana_er:
                    return "🛡️ Alta Fidelización"
                
                elif row['Alcance'] > mediana_alcance and row['ER'] < mediana_er:
                    return "⚠️ Viral Superficial"
                
                else:
                    return "📉 Bajo Impacto"

            df['Categoria'] = df.apply(clasificar, axis=1)

            st.divider()
            
            # --- 6. VISUALIZACIÓN (GRÁFICO) ---
            col_graph, col_kpi = st.columns([3, 1])
            
            with col_graph:
                st.subheader("2. Mapa Estratégico")
                
                # Definir colores corporativos
                domain = ['💎 Éxito Total', '🛡️ Alta Fidelización', '⚠️ Viral Superficial', '📉 Bajo Impacto', '⚖️ Rendimiento Estándar', '📉 Revisar Datos']
                range_ = ['#2ecc71', '#3498db', '#f1c40f', '#95a5a6', '#bdc3c7', '#000000'] # Verde, Azul, Amarillo, Gris Oscuro, Gris Claro, Negro

                base = alt.Chart(df).encode(
                    x=alt.X('Alcance', title='Viralidad (Alcance)'),
                    y=alt.Y('ER', title='Calidad (Engagement Rate %)'),
                    tooltip=['Nombre del Post', 'Categoria', 'Alcance', 'ER', 'Likes', 'Guardados']
                )

                # Puntos
                points = base.mark_circle(size=200).encode(
                    color=alt.Color('Categoria', scale=alt.Scale(domain=domain, range=range_), legend=alt.Legend(orient='bottom', title="Categoría")),
                    opacity=alt.value(0.9)
                )

                # Texto (Nombres)
                text = base.mark_text(align='left', baseline='middle', dx=12).encode(text='Nombre del Post')

                # Líneas Promedio
                rule_x = alt.Chart(pd.DataFrame({'x': [mediana_alcance]})).mark_rule(color='gray', strokeDash=[3,3]).encode(x='x')
                rule_y = alt.Chart(pd.DataFrame({'y': [mediana_er]})).mark_rule(color='gray', strokeDash=[3,3]).encode(y='y')
                
                st.altair_chart(points + text + rule_x + rule_y, use_container_width=True)

            # --- 7. KPIS LATERALES ---
            with col_kpi:
                st.subheader("Resumen")
                st.metric("Promedio Alcance", f"{mediana_alcance:,.0f}")
                st.metric("Promedio Engagement", f"{mediana_er:.2f}%")
                
                # Encontrar el mejor post absoluto
                if not df.empty:
                    best_idx = df['ER'].idxmax()
                    best_post = df.loc[best_idx]
                    st.success(f"🏆 **MVP (Mejor Post):**\n\n{best_post['Nombre del Post']}\n\n({best_post['ER']:.2f}% ER)")

            # --- 8. TABLAS DE ACCIÓN ---
            st.divider()
            st.subheader("3. Acciones Recomendadas")
            
            t1, t2, t3 = st.tabs(["💎 Replicar (Éxitos)", "🛡️ Potenciar (Fieles)", "⚖️ Todo el Contenido"])
            
            with t1:
                st.success("**Estos contenidos funcionan perfecto.** Mantener línea editorial.")
                filtros = ['💎 Éxito Total']
                st.dataframe(df[df['Categoria'].isin(filtros)][['Nombre del Post', 'Alcance', 'ER', 'Categoria']], hide_index=True, use_container_width=True)
            
            with t2:
                st.info("**Contenido de nicho muy valioso.** Intentar nuevas portadas o resubir en Stories.")
                filtros = ['🛡️ Alta Fidelización']
                st.dataframe(df[df['Categoria'].isin(filtros)][['Nombre del Post', 'Alcance', 'ER', 'Categoria']], hide_index=True, use_container_width=True)
                
            with t3:
                st.markdown("**Listado completo con clasificación.**")
                st.dataframe(df[['Nombre del Post', 'Alcance', 'ER', 'Categoria']], hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"Error en el cálculo: {e}")
else:
    st.info("💡 Tip: Copia y pega tus datos de Excel directamente en la tabla de arriba.")

