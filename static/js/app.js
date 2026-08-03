// Estado Global de la Aplicación
let currentData = {
  localizacion: [],
  linea: [],
  circulo: [],
  radiacion: []
};

let autoUpdateTimer = null;
let loadingSafetyTimeout = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadInitialData();
  bindEvents();
});

// Inicializar Pestañas del Editor
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const tabId = btn.getAttribute('data-tab');
      document.getElementById(tabId).classList.add('active');
    });
  });
}

// Cargar Datos Iniciales desde Servidor y Auto-Generar Mapa
async function loadInitialData() {
  try {
    const res = await fetch('/api/load-data');
    const json = await res.json();

    if (json.status === 'ok' && json.data) {
      currentData = json.data;
    }
    renderAllTables();
    
    // Auto-generar mapa en el primer inicio
    generateMap(true);
  } catch (err) {
    console.warn('No se pudieron cargar los datos iniciales:', err);
  }
}

// Eventos de Botones e Inputs
function bindEvents() {
  // Subir Excel
  document.getElementById('btnUploadExcel').addEventListener('click', () => {
    document.getElementById('excelFileInput').click();
  });

  document.getElementById('excelFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    showLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('grid_step', document.getElementById('gridStepSelect').value);
    formData.append('coord_system', document.getElementById('coordSystemSelect').value);
    formData.append('show_perimeter_markers', document.getElementById('chkShowPerimeterMarkers').checked);

    try {
      const res = await fetch('/api/upload-excel', {
        method: 'POST',
        body: formData
      });
      const json = await res.json();
      if (json.status === 'ok' && json.data) {
        currentData = json.data;
        renderAllTables();
        reloadMapFrame(json.map_url);
      } else {
        showLoading(false);
        alert('⚠️ Error al leer Excel: ' + (json.message || 'Formato no válido'));
      }
    } catch (err) {
      showLoading(false);
      alert('❌ Error al subir archivo Excel: ' + err);
    }
  });

  // Cambio de Sistema de Coordenadas -> Auto Actualizar
  document.getElementById('coordSystemSelect').addEventListener('change', (e) => {
    const modalSelect = document.getElementById('modal_coord_system');
    if (modalSelect) modalSelect.value = e.target.value;
    triggerAutoUpdateMap(true);
  });

  // Cambio de Grilla -> Auto Actualizar
  document.getElementById('gridStepSelect').addEventListener('change', () => {
    triggerAutoUpdateMap(true);
  });

  // Toggle de Marcadores RF -> Auto Actualizar
  document.getElementById('chkShowPerimeterMarkers').addEventListener('change', () => {
    triggerAutoUpdateMap(true);
  });

  // Escuchar edición en vivo en las tablas (delegación de eventos)
  const editorPanel = document.querySelector('.editor-panel');
  if (editorPanel) {
    editorPanel.addEventListener('input', (e) => {
      if (e.target.tagName === 'INPUT') {
        triggerAutoUpdateMap(true);
      }
    });
  }

  // Generar Mapa Manual
  document.getElementById('btnGenerateMap').addEventListener('click', () => generateMap(false));

  // Exportar Mapa como Imagen PNG
  document.getElementById('btnExportPNG').addEventListener('click', exportMapPNG);

  // Abrir Modal de Configuración de Cajetín para Exportar PDF
  const cajModal = document.getElementById('cajetinModal');
  const chkIncludeCajetin = document.getElementById('chkIncludeCajetin');
  const cajFieldsGroup = document.getElementById('cajetinFieldsGroup');

  document.getElementById('btnExportPDF').addEventListener('click', () => {
    const now = new Date();
    const formattedDate = `${now.getDate().toString().padStart(2, '0')}/${(now.getMonth() + 1).toString().padStart(2, '0')}/${now.getFullYear()}`;
    document.getElementById('caj_fecha').value = formattedDate;
    
    const navSys = document.getElementById('coordSystemSelect');
    const modalSys = document.getElementById('modal_coord_system');
    if (navSys && modalSys) {
      modalSys.value = navSys.value;
    }
    
    cajModal.style.display = 'flex';
  });

  chkIncludeCajetin.addEventListener('change', () => {
    cajFieldsGroup.style.opacity = chkIncludeCajetin.checked ? '1' : '0.4';
    cajFieldsGroup.style.pointerEvents = chkIncludeCajetin.checked ? 'auto' : 'none';
  });

  document.getElementById('btnCloseCajetin').addEventListener('click', () => cajModal.style.display = 'none');
  document.getElementById('btnCancelCajetin').addEventListener('click', () => cajModal.style.display = 'none');

  // Confirmar Impresión de PDF actualizando el Cajetín en vivo (o bien ocultándolo si es opcional)
  document.getElementById('btnConfirmPrintPDF').addEventListener('click', async () => {
    cajModal.style.display = 'none';
    const includeCajetin = chkIncludeCajetin.checked;

    const selectedSys = document.getElementById('modal_coord_system').value;
    const currentNavSys = document.getElementById('coordSystemSelect').value;
    
    if (selectedSys !== currentNavSys) {
      document.getElementById('coordSystemSelect').value = selectedSys;
      await generateMap(true);
    }
    
    const caj_titulo = document.getElementById('caj_titulo').value || 'MAP DRAW ADVANCE v2.0 — PLANO GEOESPACIAL';
    const caj_proyecto = document.getElementById('caj_proyecto').value || 'Levantamiento de Coordenadas & Patrón de Radiación RF';
    const caj_cliente = document.getElementById('caj_cliente').value || 'General';
    const caj_autor = document.getElementById('caj_autor').value || 'Antonio Martínez (@metantonio)';
    const caj_revisado = document.getElementById('caj_revisado').value || 'Ing. Coordinador';
    const caj_fecha = document.getElementById('caj_fecha').value || new Date().toLocaleDateString();
    
    let defaultNotas = selectedSys === 'utm' ? 'SISTEMA: UTM Transverse Mercator (Proyectado)' : 'SISTEMA: WGS-84 (Geográfico Lat/Lon)';
    const caj_notas = document.getElementById('caj_notas').value || defaultNotas;

    // Actualizar directamente el DOM del iFrame sin reiniciar Leaflet
    const iframe = document.getElementById('mapFrame');
    try {
      const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
      if (iframeDoc) {
        const cajetinEl = iframeDoc.getElementById('cajetin-plano');
        if (cajetinEl) {
          if (includeCajetin) {
            cajetinEl.classList.remove('hide-cajetin-print');
          } else {
            cajetinEl.classList.add('hide-cajetin-print');
          }
        }

        const elTitulo = iframeDoc.getElementById('cj-hdr-titulo');
        if (elTitulo) elTitulo.textContent = caj_titulo;

        const elProyecto = iframeDoc.getElementById('cj-val-proyecto');
        if (elProyecto) elProyecto.textContent = caj_proyecto;

        const elCliente = iframeDoc.getElementById('cj-val-cliente');
        if (elCliente) elCliente.textContent = caj_cliente;

        const elAutor = iframeDoc.getElementById('cj-val-autor');
        if (elAutor) elAutor.textContent = caj_autor;

        const elRevisado = iframeDoc.getElementById('cj-val-revisado');
        if (elRevisado) elRevisado.textContent = caj_revisado;

        const elFecha = iframeDoc.getElementById('cj-val-fecha');
        if (elFecha) elFecha.textContent = caj_fecha;

        const elNotas = iframeDoc.getElementById('cj-val-notas');
        if (elNotas) elNotas.textContent = caj_notas;
      }
    } catch(e) {
      console.warn("No se pudo actualizar el DOM del Cajetín en iFrame:", e);
    }

    // Disparar la impresión inmediata conservando encuadre, zoom y capa activa
    setTimeout(() => {
      exportMapPDF();
    }, 200);
  });

  // Modal de Créditos
  const modal = document.getElementById('creditsModal');
  document.getElementById('btnOpenCredits').addEventListener('click', () => {
    modal.style.display = 'flex';
  });

  document.getElementById('btnCloseCredits').addEventListener('click', () => {
    modal.style.display = 'none';
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.style.display = 'none';
  });

  // Ocultar overlay al terminar de cargar el iFrame
  iframe.addEventListener('load', () => {
    showLoading(false);
  });
}

