(() => {
  const carousel = document.getElementById('carousel');
  if (!carousel) return;
  document.querySelectorAll('[data-carousel]').forEach(button => {
    button.addEventListener('click', () => {
      const card = carousel.querySelector('.movie');
      const distance = card ? card.getBoundingClientRect().width + 18 : 320;
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      carousel.scrollBy({left: button.dataset.carousel === 'next' ? distance : -distance, behavior: reduce ? 'auto' : 'smooth'});
    });
  });
})();
