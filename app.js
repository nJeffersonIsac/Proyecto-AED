/**
 * RESTAURANTE "EL FILETE" - POS Frontend Logic
 * Conectado directamente a la API REST de Python y la Base de Datos Filete2.db.
 */

// Estado global de la aplicación
let catalogo = [];
let categorias = [];
let mesas = [];
let order = [];
let currentCategory = 'Todas';
let searchQuery = '';
const TAX_RATE = 0.15; // 15% IVA

// Elementos del DOM
const productsGrid = document.getElementById('products-grid');
const categoriesContainer = document.getElementById('categories-container');
const searchInput = document.getElementById('search-input');
const orderItemsContainer = document.getElementById('order-items');
const summarySubtotal = document.getElementById('summary-subtotal');
const summaryTax = document.getElementById('summary-tax');
const summaryTotal = document.getElementById('summary-total');
const btnTotal = document.getElementById('btn-total');
const btnClearOrder = document.getElementById('btn-clear-order');
const btnProcessOrder = document.getElementById('btn-process-order');
const mesaSelect = document.getElementById('order-mesa-select');
const clienteInput = document.getElementById('order-cliente-input');

// Iconos representativos por categoría
const categoryIcons = {
    "Entradas": "fa-cookie-bite",
    "Bebida": "fa-bottle-water",
    "Mariscos": "fa-fish",
    "Cortes": "fa-drumstick-bite",
    "Desayunos": "fa-mug-saucer",
    "Pollo": "fa-bowl-food",
    "Cocteles": "fa-martini-glass-citrus",
    "Postres": "fa-ice-cream",
    "Licores": "fa-wine-glass",
    "Cervezas": "fa-beer-mug-empty",
    "Sopa": "fa-bowl-hot",
    "Extras": "fa-plus-circle",
    "Todas": "fa-border-all"
};

const API_BASE = (window.location.protocol === 'file:') ? 'http://localhost:5000' : '';

// Inicialización de la aplicación
async function initApp() {
    startClock();
    setupEventListeners();
    await cargarDatosIniciales();
    await cargarFacturas();
}

// 1. CARGA DINÁMICA DESDE LA BASE DE DATOS (API REST)
async function cargarDatosIniciales() {
    try {
        // Cargar Categorías
        const resCat = await fetch(`${API_BASE}/api/categorias`);
        if (resCat.ok) {
            categorias = await resCat.json();
            renderCategories();
        }

        // Cargar Productos (Menú completo desde SQLite)
        const resProd = await fetch(`${API_BASE}/api/productos`);
        if (resProd.ok) {
            catalogo = await resProd.json();
            renderProducts();
        } else {
            showToast("No se pudo cargar el catálogo de productos", "error");
        }

        // Cargar Mesas
        const resMesas = await fetch(`${API_BASE}/api/mesas`);
        if (resMesas.ok) {
            mesas = await resMesas.json();
            renderMesasSelect();
        }
    } catch (err) {
        console.error("Error al conectar con la API:", err);
        showToast("Error conectando con el servidor backend", "error");
    }
}

// Reloj digital
function startClock() {
    const clockEl = document.getElementById('clock');
    if (clockEl) {
        const updateTime = () => {
            const now = new Date();
            clockEl.textContent = now.toLocaleTimeString('es-NI');
        };
        updateTime();
        setInterval(updateTime, 1000);
    }
}

// Renderizar Selector de Mesas
function renderMesasSelect() {
    if (!mesaSelect) return;
    mesaSelect.innerHTML = `<option value="">Para Llevar / Caja</option>` + mesas.map(m => `
        <option value="${m.id_mesa}">Mesa #${m.numero_mesa} (Cap: ${m.capacidad} - ${m.estado})</option>
    `).join('');
}

// Renderizar Categorías
function renderCategories() {
    if (!categoriesContainer) return;
    const listaCategorias = ['Todas', ...categorias.map(c => c.nombre)];
    
    categoriesContainer.innerHTML = listaCategorias.map(cat => `
        <div class="category-chip ${cat === currentCategory ? 'active' : ''}" data-cat="${cat}">
            <i class="fa-solid ${categoryIcons[cat] || 'fa-tag'}"></i> ${cat}
        </div>
    `).join('');

    document.querySelectorAll('.category-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            document.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
            e.currentTarget.classList.add('active');
            currentCategory = e.currentTarget.dataset.cat;
            renderProducts();
        });
    });
}

