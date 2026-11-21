# HDS multiobjetivo con Streamlit

Aplicación para estudiar el compromiso entre conversión de azufre y carga térmica del
horno en una unidad de hidrodesulfuración simplificada.

## Estructura

```
app.py                 interfaz (controles, pestañas, métricas)
requirements.txt
.streamlit/config.toml tema
utilidades/
    modelo.py          cinética, balance térmico, sensibilidad y validaciones
    pareto.py          frontera de Pareto, knee point, estudio de peso de energía
    graficos.py        figuras de Plotly
    carga.py           funciones con st.cache_data
```

## Qué incluye

- Controles para Tin, ε y los parámetros del modelo
- Malla Tin × ε con marcado de factibilidad (Sout ≤ 10 ppm).
- Frontera de Pareto (sin puntos dominados) y knee point por distancia perpendicular
  con objetivos normalizados min-max.
- Sensibilidad ±10 % en ṁ, Cp, Ea, k₀ y τ; barrido de Sin entre 450 y 550 ppm.
- Los tres sanity checks de validación.
- Estudio opcional de la rodilla frente al peso de la energía.
