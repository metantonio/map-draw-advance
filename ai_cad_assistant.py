"""
ai_cad_assistant.py - Asistente de IA para Comandos en Lenguaje Natural
Permite conectar con Ollama (y otros proveedores) o utilizar un motor de parsing
estructurado para traducir órdenes como:
"Dibuja una nube de radiales en (730000, 1160000) con radios en km de 10.5, 15, 20, 15.2, 10 y un incremento de 20 grados"
a geometrías exactas en el mapa y plano CAD.
"""

import re
import json
import requests

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:7b"

SYSTEM_PROMPT = """Eres el Asistente CAD & Geoespacial de 'Map Draw Advance'.
Tu objetivo es traducir las órdenes en lenguaje natural del usuario a acciones geométricas precisas para el mapa y plano CAD.

DEBES responder EXCLUSIVAMENTE con un JSON válido (sin texto antes ni después) con este esquema exacto:
{
  "explanation": "Explicación breve y amigable en español de lo realizado",
  "actions": [
    {
      "action": "add_radiation_cloud" | "add_circle" | "add_points" | "add_line" | "clear",
      "params": { ... }
    }
  ]
}

Parámetros admitidos por cada acción:
1. "add_radiation_cloud":
   - "center": [norte/y, este/x] o [latitud, longitud] (por defecto [0.0, 0.0]; admite UTM ej: [730000, 1160000] o grados ej: [10.488, -66.889])
   - "radii": [radio1, radio2, ...] (lista de números en km)
   - "angle_start": 0.0 (en grados, 0º a 360º)
   - "angle_step": 20.0 (incremento en grados entre cada radial)
   - "label": "Nombre del patrón" (opcional)
   - "color": "red" | "blue" | "green" | "yellow" (opcional)

2. "add_circle":
   - "center": [latitud, longitud]
   - "radius": radio_en_metros (número)

3. "add_points":
   - "points": [ {"lat": float, "lon": float, "label": "Nombre", "color": "blue"} ]

4. "add_line":
   - "points": [ [lat1, lon1], [lat2, lon2], ... ]

5. "clear":
   - "target": "all" | "radiacion" | "linea" | "circulo" | "localizacion"
"""

def check_llm_status(api_url=DEFAULT_OLLAMA_URL):
    """
    Verifica si el servidor LLM está activo. Detecta automáticamente si es
    Ollama (puerto 11434 /api/tags) o llama.cpp / OpenAI-compatible (puerto 8080 /v1/models o /health).
    """
    clean_url = (api_url or DEFAULT_OLLAMA_URL).rstrip('/')

    # 1. Probar endpoint nativo de Ollama (/api/tags)
    try:
        resp = requests.get(f"{clean_url}/api/tags", timeout=1.8)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get('name') for m in data.get('models', []) if m.get('name')]
            return {
                'online': True,
                'provider': 'Ollama',
                'models': models,
                'default_model': DEFAULT_MODEL if DEFAULT_MODEL in models else (models[0] if models else DEFAULT_MODEL),
                'url': clean_url
            }
    except Exception:
        pass

    # 2. Probar endpoint de llama.cpp / OpenAI (/v1/models o /health)
    try:
        resp_models = requests.get(f"{clean_url}/v1/models", timeout=1.8)
        if resp_models.status_code == 200:
            data = resp_models.json()
            models = [m.get('id') for m in data.get('data', []) if m.get('id')]
            return {
                'online': True,
                'provider': 'llama.cpp',
                'models': models if models else ['default'],
                'default_model': models[0] if models else 'default',
                'url': clean_url
            }
    except Exception:
        pass

    try:
        resp_health = requests.get(f"{clean_url}/health", timeout=1.5)
        if resp_health.status_code == 200:
            return {
                'online': True,
                'provider': 'llama.cpp',
                'models': ['llama.cpp (activo)'],
                'default_model': 'llama.cpp (activo)',
                'url': clean_url
            }
    except Exception:
        pass

    return {
        'online': False,
        'provider': 'Desconectado',
        'models': [],
        'default_model': DEFAULT_MODEL,
        'url': clean_url
    }