// Disparador de actualización automática con debounce (500ms)
function triggerAutoUpdateMap(silent = true) {
  if (autoUpdateTimer) clearTimeout(autoUpdateTimer);
  autoUpdateTimer = setTimeout(() => {
    generateMap(silent);
  }, 500);
}

// Mostrar / Ocultar Overlay de Carga (Loading Bar con temporizador de seguridad)
function showLoading(show) {
  const overlay = document.getElementById('loadingOverlay');
  if (!overlay) return;

  if (loadingSafetyTimeout) {
    clearTimeout(loadingSafetyTimeout);
    loadingSafetyTimeout = null;
  }

  if (show) {
    overlay.style.display = 'flex';
    // Temporizador de seguridad máximo de 2 segundos para evitar que se quede pegado
    loadingSafetyTimeout = setTimeout(() => {
      overlay.style.display = 'none';
    }, 2000);
  } else {
    overlay.style.display = 'none';
  }
}

// Recopilar datos exactos desde los inputs del DOM
function collectCurrentDataFromDOM() {
  // Localización
  const locRows = document.querySelectorAll('#table-loc tbody tr');
  const locList = [];
  locRows.forEach(tr => {
    const inputs = tr.querySelectorAll('input');
    if (inputs.length >= 4) {
      const n = parseFloat(inputs[0].value);
      const e = parseFloat(inputs[1].value);
      if (!isNaN(n) && !isNaN(e)) {
        locList.push({
          norte: n,
          este: e,
          color: inputs[2].value || 'blue',
          sobrenombre: inputs[3].value || ''
        });
      }
    }
  });

  // Línea
  const linRows = document.querySelectorAll('#table-lin tbody tr');
  const linList = [];
  linRows.forEach(tr => {
    const inputs = tr.querySelectorAll('input');
    if (inputs.length >= 2) {
      const n = parseFloat(inputs[0].value);
      const e = parseFloat(inputs[1].value);
      if (!isNaN(n) && !isNaN(e)) {
        linList.push({ norte: n, este: e });
      }
    }
  });

  // Círculo
  const cirRows = document.querySelectorAll('#table-cir tbody tr');
  const cirList = [];
  cirRows.forEach(tr => {
    const inputs = tr.querySelectorAll('input');
    if (inputs.length >= 3) {
      const n = parseFloat(inputs[0].value);
      const e = parseFloat(inputs[1].value);
      const r = parseFloat(inputs[2].value);
      if (!isNaN(n) && !isNaN(e)) {
        cirList.push({ norte: n, este: e, radio: isNaN(r) ? 100 : r });
      }
    }
  });

  // Radiación
  const radRows = document.querySelectorAll('#table-rad tbody tr');
  const radList = [];
  radRows.forEach(tr => {
    const inputs = tr.querySelectorAll('input');
    if (inputs.length >= 4) {
      const n = parseFloat(inputs[0].value);
      const e = parseFloat(inputs[1].value);
      const ang = parseFloat(inputs[2].value);
      const dist = parseFloat(inputs[3].value);
      if (!isNaN(n) && !isNaN(e)) {
        radList.push({
          norte: n,
          este: e,
          angulo: isNaN(ang) ? 0 : ang,
          distancia: isNaN(dist) ? 1.0 : dist
        });
      }
    }
  });

  currentData = {
    localizacion: locList,
    linea: linList,
    circulo: cirList,
    radiacion: radList
  };
}

