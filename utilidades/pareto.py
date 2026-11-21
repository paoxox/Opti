import numpy as np
import pandas as pd

def frontera_pareto(factibles: pd.DataFrame) -> pd.DataFrame:
    if factibles.empty:
        return factibles.copy()
    d = factibles.assign(f1=1.0 - factibles["X_S"])
    d = d.sort_values(["f1", "Q_kJh"], kind="mergesort").reset_index(drop=True)
    mejor_q = np.inf
    mantener = []
    for q in d["Q_kJh"].to_numpy():
        if q < mejor_q:
            mantener.append(True)
            mejor_q = q
        else:
            mantener.append(False)
    return d[mantener].reset_index(drop=True)

def _normalizar(v: np.ndarray) -> np.ndarray:
    rango = v.max() - v.min()
    return np.zeros_like(v) if rango == 0 else (v - v.min()) / rango

def punto_rodilla(frontera: pd.DataFrame):
    if len(frontera) < 3:
        return 0, np.zeros(len(frontera))
    f1 = _normalizar((1.0 - frontera["X_S"]).to_numpy())
    f2 = _normalizar(frontera["Q_kJh"].to_numpy())
    p = np.column_stack([f1, f2])
    a, b = p[0], p[-1]
    ab = b - a
    norma = np.hypot(*ab)
    if norma == 0:
        return 0, np.zeros(len(p))
    # producto cruz 2D / |ab| = distancia perpendicular
    dist = np.abs(ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) / norma
    return int(np.argmax(dist)), dist

def rodilla_vs_peso_energia(frontera: pd.DataFrame, pesos=None) -> pd.DataFrame:
    if pesos is None:
        pesos = np.linspace(0.05, 0.95, 19)
    f1 = _normalizar((1.0 - frontera["X_S"]).to_numpy())
    f2 = _normalizar(frontera["Q_kJh"].to_numpy())
    filas = []
    for w in pesos:
        i = int(np.argmin(w * f2 + (1 - w) * f1))
        fila = frontera.iloc[i]
        filas.append({"peso_energia": float(w), "T_in": fila["T_in"], "eps": fila["eps"],
                      "X_S": fila["X_S"], "S_out": fila["S_out"], "Q_kW": fila["Q_kW"]})
    return pd.DataFrame(filas)
    knee_point = df_pareto.loc[df_pareto["distancia_knee"].idxmax()].to_dict()

    return df_grid, df_pareto, knee_point
