/* Isak Žvegelj — site JS */
(function () {
  'use strict';

  /* ---- Dark mode ---- */
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem('theme'); } catch (e) {}
  var systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  function applyTheme(theme) {
    if (theme === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
  }
  applyTheme(stored || (systemDark ? 'dark' : 'light'));
  var themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  /* Header: add .scrolled past 40px */
  var header = document.getElementById('siteHeader');
  function onScroll() {
    if (window.scrollY > 40) header.classList.add('scrolled');
    else header.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Mobile nav toggle */
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  function closeNav() {
    links.classList.remove('open');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  toggle.addEventListener('click', function () {
    var open = links.classList.toggle('open');
    toggle.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  /* close nav when a link is tapped */
  Array.prototype.forEach.call(links.querySelectorAll('a'), function (a) {
    a.addEventListener('click', closeNav);
  });

  /* Scroll reveal */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('visible'); });
  }

  /* footer year */
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  /* contact form → compose an email */
  var cf = document.getElementById('contactForm');
  if (cf) {
    cf.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = (document.getElementById('cfName').value || '').trim();
      var email = (document.getElementById('cfEmail').value || '').trim();
      var msg = (document.getElementById('cfMessage').value || '').trim();
      if (!name || !email || !msg) {
        alert('Please fill in your name, email and message first.');
        return;
      }
      var subject = 'New message from ' + name + ' (via isakzvegelj.github.io)';
      var body = 'Hi Isak,\n\n' + msg + '\n\n— ' + name + '\n' + email + '\n';
      var href = 'mailto:inquire@isakzvegelj.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      window.location.href = href;
    });
  }
})();