// Renderizar Productos en Grid
function renderProducts() {
    if (!productsGrid) return;
    let filtered = catalogo;

    if (currentCategory !== 'Todas') {
        filtered = filtered.filter(p => p.categoria === currentCategory);
    }
    if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase().trim();
        filtered = filtered.filter(p => 
            p.nombre.toLowerCase().includes(query) || 
            p.categoria.toLowerCase().includes(query) ||
            (p.descripcion && p.descripcion.toLowerCase().includes(query))
        );
    }

    if (filtered.length === 0) {
        productsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">
            <i class="fa-solid fa-magnifying-glass" style="font-size: 2rem; margin-bottom: 0.5rem; display:block;"></i>
            No se encontraron productos disponibles.
        </div>`;
        return;
    }

    productsGrid.innerHTML = filtered.map(p => {
        const cssVarCat = `var(--cat-${p.categoria.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")})`;
        const imagenHtml = p.imagen_url ? 
            `<img src="${p.imagen_url}" alt="${p.nombre}" class="product-card-img" onerror="this.parentElement.innerHTML='<i class=\\'fa-solid ${categoryIcons[p.categoria] || 'fa-utensils'}\\'></i>'">` :
            `<i class="fa-solid ${categoryIcons[p.categoria] || 'fa-utensils'}"></i>`;

        return `
        <div class="product-card" onclick="addToOrder(${p.id_producto})" title="${p.descripcion || p.nombre}">
            <span class="product-cat-badge" style="color: ${cssVarCat}; border: 1px solid ${cssVarCat}">${p.categoria}</span>
            <div class="product-img-box">
                ${imagenHtml}
            </div>
            <div class="product-info">
                <h3 class="product-name">${p.nombre}</h3>
                <span class="product-price">C$ ${p.precio.toFixed(2)}</span>
            </div>
        </div>
        `;
    }).join('');
}

// 2. GESTIÓN DE LA ORDEN ACTUAL
window.addToOrder = function(id) {
    const product = catalogo.find(p => p.id_producto === id);
    if (!product) return;
    const existingItem = order.find(item => item.id_producto === id);
    if (existingItem) {
        existingItem.cantidad++;
    } else {
        order.push({ ...product, cantidad: 1, observacion: '' });
    }
    renderOrder();
    showToast(`${product.nombre} agregado`, 'info');
};

window.updateQty = function(id, delta) {
    const item = order.find(i => i.id_producto === id);
    if (item) {
        item.cantidad += delta;
        if (item.cantidad <= 0) removeFromOrder(id);
        else renderOrder();
    }
};

window.setQty = function(id, value) {
    const val = parseInt(value);
    const item = order.find(i => i.id_producto === id);
    if (item) {
        if (isNaN(val) || val <= 0) removeFromOrder(id);
        else { item.cantidad = val; renderOrder(); }
    }
};

window.removeFromOrder = function(id) {
    order = order.filter(i => i.id_producto !== id);
    renderOrder();
};

function renderOrder() {
    if (!orderItemsContainer) return;
    if (order.length === 0) {
        orderItemsContainer.innerHTML = `
            <div class="empty-order-msg">
                <i class="fa-solid fa-cart-arrow-down"></i>
                <p>No hay productos en la orden</p>
            </div>`;
        btnProcessOrder.disabled = true;
    } else {
        btnProcessOrder.disabled = false;
        orderItemsContainer.innerHTML = order.map(item => `
            <div class="order-item">
                <div class="item-top">
                    <span class="item-name">${item.nombre}</span>
                    <button class="item-delete" onclick="removeFromOrder(${item.id_producto})" title="Eliminar"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="item-bottom">
                    <div class="qty-controls">
                        <button class="qty-btn" onclick="updateQty(${item.id_producto}, -1)"><i class="fa-solid fa-minus"></i></button>
                        <input type="number" class="qty-input" value="${item.cantidad}" onchange="setQty(${item.id_producto}, this.value)" min="1">
                        <button class="qty-btn" onclick="updateQty(${item.id_producto}, 1)"><i class="fa-solid fa-plus"></i></button>
                    </div>
                    <span class="item-total">C$ ${(item.precio * item.cantidad).toFixed(2)}</span>
                </div>
            </div>
        `).join('');
    }
    updateOrderSummary();
}

function updateOrderSummary() {
    if (!summarySubtotal) return;
    const subtotal = order.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    const tax = subtotal * TAX_RATE;
    const total = subtotal + tax;

    summarySubtotal.textContent = `C$ ${subtotal.toFixed(2)}`;
    summaryTax.textContent = `C$ ${tax.toFixed(2)}`;
    summaryTotal.textContent = `C$ ${total.toFixed(2)}`;
    btnTotal.textContent = `C$ ${total.toFixed(2)}`;
}

