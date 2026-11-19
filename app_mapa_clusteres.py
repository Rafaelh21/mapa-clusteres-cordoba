import folium
from folium.plugins import MarkerCluster
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# 1. Configuración de la página
st.set_page_config(
    page_title="Mapa Interactivo de Clústeres - Córdoba Acelera",
    page_icon="🗺️",
    layout="wide",
)

# --- 2. DISEÑO Y ESTÉTICA AVANZADA (CSS) ---
estilo_personalizado = """
<style>
    /* Ocultar menú y footer nativos */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Color de fondo general de la aplicación */
    .stApp {
        background-color: #f4f6f9;
    }
    
    /* Centrar los títulos */
    .titulo-centrado {
        text-align: center;
        color: #1f2937;
        font-weight: 800;
        padding-bottom: 10px;
        padding-top: 1rem;
    }
    .subtitulo-centrado {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }

    /* Estilo de las tarjetas de métricas */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        border-left: 6px solid #1f77b4;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
</style>
"""
st.markdown(estilo_personalizado, unsafe_allow_html=True)

# 3. Título Centrado
st.markdown('<h1 class="titulo-centrado">🗺️ Mapa Interactivo de Clústeres</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo-centrado">Directorio geolocalizado de empresas y actores estratégicos en Córdoba.</p>', unsafe_allow_html=True)

# 4. Carga de datos y cálculo de faltantes
# 4. Carga de datos y cálculo de faltantes
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("2026_Empresas_cluster_CUIT.xlsx")
        
        # 1. Eliminar filas "fantasma" de Excel (si no hay nombre de empresa, no existe)
        df_real = df.dropna(subset=["Empresa"])
        
        # 2. Calcular cuántas empresas reales tenemos
        total_original = len(df_real)
        
        # 3. Limpiar filas que no tengan coordenadas
        df_limpio = df_real.dropna(subset=["Lat", "Log"])
        
        # 4. Calcular cuántas se quedaron sin mapear
        empresas_sin_coord = total_original - len(df_limpio)
        
        return df_limpio, empresas_sin_coord
    except FileNotFoundError:
        st.error("No se encontró el archivo '2026_Empresas_cluster_CUIT.xlsx'.")
        return pd.DataFrame(), 0

df, empresas_faltantes = cargar_datos()

if not df.empty:
    # 5. Barra lateral: Filtros
    st.sidebar.header("🔍 Filtros y Datos")
    clusters_disponibles = sorted(df["Cluster"].dropna().unique())
    cluster_seleccionado = st.sidebar.multiselect(
        "Filtrar por Clúster:",
        options=clusters_disponibles,
        default=clusters_disponibles,
    )

    df_filtrado = df[df["Cluster"].isin(cluster_seleccionado)]

    # 6. Barra lateral: Métricas Clave
    st.sidebar.metric(label="✅ Empresas Mapeadas", value=len(df_filtrado))
    
    # NUEVO: Métrica de empresas sin lat/long
    st.sidebar.metric(label="⚠️ Empresas sin Coordenadas", value=empresas_faltantes)

    # 7. Colores y Leyenda (Para que coincidan con el mapa)
    # Diccionario con colores en formato Hexadecimal para la barra lateral
    colores_hex = {
        "Córdoba BIM Cluster": "#3186cc",          # Azul
        "Cluster Fintech Córdoba": "#69a130",      # Verde
        "Córdoba Welcome": "#f2932b",              # Naranja
        "BPO & KPO Córdoba Cluster": "#952d98",    # Morado
        "Cluster de Localización e Interpretación de Córdoba (CLIC)": "#8b0000", # Rojo Oscuro
        "Cluster Turismo Salud Córdoba": "#539ea4", # Azul Cadete
        "Cluster de Investigación e Innovación en Salud Humana": "#006400", # Verde Oscuro
    }
    
    # Diccionario paralelo para Folium (solo lee colores de texto específicos)
    colores_folium = {
        "Córdoba BIM Cluster": "blue",
        "Cluster Fintech Córdoba": "green",
        "Córdoba Welcome": "orange",
        "BPO & KPO Córdoba Cluster": "purple",
        "Cluster de Localización e Interpretación de Córdoba (CLIC)": "darkred",
        "Cluster Turismo Salud Córdoba": "cadetblue",
        "Cluster de Investigación e Innovación en Salud Humana": "darkgreen",
    }

    # Dibujar la leyenda de colores en el menú lateral
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎨 Referencias en el Mapa")
    for cluster_name in clusters_disponibles:
        color = colores_hex.get(cluster_name, "#808080")
        st.sidebar.markdown(
            f'<div style="display: flex; align-items: center; margin-bottom: 8px;">'
            f'<div style="background-color: {color}; min-width: 16px; height: 16px; border-radius: 50%; margin-right: 10px; border: 1px solid #ccc;"></div>'
            f'<span style="font-size: 13px; font-weight: 500;">{cluster_name}</span>'
            f'</div>', 
            unsafe_allow_html=True
        )

    # 8. Creación del mapa
    m = folium.Map(location=[-31.4201, -64.1888], zoom_start=13, tiles="OpenStreetMap")
    marker_cluster = MarkerCluster(name="Agrupación de Empresas").add_to(m)

    for idx, row in df_filtrado.iterrows():
        cluster_name = row.get("Cluster", "Sin Clúster")
        f_color = colores_folium.get(cluster_name, "gray")

        # Popup mejorado
        html_content = f"""
        <div style="font-family: Arial, sans-serif; font-size: 13px; width: 240px;">
            <b style="color: #1f77b4; font-size: 14px;">{row['Empresa']}</b><br>
            <b>Razón Social:</b> {row.get('Razón Social', 'N/D')}<br>
            <b>Clúster:</b> <span style="background-color: #eee; padding: 2px 6px; border-radius: 4px;">{cluster_name}</span><br>
            <b>Dirección:</b> {row.get('Direccion ', 'N/D')}<br>
            <hr style="margin: 6px 0; border: 0; border-top: 1px solid #ddd;">
            <a href="{row.get('Web', '#')}" target="_blank" style="color: #0066cc; text-decoration: none;">🌐 Visitar Sitio Web</a>
        </div>
        """

        icono = folium.Icon(color=f_color, icon="briefcase", prefix="fa")
        folium.Marker(
            location=[row["Lat"], row["Log"]],
            popup=folium.Popup(html_content, max_width=300),
            tooltip=row["Empresa"],
            icon=icono,
        ).add_to(marker_cluster)

    st_folium(m, use_container_width=True, height=650, returned_objects=[])