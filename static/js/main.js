// ── Role card selector ──
document.querySelectorAll('.role-card').forEach(function(card) {
  card.addEventListener('click', function() {
    document.querySelectorAll('.role-card').forEach(function(c) {
      c.classList.remove('selected');
    });
    card.classList.add('selected');
    var radio = card.querySelector('input[type="radio"]');
    if (radio) radio.checked = true;
  });
});

// ── Modal open/close ──
function openModal(id) {
  var el = document.getElementById(id);
  if (el) el.classList.add('open');
}
function closeAllModals() {
  document.querySelectorAll('.modal-overlay').forEach(function(m) {
    m.classList.remove('open');
  });
}
document.querySelectorAll('.modal-close').forEach(function(btn) {
  btn.addEventListener('click', closeAllModals);
});
document.querySelectorAll('.modal-overlay').forEach(function(overlay) {
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) closeAllModals();
  });
});

// ── Post trigger ──
var trigger = document.querySelector('.post-trigger');
if (trigger) {
  trigger.addEventListener('click', function() {
    openModal('announceModal');
  });
}

// ── Auto-dismiss alerts ──
document.querySelectorAll('.alert').forEach(function(alert) {
  setTimeout(function() {
    alert.style.transition = 'opacity 0.4s';
    alert.style.opacity = '0';
    setTimeout(function() {
      if (alert.parentNode) alert.parentNode.removeChild(alert);
    }, 400);
  }, 4000);
});

// ── Active sidebar link ──
var path = window.location.pathname;
document.querySelectorAll('.sidebar-link').forEach(function(link) {
  if (link.getAttribute('href') === path) {
    link.classList.add('active');
  }
});