# Alias para compatibilidad hacia atrás
check_ollama_status = check_llm_status

def fallback_regex_parser(prompt, current_data):
    """
    Parser determinista de reserva (Rule-based NLP).
    Garantiza que órdenes directas como:
    'Dibuja una nube de radiales en (730000, 1160000) con radios en km de 10.5, 15, 20, 15.2, 10 y un incremento de 20 grados'
    funcionen siempre, incluso si Ollama no está iniciado en ese instante.
    """
    text = prompt.strip().lower()

    # 1. Nube de radiales
    if 'radial' in text or 'radiacion' in text or 'rayos' in text:
        # Extraer centro: (x, y) o en x, y
        center = [0.0, 0.0]
        coord_match = re.search(r'\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)', text)
        if coord_match:
            center = [float(coord_match.group(1)), float(coord_match.group(2))]
        else:
            coord_alt = re.search(r'en\s+([-\d\.]+)\s*,\s*([-\d\.]+)', text)
            if coord_alt:
                center = [float(coord_alt.group(1)), float(coord_alt.group(2))]

        # Extraer radios
        radii = []
        # Buscar radios luego de "radios" o "radio" (ej: "radios 10.5, 15", "radios en km de 10.5, 15, ...", "radios de 10.5, 15")
        radios_match = re.search(r'radios?\s*(?:(?:en\s+(?:km|m|metros))?\s*(?:de)?)?\s*([0-9\.,\s]+?)(?:y\s+un|con\s+un|incremento|grados|$)', text)
        if radios_match:
            tokens = re.split(r'[,;\s]+', radios_match.group(1).strip())
            for t in tokens:
                try:
                    if t:
                        radii.append(float(t))
                except ValueError:
                    continue
        if not radii:
            # Fallback general de todos los números flotantes
            all_floats = [float(x) for x in re.findall(r'\b\d+(?:\.\d+)?\b', text)]
            if len(all_floats) >= 2:
                radii = all_floats

        # Extraer incremento de ángulo
        step_match = re.search(r'incremento\s*(?:de)?\s*([0-9\.]+)\s*(?:grados|deg|°)?', text)
        angle_step = float(step_match.group(1)) if step_match else 20.0

        # Extraer ángulo inicial
        start_match = re.search(r'(?:inicio|iniciando|desde)\s*(?:en)?\s*([0-9\.]+)\s*(?:grados|deg|°)?', text)
        angle_start = float(start_match.group(1)) if start_match else 0.0

        if not radii:
            radii = [10.5, 15.0, 20.0, 15.2, 10.0]

        c_display_0 = f"{int(center[0]) if center[0].is_integer() else center[0]}"
        c_display_1 = f"{int(center[1]) if center[1].is_integer() else center[1]}"
        step_display = f"{int(angle_step) if angle_step.is_integer() else angle_step}"
        return {
            'explanation': f'Se generó una nube de {len(radii)} radiales centrada en ({c_display_0}, {c_display_1}) con paso angular de {step_display}º.',
            'actions': [{
                'action': 'add_radiation_cloud',
                'params': {
                    'center': center,
                    'radii': radii,
                    'angle_start': angle_start,
                    'angle_step': angle_step,
                    'label': 'Nube Radial AI',
                    'color': 'red'
                }
            }]
        }

    # 2. Círculo
    if 'circulo' in text or 'círculo' in text:
        center = [0.0, 0.0]
        coord_match = re.search(r'\(\s*([-\d\.]+)\s*,\s*([-\d\.]+)\s*\)', text)
        if coord_match:
            center = [float(coord_match.group(1)), float(coord_match.group(2))]
        rad_match = re.search(r'radio\s*(?:de)?\s*([0-9\.]+)\s*(?:m|metros|km)?', text)
        radius = 500.0
        if rad_match:
            val = float(rad_match.group(1))
            radius = val * 1000.0 if 'km' in text else val

        return {
            'explanation': f'Círculo creado con centro en ({center[0]}, {center[1]}) y radio de {radius} m.',
            'actions': [{
                'action': 'add_circle',
                'params': {
                    'center': center,
                    'radius': radius
                }
            }]
        }

    # 3. Limpiar
    if 'limpia' in text or 'borra' in text or 'elimina' in text:
        target = 'all'
        if 'radial' in text: target = 'radiacion'
        elif 'linea' in text or 'poligono' in text: target = 'linea'
        elif 'circulo' in text: target = 'circulo'
        elif 'punto' in text: target = 'localizacion'
        return {
            'explanation': f'Capa(s) {target} vaciada(s) según la instrucción.',
            'actions': [{'action': 'clear', 'params': {'target': target}}]
        }

    return None

