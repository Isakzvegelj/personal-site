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
  var navLinksForTheme = document.getElementById('navLinks');
  var navToggleForTheme = document.getElementById('navToggle');
  var desktopThemeParent = themeToggle ? themeToggle.parentNode : null;
  function positionThemeToggle() {
    if (!themeToggle || !navLinksForTheme || !desktopThemeParent) return;
    if (window.matchMedia('(max-width: 860px)').matches) {
      navLinksForTheme.appendChild(themeToggle);
    } else if (themeToggle.parentNode !== desktopThemeParent) {
      desktopThemeParent.insertBefore(themeToggle, navToggleForTheme);
    }
  }
  positionThemeToggle();
  if (window.matchMedia) {
    window.matchMedia('(max-width: 860px)').addEventListener('change', positionThemeToggle);
  }
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
  var lockedScrollY = 0;
  function lockPageScroll() {
    lockedScrollY = window.scrollY || window.pageYOffset || 0;
    document.documentElement.classList.add('menu-open');
    document.body.classList.add('menu-open');
    document.body.style.position = 'fixed';
    document.body.style.top = '-' + lockedScrollY + 'px';
    document.body.style.width = '100%';
  }
  function unlockPageScroll() {
    document.documentElement.classList.remove('menu-open');
    document.body.classList.remove('menu-open');
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.width = '';
    window.scrollTo(0, lockedScrollY);
  }
  function closeNav() {
    links.classList.remove('open');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    unlockPageScroll();
  }
  toggle.addEventListener('click', function () {
    var open = links.classList.toggle('open');
    toggle.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) lockPageScroll();
    else unlockPageScroll();
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

  /* ---- Email anti-scraper: rebuild mailto hrefs from split data-attrs ---- */
  /* The addresses are kept out of a single scrapeable string in the HTML;
     user + host are stored separately and recombined only in the browser. */
  function emailFor(a) {
    var user = a.getAttribute('data-email-user') || '';
    var host = a.getAttribute('data-email-host') || '';
    return user && host ? user + '@' + host : '';
  }
  var mailtoLinks = document.querySelectorAll('a.mailto');
  Array.prototype.forEach.call(mailtoLinks, function (a) {
    var addr = emailFor(a);
    if (!addr) return;
    var subject = a.getAttribute('data-email-subject') || '';
    var href = 'mailto:' + addr;
    if (subject) href += '?subject=' + encodeURIComponent(subject);
    a.href = href;
    a.removeAttribute('data-email-user');
    a.removeAttribute('data-email-host');
    if (a.classList.contains('mailto-self')) {
      /* re-show the plain address as visible text for real visitors */
      a.textContent = addr;
    }
  });

  /* contact form → compose an email */
  var cf = document.getElementById('contactForm');
  if (cf) {
    cf.addEventListener('submit', function (e) {
      e.preventDefault();
      /* honeypot: a real user never fills the hidden 'company' field */
      var hp = document.getElementById('cfCompany');
      if (hp && hp.value && String(hp.value).trim() !== '') {
        return; /* silent discard — bot */
      }
      var name = (document.getElementById('cfName').value || '').trim();
      var email = (document.getElementById('cfEmail').value || '').trim();
      var msg = (document.getElementById('cfMessage').value || '').trim();
      if (!name || !email || !msg) {
        alert('Please fill in your name, email and message first.');
        return;
      }
      var subject = 'New message from ' + name + ' (via isakzvegelj.github.io)';
      var body = 'Hi Isak,\n\n' + msg + '\n\n— ' + name + '\n' + email + '\n';
      var to = emailFor(cf) || (cf.getAttribute('data-email-user') + '@' + cf.getAttribute('data-email-host'));
      var href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      window.location.href = href;
    });
  }
})();
