import numpy as np
import pandas as pd

# Constantes fijas del modelo
R_GAS = 8.314  # J/(mol*K)
T_ALIM = 300.0  # K
X_CALIB = 0.985
T_CALIB = 600.0  # K
TAU_CALIB = 0.5  # h
EA_CALIB = 80000.0  # J/mol
DT_AD_MAX = 15.0  # K

def calcular_k0(ea: float = EA_CALIB, tau: float = TAU_CALIB, x_ref: float = X_CALIB, t_ref: float = T_CALIB) -> float:
    """Calcula el factor preexponencial calibrado k0 [h^-1]."""
    return -np.log(1.0 - x_ref) / (tau * np.exp(-ea / (R_GAS * t_ref)))

def evaluar_hds(t_in, epsilon, m_dot, s_in, cp, ea, k0, tau):
    """Evalúa cinética, calidad de nafta, balance térmico y carga del horno."""
    k_t = k0 * np.exp(-ea / (R_GAS * t_in))
    x_s = 1.0 - np.exp(-k_t * tau)
    s_out = s_in * (1.0 - x_s)
    factible = s_out <= 10.0

    delta_t_ad = DT_AD_MAX * x_s
    t_efluente = t_in + delta_t_ad
    t_intercambiador = T_ALIM + epsilon * (t_efluente - T_ALIM)

    q_horno_kjh = m_dot * cp * (t_in - t_intercambiador)
    q_horno_kw = q_horno_kjh / 3600.0

    return {
        "Tin_K": t_in, "epsilon": epsilon, "k_h-1": k_t, "Xs": x_s,
        "Sout_ppm": s_out, "factible": factible, "dT_ad_K": delta_t_ad,
        "T_efluente_K": t_efluente, "T_intercambiador_K": t_intercambiador,
        "Q_horno_kJ_h": q_horno_kjh, "Q_horno_kW": q_horno_kw,
    }

def calcular_sensibilidad(t_in_base, eps_base, m_dot_base, s_in_base, cp_base, ea_base, k0_base, tau_base):
    """Genera la tabla de sensibilidad ±10% corrigiendo la coherencia de k0, Ea y tau."""
    caso_base = evaluar_hds(t_in_base, eps_base, m_dot_base, s_in_base, cp_base, ea_base, k0_base, tau_base)
    parametros = [("Flujo másico (ṁ)", "m_dot", m_dot_base), ("Capacidad calorífica (Cp)", "cp", cp_base), 
                  ("Energía de activación (Ea)", "ea", ea_base), ("Factor preexponencial (k0)", "k0", k0_base),
                  ("Tiempo espacial (tau)", "tau", tau_base), ("Efectividad (ε)", "epsilon", eps_base)]
    
    filas = []
    for nombre, clave, val_base in parametros:
        for factor, etiqueta in [(0.90, "-10%"), (1.10, "+10%")]:
            kwargs = {"t_in": t_in_base, "epsilon": eps_base, "m_dot": m_dot_base, "s_in": s_in_base, "cp": cp_base, "ea": ea_base, "k0": k0_base, "tau": tau_base}
            val_pert = val_base * factor
            if clave == "epsilon": val_pert = min(max(val_pert, 0.0), 1.0)
            kwargs[clave] = val_pert
            
            # Si se perturba Ea o tau, recalcular k0 para mantener la coherencia física de la calibración
            if clave in ["ea", "tau"]: kwargs["k0"] = calcular_k0(kwargs["ea"], kwargs["tau"])
            
            res = evaluar_hds(**kwargs)
            delta_q_pct = ((res["Q_horno_kW"] - caso_base["Q_horno_kW"]) / abs(caso_base["Q_horno_kW"]) * 100.0) if abs(caso_base["Q_horno_kW"]) > 1e-9 else 0.0
            delta_s_pct = ((res["Sout_ppm"] - caso_base["Sout_ppm"]) / caso_base["Sout_ppm"] * 100.0) if caso_base["Sout_ppm"] > 0 else 0.0

            filas.append({"Parámetro": nombre, "Perturbación": etiqueta, "Valor": f"{val_pert:.4g}", 
                          "Q_horno (kW)": round(res["Q_horno_kW"], 2), "ΔQ (%)": round(delta_q_pct, 2),
                          "Sout (ppm)": round(res["Sout_ppm"], 3), "ΔSout (%)": round(delta_s_pct, 2), "Factible": "Sí" if res["factible"] else "No"})
    return pd.DataFrame(filas)