// 3. PROCESAR VENTA (GUARDAR EN BASE DE DATOS)
async function processOrder() {
    if (order.length === 0) return;

    btnProcessOrder.disabled = true;
    btnProcessOrder.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Procesando...`;

    const mesaIdVal = mesaSelect ? mesaSelect.value : "";
    const clienteNombreVal = clienteInput && clienteInput.value.trim() ? clienteInput.value.trim() : "Consumidor Final";
    const paymentMethodEl = document.querySelector('input[name="payment"]:checked');
    const paymentMethod = paymentMethodEl ? paymentMethodEl.value : 'Efectivo';

    const payload = {
        id_mesa: mesaIdVal ? parseInt(mesaIdVal) : null,
        tipo_pedido: mesaIdVal ? "Mesa" : "Para Llevar",
        cliente_nombre: clienteNombreVal,
        metodo_pago: paymentMethod,
        items: order.map(it => ({
            id_producto: it.id_producto,
            cantidad: it.cantidad,
            observacion: it.observacion || null
        }))
    };

    try {
        const response = await fetch(`${API_BASE}/api/ventas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // Mostrar Comprobante Modal con datos oficiales de la DB
            mostrarComprobanteModal({
                id_factura: result.id_factura,
                fecha_hora: new Date().toLocaleString('es-NI'),
                cliente_nombre: clienteNombreVal,
                mesa_texto: mesaIdVal ? `Mesa #${mesaSelect.options[mesaSelect.selectedIndex].text.split(' ')[0].replace('#','')}` : 'Para Llevar',
                subtotal: result.subtotal,
                impuesto: result.impuesto,
                monto_total: result.monto_total,
                metodo_pago: result.metodo_pago,
                items: [...order]
            }, true);

            showToast(`Venta #${String(result.id_factura).padStart(6, '0')} guardada en la base de datos`, 'success');
        } else {
            showToast(result.error || "Error al procesar la venta", 'error');
        }
    } catch (error) {
        console.error("Error al procesar la orden:", error);
        showToast("Error de conexión al guardar la venta", 'error');
    } finally {
        btnProcessOrder.disabled = false;
        updateOrderSummary();
    }
}

