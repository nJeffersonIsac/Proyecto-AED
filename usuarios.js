function abrirModalUsuario() {
    document.getElementById('user-modal').classList.add('active');
    document.getElementById('user-error').style.display = 'none';
    const rolSelect = document.getElementById('new-rol');
    if (window.esMesero()) {
        rolSelect.innerHTML = '<option value="mesero">Mesero</option>';
    } else {
        rolSelect.innerHTML = '<option value="mesero">Mesero</option><option value="cajero">Cajero</option><option value="admin">Admin</option>';
    }
}

function cerrarModalUsuario() {
    document.getElementById('user-modal').classList.remove('active');
    document.getElementById('user-form').reset();
}

async function cargarUsuarios() {
    const tbody = document.getElementById('usuarios-tbody');
    if (!tbody) return;
    if (window.esMesero()) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Como mesero, solo puedes crear usuarios. Usa el botón superior.</td></tr>';
        return;
    }
    try {
        const res = await window.fetchAuth('/api/usuarios');
        const users = await res.json();
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${u.id_usuario}</td>
                <td>${u.username}</td>
                <td>${u.nombre_completo}</td>
                <td><span class="badge badge-${u.rol}">${u.rol}</span></td>
                <td>${u.activo ? 'Sí' : 'No'}</td>
                <td>
                    ${window.esAdmin() && u.id_usuario !== window.usuarioActual.id_usuario ? 
                    `<button class="action-btn delete" onclick="eliminarUsuario(${u.id_usuario})"><i class="fa-solid fa-trash-can"></i></button>` : '—'}
                </td>
            </tr>
        `).join('');
    } catch (e) { tbody.innerHTML = '<tr><td colspan="6">Error al cargar usuarios</td></tr>'; }
}

window.eliminarUsuario = async (id) => {
    if (!confirm('¿Eliminar/desactivar este usuario?')) return;
    const res = await window.fetchAuth('/api/usuarios/' + id, { method: 'DELETE' });
    if (res.ok) { showToast('Usuario procesado', 'success'); cargarUsuarios(); }
    else showToast('Error', 'error');
};

document.getElementById('user-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errBox = document.getElementById('user-error');
    errBox.style.display = 'none';

    const payload = {
        username: document.getElementById('new-username').value,
        nombre_completo: document.getElementById('new-nombre').value,
        password: document.getElementById('new-password').value,
        rol: document.getElementById('new-rol').value
    };

    try {
        const res = await window.fetchAuth('/api/usuarios', { method: 'POST', body: JSON.stringify(payload) });
        const data = await res.json();
        if (res.ok) {
            showToast('Usuario creado', 'success');
            cerrarModalUsuario();
            cargarUsuarios();
        } else {
            errBox.textContent = data.error; errBox.style.display = 'block';
        }
    } catch (e) {
        errBox.textContent = 'Error de conexión'; errBox.style.display = 'block';
    }
});

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if (item.dataset.tab === 'usuarios') cargarUsuarios();
    });
});