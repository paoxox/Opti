import plotly.graph_objects as go

AZUL, ROJO, GRIS, VERDE, NARANJA = "#1F77B4", "#D62728", "#9AA0A6", "#2CA02C", "#FF7F0E"

LEYENDA_ABAJO = dict(orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0)

def fig_factibilidad(df, t_in=None, eps=None):
    """Mapa T_in vs eps coloreado por S_out; la línea negra marca S_out = 10 ppm."""
    z = df.pivot(index="eps", columns="T_in", values="S_out")
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        x=z.columns, y=z.index, z=z.values, zmin=0, zmax=50, colorscale="RdYlGn_r",
        colorbar=dict(title=dict(text="S<sub>out (ppm)", side="right"), thickness=14, len=0.85),
        hovertemplate="T_in=%{x:.1f} K<br>ε=%{y:.3f}<br>S_out=%{z:.2f} ppm<extra></extra>",
        name="S_out"))
    fig.add_trace(go.Contour(
        x=z.columns, y=z.index, z=z.values, showscale=False, hoverinfo="skip",
        contours=dict(start=10, end=10, size=1, coloring="lines"),
        line=dict(color="black", width=2), name="límite 10 ppm", showlegend=True))
    if t_in is not None:
        fig.add_trace(go.Scatter(x=[t_in], y=[eps], mode="markers", name="punto elegido",
                                 marker=dict(size=13, symbol="x", color="black",
                                             line=dict(color="white", width=1))))
    fig.update_layout(
        title=dict(text="Dominio de decisión (a la derecha de la línea negra se cumple S<sub>out ≤ 10 ppm)",
                   font=dict(size=14)),
        xaxis_title="T<sub>in (K)", yaxis_title="Efectividad ε",
        legend=LEYENDA_ABAJO, margin=dict(t=60, b=90, r=20))
    return fig

def fig_pareto(df, frontera, idx_rodilla=None, solo_factibles=False):
    """Frontera de Pareto: carga térmica (kW) en x y conversión X_S (%) en y."""
    fig = go.Figure()
    if not solo_factibles:
        nofact = df[~df["factible"]]
        fig.add_trace(go.Scattergl(x=nofact["Q_kW"], y=nofact["X_S"] * 100, mode="markers",
                                   name="Infactibles (S<sub>out > 10 ppm)",
                                   marker=dict(size=4, color=GRIS, opacity=0.35)))
    fact = df[df["factible"]]
    fig.add_trace(go.Scattergl(
        x=fact["Q_kW"], y=fact["X_S"] * 100, mode="markers", name="Factibles",
        marker=dict(size=4, color="lightskyblue", opacity=0.5),
        customdata=fact[["T_in", "eps"]],
        hovertemplate="Q=%{x:.0f} kW<br>X_S=%{y:.4f} %<br>T_in=%{customdata[0]:.1f} K"
                      "<br>ε=%{customdata[1]:.3f}<extra></extra>"))
    if len(frontera):
        fig.add_trace(go.Scatter(
            x=frontera["Q_kW"], y=frontera["X_S"] * 100, mode="lines+markers",
            name="Frontera de Pareto", line=dict(color="royalblue", width=3), marker=dict(size=5),
            customdata=frontera[["T_in", "eps", "S_out"]],
            hovertemplate="<b>Pareto</b><br>Q=%{x:.0f} kW<br>X_S=%{y:.4f} %"
                          "<br>T_in=%{customdata[0]:.1f} K<br>ε=%{customdata[1]:.3f}"
                          "<br>S_out=%{customdata[2]:.2f} ppm<extra></extra>"))
    if idx_rodilla is not None and len(frontera):
        k = frontera.iloc[idx_rodilla]
        fig.add_trace(go.Scatter(x=[k["Q_kW"]], y=[k["X_S"] * 100], mode="markers", name="Knee point",
                                 marker=dict(size=16, symbol="star", color="crimson",
                                             line=dict(color="black", width=1))))
    fig.update_layout(
        title=dict(text="Optimización Multiobjetivo", font=dict(size=14)),
        xaxis_title="Carga térmica Q<sub>horno (kW)", yaxis_title="Conversión X<sub>s (%)",
        legend=LEYENDA_ABAJO, margin=dict(t=60, b=90, r=20), height=520)
    return fig

def fig_distancias(frontera, dist, idx):
    fig = go.Figure(go.Scatter(x=frontera["T_in"], y=dist, mode="lines", line=dict(color=AZUL)))
    if len(frontera):
        fig.add_vline(x=float(frontera.iloc[idx]["T_in"]), line_dash="dash", line_color=NARANJA)
    fig.update_layout(xaxis_title="T<sub>in sobre la frontera (K)",
                      yaxis_title="Distancia perpendicular (normalizada)",
                      title="Cómo se localiza el Knee Point", margin=dict(t=50, b=40))
    return fig

def fig_tornado(sens, columna="dQ_%", titulo="Efecto sobre Q<sub>horno"):
    nombres = {"m": "ṁ", "cp": "Cp", "ea": "Ea", "k0": "k₀", "tau": "τ"}
    fig = go.Figure()
    for signo, color in ((-10, VERDE), (10, ROJO)):
        sub = sens[sens["cambio_%"].round() == signo]
        fig.add_trace(go.Bar(y=[nombres[x] for x in sub["parametro"]], x=sub[columna],
                             orientation="h", name=f"{signo:+d} %", marker_color=color))
    fig.update_layout(barmode="relative", xaxis_title="Variación (%)", title=titulo,
                      legend=LEYENDA_ABAJO, margin=dict(t=50, b=90))
    return fig

def fig_s_in(barrido):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=barrido["S_in_ppm"], y=barrido["S_out_ppm"], mode="lines+markers",
                             line=dict(color=AZUL), name="S_out"))
    fig.add_hline(y=10, line_dash="dash", line_color=ROJO, annotation_text="límite 10 ppm")
    fig.update_layout(xaxis_title="S<sub>in (ppm)", yaxis_title="S<sub>out (ppm)",
                      title="Efecto del azufre de alimentación", margin=dict(t=50, b=40))
    return fig

def fig_rodilla_precio(tabla):
    fig = go.Figure(go.Scatter(x=tabla["peso_energia"], y=tabla["T_in"], mode="lines+markers",
                               line=dict(color=NARANJA)))
    fig.update_layout(xaxis_title="Peso relativo de la energía (w)",
                      yaxis_title="T<sub>in</sub> del punto elegido (K)",
                      title="Punto elegido según el peso de la energía", margin=dict(t=50, b=40))
    return fig
