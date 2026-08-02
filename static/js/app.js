// Estado Global de la Aplicación
let currentData = {
  localizacion: [],
  linea: [],
  circulo: [],
  radiacion: []
};

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
    generateMap();
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

  // Generar Mapa
  document.getElementById('btnGenerateMap').addEventListener('click', generateMap);

  // Exportar PNG y PDF
  document.getElementById('btnExportPNG').addEventListener('click', exportMapPNG);
  document.getElementById('btnExportPDF').addEventListener('click', exportMapPDF);

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
  const iframe = document.getElementById('mapFrame');
  iframe.addEventListener('load', () => {
    showLoading(false);
  });
}

// Mostrar / Ocultar Overlay de Carga (Loading Bar)
function showLoading(show) {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) {
    overlay.style.display = show ? 'flex' : 'none';
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

// Añadir Fila
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
}

// Eliminar Fila
function removeRow(type, index) {
  collectCurrentDataFromDOM();
  if (currentData[type]) {
    currentData[type].splice(index, 1);
    renderAllTables();
  }
}

// Recargar el iframe asegurando que cargue la versión fresca del mapa
function reloadMapFrame(url) {
  const iframe = document.getElementById('mapFrame');
  const targetUrl = url || `/Mapa.html?t=${Date.now()}`;
  iframe.src = targetUrl;
}

// Generar Mapa enviando datos al Backend
async function generateMap() {
  const btn = document.getElementById('btnGenerateMap');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generando...';
  showLoading(true);

  // Recopilar valores más recientes del DOM
  collectCurrentDataFromDOM();
  const grid_step = document.getElementById('gridStepSelect').value;

  try {
    const res = await fetch('/api/generate-map', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...currentData,
        grid_step: grid_step
      })
    });

    const json = await res.json();
    if (json.status === 'ok') {
      reloadMapFrame(json.map_url);
    } else {
      showLoading(false);
      alert('⚠️ No se pudo generar el mapa: ' + json.message);
    }
  } catch (err) {
    showLoading(false);
    alert('❌ Error de comunicación al generar el mapa: ' + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Generar Mapa';
  }
}

// Exportar Mapa como Imagen (PNG)
function exportMapPNG() {
  const iframe = document.getElementById('mapFrame');
  try {
    const iframeWindow = iframe.contentWindow;
    if (iframeWindow && iframeWindow.printMapPDF) {
      iframeWindow.printMapPDF();
    } else {
      window.print();
    }
  } catch (e) {
    window.print();
  }
}

// Exportar Mapa como PDF
function exportMapPDF() {
  const element = document.getElementById('mapExportContainer');
  const opt = {
    margin:       [0.2, 0.2, 0.2, 0.2],
    filename:     'Map_Draw_Advance_Report.pdf',
    image:        { type: 'jpeg', quality: 0.98 },
    html2canvas:  { scale: 2, useCORS: true, logging: false },
    jsPDF:        { unit: 'in', format: 'letter', orientation: 'landscape' }
  };
  html2pdf().set(opt).from(element).save();
}
