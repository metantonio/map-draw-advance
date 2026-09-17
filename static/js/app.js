// Estado Global de la Aplicación
let currentData = {
  localizacion: [],
  linea: [],
  circulo: [],
  radiacion: []
};

let currentProject = ''; // Nombre del proyecto activo, o '' si es un proyecto nuevo
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

// ----------------------------------------------------
// Gestión de Proyectos Guardados (Biblioteca de Proyectos)
// ----------------------------------------------------
async function fetchProjectsList(selectProject = null) {
  try {
    const res = await fetch('/api/projects');
    const json = await res.json();
    if (json.status === 'ok' && json.projects) {
      renderProjectOptions(json.projects, selectProject);
    }
  } catch (err) {
    console.warn('Error al cargar la lista de proyectos:', err);
  }
}

function renderProjectOptions(projects, selectProject = null) {
  const select = document.getElementById('projectSelect');
  if (!select) return;

  select.innerHTML = '<option value="">-- Nuevo Proyecto (Limpio) --</option>';
  projects.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.name;
    opt.textContent = `📁 ${p.name} (${p.mtime})`;
    select.appendChild(opt);
  });

  if (selectProject !== null) {
    select.value = selectProject;
    currentProject = selectProject;
  } else if (currentProject) {
    select.value = currentProject;
  }
  updateProjectDeleteButtonVisibility();
}

function updateProjectDeleteButtonVisibility() {
  const btnDel = document.getElementById('btnDeleteProject');
  const select = document.getElementById('projectSelect');
  if (btnDel && select) {
    btnDel.style.display = select.value ? 'inline-flex' : 'none';
  }
}

async function loadProject(projectName) {
  if (!projectName) {
    // Modo Proyecto Nuevo y Limpio (sin precarga)
    currentProject = '';
    currentData = {
      localizacion: [],
      linea: [],
      circulo: [],
      radiacion: []
    };
    renderAllTables();
    await generateMap(false);
    updateProjectDeleteButtonVisibility();
    return;
  }

  showLoading(true);
  try {
    const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}`);
    const json = await res.json();
    if (json.status === 'ok' && json.data) {
      currentProject = projectName;
      currentData = json.data;
      renderAllTables();
      await generateMap(false);
    } else {
      alert('⚠️ Error al cargar el proyecto: ' + (json.message || 'No se encontró'));
    }
  } catch (err) {
    alert('❌ Error al cargar el proyecto: ' + err);
  } finally {
    showLoading(false);
    updateProjectDeleteButtonVisibility();
  }
}

async function saveCurrentProject(name) {
  if (!name || name.trim() === '') {
    alert('Por favor especifique un nombre para el proyecto.');
    return;
  }
  collectCurrentDataFromDOM();
  showLoading(true);
  try {
    const res = await fetch('/api/projects/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_name: name.trim(),
        ...currentData
      })
    });
    const json = await res.json();
    if (json.status === 'ok') {
      currentProject = json.project_name;
      renderProjectOptions(json.projects, currentProject);
      const modal = document.getElementById('saveProjectModal');
      if (modal) modal.style.display = 'none';
    } else {
      alert('⚠️ Error al guardar: ' + json.message);
    }
  } catch (err) {
    alert('❌ Error de comunicación al guardar proyecto: ' + err);
  } finally {
    showLoading(false);
  }
}

async function deleteProject(projectName) {
  if (!projectName) return;
  if (!confirm(`¿Está seguro de eliminar el proyecto "${projectName}" de la biblioteca?`)) {
    return;
  }
  showLoading(true);
  try {
    const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}`, {
      method: 'DELETE'
    });
    const json = await res.json();
    if (json.status === 'ok') {
      currentProject = '';
      renderProjectOptions(json.projects, '');
      currentData = { localizacion: [], linea: [], circulo: [], radiacion: [] };
      renderAllTables();
      generateMap(true);
    } else {
      alert('⚠️ No se pudo eliminar: ' + json.message);
    }
  } catch (err) {
    alert('❌ Error al eliminar proyecto: ' + err);
  } finally {
    showLoading(false);
  }
}

