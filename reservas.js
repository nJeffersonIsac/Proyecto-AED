let reservasCache = [];

async function cargarReservas() {
    const tbody = document.getElementById('reservas-tbody');
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Cargando...</td></tr>';
    try {
        const fecha = document.getElementById('filtro-fecha').value;
        const estado = document.getElementById('filtro-estado').value;
        const qs = new URLSearchParams({ ...(fecha && {fecha}), ...(estado && {estado}) }).toString();
        
        const res = await window.fetchAuth(`/api/reservas${qs ? '?' + qs : ''}`);
        reservasCache = await res.json();
        
        if (!reservasCache.length) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No hay reservas.</td></tr>';
            return;
        }
        tbody.innerHTML = reservasCache.map(r => {
            const btns = [];
            if (r.estado === 'pendiente') btns.push(`<button class="action-btn" onclick="cambiarEstado(${r.id_reserva}, 'confirmada')" title="Confirmar"><i class="fa-solid fa-check"></i></button>`);
            if (r.estado === 'confirmada') btns.push(`<button class="action-btn" onclick="cambiarEstado(${r.id_reserva}, 'completada')" title="Completar"><i class="fa-solid fa-flag-checkered"></i></button>`);
            if (r.estado === 'pendiente' || r.estado === 'confirmada') btns.push(`<button class="action-btn delete" onclick="cambiarEstado(${r.id_reserva}, 'cancelada')" title="Cancelar"><i class="fa-solid fa-ban"></i></button>`);
            
            return `<tr>
                <td>${r.fecha_reserva}</td><td>${r.hora_reserva}</td><td>${r.nombre_cliente}</td>
                <td>${r.num_personas}</td><td>${r.numero_mesa ? 'Mesa #'+r.numero_mesa : '—'}</td>
                <td><span class="badge badge-${r.estado}">${r.estado}</span></td>
                <td>${btns.join('')}</td>
            </tr>`;
        }).join('');
    } catch (e) { tbody.innerHTML = '<tr><td colspan="7">Error al cargar</td></tr>'; }
}

async function abrirModalReserva() {
    document.getElementById('reserva-form').reset();
    const hoy = new Date().toISOString().split('T')[0];
    document.getElementById('res-fecha').value = hoy;
    document.getElementById('res-fecha').min = hoy;
    document.getElementById('reserva-error').style.display = 'none';
    
    const sel = document.getElementById('res-mesa');
    sel.innerHTML = '<option value="">Cargando...</option>';
    const res = await window.fetchAuth('/api/reservas/disponibilidad?personas=1');
    const mesas = await res.json();
    sel.innerHTML = '<option value="">Sin asignar</option>' + mesas.map(m => `<option value="${m.id_mesa}">Mesa #${m.numero_mesa} (Cap. ${m.capacidad})</option>`).join('');
    
    document.getElementById('reserva-modal').classList.add('active');
}

function cerrarModalReserva() { document.getElementById('reserva-modal').classList.remove('active'); }

window.cambiarEstado = async (id, estado) => {
    const res = await window.fetchAuth('/api/reservas/' + id, { method: 'PUT', body: JSON.stringify({ estado }) });
    if (res.ok) cargarReservas();
};

document.getElementById('reserva-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errBox = document.getElementById('reserva-error');
    const payload = {
        nombre_cliente: document.getElementById('res-nombre').value,
        telefono: document.getElementById('res-telefono').value,
        fecha_reserva: document.getElementById('res-fecha').value,
        hora_reserva: document.getElementById('res-hora').value,
        num_personas: parseInt(document.getElementById('res-personas').value),
        id_mesa: document.getElementById('res-mesa').value ? parseInt(document.getElementById('res-mesa').value) : null,
        notas: document.getElementById('res-notas').value
    };
    try {
        const res = await window.fetchAuth('/api/reservas', { method: 'POST', body: JSON.stringify(payload) });
        const data = await res.json();
        if (res.ok) {
            cerrarModalReserva();
            cargarReservas();
        } else {
            errBox.textContent = data.error; errBox.style.display = 'block';
        }
    } catch (e) { errBox.textContent = 'Error de conexión'; errBox.style.display = 'block'; }
});

document.addEventListener('DOMContentLoaded', async () => {
    await window.cargarUsuarioActual();
    
    // REGLA: Si es admin, ocultar el botón de crear reserva
    if (window.esAdmin()) {
        const btn = document.getElementById('btn-nueva-reserva');
        if (btn) btn.style.display = 'none';
    }
    
    cargarReservas();
});