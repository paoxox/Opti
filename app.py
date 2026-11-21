"""Simulación y optimización de una unidad HDS simplificada.

Ejecutar con:  streamlit run app.py
"""
import os

import numpy as np
import pandas as pd
import streamlit as st

from utilidades import graficos, modelo, pareto
from utilidades.carga import calcular_frontera, calcular_malla

st.set_page_config(
    page_title="Simulación y Optimización de HDS",
    page_icon=":material/science:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ cabecera
col_logo, col_titulo = st.columns([1, 8], vertical_alignment="center")
with col_logo:
    # Si guardas un logo en datos/logo.png se muestra aquí; si no, no pasa nada.
    if os.path.exists("datos/logo.png"):
        st.image("datos/logo.png", width=90)
with col_titulo:
    st.title("Simulación y Optimización de Hidrodesulfuración (HDS)")
    st.caption("Evaluación de la conversión de azufre ($X_{s}$) y la carga térmica del horno "
               "($Q_{horno}$) bajo la restricción $S_{out}$ ≤ 10 ppm.")

# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.header("Variables de decisión")
    t_in = st.slider("Temperatura entrada reactor $T_{in}$ $(K)$", 550.0, 650.0, 600.0, 1.0)
    eps = st.slider("Efectividad del intercambiador ε", 0.60, 0.90, 0.75, 0.01)

    st.header("Parámetros del modelo")
    m_dot = st.number_input("Flujo másico $ṁ$ $(kg/h)$", 90_000.0, 110_000.0, 100_000.0, 1000.0)
    s_in = st.number_input("Azufre de alimentación $S_{in}$ $(ppm)$", 450.0, 550.0, 500.0, 5.0)
    cp = st.number_input("Capacidad calorífica $Cp$ $(kJ/kg·K)$", 2.25, 2.75, 2.50, 0.05)
    ea = st.number_input("Energía de activación $Ea$ $(J/mol)$", 72_000.0, 88_000.0, 80_000.0, 500.0)
    tau = st.number_input("Tiempo espacial τ $(h)$", 0.45, 0.55, 0.50, 0.01)
    f_k0 = st.slider("Factor sobre $k_{o}$ calibrado", 0.90, 1.10, 1.00, 0.01,
                     help="$k_{o}$ se calibra una sola vez ($X_{S}$ $(600 K)$ = 0.985 con $Ea$ y τ base). "
                          "Aquí solo se ajusta ±10 %.")

    with st.expander("Resolución de la malla"):
        n_t = st.select_slider("Puntos en $T_{in}$", [51, 101, 201, 401], value=201)
        n_e = st.select_slider("Puntos en ε", [16, 31, 61, 121], value=61)

p = modelo.Parametros(m=m_dot, s_in=s_in, cp=cp, ea=ea, k0=modelo.K0_BASE * f_k0, tau=tau)

# ------------------------------------------------------------------ punto operativo
actual = modelo.evaluar(t_in, eps, p)

st.subheader("Punto operativo seleccionado")
if actual["factible"]:
    st.success(f"Cumple la especificación: $S_{{out}}$ = {float(actual['S_out']):.2f} ppm (≤ 10 ppm).")
else:
    st.warning(f"No cumple la especificación: $S_{{out}}$ = {float(actual['S_out']):.2f} ppm (> 10 ppm).")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Conversión $X_{S}$", f"{float(actual['X_S']) * 100:.2f} %")
c2.metric("Azufre de salida $S_{out}$", f"{float(actual['S_out']):.2f} ppm")
c3.metric("$Q_{horno}$", f"{float(actual['Q_kW']):,.1f} kW")
c4.metric("$Q_{horno}$", f"{float(actual['Q_kJh']):,.0f} kJ/h")

st.divider()

# ------------------------------------------------------------------ malla y Pareto
malla = calcular_malla(p.m, p.s_in, p.cp, p.ea, p.k0, p.tau, n_t, n_e)
frontera, idx_rodilla, dist = calcular_frontera(malla)

tab_par, tab_san, tab_sens, tab_mod = st.tabs(
    ["Frontera de Pareto", "Sanity checks y malla", "Sensibilidad", "Modelo"])

# ---- Pareto
with tab_par:
    if frontera.empty:
        st.error("No se encontraron puntos factibles en el dominio con estos parámetros.")
    else:
        rod = frontera.iloc[idx_rodilla]
        col_graf, col_knee = st.columns([2.5, 1])

        with col_graf:
            solo_fact = st.toggle("Mostrar solo puntos factibles", value=False)
            st.plotly_chart(graficos.fig_pareto(malla, frontera, idx_rodilla, solo_fact),
                            width="stretch")

        with col_knee:
            st.markdown("### Knee point (rodilla)")
            st.info("Solución de compromiso entre conversión y energía.")
            st.metric("Temperatura T_in", f"{rod['T_in']:.1f} K", f"{rod['T_in'] - 273.15:.1f} °C",
                      delta_color="off")
            st.metric("Efectividad ε", f"{rod['eps']:.2f}")
            st.metric("Conversión X_S", f"{rod['X_S'] * 100:.3f} %")
            st.metric("S_out", f"{rod['S_out']:.2f} ppm")
            st.metric("Q_horno", f"{rod['Q_kW']:,.1f} kW")

        st.subheader("Puntos representativos de la frontera")
        pos = sorted(set(np.linspace(0, len(frontera) - 1, 6).astype(int)) | {idx_rodilla})
        repres = frontera.iloc[pos][["T_in", "eps", "X_S", "S_out", "Q_kJh", "Q_kW"]].copy()
        repres.insert(0, "Nota", ["Knee point" if i == idx_rodilla else "" for i in pos])
        st.dataframe(repres, hide_index=True, width="stretch", column_config={
            "T_in": st.column_config.NumberColumn("T_in (K)", format="%.1f"),
            "eps": st.column_config.NumberColumn("ε", format="%.3f"),
            "X_S": st.column_config.NumberColumn("X_S", format="%.5f"),
            "S_out": st.column_config.NumberColumn("S_out (ppm)", format="%.3f"),
            "Q_kJh": st.column_config.NumberColumn("Q (kJ/h)", format="%.3e"),
            "Q_kW": st.column_config.NumberColumn("Q (kW)", format="%.0f"),
        })

        with st.expander("Resolución de la malla y limitaciones"):
            st.write(
                f"La malla usa pasos de {100 / (n_t - 1):.2f} K en T_in y {0.30 / (n_e - 1):.4f} "
                "en ε. La frontera es un conjunto discreto: el knee point tiene una "
                "incertidumbre del orden de un paso de malla en T_in. Como el modelo es "
                "algebraico, evaluar miles de puntos toma milisegundos, así que afinar la malla "
                "es barato; aun así, un grid search no garantiza el óptimo exacto.")
            st.write(
                "X_S depende solo de T_in, y a T_in fijo Q_horno baja cuando ε sube. Por eso "
                "todos los puntos con ε < 0.90 quedan dominados y la frontera se forma sobre "
                "la línea ε = 0.90.")
            st.plotly_chart(graficos.fig_distancias(frontera, dist, idx_rodilla), width="stretch")

        with st.expander("Sensibilidad del knee point al precio de la energía (opcional)"):
            st.write("Se minimiza una suma ponderada de los objetivos normalizados; w grande "
                     "equivale a una energía más cara frente a la calidad. No es un modelo "
                     "económico completo.")
            tabla_w = pareto.rodilla_vs_peso_energia(frontera)
            st.plotly_chart(graficos.fig_rodilla_precio(tabla_w), width="stretch")
            st.dataframe(tabla_w, hide_index=True, width="stretch")

        st.download_button("Descargar frontera (CSV)",
                           frontera.drop(columns="f1").to_csv(index=False).encode("utf-8"),
                           file_name="frontera_pareto.csv", mime="text/csv")

# ---- Sanity checks y malla
with tab_san:
    st.subheader("Sanity checks (parámetros base)")
    base = modelo.Parametros()
    v = modelo.validaciones(base)
    c1, c2 = v["check1"], v["check2"]

    tabla = pd.DataFrame([
        {"Caso": "1) T_in = 650 K, ε = 0.90", "X_S": f"{float(c1['X_S']):.7f}",
         "S_out (ppm)": f"{float(c1['S_out']):.4f}", "Factible": "Sí" if c1["factible"] else "No",
         "Q (kJ/h)": f"{float(c1['Q_kJh']):.4e}", "Q (kW)": f"{float(c1['Q_kW']):,.1f}"},
        {"Caso": "2) T_in = 550 K, ε = 0.75", "X_S": f"{float(c2['X_S']):.7f}",
         "S_out (ppm)": f"{float(c2['S_out']):.2f}", "Factible": "Sí" if c2["factible"] else "No",
         "Q (kJ/h)": f"{float(c2['Q_kJh']):.4e}", "Q (kW)": f"{float(c2['Q_kW']):,.1f}"},
    ])
    st.dataframe(tabla, hide_index=True, width="stretch")

    st.markdown("**3) Límite ε → 1** (a T_in = 650 K)")
    eps_lim = np.array([0.90, 0.99, 0.999, 1.0])
    lim = modelo.evaluar(np.full(4, 650.0), eps_lim, base)
    st.dataframe(pd.DataFrame({
        "ε": eps_lim,
        "T_intercambiador (K)": lim["T_intercambiador"],
        "T_efluente (K)": lim["T_efluente"],
        "Q_horno (kJ/h)": lim["Q_kJh"],
    }), hide_index=True, width="stretch", column_config={
        "T_intercambiador (K)": st.column_config.NumberColumn(format="%.4f"),
        "T_efluente (K)": st.column_config.NumberColumn(format="%.4f"),
        "Q_horno (kJ/h)": st.column_config.NumberColumn(format="%.4e"),
    })
    st.caption(f"Cuando ε → 1, T_intercambiador → T_efluente y Q → ṁ·Cp·(T_in − T_efluente) = "
               f"{v['q_limite_kJh']:.4e} kJ/h. El signo negativo indica que el efluente está "
               "más caliente que la entrada al reactor: con un intercambiador ideal sobraría "
               "calor y no haría falta horno.")

    st.subheader("Estadísticas de la malla")
    n_fact = int(malla["factible"].sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Puntos de la malla", f"{len(malla):,}")
    m2.metric("Puntos factibles", f"{n_fact:,}")
    m3.metric("Fracción factible", f"{n_fact / len(malla):.1%}")
    m4.metric("Puntos en Pareto", f"{len(frontera):,}")
    st.caption(f"Rango de S_out: {malla['S_out'].min():.3g} a {malla['S_out'].max():.1f} ppm. "
               f"Rango de Q_horno: {malla['Q_kJh'].min():.3e} a {malla['Q_kJh'].max():.3e} kJ/h "
               f"({malla['Q_kW'].min():,.0f} a {malla['Q_kW'].max():,.0f} kW).")
    st.plotly_chart(graficos.fig_factibilidad(malla, t_in, eps), width="stretch")

# ---- Sensibilidad
with tab_sens:
    st.subheader("Análisis de sensibilidad paramétrica")
    opciones = ["Punto de la barra lateral"]
    if not frontera.empty:
        opciones.insert(0, "Knee point")
    ref = st.radio("Punto de referencia", opciones, horizontal=True)
    if ref == "Knee point":
        t_ref, e_ref = float(frontera.iloc[idx_rodilla]["T_in"]), float(frontera.iloc[idx_rodilla]["eps"])
    else:
        t_ref, e_ref = t_in, eps
    st.caption(f"Referencia: T_in = {t_ref:.1f} K, ε = {e_ref:.2f}. Cada parámetro se perturba "
               "por separado; k₀ no se recalcula cuando cambian Ea o τ.")

    sens = modelo.sensibilidad(t_ref, e_ref, p)
    g1, g2 = st.columns(2)
    g1.plotly_chart(graficos.fig_tornado(sens, "dQ_%", "Efecto sobre Q_horno (%)"), width="stretch")
    g2.plotly_chart(graficos.fig_s_in(modelo.barrido_s_in(t_ref, e_ref, p)), width="stretch")

    st.dataframe(sens, hide_index=True, width="stretch", column_config={
        "parametro": "Parámetro",
        "cambio_%": st.column_config.NumberColumn("Cambio (%)", format="%+.0f"),
        "Q_kJh": st.column_config.NumberColumn("Q (kJ/h)", format="%.4e"),
        "dQ_%": st.column_config.NumberColumn("ΔQ (%)", format="%+.3f"),
        "S_out_ppm": st.column_config.NumberColumn("S_out (ppm)", format="%.3f"),
        "dS_out_%": st.column_config.NumberColumn("ΔS_out (%)", format="%+.1f"),
        "factible": "¿Factible?",
    })
    st.download_button("Descargar sensibilidad (CSV)", sens.to_csv(index=False).encode("utf-8"),
                       file_name="sensibilidad.csv", mime="text/csv")

# ---- Modelo
with tab_mod:
    st.latex(r"k(T)=k_0\,e^{-E_a/(RT)},\quad X_S=1-e^{-k\tau},\quad S_{out}=S_{in}(1-X_S)")
    st.latex(r"k_0=\frac{-\ln(1-0.985)}{\tau\,e^{-E_a/(R\cdot 600)}}")
    st.latex(r"\Delta T_{ad}=15\,X_S,\quad T_{ef}=T_{in}+\Delta T_{ad}")
    st.latex(r"T_{int}=T_{alim}+\varepsilon\,(T_{ef}-T_{alim}),\quad Q_{horno}=\dot m\,C_p\,(T_{in}-T_{int})")
    st.markdown(
        "- La calibración de k₀ y el incremento adiabático de 15 K son elecciones pedagógicas.\n"
        "- Intercambiador por efectividad constante, Cp constante, sin pérdidas.\n"
        "- Q_horno negativo se conserva: indica excedente de calor.")