// Cargar Datos Iniciales (Arranque limpio: sin precargar tablas, cargando biblioteca de proyectos)
async function loadInitialData() {
  try {
    // 1. Obtener la lista de proyectos disponibles
    await fetchProjectsList();

    // 2. Iniciar sesión limpia (0 filas)
    currentProject = '';
    currentData = {
      localizacion: [],
      linea: [],
      circulo: [],
      radiacion: []
    };
    renderAllTables();
    
    // Auto-generar mapa limpio en el primer inicio
    generateMap(true);
  } catch (err) {
    console.warn('No se pudieron inicializar los datos:', err);
  }
}

// Eventos de Botones e Inputs
function bindEvents() {
  // Selector de Proyectos Guardados
  const projectSelect = document.getElementById('projectSelect');
  if (projectSelect) {
    projectSelect.addEventListener('change', (e) => {
      loadProject(e.target.value);
    });
  }

  // Botón Nuevo Proyecto
  const btnNewProject = document.getElementById('btnNewProject');
  if (btnNewProject) {
    btnNewProject.addEventListener('click', () => {
      if (projectSelect) projectSelect.value = '';
      loadProject('');
    });
  }

  // Botón Abrir Modal Guardar Proyecto
  const btnSaveProject = document.getElementById('btnSaveProject');
  const saveModal = document.getElementById('saveProjectModal');
  const txtProjectName = document.getElementById('txtProjectName');
  if (btnSaveProject && saveModal) {
    btnSaveProject.addEventListener('click', () => {
      if (txtProjectName) {
        if (currentProject) {
          txtProjectName.value = currentProject.replace(/\.(xlsx|xls)$/i, '');
        } else {
          const now = new Date();
          const pad = n => n.toString().padStart(2, '0');
          txtProjectName.value = `Proyecto_${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}`;
        }
      }
      saveModal.style.display = 'flex';
      if (txtProjectName) txtProjectName.focus();
    });
  }

  const btnCloseSaveProject = document.getElementById('btnCloseSaveProject');
  if (btnCloseSaveProject && saveModal) {
    btnCloseSaveProject.addEventListener('click', () => saveModal.style.display = 'none');
  }

  const btnCancelSaveProject = document.getElementById('btnCancelSaveProject');
  if (btnCancelSaveProject && saveModal) {
    btnCancelSaveProject.addEventListener('click', () => saveModal.style.display = 'none');
  }

  const btnConfirmSaveProject = document.getElementById('btnConfirmSaveProject');
  if (btnConfirmSaveProject && txtProjectName) {
    btnConfirmSaveProject.addEventListener('click', () => {
      saveCurrentProject(txtProjectName.value);
    });
  }

  // Botón Eliminar Proyecto
  const btnDeleteProject = document.getElementById('btnDeleteProject');
  if (btnDeleteProject) {
    btnDeleteProject.addEventListener('click', () => {
      if (projectSelect && projectSelect.value) {
        deleteProject(projectSelect.value);
      }
    });
  }

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
        currentProject = json.project_name || file.name;
        renderAllTables();
        reloadMapFrame(json.map_url);
        if (json.projects) {
          renderProjectOptions(json.projects, currentProject);
        } else {
          fetchProjectsList(currentProject);
        }
      } else {
        showLoading(false);
        alert('⚠️ Error al procesar Excel: ' + (json.message || 'Formato no válido'));
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

  // Control para Ocultar / Mostrar el Menú Lateral de Coordenadas
  const mainLayout = document.querySelector('.main-layout');
  const btnToggleSidebar = document.getElementById('btnToggleSidebar');
  const btnCollapseSidebar = document.getElementById('btnCollapseSidebar');
  const btnRestoreSidebar = document.getElementById('btnRestoreSidebar');

  function toggleSidebar(collapse) {
    if (!mainLayout) return;
    const shouldCollapse = collapse !== undefined ? collapse : !mainLayout.classList.contains('sidebar-collapsed');
    
    if (shouldCollapse) {
      mainLayout.classList.add('sidebar-collapsed');
      if (btnToggleSidebar) {
        btnToggleSidebar.innerHTML = '<i class="fa-solid fa-table-columns"></i> Mostrar Menú';
        btnToggleSidebar.classList.add('btn-primary');
        btnToggleSidebar.classList.remove('btn-outline');
      }
      if (btnRestoreSidebar) btnRestoreSidebar.style.display = 'flex';
    } else {
      mainLayout.classList.remove('sidebar-collapsed');
      if (btnToggleSidebar) {
        btnToggleSidebar.innerHTML = '<i class="fa-solid fa-table-columns"></i> Ocultar Menú';
        btnToggleSidebar.classList.remove('btn-primary');
        btnToggleSidebar.classList.add('btn-outline');
      }
      if (btnRestoreSidebar) btnRestoreSidebar.style.display = 'none';
    }

    // Notificar al iframe del mapa para que invalide su tamaño y ocupe el 100% de la pantalla
    setTimeout(() => {
      try {
        const iframe = document.getElementById('mapFrame');
        if (iframe && iframe.contentWindow && iframe.contentWindow.fixLeafletMapSize) {
          iframe.contentWindow.fixLeafletMapSize();
        }
      } catch (err) {}
    }, 360);
  }

  if (btnToggleSidebar) btnToggleSidebar.addEventListener('click', () => toggleSidebar());
  if (btnCollapseSidebar) btnCollapseSidebar.addEventListener('click', () => toggleSidebar(true));
  if (btnRestoreSidebar) btnRestoreSidebar.addEventListener('click', () => toggleSidebar(false));

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
    
    // Obtener la Escala Real calculada del mapa Leaflet
    try {
      const iframe = document.getElementById('mapFrame');
      if (iframe && iframe.contentWindow && typeof iframe.contentWindow.getLeafletMapScale === 'function') {
        document.getElementById('caj_escala').value = iframe.contentWindow.getLeafletMapScale();
      } else {
        document.getElementById('caj_escala').value = '1:250000';
      }
    } catch(e) {
      document.getElementById('caj_escala').value = '1:250000';
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
    const caj_escala = document.getElementById('caj_escala').value || '1:250000';
    
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

        const elEscala = iframeDoc.getElementById('cj-val-escala');
        if (elEscala) elEscala.textContent = caj_escala;

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
    if (inputs.length >= 6) {
      const n = parseFloat(inputs[0].value);
      const e = parseFloat(inputs[1].value);
      const ang = parseFloat(inputs[2].value);
      const dist = parseFloat(inputs[3].value);
      const etiq = inputs[4].value.trim();
      const col = inputs[5].value.trim();
      if (!isNaN(n) && !isNaN(e)) {
        radList.push({
          norte: n,
          este: e,
          angulo: isNaN(ang) ? 0 : ang,
          distancia: isNaN(dist) ? 1.0 : dist,
          etiqueta: etiq,
          color: col
        });
      }
    } else if (inputs.length >= 4) {
      const n = parseFloat(inputs[0].value);
      const e = parseFloat(inputs[1].value);
      const ang = parseFloat(inputs[2].value);
      const dist = parseFloat(inputs[3].value);
      if (!isNaN(n) && !isNaN(e)) {
        radList.push({
          norte: n,
          este: e,
          angulo: isNaN(ang) ? 0 : ang,
          distancia: isNaN(dist) ? 1.0 : dist,
          etiqueta: '',
          color: ''
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

  computeRadiationDefaults();
}

// Renderizar todas las tablas
function renderAllTables() {
  computeRadiationDefaults();
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
const RAD_PALETTE = ['#8e44ad', '#e74c3c', '#2980b9', '#27ae60', '#e67e22', '#16a085', '#d35400', '#2c3e50', '#f39c12'];

function computeRadiationDefaults() {
  if (!currentData || !currentData.radiacion) return;

  const centerMap = [];

  currentData.radiacion.forEach(item => {
    const n = parseFloat(item.norte) || 0;
    const e = parseFloat(item.este) || 0;

    let match = centerMap.find(c => Math.abs(c.norte - n) < 0.0001 && Math.abs(c.este - e) < 0.0001);
    if (!match) {
      const idx = centerMap.length;
      match = {
        norte: n,
        este: e,
        defaultEtiqueta: `Patrón ${idx + 1}`,
        defaultColor: RAD_PALETTE[idx % RAD_PALETTE.length]
      };
      centerMap.push(match);
    }

    if (!item.etiqueta || item.etiqueta.trim() === '') {
      item.etiqueta = match.defaultEtiqueta;
    }
    if (!item.color || item.color.trim() === '') {
      item.color = match.defaultColor;
    }
  });
}

function renderTableRad() {
  computeRadiationDefaults();
  const tbody = document.querySelector('#table-rad tbody');
  tbody.innerHTML = '';
  currentData.radiacion.forEach((item, index) => {
    const tr = document.createElement('tr');
    const colorVal = item.color || RAD_PALETTE[index % RAD_PALETTE.length];
    const etiqVal = item.etiqueta || `Patrón 1`;
    tr.innerHTML = `
      <td><input type="number" step="any" value="${item.norte}"></td>
      <td><input type="number" step="any" value="${item.este}"></td>
      <td><input type="number" step="any" value="${item.angulo || 0}"></td>
      <td><input type="number" step="any" value="${item.distancia || 1}"></td>
      <td><input type="text" value="${etiqVal}" placeholder="Ej: Patrón 1"></td>
      <td><input type="color" value="${colorVal.startsWith('#') ? colorVal : '#8e44ad'}" style="padding:1px; cursor:pointer; height:28px;"></td>
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
    const last = currentData.radiacion[currentData.radiacion.length - 1] || { norte: 10.48, este: -66.89, etiqueta: '', color: '' };
    currentData.radiacion.push({
      norte: last.norte,
      este: last.este,
      angulo: 0,
      distancia: 1.0,
      etiqueta: last.etiqueta || '',
      color: last.color || ''
    });
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

// Exportar Mapa como Imagen (PNG) usando html2canvas (Excluyendo modales y controles superpuestos)
async function exportMapPNG() {
  const container = document.getElementById('mapExportContainer');
  const iframe = document.getElementById('mapFrame');
  if (!container || !iframe) return;

  const btn = document.getElementById('btnExportPNG');
  const origBtnHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Exportando...';
  }

  // Elementos a ocultar temporalmente para que no salgan sobre el mapa en el PNG
  const hiddenElements = [];
  const hideElement = (el) => {
    if (el) {
      hiddenElements.push({
        el: el,
        prevDisplay: el.style.display,
        prevVisibility: el.style.visibility
      });
      el.style.display = 'none';
      el.style.visibility = 'hidden';
      el.setAttribute('data-html2canvas-ignore', 'true');
    }
  };

  try {
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

    // 1. Ocultar modales y elementos flotantes dentro del iframe del mapa
    if (iframeDoc) {
      // Modal / leyenda flotante de la escala RF y botón PDF
      hideElement(iframeDoc.getElementById('maplegend'));
      // Cajetín si estuviese visible
      hideElement(iframeDoc.getElementById('cajetin-plano'));
      // Controles interactivos de Leaflet (botones de zoom, capas, regla, minimap, herramientas de dibujo)
      iframeDoc.querySelectorAll('.leaflet-control-container, .leaflet-popup, .leaflet-tooltip-pane .leaflet-popup').forEach(el => {
        hideElement(el);
      });
    }

    // 2. Ocultar modales, overlays y controles en la página principal
    hideElement(document.getElementById('loadingOverlay'));
    hideElement(document.getElementById('btnRestoreSidebar'));
    document.querySelectorAll('.modal-backdrop').forEach(el => hideElement(el));

    // Determinar el elemento exacto del mapa a capturar
    let targetElement = container;
    if (iframeDoc) {
      targetElement = iframeDoc.querySelector('.folium-map') || iframeDoc.getElementById('map') || iframeDoc.body;
    }

    const canvas = await html2canvas(targetElement, {
      useCORS: true,
      allowTaint: true,
      logging: false,
      scale: 3,
      imageTimeout: 0,
      ignoreElements: (element) => {
        if (!element) return false;
        if (element.getAttribute && element.getAttribute('data-html2canvas-ignore') === 'true') return true;
        const id = element.id || '';
        const className = typeof element.className === 'string' ? element.className : '';
        if (id === 'maplegend' || id === 'cajetin-plano' || id === 'loadingOverlay' || id === 'btnRestoreSidebar') return true;
        if (className.includes('leaflet-control') || className.includes('modal-backdrop')) return true;
        return false;
      }
    });

    const image = canvas.toDataURL("image/png");
    const link = document.createElement('a');
    link.href = image;
    link.download = `Mapa_Draw_Advance_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (err) {
    console.warn("Fallo al capturar canvas PNG:", err);
    alert("⚠️ No se pudo generar la exportación PNG del mapa: " + err);
  } finally {
    // Restaurar visibilidad original de todos los elementos
    hiddenElements.forEach(item => {
      item.el.style.display = item.prevDisplay;
      item.el.style.visibility = item.prevVisibility;
      item.el.removeAttribute('data-html2canvas-ignore');
    });

    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origBtnHtml;
    }
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
