from branca.element import Template, MacroElement
import time

def leyenda(htmlMap, map_title="Map Draw Advance", cajetin_info=None, puntos_cajetin=None, patrones_cajetin=None):
    if not cajetin_info:
        cajetin_info = {
            'titulo': 'MAP DRAW ADVANCE v2.0 — PLANO GEOESPACIAL',
            'proyecto': 'Levantamiento de Coordenadas & Patrón de Radiación RF',
            'cliente': 'General',
            'autor': 'Antonio Martínez (@metantonio)',
            'revisado': 'Ing. Coordinador',
            'fecha': time.strftime("%d/%m/%Y"),
            'notas': 'WGS-84 / UTM Transverse Mercator'
        }

    if puntos_cajetin is None:
        puntos_cajetin = []
    if patrones_cajetin is None:
        patrones_cajetin = []

    # Construir HTML de la tabla de puntos dentro del Cajetín
    puntos_html = ""
    if puntos_cajetin:
        puntos_rows = ""
        for pt in puntos_cajetin[:10]: # Limitar a los primeros 10 para ajustar espacio en cajetín
            puntos_rows += f"""
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">{pt.get('nombre', 'Punto')}</td>
              <td style="border: 1px solid #000; padding: 2px 4px;">{pt.get('wgs84', '')}</td>
              <td style="border: 1px solid #000; padding: 2px 4px;">{pt.get('utm', '')}</td>
            </tr>
            """
        puntos_html = f"""
        <tr>
          <td colspan="2" style="padding: 0;">
            <div style="background: #000000; color: #ffffff; font-size: 8px; font-weight: bold; padding: 2px 4px; text-transform: uppercase; text-align: center;">
              📍 VÉRTICES & PUNTOS DE INTERÉS
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:8px; background:#fff;">
              <thead>
                <tr style="background:#e2e8f0; font-weight:bold; font-size:7.5px; text-transform:uppercase;">
                  <td style="border:1px solid #000; padding:2px 4px;">Etiqueta</td>
                  <td style="border:1px solid #000; padding:2px 4px;">WGS-84 (Lat, Lon)</td>
                  <td style="border:1px solid #000; padding:2px 4px;">UTM (Norte, Este, Huso)</td>
                </tr>
              </thead>
              <tbody>
                {puntos_rows}
              </tbody>
            </table>
          </td>
        </tr>
        """

    # Construir HTML de la tabla de Patrones de Radiación dentro del Cajetín
    patrones_html = ""
    if patrones_cajetin:
        patrones_rows = ""
        for p in patrones_cajetin:
            c_box = f'<span class="legend-color-box" style="background:{p.get("color", "#8e44ad")}; width:12px; height:8px; display:inline-block; margin-right:4px;"></span>'
            patrones_rows += f"""
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">{c_box}{p.get('etiqueta', 'Patrón')}</td>
              <td style="border: 1px solid #000; padding: 2px 4px;">{p.get('wgs84', '')}</td>
              <td style="border: 1px solid #000; padding: 2px 4px;">{p.get('utm', '')}</td>
              <td style="border: 1px solid #000; padding: 2px 4px; text-align:center;">{p.get('max_dist', '')}</td>
            </tr>
            """
        patrones_html = f"""
        <tr>
          <td colspan="2" style="padding: 0;">
            <div style="background: #1e293b; color: #ffffff; font-size: 8px; font-weight: bold; padding: 2px 4px; text-transform: uppercase; text-align: center;">
              📡 PATRONES DE RADIACIÓN RF REGISTRADOS
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:8px; background:#fff;">
              <thead>
                <tr style="background:#e2e8f0; font-weight:bold; font-size:7.5px; text-transform:uppercase;">
                  <td style="border:1px solid #000; padding:2px 4px;">Patrón / Etiqueta</td>
                  <td style="border:1px solid #000; padding:2px 4px;">Centro WGS-84</td>
                  <td style="border:1px solid #000; padding:2px 4px;">Centro UTM</td>
                  <td style="border:1px solid #000; padding:2px 4px; text-align:center;">Alcance Máx</td>
                </tr>
              </thead>
              <tbody>
                {patrones_rows}
              </tbody>
            </table>
          </td>
        </tr>
        """

    # Construir HTML de la leyenda flotante en pantalla
    patrones_legend_ui = ""
    if patrones_cajetin:
        items_ui = ""
        for p in patrones_cajetin:
            items_ui += f"""<li style='display:flex; align-items:center; margin-bottom:3px;'><span style='background:{p.get("color", "#8e44ad")}; width:16px; height:12px; display:inline-block; border-radius:2px; margin-right:8px; border:1px solid #333;'></span><b>{p.get("etiqueta")}</b> &nbsp;<span style="color:#64748b; font-size:10px;">({p.get("max_dist")})</span></li>"""
        patrones_legend_ui = f"""
        <div style="margin-top:8px; border-top:1px solid #cbd5e1; padding-top:6px;">
          <div style="font-size:11px; font-weight:bold; color:#0f172a; margin-bottom:4px;">📡 Patrones de Radiación ({len(patrones_cajetin)}):</div>
          <ul style='list-style:none; padding:0; margin:0; font-size:11px;'>
            {items_ui}
          </ul>
        </div>
        """

    template = f"""
    {{% macro html(this, kwargs) %}}

    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{map_title} - Plano Geoespacial</title>
      <link rel="stylesheet" href="https://code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">

      <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
      <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>

      <script>
      $( function() {{
        $( "#maplegend" ).draggable({{
            containment: "window",
            start: function (event, ui) {{
                $(this).css({{
                    right: "auto",
                    bottom: "auto"
                }});
            }}
        }});
      }});

      function printMapPDF() {{
        window.print();
      }}
      </script>

      <style>
      /* Estilos para Pantalla Normal */
      #cajetin-plano {{
        display: none;
      }}

      /* ESTILOS DE ETIQUETAS PERMANENTES DE MARCADORES */
      .leaflet-tooltip.marker-label-style {{
        background-color: rgba(255, 255, 255, 0.92) !important;
        border: 1px solid #1e293b !important;
        border-radius: 4px !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        padding: 2px 6px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25) !important;
        white-space: nowrap !important;
      }}

      .leaflet-tooltip-bottom:before {{
        border-bottom-color: #1e293b !important;
      }}

      /* ESTILOS ETIQUETAS DE BORDES DE GRILLA */
      .grid-edge-marker {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        overflow: visible !important;
        z-index: 99999 !important;
      }}

      .grid-edge-label {{
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1.5px solid #38bdf8 !important;
        border-radius: 4px !important;
        font-family: Consolas, Monaco, monospace !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        padding: 3px 6px !important;
        white-space: nowrap !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.4) !important;
        pointer-events: none !important;
        display: inline-block !important;
      }}

      .grid-edge-top {{ transform: translate(-50%, 0%); margin-top: 2px; }}
      .grid-edge-bottom {{ transform: translate(-50%, -100%); margin-top: -2px; }}
      .grid-edge-left {{ transform: translate(0%, -50%); margin-left: 2px; }}
      .grid-edge-right {{ transform: translate(-100%, -50%); margin-left: -2px; }}

      /* ESTILOS DE IMPRESIÓN Y EXPORTACIÓN PDF */
      @media print {{
        * {{
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
          color-adjust: exact !important;
        }}

        @page {{
          size: A4 landscape;
          margin: 6mm;
        }}

        body {{
          background: white !important;
          margin: 0 !important;
          padding: 0 !important;
        }}

        .leaflet-container {{
          background: #ffffff !important;
        }}

        .leaflet-tile {{
          opacity: 1 !important;
          visibility: visible !important;
          filter: none !important;
        }}

        /* ETIQUETAS VISIBLES E IMPRESAS DEBAJO DE LOS MARCADORES */
        .leaflet-tooltip {{
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          background: #ffffff !important;
          color: #000000 !important;
          border: 1px solid #000000 !important;
          font-weight: bold !important;
          font-size: 10px !important;
          box-shadow: none !important;
        }}

        /* ETIQUETAS DE BORDES DE GRILLA (SIEMPRE VISIBLES CON FONDO BLANCO Y BORDE NEGRO) */
        .grid-edge-label {{
          display: inline-block !important;
          visibility: visible !important;
          opacity: 1 !important;
          background: #ffffff !important;
          background-color: #ffffff !important;
          color: #000000 !important;
          border: 2px solid #000000 !important;
          border-radius: 3px !important;
          font-weight: 800 !important;
          font-size: 10px !important;
          padding: 2px 6px !important;
          z-index: 9999999 !important;
          box-shadow: none !important;
          white-space: nowrap !important;
        }}

        /* ELIMINAR FONDO BLANCO Y SOMBRAS EN ICONOS DE MARCADORES (EXCLUYENDO ETIQUETAS DE GRILLA) */
        .leaflet-marker-shadow {{
          display: none !important;
        }}

        .leaflet-marker-icon:not(.grid-edge-label),
        .awesome-marker,
        .leaflet-div-icon:not(.grid-edge-label),
        .awesome-marker i {{
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          filter: none !important;
        }}

        /* Ocultar Todos los Menús Contextuales, Botones y Cuadro de Coordenadas del Mapa */
        .leaflet-control-zoom,
        .leaflet-control-layers,
        .leaflet-draw,
        .leaflet-draw-toolbar,
        .leaflet-control-fullscreen,
        .leaflet-control-measure,
        .leaflet-control-mouseposition,
        .leaflet-container .leaflet-control-mouseposition,
        .no-print {{
          display: none !important;
        }}

        /* Barra de Escala Gráfica Única en Sistema Internacional (Metros / Km) Centrada en Borde Inferior */
        .leaflet-control-scale {{
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          position: fixed !important;
          bottom: 10mm !important;
          left: 50% !important;
          transform: translateX(-50%) !important;
          margin: 0 !important;
          z-index: 9999999 !important;
        }}

        .leaflet-control-scale-line {{
          background: rgba(255, 255, 255, 0.95) !important;
          border: 2px solid #000000 !important;
          border-top: none !important;
          color: #000000 !important;
          font-weight: 800 !important;
          font-size: 10.5px !important;
          padding: 2px 8px !important;
          box-shadow: none !important;
          text-align: center !important;
          line-height: 1.2 !important;
        }}

        /* Ocultar Estrictamente Escala en Millas o Pies */
        .leaflet-control-scale-line:not(:first-child),
        .leaflet-control-scale-line:nth-child(2) {{
          display: none !important;
        }}

        /* Clase para ocultar explícitamente el Cajetín si el usuario lo desea */
        .hide-cajetin-print {{
          display: none !important;
        }}

        /* Cajetín de Plano de Ingeniería */
        #cajetin-plano {{
          display: block;
          position: fixed !important;
          bottom: 10mm !important;
          right: 10mm !important;
          width: 360px !important;
          background: #ffffff !important;
          border: 2.5px solid #000000 !important;
          box-shadow: none !important;
          z-index: 9999999 !important;
          font-family: Arial, Helvetica, sans-serif !important;
          color: #000000 !important;
          padding: 0 !important;
        }}

        .cajetin-header {{
          background: #000000 !important;
          color: #ffffff !important;
          padding: 5px 8px !important;
          text-align: center !important;
          font-size: 10.5px !important;
          font-weight: bold !important;
          letter-spacing: 0.5px !important;
          text-transform: uppercase !important;
        }}

        .cajetin-table {{
          width: 100% !important;
          border-collapse: collapse !important;
          font-size: 8.5px !important;
        }}

        .cajetin-table td {{
          border: 1px solid #000000 !important;
          padding: 3px 5px !important;
          vertical-align: top !important;
        }}

        .cajetin-label {{
          font-weight: bold !important;
          font-size: 7.5px !important;
          color: #333333 !important;
          text-transform: uppercase !important;
          display: block !important;
        }}

        .cajetin-val {{
          font-size: 8.5px !important;
          color: #000000 !important;
          font-weight: 600 !important;
        }}

        .legend-color-box {{
          display: inline-block !important;
          width: 14px !important;
          height: 9px !important;
          margin-right: 4px !important;
          border: 1px solid #000 !important;
          vertical-align: middle !important;
        }}
      }}
      </style>
    </head>
    <body>

    <!-- Leyenda Flotante en Pantalla -->
    <div id='maplegend' class='maplegend' 
        style='position: absolute; z-index:9999; border:1px solid #ccc; background-color: rgba(255, 255, 255, 0.94);
         border-radius:8px; padding: 12px; font-size:13px; right: 20px; bottom: 40px; box-shadow: 0 4px 14px rgba(0,0,0,0.2); font-family: system-ui, -apple-system, sans-serif;'>

      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
        <button type="button" class="collapsible" style="cursor:pointer; background:none; border:none; font-weight:bold; font-size:13px; color:#2c3e50; outline:none; padding:0;">    
            🎨 Escala de Radiación RF
        </button> 
        <button onclick="printMapPDF()" class="no-print" style="cursor:pointer; background:#2563eb; color:white; border:none; border-radius:4px; padding:3px 8px; font-size:11px; font-weight:600; margin-left:10px;" title="Imprimir o Guardar PDF con Escala">
            🖨️ PDF
        </button>
      </div>

      <div class='legend-scale content' style='margin-top:6px; display:block;'>
        <ul class='legend-labels' style='list-style:none; padding:0; margin:0;'>
          <li style='display:flex; align-items:center; margin-bottom:3px;'><span style='background:#ff0000; opacity:0.9; width:26px; height:13px; display:inline-block; border-radius:2px; margin-right:8px; border:1px solid #777;'></span>100% (Centro Transmisor)</li>
          <li style='display:flex; align-items:center; margin-bottom:3px;'><span style='background:#ffff00; opacity:0.9; width:26px; height:13px; display:inline-block; border-radius:2px; margin-right:8px; border:1px solid #777;'></span>70%</li>
          <li style='display:flex; align-items:center; margin-bottom:3px;'><span style='background:#00af50; opacity:0.9; width:26px; height:13px; display:inline-block; border-radius:2px; margin-right:8px; border:1px solid #777;'></span>40%</li>
          <li style='display:flex; align-items:center; margin-bottom:3px;'><span style='background:#819fdd; opacity:0.9; width:26px; height:13px; display:inline-block; border-radius:2px; margin-right:8px; border:1px solid #777;'></span>20%</li>
          <li style='display:flex; align-items:center; margin-bottom:3px;'><span style='background:#ffcdfd; opacity:0.9; width:26px; height:13px; display:inline-block; border-radius:2px; margin-right:8px; border:1px solid #777;'></span>0% (Perímetro RF)</li>
        </ul>
        {patrones_legend_ui}
      </div>
    </div>

    <!-- CAJETÍN TÉCNICO DE PLANO (PERSONALIZABLE - VISIBILIDAD EXCLUSIVA AL IMPRIMIR EN PDF) -->
    <div id="cajetin-plano">
      <div class="cajetin-header" id="cj-hdr-titulo">
        {cajetin_info.get('titulo', 'MAP DRAW ADVANCE v2.0 — PLANO GEOESPACIAL')}
      </div>
      <table class="cajetin-table">
        <tr>
          <td colspan="2">
            <span class="cajetin-label">PROYECTO / DOCUMENTO</span>
            <span class="cajetin-val" id="cj-val-proyecto">{cajetin_info.get('proyecto', 'Levantamiento de Coordenadas & Patrón de Radiación RF')}</span>
          </td>
        </tr>
        <tr>
          <td>
            <span class="cajetin-label">CLIENTE / EMPRESA</span>
            <span class="cajetin-val" id="cj-val-cliente">{cajetin_info.get('cliente', 'General')}</span>
          </td>
          <td>
            <span class="cajetin-label">DIBUJADO POR</span>
            <span class="cajetin-val" id="cj-val-autor">{cajetin_info.get('autor', 'Antonio Martínez (@metantonio)')}</span>
          </td>
        </tr>
        <tr>
          <td>
            <span class="cajetin-label">REVISADO POR</span>
            <span class="cajetin-val" id="cj-val-revisado">{cajetin_info.get('revisado', 'Ing. Coordinador')}</span>
          </td>
          <td>
            <span class="cajetin-label">FECHA DE EMISIÓN</span>
            <span class="cajetin-val" id="cj-val-fecha">{cajetin_info.get('fecha', time.strftime("%d/%m/%Y"))}</span>
          </td>
          <td>
            <span class="cajetin-label">ESCALA DEL PLANO</span>
            <span class="cajetin-val" id="cj-val-escala">{cajetin_info.get('escala', '1:250000')}</span>
          </td>
        </tr>
        <tr>
          <td colspan="2">
            <span class="cajetin-label">SISTEMA & NOTAS</span>
            <span class="cajetin-val" id="cj-val-notas">{cajetin_info.get('notas', 'WGS-84 / UTM Transverse Mercator')}</span>
          </td>
        </tr>
        {puntos_html}
        {patrones_html}
        <tr>
          <td colspan="2">
            <span class="cajetin-label">LEYENDA DE RADIACIÓN RF (ATENUACIÓN NO LINEAL)</span>
            <div style="margin-top: 2px; font-size: 7.5px;">
              <span class="legend-color-box" style="background:#ff0000;"></span> 100% Centro
              <span class="legend-color-box" style="background:#ffff00; margin-left: 5px;"></span> 70%
              <span class="legend-color-box" style="background:#00af50; margin-left: 5px;"></span> 40%
              <span class="legend-color-box" style="background:#819fdd; margin-left: 5px;"></span> 20%
              <span class="legend-color-box" style="background:#ffcdfd; margin-left: 5px;"></span> 0% Perímetro
            </div>
          </td>
        </tr>
      </table>
    </div>

    <script>
        var coll = document.getElementsByClassName("collapsible");
        for (var i = 0; i < coll.length; i++) {{
          coll[i].addEventListener("click", function() {{
            var content = this.nextElementSibling;
            if (content.style.display === "none") {{
              content.style.display = "block";
            }} else {{
              content.style.display = "none";
            }}
          }});
        }}
    </script>
    </body>
    </html>
    {{% endmacro %}}"""

    macro = MacroElement()
    macro._template = Template(template)
    return htmlMap.get_root().add_child(macro)