// Renderizar todas las tablas
function renderAllTables() {
  renderTableLoc();
  renderTableLin();
  renderTableCir();
  renderTableRad();
  updateCounts();
}

function updateCounts() {
  document.getElementById('count-loc').textContent = currentData.localizacion.length;
  document.getElementById('count-lin').textContent = currentData.linea.length;
  document.getElementById('count-cir').textContent = currentData.circulo.length;
  document.getElementById('count-rad').textContent = currentData.radiacion.length;
}

// 1. Tabla Localizaciones
function renderTableLoc() {
  const tbody = document.querySelector('#table-loc tbody');
  tbody.innerHTML = '';
  currentData.localizacion.forEach((item, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="number" step="any" value="${item.norte}"></td>
      <td><input type="number" step="any" value="${item.este}"></td>
      <td><input type="text" value="${item.color || 'blue'}"></td>
      <td><input type="text" value="${item.sobrenombre || ''}"></td>
      <td><button class="btn-danger-icon" onclick="removeRow('localizacion', ${index})"><i class="fa-solid fa-trash"></i></button></td>
    `;
    tbody.appendChild(tr);
  });
}

// 2. Tabla Polilínea
function renderTableLin() {
  const tbody = document.querySelector('#table-lin tbody');
  tbody.innerHTML = '';
  currentData.linea.forEach((item, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="number" step="any" value="${item.norte}"></td>
      <td><input type="number" step="any" value="${item.este}"></td>
      <td><button class="btn-danger-icon" onclick="removeRow('linea', ${index})"><i class="fa-solid fa-trash"></i></button></td>
    `;
    tbody.appendChild(tr);
  });
}

// 3. Tabla Círculos
function renderTableCir() {
  const tbody = document.querySelector('#table-cir tbody');
  tbody.innerHTML = '';
  currentData.circulo.forEach((item, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="number" step="any" value="${item.norte}"></td>
      <td><input type="number" step="any" value="${item.este}"></td>
      <td><input type="number" step="any" value="${item.radio || 100}"></td>
      <td><button class="btn-danger-icon" onclick="removeRow('circulo', ${index})"><i class="fa-solid fa-trash"></i></button></td>
    `;
    tbody.appendChild(tr);
  });
}

// 4. Tabla Radiación
function renderTableRad() {
  const tbody = document.querySelector('#table-rad tbody');
  tbody.innerHTML = '';
  currentData.radiacion.forEach((item, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="number" step="any" value="${item.norte}"></td>
      <td><input type="number" step="any" value="${item.este}"></td>
      <td><input type="number" step="any" value="${item.angulo || 0}"></td>
      <td><input type="number" step="any" value="${item.distancia || 1}"></td>
      <td><button class="btn-danger-icon" onclick="removeRow('radiacion', ${index})"><i class="fa-solid fa-trash"></i></button></td>
    `;
    tbody.appendChild(tr);
  });
}

