(function () {
    function getCookie(name) {
        const raw = document.cookie || '';
        for (const part of raw.split(';')) {
            const [k, ...rest] = part.trim().split('=');
            if (k === name) return rest.join('=');
        }
        return null;
    }

    window.getCsrfToken = () => getCookie('csrf_token') || '';
    window.usuarioActual = null;

    window.fetchAuth = async function (url, opts = {}) {
        const method = (opts.method || 'GET').toUpperCase();
        const headers = new Headers(opts.headers || {});
        if (opts.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
        if (['POST', 'PUT', 'DELETE'].includes(method)) headers.set('X-CSRF-Token', window.getCsrfToken());

        const res = await fetch(url, { ...opts, method, headers, credentials: 'same-origin' });
        
        if (res.status === 401) {
            window.location.href = 'login.html';
            throw new Error('Sesión expirada. Vuelve a iniciar sesión.');
        }
        
        return res;
    };

    window.cargarUsuarioActual = async function () {
        try {
            const res = await window.fetchAuth('/api/auth/me');
            if (res.ok) window.usuarioActual = await res.json();
            return window.usuarioActual;
        } catch (err) { return null; }
    };

    window.cerrarSesion = async function () {
        try { await window.fetchAuth('/api/auth/logout', { method: 'POST' }); } catch (e) {}
        window.location.href = 'login.html';
    };

    window.esAdmin = () => window.usuarioActual && window.usuarioActual.rol === 'admin';
    window.esCajero = () => window.usuarioActual && window.usuarioActual.rol === 'cajero';
    window.esMesero = () => window.usuarioActual && window.usuarioActual.rol === 'mesero';
})();