def _normalize_center_coords(val1, val2):
    """
    Normaliza un par de coordenadas (val1, val2). Si se detecta que están
    en formato métrico UTM (e.g. 730000, 1160000), las convierte a grados WGS84
    para su correcta representación en el visor Folium y cálculos de azimut/distancia.
    """
    v1, v2 = float(val1), float(val2)
    if abs(v1) > 90 or abs(v2) > 180:
        try:
            from eqa2utm import utm2gms
            if v1 < v2:
                este_m, norte_m = v1, v2
            else:
                norte_m, este_m = v1, v2
            lat_conv, lon_conv = utm2gms(norte_m, este_m, huso=19)
            if abs(lat_conv) <= 90 and abs(lon_conv) <= 180:
                return lat_conv, lon_conv
        except Exception:
            pass
    return v1, v2

def apply_actions_to_data(actions, current_data):
    """
    Aplica la lista de acciones a las 4 capas de datos:
    localizacion, linea, circulo, radiacion.
    Retorna el estado de datos actualizado y un conteo de entidades creadas.
    """
    loc = list(current_data.get('localizacion', []))
    lin = list(current_data.get('linea', []))
    cir = list(current_data.get('circulo', []))
    rad = list(current_data.get('radiacion', []))

    created_summary = []

    for item in actions:
        act = item.get('action')
        params = item.get('params', {})

        if act == 'add_radiation_cloud':
            center = params.get('center', [0.0, 0.0])
            c_lat, c_lon = _normalize_center_coords(center[0], center[1])
            radii = params.get('radii', [10.0])
            ang_start = float(params.get('angle_start', 0.0))
            ang_step = float(params.get('angle_step', 20.0))
            label = params.get('label', 'Radial AI')
            color = params.get('color', 'red')

            count_rays = 0
            for i, r in enumerate(radii):
                try:
                    cur_ang = (ang_start + i * ang_step) % 360.0
                    dist = float(r)
                    rad.append({
                        'norte': round(c_lat, 6),
                        'este': round(c_lon, 6),
                        'angulo': round(cur_ang, 2),
                        'distancia': round(dist, 3),
                        'etiqueta': f"{label}_{i+1}",
                        'color': color
                    })
                    count_rays += 1
                except Exception:
                    continue
            created_summary.append(f"{count_rays} radiales")

        elif act == 'add_circle':
            center = params.get('center', [0.0, 0.0])
            c_lat = float(center[0])
            c_lon = float(center[1])
            r_val = float(params.get('radius', 500.0))
            cir.append({
                'norte': round(c_lat, 6),
                'este': round(c_lon, 6),
                'radio': round(r_val, 2)
            })
            created_summary.append(f"1 círculo (R={r_val}m)")

        elif act == 'add_points':
            pts = params.get('points', [])
            count_p = 0
            for p in pts:
                try:
                    lat = float(p.get('lat', 0.0))
                    lon = float(p.get('lon', 0.0))
                    lbl = p.get('label', f'Punto_{len(loc)+1}')
                    col = p.get('color', 'blue')
                    loc.append({
                        'norte': round(lat, 6),
                        'este': round(lon, 6),
                        'color': col,
                        'tipo': 'Default',
                        'direccion': '',
                        'sobrenombre': lbl
                    })
                    count_p += 1
                except Exception:
                    continue
            created_summary.append(f"{count_p} puntos")

        elif act == 'add_line':
            pts = params.get('points', [])
            count_v = 0
            for p in pts:
                try:
                    lat = float(p[0])
                    lon = float(p[1])
                    lin.append({'norte': round(lat, 6), 'este': round(lon, 6)})
                    count_v += 1
                except Exception:
                    continue
            created_summary.append(f"polilínea con {count_v} vértices")

        elif act == 'clear':
            target = params.get('target', 'all')
            if target in ['all', 'localizacion']: loc = []
            if target in ['all', 'linea']: lin = []
            if target in ['all', 'circulo']: cir = []
            if target in ['all', 'radiacion']: rad = []
            created_summary.append(f"capa(s) '{target}' limpiadas")

    updated_data = {
        'localizacion': loc,
        'linea': lin,
        'circulo': cir,
        'radiacion': rad
    }

    return updated_data, created_summary