// Añadir Fila -> Auto Actualizar Mapa
function addRow(tableId) {
  collectCurrentDataFromDOM();
  if (tableId === 'table-loc') {
    const last = currentData.localizacion[currentData.localizacion.length - 1] || { norte: 10.48, este: -66.89 };
    currentData.localizacion.push({ norte: last.norte, este: last.este, color: 'blue', tipo: 'Default', direccion: '', sobrenombre: `Punto_${currentData.localizacion.length + 1}` });
  } else if (tableId === 'table-lin') {
    const last = currentData.linea[currentData.linea.length - 1] || { norte: 10.48, este: -66.89 };
    currentData.linea.push({ norte: last.norte, este: last.este });
  } else if (tableId === 'table-cir') {
    const last = currentData.circulo[currentData.circulo.length - 1] || { norte: 10.48, este: -66.89 };
    currentData.circulo.push({ norte: last.norte, este: last.este, radio: 100 });
  } else if (tableId === 'table-rad') {
    const last = currentData.radiacion[currentData.radiacion.length - 1] || { norte: 10.48, este: -66.89 };
    currentData.radiacion.push({ norte: last.norte, este: last.este, angulo: 0, distancia: 1.0 });
  }
  renderAllTables();
  triggerAutoUpdateMap(true);
}

// Eliminar Fila -> Auto Actualizar Mapa
function removeRow(type, index) {
  collectCurrentDataFromDOM();
  if (currentData[type]) {
    currentData[type].splice(index, 1);
    renderAllTables();
    triggerAutoUpdateMap(true);
  }
}

// Recargar el iframe asegurando que cargue la versión fresca del mapa
function reloadMapFrame(url) {
  const iframe = document.getElementById('mapFrame');
  const targetUrl = url || `/Mapa.html?t=${Date.now()}`;
  iframe.src = targetUrl;
}

// Generar Mapa enviando datos al Backend
async function generateMap(silent = false, cajetin_info = null) {
  const btn = document.getElementById('btnGenerateMap');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generando...';
  
  if (!silent) {
    showLoading(true);
  }

  // Recopilar valores más recientes del DOM
  collectCurrentDataFromDOM();
  const grid_step = document.getElementById('gridStepSelect').value;
  const coord_system = document.getElementById('coordSystemSelect').value;
  const show_perimeter_markers = document.getElementById('chkShowPerimeterMarkers').checked;

  try {
    const res = await fetch('/api/generate-map', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...currentData,
        grid_step: grid_step,
        coord_system: coord_system,
        show_perimeter_markers: show_perimeter_markers,
        cajetin_info: cajetin_info
      })
    });

    const json = await res.json();
    if (json.status === 'ok') {
      reloadMapFrame(json.map_url);
    } else {
      showLoading(false);
      if (!silent) alert('⚠️ No se pudo generar el mapa: ' + json.message);
    }
  } catch (err) {
    showLoading(false);
    if (!silent) alert('❌ Error de comunicación al generar el mapa: ' + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Generar Mapa';
  }
}

// Exportar Mapa como Imagen (PNG) usando html2canvas
async function exportMapPNG() {
  const container = document.getElementById('mapExportContainer');
  const iframe = document.getElementById('mapFrame');
  if (!container || !iframe) return;

  showLoading(true);

  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    const targetElement = iframeDoc ? iframeDoc.body : container;

    const canvas = await html2canvas(targetElement, {
      useCORS: true,
      allowTaint: true,
      logging: false,
      scale: 3,
      imageTimeout: 0
    });

    const image = canvas.toDataURL("image/png");
    const link = document.createElement('a');
    link.href = image;
    link.download = `Mapa_Draw_Advance_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (err) {
    console.warn("Fallo al capturar canvas PNG, invocando cuadro de diálogo de mapa:", err);
    window.print();
  } finally {
    showLoading(false);
  }
}

// Exportar Mapa como PDF / Plano Técnico con Cajetín
function exportMapPDF() {
  const iframe = document.getElementById('mapFrame');
  try {
    if (iframe && iframe.contentWindow) {
      if (typeof iframe.contentWindow.fixLeafletMapSize === 'function') {
        iframe.contentWindow.fixLeafletMapSize();
      }
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    } else {
      window.print();
    }
  } catch (e) {
    window.print();
  }
}
