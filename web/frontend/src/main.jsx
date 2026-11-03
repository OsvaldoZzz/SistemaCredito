import React, { useEffect, useId, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { api, configureSession, currency, dateLabel, today } from './api';
import Map from './Map';
import './styles.css';

const roleNames = { administrador: 'Administración', recepcionista: 'Recepción', cobrador: 'Cobranza', cliente: 'Cliente' };
const icons = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  clientes: <><circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-3-5"/></>,
  prestamos: <><rect x="3" y="5" width="18" height="15" rx="3"/><path d="M3 10h18M7 15h4"/></>,
  solicitudes: <><path d="M14 3H6a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM14 3v6h6M8 14h8M8 18h5"/></>,
  citas: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M8 15h2M14 15h2"/></>,
  usuarios: <><path d="m12 3 8 4v6c0 5-8 9-8 9s-8-4-8-9V7z"/><path d="m8 12 3 3 5-6"/></>,
  reportes: <><path d="M4 21h16M6 17v-6M12 17V4M18 17V8"/></>,
  ubicacion: <><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></>,
  exit: <><path d="M9 4H4v16h5M14 8l4 4-4 4M8 12h13"/></>,
  plus: <path d="M12 5v14M5 12h14"/>,
  search: <><circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/></>,
};
function Icon({ name }) { return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{icons[name] || icons.prestamos}</svg>; }
function Brand() { return <div className="brand"><span className="brand-symbol">S<span>c</span></span><div>SistCreditos<small>GESTIÓN FINANCIERA</small></div></div>; }
function Badge({ value }) { return <span className={`badge ${['Pagado', 'Aprobada', 'Activo'].includes(value) ? 'green' : ['Vencido', 'Rechazada'].includes(value) ? 'red' : 'amber'}`}>{value}</span>; }
function Empty({ children = 'No hay registros para mostrar.' }) { return <div className="empty"><Icon name="solicitudes"/><p>{children}</p></div>; }
function Field({ label, children, ...props }) {
  const fieldId = useId();
  return <div className="field"><label htmlFor={fieldId}>{label}</label>{children ? React.cloneElement(children, { id: fieldId }) : <input id={fieldId} {...props}/>}</div>;
}
function Table({ columns, rows, rowKey = 'id', empty }) {
  if (!rows.length) return <Empty>{empty}</Empty>;
  return <div className="table-wrap"><table><thead><tr>{columns.map(c => <th key={c.label}>{c.label}</th>)}</tr></thead><tbody>{rows.map((r, i) => <tr key={r[rowKey] ?? i}>{columns.map(c => <td key={c.label}>{c.render(r)}</td>)}</tr>)}</tbody></table></div>;
}
function Modal({ title, children, onClose, wide = false }) {
  const ref = useRef(null);
  useEffect(() => { const el = ref.current; el.showModal(); return () => el.close(); }, []);
  return <dialog ref={ref} className={`modal ${wide ? 'wide' : ''}`} onCancel={onClose} onClick={e => { if (e.target === ref.current) onClose(); }}>
    <div className="modal-head"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Cerrar">×</button></div>{children}
  </dialog>;
}
function Form({ onSubmit, children, onCancel, submit = 'Guardar', busy: externalBusy = false }) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  return <form onSubmit={async e => {
    e.preventDefault(); if (busy || externalBusy) return; setBusy(true); setError('');
    try { await onSubmit(); } catch (e) { setError(e.message); } finally { setBusy(false); }
  }}>{children}{error && <div role="alert" className="alert error">{error}</div>}<div className="form-actions">{onCancel && <button type="button" className="secondary" onClick={onCancel}>Cancelar</button>}<button disabled={busy || externalBusy} type="submit">{busy ? 'Guardando…' : submit}</button></div></form>;
}

