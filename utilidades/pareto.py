import numpy as np
import pandas as pd
from .modelo import evaluar_hds, EA_CALIB, TAU_CALIB

def calcular_malla_y_pareto(n_puntos=50, m_dot=100000.0, s_in=500.0, cp=2.5, ea=EA_CALIB, k0=None, tau=TAU_CALIB):
    """Genera la malla de 2500 puntos y calcula la Frontera de Pareto y el Knee Point."""
    grid_tin = np.linspace(550.0, 650.0, n_puntos)
    grid_eps = np.linspace(0.60, 0.90, n_puntos)
    T_grid, E_grid = np.meshgrid(grid_tin, grid_eps)
    T_flat, E_flat = T_grid.flatten(), E_grid.flatten()

    # Vectorización: evalúa todos los puntos a la vez
    res = evaluar_hds(t_in=T_flat, epsilon=E_flat, m_dot=m_dot, s_in=s_in, cp=cp, ea=ea, k0=k0, tau=tau)
    
    df_grid = pd.DataFrame(res)
    df_factible = df_grid[df_grid["factible"]].copy()

    if df_factible.empty:
        return df_grid, pd.DataFrame(), None

    # Filtrado de Pareto expresando Xs como minimización (1 - Xs)
    df_factible["obj_xs"] = 1.0 - df_factible["Xs"]
    df_factible["obj_q"] = df_factible["Q_horno_kW"]
    df_sorted = df_factible.sort_values(by=["obj_xs", "obj_q"], ascending=[True, True]).reset_index(drop=True)

    pareto_indices = []
    min_q_visto = float("inf")
    for i, row in df_sorted.iterrows():
        if row["obj_q"] < min_q_visto:
            pareto_indices.append(i)
            min_q_visto = row["obj_q"]

    df_pareto = df_sorted.loc[pareto_indices].copy()

    # Cálculo del Knee Point (Normalización min-max)
    xs_min, xs_max = df_pareto["obj_xs"].min(), df_pareto["obj_xs"].max()
    q_min, q_max = df_pareto["obj_q"].min(), df_pareto["obj_q"].max()

    denom_xs = (xs_max - xs_min) if (xs_max - xs_min) > 0 else 1.0
    denom_q = (q_max - q_min) if (q_max - q_min) > 0 else 1.0

    df_pareto["xs_norm"] = (df_pareto["obj_xs"] - xs_min) / denom_xs
    df_pareto["q_norm"] = (df_pareto["obj_q"] - q_min) / denom_q

    x1, y1 = df_pareto.iloc[0]["xs_norm"], df_pareto.iloc[0]["q_norm"]
    x2, y2 = df_pareto.iloc[-1]["xs_norm"], df_pareto.iloc[-1]["q_norm"]

    # Distancia a la recta
    a = y2 - y1
    b = -(x2 - x1)
    c = x2 * y1 - y2 * x1
    norma = np.sqrt(a**2 + b**2)

    distancias = []
    for _, row in df_pareto.iterrows():
        x0, y0 = row["xs_norm"], row["q_norm"]
        d = abs(a * x0 + b * y0 + c) / norma if norma != 0 else 0.0
        distancias.append(d)

    df_pareto["distancia_knee"] = distancias
    knee_point = df_pareto.loc[df_pareto["distancia_knee"].idxmax()].to_dict()

    return df_grid, df_pareto, knee_point
