from branca.element import Template, MacroElement

def leyenda(htmlMap, map_title="Map Draw Advance"):
    template = f"""
    {{% macro html(this, kwargs) %}}

    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{map_title}</title>
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
      @media print {{
        .leaflet-control-container .leaflet-top.leaflet-left,
        .leaflet-control-container .leaflet-top.leaflet-right {{
            display: none !important;
        }}
        .no-print {{
            display: none !important;
        }}
        #maplegend {{
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 99999 !important;
            background: white !important;
            border: 2px solid #333 !important;
            box-shadow: none !important;
        }}
        body {{
            background: white !important;
        }}
      }}
      </style>
    </head>
    <body>

    <!-- Leyenda Flotante -->
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