function Login({ onLogin }) {
  const [form, setForm] = useState({ usuario: '', password: '' }), [health, setHealth] = useState(null);
  useEffect(() => { let live = true; api('/health').then(() => { if (live) setHealth('ok'); }).catch(e => { if (live) setHealth(e.message); }); return () => { live = false; }; }, []);
  return <div className="login-layout"><section className="login-story"><Brand/><div><span className="eyebrow light">CADA CUENTA, EN ORDEN</span><h1>Más claridad.<br/>Mejor gestión.</h1><p>Clientes, préstamos y cobranza en un solo lugar. Todo lo que necesitas para acompañar cada crédito.</p><div className="login-stat"><span>15<small>%</small></span><div>Interés sobre el capital<small>Para los nuevos préstamos</small></div></div></div><small>Tu cartera, con una visión completa.</small></section>
    <main className="login-main"><div className="login-card"><span className="eyebrow">BIENVENIDO A SISTCREDITOS</span><h2>Inicia sesión</h2><p className="muted">Ingresa con tu usuario del personal o tu correo de cliente.</p>
      {health && health !== 'ok' && <div className="alert">{health}</div>}
      <Form submit="Ingresar al sistema →" onSubmit={async () => onLogin(await api('/login', { method: 'POST', body: form }))}>
        <Field label="Usuario o correo" value={form.usuario} onChange={e => setForm({ ...form, usuario: e.target.value })} autoComplete="username" required maxLength={254}/>
        <Field label="Contraseña" type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} autoComplete="current-password" minLength={8} maxLength={12} required/>
      </Form><p className="login-note">El acceso y las funciones dependen de tu rol.</p>
    </div></main></div>;
}

