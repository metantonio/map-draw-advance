from branca.element import Template, MacroElement
import time

def leyenda(htmlMap, map_title="Map Draw Advance", cajetin_info=None):
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

    template = f"""
    {{% macro html(this, kwargs) %}}

    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
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

      /* ESTILOS DE IMPRESIÓN Y EXPORTACIÓN PDF (CAJETÍN DE PLANO TÉCNICO DE INGENIERÍA) */
      @media print {{
        @page {{
          size: A4 landscape;
          margin: 8mm;
        }}

        body {{
          background: white !important;
          margin: 0 !important;
          padding: 0 !important;
        }}

        /* ELIMINAR FONDO BLANCO Y SOMBRAS EN ICONOS DE MARCADORES */
        .leaflet-marker-shadow {{
          display: none !important;
        }}

        .leaflet-marker-icon,
        .awesome-marker,
        .leaflet-div-icon,
        .awesome-marker i {{
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          filter: none !important;
        }}

        /* Ocultar Todos los Menús Contextuales y Botones del Mapa */
        .leaflet-control-zoom,
        .leaflet-control-layers,
        .leaflet-draw,
        .leaflet-draw-toolbar,
        .leaflet-control-fullscreen,
        .leaflet-control-measure,
        .no-print {{
          display: none !important;
        }}

        /* Ocultar Leyenda Flotante Normal */
        #maplegend {{
          display: none !important;
        }}

        /* Mostrar Cajetín de Plano de Ingeniería en Esquina Inferior Derecha */
        #cajetin-plano {{
          display: block !important;
          position: fixed !important;
          bottom: 10mm !important;
          right: 10mm !important;
          width: 340px !important;
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
          font-size: 9px !important;
        }}

        .cajetin-table td {{
          border: 1px solid #000000 !important;
          padding: 4px 6px !important;
          vertical-align: top !important;
        }}

        .cajetin-label {{
          font-weight: bold !important;
          font-size: 8px !important;
          color: #333333 !important;
          text-transform: uppercase !important;
          display: block !important;
        }}

        .cajetin-val {{
          font-size: 9px !important;
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
        </tr>
        <tr>
          <td colspan="2">
            <span class="cajetin-label">SISTEMA & NOTAS</span>
            <span class="cajetin-val" id="cj-val-notas">{cajetin_info.get('notas', 'WGS-84 / UTM Transverse Mercator')}</span>
          </td>
        </tr>
        <tr>
          <td colspan="2">
            <span class="cajetin-label">LEYENDA DE RADIACIÓN RF (ATENUACIÓN NO LINEAL)</span>
            <div style="margin-top: 2px; font-size: 8px;">
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
