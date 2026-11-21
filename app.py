import streamlit as st
import pandas as pd

# Importar nuestros módulos locales
from utilidades import modelo, pareto, graficos

# 1. Configuración de página
st.set_page_config(page_title="Simulación y Optimización de HDS", page_icon="⚗️", layout="wide")

# 2. Cabecera con Logo y Título
col_logo, col_titulo = st.columns([1, 8], vertical_alignment="center")
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=90)
with col_titulo:
    st.title("Simulación y Optimización de Hidrodesulfuración (HDS)")
    st.caption("Evaluación de conversión de azufre (Xs) y carga térmica del horno (Q_horno) bajo restricción Sout ≤ 10 ppm.")

# 3. Barra Lateral (Controles)
with st.sidebar:
    st.header("Variables de decisión")
    t_in = st.slider("Temperatura entrada reactor Tin (K)", 550.0, 650.0, 600.0, 1.0)
    epsilon = st.slider("Efectividad intercambiador ε", 0.60, 0.90, 0.75, 0.01)

    st.header("Parámetros del modelo")
    m_dot = st.number_input("Flujo másico ṁ (kg/h)", 90000.0, 110000.0, 100000.0, 1000.0)
    s_in = st.number_input("Azufre alimentación Sin (ppm)", 450.0, 550.0, 500.0, 5.0)
    cp = st.number_input("Capacidad calorífica Cp (kJ/(kg·K))", 2.25, 2.75, 2.50, 0.05)
    ea = st.number_input("Energía de activación Ea (J/mol)", 72000.0, 88000.0, 80000.0, 500.0)
    tau = st.number_input("Tiempo espacial τ (h)", 0.45, 0.55, 0.50, 0.01)

    k0_base = modelo.calcular_k0(ea=ea, tau=tau)
    k0 = st.number_input("Factor preexponencial k0 (h⁻¹)", min_value=float(k0_base * 0.90), max_value=float(k0_base * 1.10), value=float(k0_base), format="%.4e")

# 4. Evaluación del Punto Actual
res_actual = modelo.evaluar_hds(t_in, epsilon, m_dot, s_in, cp, ea, k0, tau)

st.subheader("Punto operativo seleccionado")
if res_actual["factible"]:
    st.success(f"Cumple especificación de calidad: Sout = {res_actual['Sout_ppm']:.2f} ppm (≤ 10 ppm).")
else:
    st.warning(f"No cumple especificación de calidad: Sout = {res_actual['Sout_ppm']:.2f} ppm (> 10 ppm).")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Conversión Xs", f"{res_actual['Xs']*100:.2f}%")
c2.metric("Azufre salida Sout", f"{res_actual['Sout_ppm']:.2f} ppm", delta_color="inverse")
c3.metric("Carga horno Q_horno", f"{res_actual['Q_horno_kW']:.2f} kW")
c4.metric("Carga horno Q_horno", f"{res_actual['Q_horno_kJ_h']:,.0f} kJ/h")

st.markdown("---")

# 5. Cálculo de Malla y Pareto (con caché para velocidad)
@st.cache_data
def obtener_datos_pareto(m, s, c, e, k, t):
    return pareto.calcular_malla_y_pareto(m_dot=m, s_in=s, cp=c, ea=e, k0=k, tau=t)

df_grid, df_pareto, knee_point = obtener_datos_pareto(m_dot, s_in, cp, ea, k0, tau)

# 6. Pestañas de Visualización
tab_pareto, tab_sanity, tab_sensibilidad = st.tabs(["📈 Frontera de Pareto", "✅ Sanity Checks y Malla", "🧪 Sensibilidad"])

with tab_pareto:
    if df_pareto.empty:
        st.error("No se encontraron puntos factibles en el dominio especificado.")
    else:
        col_graph, col_knee = st.columns([2.5, 1])
        with col_graph:
            fig = graficos.crear_grafico_pareto(df_grid, df_pareto, knee_point)
            st.plotly_chart(fig, use_container_width=True)
        with col_knee:
            st.markdown("### 📍 Knee Point (Rodilla)")
            st.info("Solución de compromiso óptima entre conversión y energía.")
            st.metric("Temperatura Tin", f"{knee_point['Tin_K']:.1f} K", f"{knee_point['Tin_K']-273.15:.1f} °C")
            st.metric("Efectividad ε", f"{knee_point['epsilon']:.2f}")
            st.metric("Conversión Xs", f"{knee_point['Xs']*100:.3f}%")
            st.metric("Sout", f"{knee_point['Sout_ppm']:.2f} ppm")
            st.metric("Carga Horno", f"{knee_point['Q_horno_kW']:.2f} kW")

with tab_sanity:
    st.subheader("Sanity Checks (Valores Base)")
    sc1 = modelo.evaluar_hds(650.0, 0.90, 100000.0, 500.0, 2.5, 80000.0, modelo.calcular_k0(80000.0, 0.5), 0.5)
    sc2 = modelo.evaluar_hds(550.0, 0.75, 100000.0, 500.0, 2.5, 80000.0, modelo.calcular_k0(80000.0, 0.5), 0.5)
    sc3 = modelo.evaluar_hds(600.0, 0.999999, 100000.0, 500.0, 2.5, 80000.0, modelo.calcular_k0(80000.0, 0.5), 0.5)

    df_sanity = pd.DataFrame([
        {"Caso": "1) Tin = 650 K, ε = 0.90", "Xs": f"{sc1['Xs']:.4f}", "Sout (ppm)": f"{sc1['Sout_ppm']:.4f}", "Factible": "Sí" if sc1["factible"] else "No", "Q_horno (kW)": f"{sc1['Q_horno_kW']:.2f}"},
        {"Caso": "2) Tin = 550 K, ε = 0.75", "Xs": f"{sc2['Xs']:.4f}", "Sout (ppm)": f"{sc2['Sout_ppm']:.4f}", "Factible": "Sí" if sc2["factible"] else "No", "Q_horno (kW)": f"{sc2['Q_horno_kW']:.2f}"},
        {"Caso": "3) Límite ε → 1 (Tin = 600 K)", "Xs": f"{sc3['Xs']:.4f}", "Sout (ppm)": f"{sc3['Sout_ppm']:.4f}", "Factible": "Sí" if sc3["factible"] else "No", "Q_horno (kW)": f"{sc3['Q_horno_kW']:.2f}"},
    ])
    st.dataframe(df_sanity, use_container_width=True, hide_index=True)
    
    st.markdown("#### Estadísticas de la Malla")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Puntos Malla", f"{len(df_grid):,}")
    m2.metric("Puntos Factibles", f"{len(df_grid[df_grid['factible']]):,}")
    m3.metric("Fracción Factible", f"{(len(df_grid[df_grid['factible']])/len(df_grid))*100:.1f}%")
    m4.metric("Puntos en Pareto", f"{len(df_pareto):,}")

with tab_sensibilidad:
    st.subheader("Análisis de Sensibilidad Paramétrica")
    st.caption("Evaluado alrededor del punto seleccionado en la barra lateral.")
    
    df_sens = modelo.calcular_sensibilidad(t_in, epsilon, m_dot, s_in, cp, ea, k0, tau)
    st.dataframe(df_sens, use_container_width=True, hide_index=True)
