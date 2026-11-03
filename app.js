let catalogo = [];
let categorias = [];
let mesas = [];
let order = [];
let currentCategory = 'Todas';
let searchQuery = '';
const TAX_RATE = 0.15;

const productsGrid = document.getElementById('products-grid');
const categoriesContainer = document.getElementById('categories-container');
const searchInput = document.getElementById('search-input');
const orderItemsContainer = document.getElementById('order-items');
const summarySubtotal = document.getElementById('summary-subtotal');
const summaryTax = document.getElementById('summary-tax');
const summaryTotal = document.getElementById('summary-total');
const btnClearOrder = document.getElementById('btn-clear-order');
const btnProcessOrder = document.getElementById('btn-process-order');
const mesaSelect = document.getElementById('order-mesa-select');
const clienteInput = document.getElementById('order-cliente-input');

const categoryIcons = {
    "Entradas": "fa-cookie-bite", "Bebida": "fa-bottle-water", "Mariscos": "fa-fish",
    "Cortes": "fa-drumstick-bite", "Desayunos": "fa-mug-saucer", "Pollo": "fa-bowl-food",
    "Cocteles": "fa-martini-glass-citrus", "Postres": "fa-ice-cream", "Licores": "fa-wine-glass",
    "Cervezas": "fa-beer-mug-empty", "Sopa": "fa-bowl-hot", "Extras": "fa-plus-circle", "Todas": "fa-border-all"
};

async function initApp() {
    const user = await window.cargarUsuarioActual();
    if (!user) return;

    document.getElementById('sidebar-nombre-usuario').textContent = user.nombre_completo;
    document.getElementById('sidebar-rol').textContent = user.rol;
    document.getElementById('sidebar-rol').className = `badge badge-${user.rol}`;
    
    document.querySelectorAll('[data-rol-requerido]').forEach(el => {
        const roles = el.dataset.rolRequerido.split(',');
        el.style.display = roles.includes(user.rol) ? 'flex' : 'none';
    });

    setupEventListeners();
    await cargarDatosIniciales();
    await cargarFacturas();
}

async function cargarDatosIniciales() {
    try {
        const [resCat, resProd, resMesas] = await Promise.all([
            window.fetchAuth('/api/categorias'),
            window.fetchAuth('/api/productos'),
            window.fetchAuth('/api/mesas')
        ]);
        if (resCat.ok) { categorias = await resCat.json(); renderCategories(); }
        if (resProd.ok) { catalogo = await resProd.json(); renderProducts(); }
        if (resMesas.ok) { mesas = await resMesas.json(); renderMesasSelect(); }
    } catch (err) {
        showToast("Error conectando con el servidor", "error");
    }
}

function renderMesasSelect() {
    if (!mesaSelect) return;
    mesaSelect.innerHTML = `<option value="">Para Llevar</option>` + mesas.map(m => `
        <option value="${m.id_mesa}">Mesa #${m.numero_mesa} (Cap: ${m.capacidad})</option>
    `).join('');
}

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

function renderProducts() {
    if (!productsGrid) return;
    let filtered = catalogo;

    if (currentCategory !== 'Todas') filtered = filtered.filter(p => p.categoria === currentCategory);
    if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase().trim();
        filtered = filtered.filter(p => p.nombre.toLowerCase().includes(query) || p.categoria.toLowerCase().includes(query));
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
            `<img src="${p.imagen_url}" alt="${p.nombre}" class="product-card-img" onerror="this.onerror=null; this.src='Imagenes/Logo.jpg';">` : 
            `<i class="fa-solid ${categoryIcons[p.categoria] || 'fa-utensils'}"></i>`;

        return `
        <div class="product-card" onclick="addToOrder(${p.id_producto})">
            <span class="product-cat-badge" style="color: ${cssVarCat}; border: 1px solid ${cssVarCat}">${p.categoria}</span>
            <div class="product-img-box">${imagenHtml}</div>
            <div class="product-info">
                <h3 class="product-name">${p.nombre}</h3>
                <span class="product-price">C$ ${p.precio.toFixed(2)}</span>
            </div>
        </div>
        `;
    }).join('');
}

window.addToOrder = function(id) {
    const product = catalogo.find(p => p.id_producto === id);
    if (!product) return;
    const existingItem = order.find(item => item.id_producto === id);
    if (existingItem) existingItem.cantidad++;
    else order.push({ ...product, cantidad: 1 });
    renderOrder();
};

window.updateQty = function(id, delta) {
    const item = order.find(i => i.id_producto === id);
    if (item) {
        item.cantidad += delta;
        if (item.cantidad <= 0) order = order.filter(i => i.id_producto !== id);
        renderOrder();
    }
};

