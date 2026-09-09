/* Interface local de Configurações. Não navega e não envia dados por BLE. */
const configCss = document.createElement('style');
configCss.textContent = `
  .config-modal{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;background:#000b;padding:18px}
  .config-modal[hidden]{display:none}.config-dialog{width:min(420px,100%);background:#102736;border:1px solid #3d7188;border-radius:13px;padding:24px;box-shadow:0 24px 80px #000}
  .config-dialog h2{margin:0 0 8px}.config-dialog p{color:#bdd0da}.config-dialog input{display:block;width:100%;margin:16px 0 8px;padding:13px;background:#06151f;color:#fff;border:1px solid #4b8299;border-radius:7px;font-size:18px;letter-spacing:.15em}
  .config-dialog input:focus{outline:2px solid #31bce8}.config-actions{display:flex;justify-content:flex-end;gap:9px;margin-top:18px}.config-actions button{padding:10px 16px;border-radius:7px;border:1px solid #4b8299;background:#153a4e;color:#fff;font-weight:700;cursor:pointer}.config-actions .primary{background:#087be8}
  .config-error{min-height:20px;color:#ff9ba6}.local-unlocked{color:#48dc92}.config-groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0}.config-groups article{background:#071a25;border:1px solid #234555;border-radius:8px;padding:14px}.config-groups h3{margin:0 0 6px}.config-groups p{color:#9fb6c4;font-size:.85rem}.config-groups b{color:#ffca64;font-size:.8rem}.config-fields p{display:flex;justify-content:space-between;border-bottom:1px solid #234555;padding:8px 0}
`;
document.head.append(configCss);

const configState = document.getElementById('config-state');
const configFields = document.getElementById('config-fields');
const configNavButton = document.querySelector('nav button[data-view="config-view"]');
const modal = document.createElement('div');
modal.className = 'config-modal';
modal.hidden = true;
modal.innerHTML = `
  <form class="config-dialog" novalidate>
    <h2>Configurações</h2>
    <p>Digite a senha para liberar somente a interface local.</p>
    <input id="local-password" type="password" autocomplete="current-password" placeholder="Senha" aria-label="Senha">
    <div class="config-error" id="config-error"></div>
    <div class="config-actions">
      <button type="button" id="config-cancel">Cancelar</button>
      <button class="primary" type="submit">Desbloquear</button>
    </div>
  </form>
`;
document.body.append(modal);

const input = () => document.getElementById('local-password');
const errorBox = () => document.getElementById('config-error');

function openConfigPassword() {
  const field = input();
  if (!field) return;
  field.value = '';
  errorBox().textContent = '';
  modal.hidden = false;
  setTimeout(() => field.focus(), 0);
}

function closeConfigPassword() {
  modal.hidden = true;
  const field = input();
  if (field) field.value = '';
  errorBox().textContent = '';
}

if (configNavButton) {
  configNavButton.addEventListener('click', openConfigPassword);
}

modal.querySelector('#config-cancel').addEventListener('click', closeConfigPassword);
modal.querySelector('form').addEventListener('submit', (event) => {
  event.preventDefault();
  const field = input();
  if (!field.value) {
    errorBox().textContent = 'Digite uma senha para continuar.';
    field.focus();
    return;
  }

  modal.hidden = true;
  configState.textContent = 'Interface local desbloqueada. Leitura, autenticação e escrita BLE continuam bloqueadas.';
  configState.classList.add('local-unlocked');
  field.value = '';
});

fetch('/api/config/settings').then((response) => response.json()).then((data) => {
  const settings = Array.isArray(data && data.settings) ? data.settings : [];
  configFields.innerHTML = settings.map((setting) => `<p>${setting.name}<b>${setting.status}</b></p>`).join('');
}).catch(() => {
  configFields.textContent = 'Não foi possível carregar a lista local de campos planejados.';
});
