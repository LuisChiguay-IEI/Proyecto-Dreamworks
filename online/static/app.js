document.querySelectorAll('[data-open-dialog]').forEach(button => {
  button.addEventListener('click', () => document.getElementById(button.dataset.openDialog).showModal());
});
document.querySelectorAll('[data-close-dialog]').forEach(button => {
  button.addEventListener('click', () => button.closest('dialog').close());
});
document.querySelectorAll('[data-expand-dialog]').forEach(button => {
  button.addEventListener('click', () => {
    const expanded = button.closest('dialog').classList.toggle('expanded');
    button.setAttribute('aria-pressed', String(expanded));
    button.textContent = expanded ? 'Reducir' : 'Ampliar';
  });
});
document.querySelectorAll('[data-confirm]').forEach(form => {
  form.addEventListener('submit', event => { if (!window.confirm(form.dataset.confirm)) event.preventDefault(); });
});
document.querySelectorAll('[data-loading-form]').forEach(form => {
  form.addEventListener('submit', () => {
    form.querySelector('button').disabled = true;
    form.querySelector('[role="status"]').hidden = false;
  });
});
window.addEventListener('pageshow', () => document.querySelectorAll('[data-loading-form]').forEach(form => {
  form.querySelector('button').disabled = false;
  form.querySelector('[role="status"]').hidden = true;
}));

// Ambient effects are decorative and can be paused independently of the forms.
const effectsToggle = document.querySelector('.effects-toggle');
if (effectsToggle) {
  const applyEffects = paused => {
    document.body.classList.toggle('effects-paused', paused);
    effectsToggle.setAttribute('aria-pressed', String(paused));
    effectsToggle.textContent = paused ? 'Activar ambiente' : 'Pausar ambiente';
  };
  try { applyEffects(localStorage.getItem('draco-effects-paused') === 'true'); } catch (_) {}
  effectsToggle.addEventListener('click', () => {
    const paused = !document.body.classList.contains('effects-paused');
    applyEffects(paused);
    try { localStorage.setItem('draco-effects-paused', String(paused)); } catch (_) {}
  });
}

// Ajusta el arte como una sola pieza: nunca cambia sus espacios ni sus líneas.
const asciiDragons = document.querySelectorAll('.ascii-dragon');
function fitAsciiDragon(frame) {
  const art = frame.querySelector('pre');
  const scale = Math.min(1, frame.clientWidth / art.scrollWidth, frame.clientHeight / art.scrollHeight);
  art.style.transform = `scale(${scale})`;
}
if (asciiDragons.length) {
  const fitAllDragons = () => asciiDragons.forEach(fitAsciiDragon);
  fitAllDragons();
  document.fonts.ready.then(fitAllDragons);
  window.addEventListener('resize', fitAllDragons, {passive:true});
}