function renderOrder() {
    if (!orderItemsContainer) return;
    if (order.length === 0) {
        orderItemsContainer.innerHTML = `<div class="empty-order-msg"><i class="fa-solid fa-cart-arrow-down"></i><p>No hay productos</p></div>`;
        if (btnProcessOrder) btnProcessOrder.disabled = true;
    } else {
        if (btnProcessOrder) btnProcessOrder.disabled = false;
        orderItemsContainer.innerHTML = order.map(item => `
            <div class="order-item">
                <div class="item-top">
                    <span class="item-name">${item.nombre}</span>
                    <button class="item-delete" onclick="updateQty(${item.id_producto}, -999)"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="item-bottom">
                    <div class="qty-controls">
                        <button class="qty-btn" onclick="updateQty(${item.id_producto}, -1)">-</button>
                        <input type="number" class="qty-input" value="${item.cantidad}" readonly>
                        <button class="qty-btn" onclick="updateQty(${item.id_producto}, 1)">+</button>
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
    const btnTotalEl = document.getElementById('btn-total');
    if (btnTotalEl) btnTotalEl.textContent = `C$ ${total.toFixed(2)}`;
}

async function processOrder() {
    if (order.length === 0) return;
    btnProcessOrder.disabled = true;
    btnProcessOrder.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Procesando...`;

    const mesaIdVal = mesaSelect ? mesaSelect.value : "";
    const clienteNombreVal = clienteInput && clienteInput.value.trim() ? clienteInput.value.trim() : "Consumidor Final";
    const paymentEl = document.querySelector('input[name="payment"]:checked');
    
    if (!paymentEl) {
        showToast("Selecciona un método de pago", "error");
        btnProcessOrder.disabled = false;
        btnProcessOrder.innerHTML = `Cobrar <span id="btn-total">C$ 0.00</span>`;
        return;
    }

    const payload = {
        id_mesa: mesaIdVal ? parseInt(mesaIdVal) : null,
        tipo_pedido: mesaIdVal ? "Mesa" : "Para Llevar",
        cliente_nombre: clienteNombreVal,
        metodo_pago: paymentEl.value,
        items: order.map(it => ({ id_producto: it.id_producto, cantidad: it.cantidad }))
    };

    try {
        const response = await window.fetchAuth('/api/ventas', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            let errorMsg = `Error del servidor (${response.status})`;
            try {
                const data = await response.json();
                errorMsg = data.error || errorMsg;
            } catch (e) {}
            throw new Error(errorMsg);
        }

        const result = await response.json();

        if (result.status === 'success') {
            mostrarComprobanteModal({
                id_factura: result.id_factura,
                fecha_hora: new Date().toLocaleString('es-NI'),
                cliente_nombre: clienteNombreVal,
                mesa_texto: mesaIdVal ? `Mesa #${mesaIdVal}` : 'Para Llevar',
                subtotal: result.subtotal, impuesto: result.impuesto, monto_total: result.monto_total,
                metodo_pago: result.metodo_pago, items: [...order]
            }, true);
            showToast(`Venta guardada`, 'success');
        } else {
            throw new Error(result.error || "Error al procesar");
        }
    } catch (error) {
        console.error("Error al cobrar:", error);
        showToast(error.message || "Error de conexión al guardar", 'error');
    } finally {
        btnProcessOrder.innerHTML = `Cobrar <span id="btn-total">C$ 0.00</span>`;
        btnProcessOrder.disabled = false;
        updateOrderSummary();
    }
}

function mostrarComprobanteModal(datos, esNuevaVenta = false) {
    const modal = document.getElementById('invoice-modal');
    if (!modal) return;

    const partesFecha = datos.fecha_hora ? datos.fecha_hora.split(' ') : ['', ''];
    document.getElementById('inv-date').textContent = partesFecha[0] || '';
    document.getElementById('inv-time').textContent = partesFecha[1] || '';
    document.getElementById('inv-number').textContent = String(datos.id_factura).padStart(6, '0');
    document.getElementById('inv-cliente').textContent = datos.cliente_nombre;
    document.getElementById('inv-mesa').textContent = datos.mesa_texto;

    document.getElementById('inv-items').innerHTML = (datos.items || []).map(item => `
        <tr>
            <td>${item.cantidad}</td><td>${item.nombre}</td>
            <td>C$ ${item.precio.toFixed(2)}</td><td>C$ ${(item.precio * item.cantidad).toFixed(2)}</td>
        </tr>
    `).join('');

    document.getElementById('inv-subtotal').textContent = `C$ ${parseFloat(datos.subtotal).toFixed(2)}`;
    document.getElementById('inv-tax').textContent = `C$ ${parseFloat(datos.impuesto).toFixed(2)}`;
    document.getElementById('inv-total').textContent = `C$ ${parseFloat(datos.monto_total).toFixed(2)}`;
    document.getElementById('inv-payment-method').textContent = datos.metodo_pago || 'Efectivo';
    
    const btnDone = document.getElementById('btn-done');
    if (btnDone) btnDone.style.display = esNuevaVenta ? 'flex' : 'none';
    
    modal.classList.add('active');
}

function closeModal() { 
    const modal = document.getElementById('invoice-modal');
    if (modal) modal.classList.remove('active'); 
}

function finishOrder() { 
    closeModal(); 
    order = []; 
    renderOrder(); 
    if (clienteInput) clienteInput.value = ''; 
    if (mesaSelect) mesaSelect.value = ''; 
    cargarFacturas(); 
}

async function cargarFacturas() {
    const tbody = document.getElementById('facturas-table-body');
    if (!tbody) return;
    try {
        const response = await window.fetchAuth('/api/facturas');
        const facturas = await response.json();
        if (facturas.length === 0) { tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No hay facturas.</td></tr>'; return; }
        
        tbody.innerHTML = facturas.map(f => `
            <tr>
                <td><strong>#${String(f.id_factura).padStart(6, '0')}</strong></td>
                <td>${f.fecha_hora}</td>
                <td>${f.numero_mesa ? `Mesa #${f.numero_mesa}` : f.tipo_pedido}</td>
                <td>${f.cliente_nombre}</td><td>${f.metodo_pago}</td>
                <td><strong>C$ ${parseFloat(f.monto_total).toFixed(2)}</strong></td>
                <td>
                    <button class="action-btn" onclick="verFactura(${f.id_factura})"><i class="fa-solid fa-print"></i></button>
                    ${window.esAdmin() ? `<button class="action-btn delete" onclick="eliminarFactura(${f.id_factura})"><i class="fa-solid fa-trash-can"></i></button>` : ''}
                </td>
            </tr>
        `).join('');
    } catch (err) { tbody.innerHTML = '<tr><td colspan="7">Error.</td></tr>'; }
}

window.verFactura = async function(id_factura) {
    const response = await window.fetchAuth('/api/facturas/' + id_factura);
    const factura = await response.json();
    mostrarComprobanteModal(factura, false);
};

window.eliminarFactura = async function(id_factura) {
    if (!confirm('¿Estás seguro de eliminar esta factura permanentemente? Esta acción no se puede deshacer.')) return;
    
    try {
        const res = await window.fetchAuth('/api/facturas/' + id_factura, {
            method: 'DELETE',
            headers: { 'X-Confirm-Delete': 'yes' }
        });
        
        if (res.ok) {
            showToast('Factura eliminada correctamente', 'success');
            cargarFacturas(); 
        } else {
            const data = await res.json();
            showToast(data.error || 'Error al eliminar', 'error');
        }
    } catch (err) {
        showToast('Error de conexión', 'error');
    }
};

function setupEventListeners() {
    if (searchInput) searchInput.addEventListener('input', (e) => { searchQuery = e.target.value; renderProducts(); });
    if (btnClearOrder) btnClearOrder.addEventListener('click', () => { if (order.length > 0) { order = []; renderOrder(); } });
    
    document.querySelectorAll('.payment-method').forEach(method => {
        method.addEventListener('click', (e) => {
            document.querySelectorAll('.payment-method').forEach(m => m.classList.remove('selected'));
            e.currentTarget.classList.add('selected');
            e.currentTarget.querySelector('input').checked = true;
        });
    });

    if (btnProcessOrder) btnProcessOrder.addEventListener('click', processOrder);
    
    const closeBtn = document.getElementById('close-invoice');
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    
    const doneBtn = document.getElementById('btn-done');
    if (doneBtn) doneBtn.addEventListener('click', finishOrder);
    
    // EVENTO DEL BOTÓN DE IMPRIMIR
    const printBtn = document.getElementById('btn-print');
    if (printBtn) printBtn.addEventListener('click', () => window.print());

    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            e.currentTarget.classList.add('active');
            document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active-view'));
            const view = document.getElementById(`${e.currentTarget.dataset.tab}-view`);
            if (view) view.classList.add('active-view');
            if (e.currentTarget.dataset.tab === 'inventory') cargarFacturas();
            if (e.currentTarget.dataset.tab === 'usuarios' && typeof cargarUsuarios === 'function') cargarUsuarios();
        });
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fa-solid fa-info-circle"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.classList.add('fade-out'); setTimeout(() => toast.remove(), 300); }, 3000);
}

document.addEventListener('DOMContentLoaded', initApp);