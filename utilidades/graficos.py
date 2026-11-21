import plotly.graph_objects as go

def crear_grafico_pareto(df_grid, df_pareto, knee_point):
    """Genera la gráfica interactiva usando Xs real en el eje Y para interpretación ingenieril."""
    fig = go.Figure()
    df_fact = df_grid[df_grid["factible"]]
    df_infact = df_grid[~df_grid["factible"]]

    # Puntos Infactibles (Gris claro)
    fig.add_trace(go.Scatter(x=df_infact["Q_horno_kW"], y=df_infact["Xs"]*100, mode="markers",
                             name="Infactibles (Sout > 10)", marker=dict(color="lightgray", size=4, opacity=0.3)))
    
    # Puntos Factibles (Azul claro)
    fig.add_trace(go.Scatter(x=df_fact["Q_horno_kW"], y=df_fact["Xs"]*100, mode="markers",
                             name="Factibles", marker=dict(color="lightskyblue", size=5, opacity=0.6),
                             hovertemplate="Q: %{x:.1f} kW<br>Xs: %{y:.2f}%<br>Tin: %{customdata[0]:.1f} K<br>ε: %{customdata[1]:.2f}<extra></extra>",
                             customdata=df_fact[["Tin_K", "epsilon"]].values))
    
    # Frontera de Pareto (Azul oscuro)
    fig.add_trace(go.Scatter(x=df_pareto["Q_horno_kW"], y=df_pareto["Xs"]*100, mode="lines+markers",
                             name="Frontera de Pareto", line=dict(color="royalblue", width=3),
                             hovertemplate="<b>Pareto</b><br>Q: %{x:.1f} kW<br>Xs: %{y:.2f}%<br>Tin: %{customdata[0]:.1f} K<br>ε: %{customdata[1]:.2f}<extra></extra>",
                             customdata=df_pareto[["Tin_K", "epsilon"]].values))
    
    # Knee Point (Estrella roja)
    fig.add_trace(go.Scatter(x=[knee_point["Q_horno_kW"]], y=[knee_point["Xs"]*100], mode="markers",
                             name="Knee Point", marker=dict(color="crimson", size=16, symbol="star", line=dict(color="black", width=1)),
                             hovertemplate="<b>Knee Point</b><br>Q: %{x:.1f} kW<br>Xs: %{y:.2f}%<extra></extra>"))

    fig.update_layout(title="Optimización Multiobjetivo", xaxis_title="Carga Térmica Q_horno (kW)",
                      yaxis_title="Conversión Xs (%)", legend=dict(x=0.01, y=0.01, bgcolor="rgba(255,255,255,0.8)"), height=500)
    return fig
