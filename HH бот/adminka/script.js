;(function () {
	const $ = s => document.querySelector(s)
	const pageEls = {
		dashboard: $('#page-dashboard'),
		broadcasts: $('#page-broadcasts'),
	}

	// ===== Basic Auth handling =====
	function getAuthHeader() {
		let token = sessionStorage.getItem('basic64')
		if (!token) {
			const u = prompt('Admin user:')
			const p = prompt('Admin pass:')
			if (!u || !p) return null
			token = btoa(u + ':' + p)
			sessionStorage.setItem('basic64', token)
		}
		return { Authorization: 'Basic ' + token }
	}
	function resetAuth() {
		sessionStorage.removeItem('basic64')
		$('#authState').className = 'badge err'
		$('#authState').innerHTML =
			'<i class="fa-solid fa-unlock"></i> Нужна авторизация'
	}
	$('#resetAuthBtn').addEventListener('click', () => {
		resetAuth()
		toast('Авторизация сброшена', 'ok')
	})

	// ===== API helper =====
	async function api(path, opts = {}) {
		const headers = opts.headers || {}
		const auth = getAuthHeader()
		if (!auth) throw new Error('Нет логина/пароля администратора')
		Object.assign(headers, auth)
		if (opts.body && !headers['Content-Type'])
			headers['Content-Type'] = 'application/json'
		const res = await fetch(path, { ...opts, headers })
		if (res.status === 401) {
			resetAuth()
			throw new Error('401 Unauthorized — неверные логин/пароль')
		}
		if (!res.ok) {
			const t = await res.text().catch(() => '')
			throw new Error(res.status + ' ' + res.statusText + (t ? ': ' + t : ''))
		}
		const ct = res.headers.get('content-type') || ''
		return ct.includes('application/json') ? res.json() : res.text()
	}

	// ===== Toast =====
	let toastTimer
	function toast(msg, type = 'ok') {
		const t = $('#toast')
		t.textContent = msg
		t.className = 'toast show'
		clearTimeout(toastTimer)
		toastTimer = setTimeout(() => (t.className = 'toast'), 2400)
	}

	// ===== Navigation =====
	document.querySelectorAll('.nav .item').forEach(el => {
		el.addEventListener('click', () => {
			document
				.querySelectorAll('.nav .item')
				.forEach(i => i.classList.remove('active'))
			el.classList.add('active')
			const page = el.dataset.page
			$('#page-title').textContent = el.textContent.trim()
			Object.values(pageEls).forEach(p => (p.style.display = 'none'))
			pageEls[page].style.display = ''
			if (page === 'dashboard') loadMetrics()
		})
	})

	// ===== Dashboard: metrics =====
	async function loadMetrics() {
		$('#loadState').textContent = 'Запрашиваю…'
		try {
			const data = await api('/api/admin/metrics')
			// Fill cards
			$('#mTotal').textContent =
				(data.total_users ?? '—').toLocaleString?.() ??
				String(data.total_users ?? '—')
			$('#mActive').textContent =
				(data.active_today ?? '—').toLocaleString?.() ??
				String(data.active_today ?? '—')
			$('#mSearches').textContent =
				(data.searches_24h ?? '—').toLocaleString?.() ??
				String(data.searches_24h ?? '—')
			// Show raw
			$('#metricsRaw').textContent = JSON.stringify(data, null, 2)
			$('#loadState').textContent = 'OK'
			$('#authState').className = 'badge ok'
			$('#authState').innerHTML =
				'<i class="fa-solid fa-lock"></i> Авторизовано'
		} catch (e) {
			$('#loadState').textContent = 'Ошибка'
			$('#metricsRaw').textContent = String(e.message || e)
			toast('Ошибка получения метрик: ' + (e.message || e), 'err')
		}
	}
	$('#reloadBtn').addEventListener('click', loadMetrics)
	// Автозагрузка метрик при старте
	loadMetrics().catch(() => {
		/* handled in loadMetrics */
	})

	// ===== Broadcasts =====
	$('#sendBtn').addEventListener('click', async () => {
		const text = ($('#bcText').value || '').trim()
		if (!text) return toast('Введите текст рассылки', 'err')
		try {
			const resp = await api('/api/admin/broadcasts', {
				method: 'POST',
				body: JSON.stringify({ text }),
			})
			toast('Рассылка поставлена в очередь', 'ok')
		} catch (e) {
			toast('Ошибка отправки: ' + (e.message || e), 'err')
		}
	})

	$('#dryBtn').addEventListener('click', () => {
		const text = ($('#bcText').value || '').trim()
		if (!text) return toast('Введите текст для теста', 'err')
		// Просто показать превью, без запроса
		toast('Проверка payload: ок', 'ok')
		console.log('DRY RUN payload:', { text, chat_ids: undefined })
	})
})()
