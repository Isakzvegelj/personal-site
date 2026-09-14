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
  backToTop.addEventListener('click', function () {
    var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reducedMotion ? 'auto' : 'smooth' });
  });
  /* Header state + back-to-top visibility — one rAF-coalesced scroll handler.
     Class writes happen at most once per frame and only when the state actually
     changes, so momentum-scrolling (especially flicking back up on phones)
     never queues redundant style invalidation behind the scroll gesture. */
  var header = document.getElementById('siteHeader');
  var headerScrolled = false;
  var backToTopVisible = false;
  var scrollTicking = false;
  function applyScrollState() {
    scrollTicking = false;
    var y = window.scrollY || 0;
    var shouldShrinkHeader = y > 40;
    if (header && shouldShrinkHeader !== headerScrolled) {
      headerScrolled = shouldShrinkHeader;
      header.classList.toggle('scrolled', shouldShrinkHeader);
    }
    var shouldShowTop = y > 300;
    if (shouldShowTop !== backToTopVisible) {
      backToTopVisible = shouldShowTop;
      backToTop.classList.toggle('visible', shouldShowTop);
    }
  }
  window.addEventListener('scroll', function () {
    if (!scrollTicking) {
      scrollTicking = true;
      requestAnimationFrame(applyScrollState);
    }
  }, { passive: true });
  applyScrollState();

  /* ---- Dark mode ---- */
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem('theme'); } catch (e) {}
  var systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  function applyTheme(theme) {
    var dark = theme === 'dark';
    if (dark) root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
    var toggle = document.getElementById('themeToggle');
    if (toggle) {
      toggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
      toggle.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
      toggle.setAttribute('title', dark ? 'Switch to light mode' : 'Switch to dark mode');
    }
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
    var navBreakpoint = window.matchMedia('(max-width: 860px)');
    navBreakpoint.addEventListener('change', function () {
      positionThemeToggle();
      if (!navBreakpoint.matches && links && links.classList.contains('open')) closeNav(false);
    });
  }
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  /* Mobile nav toggle */
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  var lockedScrollY = 0;
  var lastFocusedElement = null;
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
  function closeNav(restoreFocus) {
    links.classList.remove('open');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    unlockPageScroll();
    if (restoreFocus && lastFocusedElement) lastFocusedElement.focus();
  }
  function openNav() {
    lastFocusedElement = document.activeElement;
    links.classList.add('open');
    toggle.classList.add('open');
    toggle.setAttribute('aria-expanded', 'true');
    lockPageScroll();
    var firstLink = links.querySelector('a');
    if (firstLink) firstLink.focus();
  }
  toggle.addEventListener('click', function () {
    if (links.classList.contains('open')) closeNav();
    else openNav();
  });
  document.addEventListener('keydown', function (e) {
    if (!links.classList.contains('open')) return;
    if (e.key === 'Escape') {
      closeNav(true);
      return;
    }
    if (e.key !== 'Tab') return;
    var focusable = links.querySelectorAll('a, button, [tabindex]:not([tabindex="-1"])');
    if (!focusable.length) return;
    var first = focusable[0];
    var last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
  /* close nav when a link is tapped */
  Array.prototype.forEach.call(links.querySelectorAll('a'), function (a) {
    a.addEventListener('click', function () { closeNav(false); });
  });

  /* Pause the results marquee on request. */
  var marquee = document.querySelector('.results-marquee');
  var marqueeToggle = document.querySelector('.marquee-toggle');
  if (marquee && marqueeToggle) {
    marqueeToggle.addEventListener('click', function () {
      var paused = marquee.classList.toggle('paused');
      marqueeToggle.setAttribute('aria-pressed', paused ? 'true' : 'false');
      marqueeToggle.textContent = paused ? 'Resume motion' : 'Pause motion';
    });
  }

  /* Projects rail: left-to-right scrolling row of project cards.
     Arrows step one card at a time; the gold progress bar mirrors the
     scroll position; ArrowLeft/ArrowRight work while the rail is focused. */
  (function () {
    var track = document.getElementById('projectsTrack');
    var prev = document.getElementById('projPrev');
    var next = document.getElementById('projNext');
    var progWrap = document.getElementById('projectsProgress');
    var bar = document.getElementById('projectsProgressBar');
    if (!track) return;
    function reducedMotion() {
      return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    function step() {
      var card = track.querySelector('.project-card');
      if (!card) return 340;
      var gap = parseFloat(getComputedStyle(track).columnGap) || 24;
      return card.getBoundingClientRect().width + gap;
    }
    function go(dir) {
      track.scrollBy({ left: dir * step(), behavior: reducedMotion() ? 'auto' : 'smooth' });
    }
    if (prev) prev.addEventListener('click', function () { go(-1); });
    if (next) next.addEventListener('click', function () { go(1); });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    });
    var ticking = false;
    function update() {
      ticking = false;
      var max = track.scrollWidth - track.clientWidth;
      var overflow = max > 4;
      if (prev) prev.disabled = !overflow || track.scrollLeft <= 2;
      if (next) next.disabled = !overflow || track.scrollLeft >= max - 2;
      if (!progWrap) return;
      progWrap.classList.toggle('hidden', !overflow);
      if (overflow && bar) {
        var visibleFrac = track.clientWidth / track.scrollWidth;
        bar.style.width = (visibleFrac * 100) + '%';
        var ratio = max > 0 ? track.scrollLeft / max : 0;
        bar.style.transform = 'translateX(' + (ratio * track.clientWidth * (1 - visibleFrac)) + 'px)';
      }
    }
    track.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  })();

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
      var error = document.getElementById('cfError');
      if (error) { error.hidden = true; error.textContent = ''; }
      if (!cf.checkValidity()) {
        cf.reportValidity();
        return;
      }
      /* honeypot: a real user never fills the hidden 'company' field */
      var hp = document.getElementById('cfCompany');
      if (hp && hp.value && String(hp.value).trim() !== '') {
        return; /* silent discard — bot */
      }
      var name = (document.getElementById('cfName').value || '').trim();
      var email = (document.getElementById('cfEmail').value || '').trim();
      var msg = (document.getElementById('cfMessage').value || '').trim();
      if (!name || !email || !msg || !document.getElementById('cfEmail').checkValidity()) {
        if (error) {
          error.hidden = false;
          error.textContent = 'Please enter your name, a valid email address and a message.';
        }
        return;
      }
      var subject = 'New message from ' + name + ' (via isakzvegelj.com)';
      var body = 'Hi Isak,\n\n' + msg + '\n\n— ' + name + '\n' + email + '\n';
      var to = emailFor(cf) || (cf.getAttribute('data-email-user') + '@' + cf.getAttribute('data-email-host'));
      var href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      window.location.href = href;
    });
  }
})();