function ClientForm({ client, onSave, onClose }) {
  const [form, setForm] = useState(client ? { ...client, password: '' } : { nombre: '', cedula: '', correo: '', password: '', direccion: '', monto: '0.00', latitud: null, longitud: null });
  const set = (key, value) => setForm(f => ({ ...f, [key]: value }));
  return <Modal title={client ? 'Editar cliente' : 'Nuevo cliente'} onClose={onClose} wide><Form onCancel={onClose} onSubmit={() => onSave(form)}>
    <div className="form-grid">
      <Field label="Nombre completo" value={form.nombre} onChange={e => set('nombre', e.target.value)} minLength={2} maxLength={80} required/>
      <Field label="Cédula" value={form.cedula} onChange={e => set('cedula', e.target.value)} minLength={6} maxLength={20} required/>
      <Field label="Correo electrónico" type="email" value={form.correo} onChange={e => set('correo', e.target.value)} maxLength={100} required/>
      <Field label={client ? 'Nueva contraseña (opcional)' : 'Contraseña'} type="password" value={form.password} onChange={e => set('password', e.target.value)} autoComplete="new-password" minLength={8} maxLength={12} required={!client}/>
      <Field label="Dirección" value={form.direccion} onChange={e => set('direccion', e.target.value)} minLength={5} maxLength={40} required/>
      <Field label="Monto de referencia (C$)" type="number" min="0" max="100000000" step="0.01" value={form.monto} onChange={e => set('monto', e.target.value)} required/>
    </div><LocationFields value={form} onChange={value => setForm(f => ({ ...f, ...value }))}/>
  </Form></Modal>;
}
function LocationFields({ value, onChange, readOnly = false }) {
  const hasPoint = value.latitud != null && value.latitud !== '' && value.longitud != null && value.longitud !== '';
  return <div className="location"><p className="muted">{readOnly ? hasPoint ? 'Ubicación guardada del cliente.' : 'El cliente todavía no ha marcado una ubicación.' : 'Marca un punto en el mapa o escribe las coordenadas. La ubicación es opcional.'}</p>
    {(!readOnly || hasPoint) && <Map latitud={value.latitud} longitud={value.longitud} onChange={onChange} readOnly={readOnly}/>}
    {!readOnly && <div className="coordinate-row"><Field label="Latitud" type="number" step="any" min="-90" max="90" value={value.latitud ?? ''} onChange={e => onChange({ latitud: e.target.value === '' ? null : e.target.value })}/><Field label="Longitud" type="number" step="any" min="-180" max="180" value={value.longitud ?? ''} onChange={e => onChange({ longitud: e.target.value === '' ? null : e.target.value })}/><button type="button" className="text-button" onClick={() => onChange({ latitud: null, longitud: null })}>Quitar punto</button></div>}
    {readOnly && hasPoint && <a className="button secondary" href={`https://www.google.com/maps/dir/?api=1&destination=${Number(value.latitud)},${Number(value.longitud)}`} target="_blank" rel="noreferrer">Abrir ruta en Google Maps ↗</a>}
  </div>;
}
function LoanForm({ clients, request = false, loan, onSave, onClose }) {
  const [form, setForm] = useState(loan ? { ...loan } : { cliente_id: clients[0]?.id ?? '', monto: '', plazo: 12, frecuencia_pago: 'Mensual', fecha_primer_pago: today(), ingreso_mensual: '', estado: 'Activo' });
  const [simulation, setSimulation] = useState(null), [previewError, setPreviewError] = useState('');
  const set = (key, value) => { setForm(f => ({ ...f, [key]: value })); setSimulation(null); setPreviewError(''); };
  const payload = () => ({ ...form, cliente_id: Number(form.cliente_id), plazo: Number(form.plazo) });
  return <Modal title={loan ? 'Editar préstamo' : request ? 'Solicitud de préstamo' : 'Nuevo préstamo'} onClose={onClose} wide><Form onCancel={onClose} onSubmit={() => onSave(payload())} submit={request ? 'Enviar solicitud' : 'Guardar préstamo'}>
    <div className="alert">{loan ? `Tasa de este préstamo: ${Number(loan.tasa_interes) * 100} %.` : 'Interés fijo del 15 % sobre el capital, distribuido entre las cuotas.'}</div>
    <div className="form-grid">
      {!loan && <Field label="Cliente"><select value={form.cliente_id} onChange={e => set('cliente_id', e.target.value)} required><option value="">Seleccionar cliente</option>{clients.map(c => <option key={c.id} value={c.id}>{c.nombre} · {c.cedula}</option>)}</select></Field>}
      <Field label="Capital (C$)" type="number" min="0.01" max="100000000" step="0.01" value={form.monto} onChange={e => set('monto', e.target.value)} required/>
      <Field label="Número de cuotas" type="number" min="1" max="360" step="1" value={form.plazo} onChange={e => set('plazo', e.target.value)} required/>
      {!loan && <Field label="Frecuencia de pago"><select value={form.frecuencia_pago} onChange={e => set('frecuencia_pago', e.target.value)}>{['Semanal', 'Quincenal', 'Mensual'].map(f => <option key={f}>{f}</option>)}</select></Field>}
      {!loan && !request && <Field label="Fecha del primer pago" type="date" min={today()} value={form.fecha_primer_pago} onChange={e => set('fecha_primer_pago', e.target.value)} required/>}
      {request && <Field label="Ingreso mensual (C$)" type="number" min="0.01" max="100000000" step="0.01" value={form.ingreso_mensual} onChange={e => set('ingreso_mensual', e.target.value)} required/>}
      {loan && <Field label="Estado"><select value={form.estado} onChange={e => set('estado', e.target.value)}>{['Activo', 'Vencido', 'Pagado'].map(s => <option key={s}>{s}</option>)}</select></Field>}
    </div>
    {!loan && <><button type="button" className="secondary" onClick={async () => { try { setSimulation(await api('/simulacion', { method: 'POST', body: payload() })); setPreviewError(''); } catch (e) { setPreviewError(e.message); } }}>Ver distribución de cuotas</button>
      {request && <p className="muted">La simulación usa hoy como primera fecha. Administración definirá el primer pago al aprobar.</p>}
      {previewError && <p className="error-text" role="alert">{previewError}</p>}
      {simulation && <div className="preview-table"><Table rows={simulation.cuotas} rowKey="numero" columns={[{ label: 'Cuota', render: q => q.numero }, { label: 'Vencimiento', render: q => dateLabel(q.fecha_vencimiento) }, { label: 'Capital', render: q => currency(q.capital) }, { label: 'Interés', render: q => currency(q.interes) }, { label: 'Total', render: q => currency(q.monto) }]}/></div>}
    </>}
  </Form></Modal>;
}
function StaffForm({ user, onSave, onClose }) {
  const [form, setForm] = useState(user ? { ...user, password: '' } : { usuario: '', rol: 'recepcionista', password: '' });
  return <Modal title={user ? 'Editar usuario' : 'Nuevo usuario'} onClose={onClose}><Form onCancel={onClose} onSubmit={() => onSave(form)}>
    <Field label="Nombre de usuario o correo" value={form.usuario} maxLength={100} required onChange={e => setForm({ ...form, usuario: e.target.value })}/>
    <Field label="Rol"><select value={form.rol} onChange={e => setForm({ ...form, rol: e.target.value })}>{['administrador', 'recepcionista', 'cobrador'].map(r => <option key={r} value={r}>{roleNames[r]}</option>)}</select></Field>
    <Field label={user ? 'Nueva contraseña (opcional)' : 'Contraseña'} type="password" minLength={8} maxLength={12} required={!user} value={form.password} autoComplete="new-password" onChange={e => setForm({ ...form, password: e.target.value })}/>
  </Form></Modal>;
}
function AssignmentForm({ user, clients, onSave, onClose }) {
  const [selected, setSelected] = useState(user.clientes_asignados || []);
  return <Modal title={`Clientes de ${user.usuario}`} onClose={onClose}><Form onCancel={onClose} onSubmit={() => onSave(selected)}>
    <div className="checkbox-list">{!clients.length && <Empty/>}{clients.map(c => <label key={c.id}><input type="checkbox" checked={selected.includes(c.id)} onChange={e => setSelected(e.target.checked ? [...selected, c.id] : selected.filter(v => v !== c.id))}/><span>{c.nombre}<small>{c.cedula}</small></span></label>)}</div>
  </Form></Modal>;
}
function LoanDetail({ loan: initial, user, onClose, onRefresh }) {
  const [loan, setLoan] = useState(initial), [payment, setPayment] = useState({ numero_cuota: initial.cuotas.find(q => Number(q.total_pendiente) > 0)?.numero ?? '', monto: '' }), [receiptId, setReceiptId] = useState(null);
  const staff = user.rol !== 'cliente';
  return <Modal title={`Préstamo #${loan.id} · ${loan.nombre}`} onClose={onClose} wide>
    <div className="detail-stats"><div><small>Capital</small><strong>{currency(loan.monto)}</strong></div><div><small>Interés ({Number(loan.tasa_interes) * 100} %)</small><strong>{currency(loan.interes_total)}</strong></div><div><small>Saldo con mora</small><strong>{currency(loan.saldo_pendiente)}</strong></div></div>
    <Table rows={loan.cuotas} rowKey="numero" columns={[
      { label: 'Cuota', render: q => q.numero }, { label: 'Vence', render: q => dateLabel(q.fecha_vencimiento) }, { label: 'Monto', render: q => currency(q.monto) }, { label: 'Abonado', render: q => currency(q.pagado) }, { label: 'Mora pendiente', render: q => currency(q.mora_pendiente) }, { label: 'Días mora', render: q => q.dias_mora }, { label: 'Saldo', render: q => currency(q.total_pendiente) },
    ]}/>
    {staff && loan.cuotas_pendientes > 0 && <div className="payment-box"><h3>Registrar abono</h3><p className="muted">El abono cubre primero la mora y luego el saldo de la cuota.</p><Form submit="Registrar abono" onSubmit={async () => {
      const result = await api(`/prestamos/${loan.id}/abonos`, { method: 'POST', body: { ...payment, numero_cuota: Number(payment.numero_cuota) } });
      setReceiptId(result.id); setPayment({ ...payment, monto: '' });
      setLoan(await api(`/prestamos/${loan.id}`)); await onRefresh();
    }}><div className="form-grid"><Field label="Cuota"><select value={payment.numero_cuota} required onChange={e => setPayment({ ...payment, numero_cuota: Number(e.target.value) })}><option value="">Seleccionar cuota</option>{loan.cuotas.filter(q => Number(q.total_pendiente) > 0).map(q => <option key={q.numero} value={q.numero}>#{q.numero} · Saldo {currency(q.total_pendiente)}</option>)}</select></Field>
      <Field label="Monto del abono (C$)" type="number" min="0.01" step="0.01" max={loan.cuotas.find(q => q.numero === Number(payment.numero_cuota))?.total_pendiente} required value={payment.monto} onChange={e => setPayment({ ...payment, monto: e.target.value })}/></div></Form></div>}
    {receiptId && <p className="alert success">Abono registrado. <a href={`/api/recibos/${receiptId}`} target="_blank" rel="noreferrer">Descargar recibo PDF ↗</a></p>}
    <h3>Historial de abonos</h3><Table rows={loan.cuotas.flatMap(q => q.pagos_calculados.map(p => ({ ...p, numero: q.numero })))} columns={[
      { label: 'Fecha', render: p => p.fecha_pago }, { label: 'Cuota', render: p => p.numero }, { label: 'Monto', render: p => currency(p.monto) }, { label: 'Aplicado a mora', render: p => currency(p.mora_aplicada) }, { label: 'Recibo', render: p => <a href={`/api/recibos/${p.id}`} target="_blank" rel="noreferrer">PDF ↗</a> },
    ]}/>
  </Modal>;
}

function App() {
  const [session, setSession] = useState(null), [checking, setChecking] = useState(true);
  const [page, setPage] = useState('dashboard'), [data, setData] = useState({ clients: [], loans: [], requests: [], appointments: [], users: [] });
  const [loading, setLoading] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState(''), [modal, setModal] = useState(null), [search, setSearch] = useState('');
  const accept = s => { configureSession(s.csrf, () => { setSession(null); setModal(null); setData({ clients: [], loans: [], requests: [], appointments: [], users: [] }); }); setSession(s); setError(''); setPage('dashboard'); };
  useEffect(() => { let live = true; api('/session').then(s => { if (live) accept(s); }).catch(() => {}).finally(() => { if (live) setChecking(false); }); return () => { live = false; }; }, []);
  const user = session?.user, admin = user?.rol === 'administrador', client = user?.rol === 'cliente', collector = user?.rol === 'cobrador';
  async function refresh() {
    if (!user) return;
    setLoading(true); setError('');
    try {
      const [clients, loans, requests, appointments, users] = await Promise.all([
        api('/clientes'), api('/prestamos'), (!client && !collector) ? api('/solicitudes') : [], !collector ? api('/citas') : [], admin ? api('/usuarios') : [],
      ]);
      setData({ clients, loans, requests, appointments, users });
    } catch (e) { setError(e.message); throw e; } finally { setLoading(false); }
  }
  useEffect(() => { if (user) refresh().catch(() => {}); }, [user?.id, user?.rol]);
  async function save(path, body, method = 'POST', message = 'Cambios guardados.') {
    await api(path, { method, body }); setModal(null); setNotice(message); await refresh();
  }
  async function act(action) { setError(''); setNotice(''); try { await action(); } catch (e) { setError(e.message); } }
  const confirmDelete = (path, name) => setModal({ type: 'delete', path, name });
  if (checking) return <div className="splash"><Brand/><p>Abriendo tu espacio…</p></div>;
  if (!session) return <Login onLogin={accept}/>;
  const menu = [ ['dashboard', 'Resumen'], ...(!client ? [['clientes', collector ? 'Mis clientes' : 'Clientes']] : []), ['prestamos', client ? 'Mis préstamos' : 'Préstamos'], ...(!client && !collector ? [['solicitudes', 'Solicitudes']] : []), ...(!collector ? [['citas', client ? 'Mis citas' : 'Citas']] : []), ...(admin ? [['usuarios', 'Usuarios y roles']] : []), ...(!client ? [['reportes', 'Reportes']] : [['ubicacion', 'Mi dirección']]) ];
  const title = menu.find(m => m[0] === page)?.[1] ?? 'Resumen';
  const filter = records => records.filter(r => `${r.nombre ?? ''} ${r.cedula ?? ''} ${r.correo ?? ''} ${r.usuario ?? ''} ${r.id}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
  const loanColumns = [
    { label: 'Préstamo / cliente', render: p => <div className="person"><span className="mini-icon">#{p.id}</span><span><strong>{p.nombre}</strong><small>{p.cedula}</small></span></div> },
    { label: 'Capital', render: p => currency(p.monto) }, { label: 'Interés', render: p => `${Number(p.tasa_interes) * 100} %` }, { label: 'Saldo pendiente', render: p => <strong>{currency(p.saldo_pendiente)}</strong> },
    { label: 'Cuotas', render: p => `${p.cuotas_pendientes} de ${p.plazo}` }, { label: 'Estado', render: p => <Badge value={p.estado_actual}/> },
    { label: 'Acciones', render: p => <div className="row-actions"><button className="text-button" onClick={() => setModal({ type: 'detail', value: p })}>Ver cuotas</button>{admin && <><button className="text-button" onClick={() => setModal({ type: 'loan', value: p })}>Editar</button><button className="text-button danger" onClick={() => confirmDelete(`/prestamos/${p.id}`, `el préstamo #${p.id} y sus abonos`)}>Eliminar</button></>}</div> },
  ];
  return <div className="app-layout"><aside className="sidebar"><Brand/><div className="workspace-name"><span className="workspace-dot"/>ESPACIO DE {client ? 'CLIENTE' : 'TRABAJO'}</div><nav aria-label="Menú principal">{menu.map(([key, label]) => <button key={key} className={page === key ? 'active' : ''} onClick={() => { setPage(key); setSearch(''); setNotice(''); }}><Icon name={key}/><span>{label}</span>{key === 'solicitudes' && data.requests.length > 0 && <b>{data.requests.length}</b>}</button>)}</nav><div className="sidebar-bottom"><div className="user"><span className="avatar">{user.usuario.slice(0, 2).toUpperCase()}</span><div><strong>{user.usuario}</strong><small>{roleNames[user.rol]}</small></div></div><button className="logout" onClick={() => act(async () => { await api('/logout', { method: 'POST' }); configureSession(''); setSession(null); setData({ clients: [], loans: [], requests: [], appointments: [], users: [] }); })}><Icon name="exit"/>Cerrar sesión</button></div></aside>
    <main className="main"><header className="topbar"><span>Tu gestión, al día <span className="online-dot"/></span><span>{new Intl.DateTimeFormat('es-NI', { dateStyle: 'long', timeZone: 'America/Managua' }).format(new Date())}</span></header>
      <div className="content"><div className="page-heading"><div><span className="eyebrow">{roleNames[user.rol]}</span><h1>{title}</h1><p className="muted">{page === 'dashboard' ? `Hola, ${user.usuario}. Así está tu cartera hoy.` : page === 'clientes' ? 'Información y seguimiento de tus clientes.' : page === 'prestamos' ? 'Cada crédito, sus cuotas y su historial de pagos.' : page === 'solicitudes' ? 'Revisa las solicitudes antes de convertirlas en préstamos.' : page === 'usuarios' ? 'Gestiona el equipo, sus roles y las asignaciones.' : page === 'reportes' ? 'Descarga la información de tu cartera en PDF.' : page === 'ubicacion' ? 'Mantén tu dirección y ubicación actualizadas.' : 'Consulta las próximas visitas agendadas.'}</p></div>
        <div className="heading-actions"><button className="secondary" onClick={() => act(refresh)} disabled={loading}>{loading ? 'Actualizando…' : 'Actualizar'}</button>
          {page === 'clientes' && <button onClick={() => setModal({ type: 'client' })}><Icon name="plus"/>Nuevo cliente</button>}
          {page === 'prestamos' && admin && <button disabled={!data.clients.length} onClick={() => setModal({ type: 'loan' })}><Icon name="plus"/>Nuevo préstamo</button>}
          {page === 'solicitudes' && <button disabled={!data.clients.length} onClick={() => setModal({ type: 'request' })}><Icon name="plus"/>Nueva solicitud</button>}
          {page === 'usuarios' && <button onClick={() => setModal({ type: 'staff' })}><Icon name="plus"/>Nuevo usuario</button>}
          {page === 'citas' && client && <button onClick={() => setModal({ type: 'appointment' })}><Icon name="plus"/>Agendar cita</button>}
        </div></div>
      {error && <div className="alert error" role="alert">{error}</div>}{notice && <div className="alert success" role="status">{notice}</div>}
      {loading && <p className="muted" role="status">Consultando los datos…</p>}
      {page === 'dashboard' && <>
        <div className="stats-grid">{[
          [client ? 'MIS PRÉSTAMOS' : 'CLIENTES', client ? data.loans.length : data.clients.length, 'clientes', 'Registros disponibles'],
          ['CAPITAL COLOCADO', currency(data.loans.reduce((s, p) => s + Number(p.monto), 0)), 'prestamos', `${data.loans.length} préstamos en cartera`],
          ['SALDO POR COBRAR', currency(data.loans.reduce((s, p) => s + Number(p.saldo_pendiente), 0)), 'reportes', 'Incluye mora pendiente'],
          ['PRÉSTAMOS VENCIDOS', data.loans.filter(p => p.estado_actual === 'Vencido').length, 'citas', 'Requieren seguimiento'],
        ].map(([label, value, icon, hint]) => <article className="stat-card" key={label}><div><span>{label}</span><Icon name={icon}/></div><strong>{value}</strong><small>{hint}</small></article>)}</div>
        <div className="overview-grid"><section className="panel"><div className="panel-heading"><div><h2>Próximos vencimientos</h2><p className="muted">Cuotas con saldo pendiente</p></div><span className="tag">SEGUIMIENTO</span></div><Table rows={data.loans.flatMap(p => p.cuotas.filter(q => Number(q.total_pendiente) > 0).map(q => ({ ...q, id: `${p.id}-${q.numero}`, nombre: p.nombre, loan: p }))).sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento)).slice(0, 6)} columns={[
          { label: 'Cliente', render: q => <strong>{q.nombre}</strong> }, { label: 'Vencimiento', render: q => dateLabel(q.fecha_vencimiento) }, { label: 'Saldo', render: q => currency(q.total_pendiente) }, { label: 'Detalle', render: q => <button className="text-button" onClick={() => setModal({ type: 'detail', value: q.loan })}>Cuota {q.numero} →</button> },
        ]}/></section><aside className="rate-card"><span className="eyebrow light">CONDICIONES DEL CRÉDITO</span><div className="rate-number">15<span>%</span></div><h2>Interés sobre el capital</h2><p>Distribuido entre las cuotas del préstamo, con frecuencia semanal, quincenal o mensual.</p><div className="rate-footer">Mora: 2 % mensual sobre el saldo de cuota vencido.</div></aside></div>
        <section className="panel"><div className="panel-heading"><h2>Préstamos recientes</h2><button className="text-button" onClick={() => setPage('prestamos')}>Ver todos →</button></div><Table rows={data.loans.slice(0, 5)} columns={loanColumns}/></section>
      </>}
      {['clientes', 'prestamos', 'usuarios'].includes(page) && <div className="search-bar"><Icon name="search"/><input aria-label="Buscar registros" placeholder="Buscar por nombre, cédula o número…" value={search} onChange={e => setSearch(e.target.value)}/></div>}
      {page === 'clientes' && <section className="panel"><Table rows={filter(data.clients)} columns={[
        { label: 'Cliente', render: c => <div className="person"><span className="avatar pale">{c.nombre.slice(0, 2).toUpperCase()}</span><span><strong>{c.nombre}</strong><small>{c.correo}</small></span></div> },
        { label: 'Cédula', render: c => c.cedula }, { label: 'Dirección', render: c => c.direccion }, { label: 'Acciones', render: c => <div className="row-actions"><button className="text-button" onClick={() => { setPage('prestamos'); setSearch(c.cedula); }}>Préstamos</button><button className="text-button" onClick={() => setModal({ type: 'location', value: c })}>Ubicación</button>{!collector && <><button className="text-button" onClick={() => setModal({ type: 'client', value: c })}>Editar</button><button className="text-button danger" onClick={() => confirmDelete(`/clientes/${c.id}`, `al cliente ${c.nombre} y sus registros relacionados`)}>Eliminar</button></>}</div> },
      ]}/></section>}
      {page === 'prestamos' && <section className="panel"><Table rows={filter(data.loans)} columns={loanColumns}/></section>}
      {page === 'solicitudes' && <section className="panel"><Table rows={data.requests} columns={[
        { label: 'Cliente', render: s => <strong>{s.nombre}</strong> }, { label: 'Capital', render: s => currency(s.monto) }, { label: 'Ingreso mensual', render: s => currency(s.ingreso_mensual) }, { label: 'Cuotas', render: s => `${s.plazo} · ${s.frecuencia_pago}` }, { label: 'Estado', render: s => <Badge value={s.estado}/> }, { label: 'Decisión', render: s => admin ? <div className="row-actions"><button className="text-button" onClick={() => setModal({ type: 'approve', value: s })}>Aprobar</button><button className="text-button danger" onClick={() => setModal({ type: 'reject', value: s })}>Rechazar</button></div> : 'Pendiente de administración' },
      ]}/></section>}
      {page === 'citas' && <section className="panel"><Table rows={data.appointments} columns={[
        { label: 'Cliente', render: a => a.nombre }, { label: 'Cédula', render: a => a.cedula }, { label: 'Fecha', render: a => dateLabel(a.fecha) }, { label: 'Estado', render: a => <Badge value={a.estado}/> },
      ]}/></section>}
      {page === 'usuarios' && <section className="panel"><Table rows={filter(data.users)} columns={[
        { label: 'Usuario', render: u => <strong>{u.usuario}</strong> }, { label: 'Rol', render: u => roleNames[u.rol] }, { label: 'Clientes', render: u => u.rol === 'cobrador' ? `${u.clientes_asignados.length} asignados` : 'Acceso por rol' }, { label: 'Acciones', render: u => <div className="row-actions"><button className="text-button" onClick={() => setModal({ type: 'staff', value: u })}>Editar</button>{u.rol === 'cobrador' && <button className="text-button" onClick={() => setModal({ type: 'assign', value: u })}>Asignar clientes</button>}{u.id !== user.id && <button className="text-button danger" onClick={() => confirmDelete(`/usuarios/${u.id}`, `al usuario ${u.usuario}`)}>Eliminar</button>}</div> },
      ]}/></section>}
      {page === 'reportes' && <div className="report-grid">{[['cartera', 'Estado de cartera', 'Capital, intereses, saldos y estado de cada préstamo.'], ['cobranza', 'Reporte de cobranza', 'Cuotas pendientes, vencimientos y mora para dar seguimiento.']].map(([key, title, desc]) => <article className="panel report-card" key={key}><span className="report-icon"><Icon name="reportes"/></span><h2>{title}</h2><p className="muted">{desc}</p><a className="button" href={`/api/reportes/${key}`} target="_blank" rel="noreferrer">Descargar PDF ↗</a></article>)}</div>}
      {page === 'ubicacion' && data.clients[0] && <AddressForm client={data.clients[0]} onSave={form => act(() => save(`/clientes/${user.id}/ubicacion`, form, 'PATCH', 'Dirección y ubicación guardadas.'))}/>}
      <footer className="footer">SistCreditos <span>Gestión de créditos y cobranza</span></footer>
    </div></main>
    {modal?.type === 'client' && <ClientForm client={modal.value} onClose={() => setModal(null)} onSave={form => save(modal.value ? `/clientes/${modal.value.id}` : '/clientes', form, modal.value ? 'PUT' : 'POST')}/>}
    {['loan', 'request'].includes(modal?.type) && <LoanForm loan={modal.value} clients={data.clients} request={modal.type === 'request'} onClose={() => setModal(null)} onSave={form => save(modal.type === 'request' ? '/solicitudes' : modal.value ? `/prestamos/${modal.value.id}` : '/prestamos', form, modal.value ? 'PUT' : 'POST')}/>}
    {modal?.type === 'staff' && <StaffForm user={modal.value} onClose={() => setModal(null)} onSave={form => save(modal.value ? `/usuarios/${modal.value.id}` : '/usuarios', form, modal.value ? 'PUT' : 'POST')}/>}
    {modal?.type === 'assign' && <AssignmentForm user={modal.value} clients={data.clients} onClose={() => setModal(null)} onSave={clients => save(`/usuarios/${modal.value.id}/asignaciones`, { clientes: clients }, 'PUT')}/>}
    {modal?.type === 'detail' && <LoanDetail loan={modal.value} user={user} onClose={() => setModal(null)} onRefresh={refresh}/>}
    {modal?.type === 'delete' && <Modal title="Confirmar eliminación" onClose={() => setModal(null)}><p>¿Eliminar {modal.name}? Esta operación elimina los registros de la versión web.</p><Form submit="Eliminar" onCancel={() => setModal(null)} onSubmit={() => save(modal.path, undefined, 'DELETE', 'Registro eliminado.')}/></Modal>}
    {modal?.type === 'appointment' && <DateModal title="Agendar cita" label="Fecha de la cita" submit="Agendar cita" onClose={() => setModal(null)} onSave={fecha => save('/citas', { fecha }, 'POST', 'Cita agendada.')}/>}
    {modal?.type === 'approve' && <DateModal title={`Aprobar solicitud #${modal.value.id}`} label="Fecha del primer pago" submit="Aprobar y crear préstamo" onClose={() => setModal(null)} onSave={fecha => save(`/solicitudes/${modal.value.id}`, { aprobada: true, fecha_primer_pago: fecha }, 'PATCH', 'Solicitud aprobada. Préstamo creado al 15 %.')}/>}
    {modal?.type === 'reject' && <Modal title="Rechazar solicitud" onClose={() => setModal(null)}><p>¿Rechazar la solicitud de {modal.value.nombre}?</p><Form submit="Rechazar solicitud" onCancel={() => setModal(null)} onSubmit={() => save(`/solicitudes/${modal.value.id}`, { aprobada: false }, 'PATCH')}/></Modal>}
    {modal?.type === 'location' && <Modal title={`Ubicación · ${modal.value.nombre}`} onClose={() => setModal(null)} wide><p>{modal.value.direccion}</p><LocationFields value={modal.value} readOnly/></Modal>}
  </div>;
}
function DateModal({ title, label, submit, onClose, onSave }) {
  const [value, setValue] = useState(today());
  return <Modal title={title} onClose={onClose}><Form submit={submit} onCancel={onClose} onSubmit={() => onSave(value)}><Field label={label} type="date" min={today()} value={value} onChange={e => setValue(e.target.value)} required/></Form></Modal>;
}
function AddressForm({ client, onSave }) {
  const [form, setForm] = useState({ ...client });
  useEffect(() => setForm({ ...client }), [client]);
  return <section className="panel address-panel"><Form onSubmit={() => onSave(form)}><Field label="Dirección" value={form.direccion} minLength={5} maxLength={40} required onChange={e => setForm({ ...form, direccion: e.target.value })}/><LocationFields value={form} onChange={point => setForm(f => ({ ...f, ...point }))}/></Form></section>;
}
createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
