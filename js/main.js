/* Isak Žvegelj — site JS */
(function () {
  'use strict';

  /* Mobile back-to-top control */
  var backToTop = document.createElement('button');
  backToTop.className = 'back-to-top';
  backToTop.type = 'button';
  backToTop.setAttribute('aria-label', 'Back to top');
  backToTop.innerHTML = '&#8593;';
  document.body.appendChild(backToTop);
  function updateBackToTop() { backToTop.classList.toggle('visible', window.scrollY > 300); }
  window.addEventListener('scroll', updateBackToTop, { passive: true });
  backToTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  updateBackToTop();

  /* ---- Dark mode ---- */
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem('theme'); } catch (e) {}
  var systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  var themeToggle = document.getElementById('themeToggle');
  function applyTheme(theme) {
    if (theme === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
    if (themeToggle) {
      var isDark = theme === 'dark';
      themeToggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
      themeToggle.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
      themeToggle.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    }
  }
  applyTheme(stored || (systemDark ? 'dark' : 'light'));
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
    if (!header) return;
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
    if (!links || !toggle) return;
    links.classList.remove('open');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    unlockPageScroll();
  }
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) lockPageScroll();
      else unlockPageScroll();
    });
    Array.prototype.forEach.call(links.querySelectorAll('a'), function (a) {
      a.addEventListener('click', closeNav);
    });
  }

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

  /* contact form: use a configured static endpoint, otherwise email fallback */
  var cf = document.getElementById('contactForm');
  if (cf) {
    cf.addEventListener('submit', function (e) {
      e.preventDefault();
      var hp = document.getElementById('cfCompany');
      var status = document.getElementById('cfStatus');
      var nameEl = document.getElementById('cfName');
      var emailEl = document.getElementById('cfEmail');
      var msgEl = document.getElementById('cfMessage');
      var name = (nameEl.value || '').trim();
      var email = (emailEl.value || '').trim();
      var msg = (msgEl.value || '').trim();
      if (hp && hp.value.trim()) return;
      if (!name || !email || !msg || !emailEl.checkValidity()) {
        if (status) status.textContent = 'Please enter your name, a valid email, and a message.';
        (name ? emailEl : nameEl).focus();
        return;
      }
      var subject = 'New message from ' + name + ' (via isakzvegelj.com)';
      var body = ['Hi Isak,', '', msg, '', '— ' + name, email, ''].join(String.fromCharCode(10));
      var to = emailFor(cf) || (cf.getAttribute('data-email-user') + '@' + cf.getAttribute('data-email-host'));
      if (status) status.textContent = 'Opening your email app…';
      window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    });
  }

  /* Scrollable results controls */
  var resultsMarquee = document.querySelector('.results-marquee');
  Array.prototype.forEach.call(document.querySelectorAll('[data-marquee-direction]'), function (button) {
    button.addEventListener('click', function () {
      if (!resultsMarquee) return;
      var distance = button.getAttribute('data-marquee-direction') === 'prev' ? -320 : 320;
      var track = resultsMarquee.querySelector('.results-marquee-track');
      if (track) track.style.animationPlayState = 'paused';
      resultsMarquee.scrollBy({ left: distance, behavior: 'smooth' });
    });
  });

  /* YouTube façade: load the third-party iframe only after an explicit click */
  Array.prototype.forEach.call(document.querySelectorAll('.video-facade'), function (button) {
    var poster = button.querySelector('img[data-fallback-src]');
    if (poster) poster.addEventListener('error', function () {
      var fallback = poster.getAttribute('data-fallback-src');
      if (fallback && poster.src !== fallback) poster.src = fallback;
    });
    button.addEventListener('click', function () {
      var id = button.getAttribute('data-video-id');
      var start = button.getAttribute('data-video-start') || '0';
      var iframe = document.createElement('iframe');
      iframe.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) + '?start=' + encodeURIComponent(start) + '&rel=0';
      iframe.title = 'Isak Žvegelj rowing';
      iframe.loading = 'lazy';
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.allowFullscreen = true;
      button.replaceWith(iframe);
    });
  });
})();