def execute_ai_command(prompt, current_data, model=DEFAULT_MODEL, api_url=DEFAULT_OLLAMA_URL):
    """
    Punto de entrada principal para procesar una orden de lenguaje natural.
    Intenta primero consultar a Ollama con JSON Schema. Si no está disponible
    o falla, recurre al parser determinista de reserva.
    """
    clean_url = (api_url or DEFAULT_OLLAMA_URL).rstrip('/')
    ollama_error = None
    ai_result = None

    # Detectar o intentar endpoints
    # 1. Probar llama.cpp / OpenAI endpoint (/v1/chat/completions) si el puerto es 8080 o similar
    is_port_8080 = ':8080' in clean_url
    endpoints_to_try = []
    if is_port_8080:
        endpoints_to_try.append(('openai', f"{clean_url}/v1/chat/completions"))
        endpoints_to_try.append(('ollama', f"{clean_url}/api/chat"))
    else:
        endpoints_to_try.append(('ollama', f"{clean_url}/api/chat"))
        endpoints_to_try.append(('openai', f"{clean_url}/v1/chat/completions"))

    for ep_type, ep_url in endpoints_to_try:
        try:
            if ep_type == 'ollama':
                payload = {
                    "model": model or DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "format": "json"
                }
            else: # openai / llama.cpp
                payload = {
                    "model": model or "default",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }

            resp = requests.post(ep_url, json=payload, timeout=25)
            if resp.status_code == 200:
                res_json = resp.json()
                content = ''
                if 'message' in res_json: # Ollama
                    content = res_json.get('message', {}).get('content', '')
                elif 'choices' in res_json and len(res_json['choices']) > 0: # llama.cpp / OpenAI
                    content = res_json['choices'][0].get('message', {}).get('content', '')

                if content:
                    # Limpiar markdown si el modelo incluye ```json
                    clean_content = content.strip()
                    if clean_content.startswith('```'):
                        clean_content = re.sub(r'^```(?:json)?\s*', '', clean_content)
                        clean_content = re.sub(r'\s*```$', '', clean_content)
                    parsed = json.loads(clean_content)
                    if isinstance(parsed, dict) and 'actions' in parsed:
                        ai_result = parsed
                        break
            else:
                ollama_error = f"Servidor ({ep_url}) respondió con código {resp.status_code}"
        except Exception as e:
            ollama_error = f"Error conectando con {ep_url}: {e}"

    # Si ningún servidor respondió o falló, utilizar el parser de reserva
    if not ai_result:
        fallback = fallback_regex_parser(prompt, current_data)
        if fallback:
            ai_result = fallback
            if ollama_error:
                ai_result['explanation'] += f" [Modo Local Autónomo: Ollama no estaba accesible en {clean_url}]"
        else:
            return {
                'status': 'error',
                'message': f"No se pudo interpretar la orden. Detalle: {ollama_error or 'Instrucción no reconocida.'}. Ejemplo: 'Dibuja una nube de radiales en (0, 0) con radios 10.5, 15, 20, 15.2, 10 y un incremento de 20 grados.'"
            }

    # Aplicar acciones a los datos
    updated_data, summary = apply_actions_to_data(ai_result.get('actions', []), current_data)

    return {
        'status': 'ok',
        'explanation': ai_result.get('explanation', 'Comando procesado correctamente.'),
        'summary': summary,
        'actions': ai_result.get('actions', []),
        'data': updated_data
    }