// 4. MOSTRAR COMPROBANTE / FACTURA
function mostrarComprobanteModal(datos, esNuevaVenta = false) {
    const partesFecha = datos.fecha_hora ? datos.fecha_hora.split(' ') : ['', ''];
    document.getElementById('inv-date').textContent = partesFecha[0] || '';
    document.getElementById('inv-time').textContent = partesFecha[1] || '';
    document.getElementById('inv-number').textContent = String(datos.id_factura).padStart(6, '0');
    
    const clienteEl = document.getElementById('inv-cliente');
    if (clienteEl) clienteEl.textContent = datos.cliente_nombre || 'Consumidor Final';

    const mesaEl = document.getElementById('inv-mesa');
    if (mesaEl) mesaEl.textContent = datos.mesa_texto || (datos.numero_mesa ? `Mesa #${datos.numero_mesa}` : datos.tipo_pedido || 'Para Llevar');

    // Llenar tabla de productos
    const invItems = document.getElementById('inv-items');
    invItems.innerHTML = (datos.items || []).map(item => `
        <tr>
            <td>${item.cantidad}</td>
            <td>${item.nombre}</td>
            <td>C$ ${(item.precio_unitario || item.precio).toFixed(2)}</td>
            <td>C$ ${((item.precio_unitario || item.precio) * item.cantidad).toFixed(2)}</td>
        </tr>
    `).join('');

    document.getElementById('inv-subtotal').textContent = `C$ ${parseFloat(datos.subtotal).toFixed(2)}`;
    document.getElementById('inv-tax').textContent = `C$ ${parseFloat(datos.impuesto).toFixed(2)}`;
    document.getElementById('inv-total').textContent = `C$ ${parseFloat(datos.monto_total || datos.total).toFixed(2)}`;
    document.getElementById('inv-payment-method').textContent = datos.metodo_pago || 'Efectivo';

    const doneBtn = document.getElementById('btn-done');
    if (doneBtn) {
        doneBtn.style.display = esNuevaVenta ? 'flex' : 'none';
    }

    document.getElementById('invoice-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('invoice-modal').classList.remove('active');
}

function finishOrder() {
    closeModal();
    order = [];
    renderOrder();
    if (clienteInput) clienteInput.value = '';
    if (mesaSelect) mesaSelect.value = '';
    document.querySelectorAll('.payment-method')[0].click();
    cargarFacturas(); // Actualiza el historial desde la DB
}

// 5. CARGAR HISTORIAL DE FACTURAS DESDE LA BASE DE DATOS
async function cargarFacturas() {
    const tbody = document.getElementById('facturas-table-body');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem;"><i class="fa-solid fa-spinner fa-spin"></i> Cargando historial desde base de datos...</td></tr>`;

    try {
        const response = await fetch(`${API_BASE}/api/facturas`);
        if (!response.ok) throw new Error("Error en la petición");
        const facturas = await response.json();

        if (facturas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">No hay facturas registradas en la base de datos.</td></tr>';
            return;
        }

        tbody.innerHTML = facturas.map(f => `
            <tr>
                <td><strong>#${String(f.id_factura).padStart(6, '0')}</strong></td>
                <td>${f.fecha_hora}</td>
                <td><span class="product-cat-badge" style="position:static; background:rgba(59, 130, 246, 0.2); color: #3b82f6;">${f.numero_mesa ? `Mesa #${f.numero_mesa}` : f.tipo_pedido}</span></td>
                <td>${f.cliente_nombre || 'Consumidor Final'}</td>
                <td>${f.metodo_pago}</td>
                <td><strong style="color: var(--secondary);">C$ ${parseFloat(f.monto_total).toFixed(2)}</strong></td>
                <td>
                    <button class="action-btn" title="Ver comprobante" onclick="verFactura(${f.id_factura})">
                        <i class="fa-solid fa-print"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error("Error al cargar facturas:", err);
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--danger);">Error al cargar facturas desde la base de datos.</td></tr>';
    }
}

// Ver / Reimprimir Factura Antigua
window.verFactura = async function(id_factura) {
    try {
        const response = await fetch(`${API_BASE}/api/facturas/${id_factura}`);
        if (!response.ok) throw new Error("Factura no encontrada");
        const factura = await response.json();
        mostrarComprobanteModal(factura, false);
    } catch (err) {
        showToast("Error al obtener datos de la factura", "error");
    }
};

// 6. CONFIGURACIÓN DE EVENT LISTENERS
function setupEventListeners() {
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            renderProducts();
        });
    }

    if (btnClearOrder) {
        btnClearOrder.addEventListener('click', () => {
            if (order.length > 0 && confirm("¿Estás seguro de vaciar la orden actual?")) {
                order = [];
                renderOrder();
                showToast("Orden vaciada", "info");
            }
        });
    }

    document.querySelectorAll('.payment-method').forEach(method => {
        method.addEventListener('click', (e) => {
            document.querySelectorAll('.payment-method').forEach(m => m.classList.remove('selected'));
            e.currentTarget.classList.add('selected');
            const radio = e.currentTarget.querySelector('input');
            if (radio) radio.checked = true;
        });
    });

    if (btnProcessOrder) btnProcessOrder.addEventListener('click', processOrder);

    const closeBtn = document.getElementById('close-invoice');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    const doneBtn = document.getElementById('btn-done');
    if (doneBtn) doneBtn.addEventListener('click', finishOrder);

    const printBtn = document.getElementById('btn-print');
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
            showToast("Imprimiendo comprobante...", "info");
        });
    }

    // Pestañas (POS vs Historial)
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            const targetTab = e.currentTarget;
            targetTab.classList.add('active');
            document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active-view'));
            const view = document.getElementById(`${targetTab.dataset.tab}-view`);
            if (view) view.classList.add('active-view');
            if (targetTab.dataset.tab === 'inventory') {
                cargarFacturas();
            }
        });
    });

    // Scroll de categorías
    const catContainer = document.getElementById('categories-container');
    const scrollLeft = document.querySelector('.scroll-btn.left');
    const scrollRight = document.querySelector('.scroll-btn.right');
    if (catContainer && scrollLeft && scrollRight) {
        scrollLeft.addEventListener('click', () => {
            catContainer.scrollBy({ left: -200, behavior: 'smooth' });
        });
        scrollRight.addEventListener('click', () => {
            catContainer.scrollBy({ left: 200, behavior: 'smooth' });
        });
    }
}

// Notificaciones Toast
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-circle-exclamation' : 'fa-info-circle');
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Arrancar App cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', initApp);