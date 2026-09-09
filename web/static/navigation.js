const viewStyle = document.createElement('style');
viewStyle.textContent = '.view{display:none}.view.active{display:block}.cards3{grid-template-columns:repeat(3,1fr)}nav button{border:0;background:transparent;color:#c7d9e5;text-align:left;font:inherit;cursor:pointer}.details p{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #163848}@media(max-width:700px){.cards3{grid-template-columns:1fr!important}}';
document.head.append(viewStyle);

const views = document.querySelectorAll('.view');
const navButtons = document.querySelectorAll('nav button[data-view]');

function activateView(viewId) {
  views.forEach((view) => {
    view.classList.toggle('active', view.id === viewId);
  });

  navButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.view === viewId);
  });
}

navButtons.forEach((button) => {
  button.addEventListener('click', () => activateView(button.dataset.view));
});

activateView('overview');

function extraView(s) {
  const f = (v, d = 3) => v == null ? '--' : Number(v).toFixed(d);
  const make = (v, i) => `<article class="cell ${v === s.cell_max ? 'max' : ''} ${v === s.cell_min ? 'min' : ''}"><div class="cell-label">C${String(i + 1).padStart(2, '0')} ${v === s.cell_max ? 'MAX' : v === s.cell_min ? 'MIN' : ''}</div><b>${f(v)} V</b><div class="bar"><i style="width:${Math.max(5, Math.min(100, (v - 3.8) / .35 * 100))}%"></i></div></article>`;
  const cellsLarge = document.getElementById('cells-large');
  if (cellsLarge) {
    cellsLarge.innerHTML = (s.cell_voltages || []).map(make).join('');
  }
  const temp1 = document.getElementById('t1-large');
  const temp2 = document.getElementById('t2-large');
  const modelSide = document.getElementById('model-side');
  if (temp1) temp1.textContent = f(s.temperature_1, 1) + ' °C';
  if (temp2) temp2.textContent = f(s.temperature_2, 1) + ' °C';
  if (modelSide) modelSide.textContent = s.model || 'JK-BD4A20S4P';
}

setInterval(() => {
  fetch('/api/status').then((r) => r.json()).then(extraView).catch(() => {});
}, 2000);
