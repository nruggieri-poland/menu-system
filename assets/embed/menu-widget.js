/*
 * menu-widget.js — Poland Schools menu embed
 *
 * Drop this into any page (e.g. a Finalsite "Custom HTML" block) — just the
 * one line, nothing else:
 *
 *   <script defer src="https://nruggieri-poland.github.io/menus/embed/menu-widget.js?school=pshs&menutype=lunch"></script>
 *
 * Config travels in the script's own src query string, not a separate HTML
 * attribute — many CMS "Custom HTML" sanitizers strip data-* attributes (and
 * sometimes the container div entirely) on save, but they can't strip a
 * script's own src without breaking it outright, so this is the one thing
 * guaranteed to survive. The script creates its own container element right
 * where it sits; you don't need to add any markup yourself.
 *
 * Multiple script tags (e.g. breakfast + lunch stacked on one page) each get
 * their own widget instance. Each feed is fetched as ONE rollup JSON file
 * (data/{menutype}-{school}.json, the whole available history, not split by
 * month) straight from this repo on page load, cached for the life of the
 * page — so it's always current, no iframe involved (works even where a host
 * CSP blocks frame-src), no rebuild/re-paste needed, and month/week
 * navigation after the first load is instant with zero extra network
 * requests.
 *
 * Optional query params: view=week (default: calendar), displayName=...
 *
 * Alternative (if you're hosting this yourself and control the surrounding
 * HTML, so data-* attributes are safe): a <div data-psmenu data-school="..."
 * data-menutype="..."></div> is still auto-detected too.
 */
(function () {
  'use strict';

  var REPO_DATA_BASE = 'https://raw.githubusercontent.com/nruggieri-poland/menus/refs/heads/master/data/';

  var DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  var MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  var SCHOOL_NAMES = {
    'pshs': 'Poland Seminary High School',
    'mckinley-middle': 'McKinley Middle School'
  };

  // ── Helpers ────────────────────────────────────────────────────────────

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function pad2(n) { return n < 10 ? '0' + n : '' + n; }

  function dateKey(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }

  function sameDay(a, b) { return dateKey(a) === dateKey(b); }

  function addDays(d, n) { var r = new Date(d); r.setDate(r.getDate() + n); return r; }

  function getMonday(d) {
    var day = new Date(d);
    var diff = (day.getDay() + 6) % 7;
    day.setDate(day.getDate() - diff);
    day.setHours(0, 0, 0, 0);
    return day;
  }

  function fmtDate(d) {
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  function fmtDateFull(d) {
    return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  }

  function fmtDateLong(d) {
    return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  }

  function daysInMonth(year, month) { return new Date(year, month, 0).getDate(); }

  // ── Data fetch: one rollup file per feed, shared across all widget
  // instances on the page and cached for the page's lifetime ──────────────

  var rollupCache = {};

  function fetchRollup(school, menutype) {
    var key = school + '/' + menutype;
    if (rollupCache[key]) return rollupCache[key];
    var filename = menutype + '-' + school + '.json';
    rollupCache[key] = fetch(REPO_DATA_BASE + filename)
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (data) {
        var itemMap = {};
        (data.days || []).forEach(function (d) { itemMap[d.date] = d.items; });
        return itemMap;
      })
      .catch(function () { return null; });
    return rollupCache[key];
  }

  // ── Stylesheet (injected once, scoped under .psmenu) ─────────────────────

  var CSS = ''
    + '.psmenu{font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1a1a2e;background:#fff;line-height:1.5;}'
    + '.psmenu *,.psmenu *::before,.psmenu *::after{box-sizing:border-box;}'
    + '.psmenu a{color:#0d2870;}'
    + '.psmenu .psmenu-sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;}'
    + '.psmenu .psmenu-announce:focus{position:static;width:auto;height:auto;margin:0 0 .5rem;padding:.4rem .6rem;overflow:visible;clip:auto;white-space:normal;display:block;background:#eef0f2;color:#1a3e9c;font-size:.85rem;font-weight:600;border-radius:6px;outline:3px solid #0b57d0;outline-offset:2px;}'
    + '.psmenu .psmenu-nav{display:flex;justify-content:flex-end;gap:.5rem;width:100%;align-items:center;flex-wrap:wrap;padding-bottom:.75rem;}'
    + '.psmenu .psmenu-nav button{background:#2d3748;color:#fff;border:0;border-radius:8px;padding:.55rem .95rem;font-size:.85rem;font-weight:600;cursor:pointer;min-height:44px;min-width:44px;}'
    + '.psmenu .psmenu-nav button:hover{background:#1c2536;}'
    + '.psmenu .psmenu-nav button:disabled{opacity:.4;cursor:default;}'
    + '.psmenu button:focus-visible{outline:3px solid #0b57d0;outline-offset:2px;}'
    + '.psmenu .psmenu-print{background:none !important;color:#0d2870 !important;text-decoration:underline;font-weight:400 !important;}'
    + '.psmenu .psmenu-daylist{border:1px solid #d8dee9;border-radius:10px;overflow:hidden;}'
    + '.psmenu .psmenu-day + .psmenu-day{border-top:1px solid #d8dee9;}'
    + '.psmenu .psmenu-day-head{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:.35rem .75rem;background:#eef0f2;padding:.7rem 1.25rem;}'
    + '.psmenu .psmenu-day.today .psmenu-day-head{background:#dce6fb;}'
    + '.psmenu .psmenu-day-head h3{font-size:1.05rem;color:#1a3e9c;margin:0;display:inline-flex;align-items:center;gap:.5rem;font-weight:700;}'
    + '.psmenu .psmenu-day-head .psmenu-date{font-weight:700;color:#1a3e9c;font-size:1rem;}'
    + '.psmenu .psmenu-flag{font-size:.65rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#0d2870;background:#cfe0fb;padding:.15rem .5rem;border-radius:999px;}'
    + '.psmenu .psmenu-day-body{padding:1rem 1.25rem 1.25rem;background:#fff;}'
    + '.psmenu ul.psmenu-items{list-style:none;margin:0;padding:0;}'
    + '.psmenu ul.psmenu-items li{padding-left:1.1rem;position:relative;margin-bottom:.4rem;color:#333;}'
    + '.psmenu ul.psmenu-items li:first-child::before{content:"";position:absolute;left:0;top:.55em;width:8px;height:8px;border-radius:50%;background:#1a3e9c;}'
    + '.psmenu .psmenu-toggle{display:flex;justify-content:center;margin-top:1.25rem;}'
    + '.psmenu .psmenu-toggle button{background:#1a3e9c;color:#fff;border:0;padding:.65rem 1.5rem;border-radius:8px;font-weight:600;cursor:pointer;min-height:44px;}'
    + '.psmenu .psmenu-toggle button:hover{background:#0d2870;}'
    + '.psmenu table.psmenu-cal{border-collapse:collapse;width:100%;margin-top:.5rem;table-layout:fixed;}'
    + '.psmenu table.psmenu-cal caption{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;}'
    + '.psmenu table.psmenu-cal th,.psmenu table.psmenu-cal td{border:1px solid #d8dee9;vertical-align:top;padding:.5rem;}'
    + '.psmenu table.psmenu-cal thead th{background:#1a3e9c;color:#fff;text-align:center;padding:.6rem;font-size:.9rem;}'
    + '.psmenu table.psmenu-cal td{width:20%;}'
    + '.psmenu table.psmenu-cal td.psmenu-empty{background:#f2f4f8;}'
    + '.psmenu .psmenu-daynum{font-weight:700;color:#1a3e9c;display:block;text-align:right;margin-bottom:.3rem;font-size:.85rem;}'
    + '.psmenu table.psmenu-cal ul{list-style:none;margin:0;padding:0;font-size:.8rem;}'
    + '.psmenu table.psmenu-cal ul li{margin-bottom:.25rem;color:#333;}'
    + '.psmenu .psmenu-status{padding:2rem 1rem;text-align:center;color:#475569;}'
    + '@media (max-width:700px){'
    + '.psmenu table.psmenu-cal thead{position:absolute;left:-9999px;top:-9999px;}'
    + '.psmenu table.psmenu-cal,.psmenu table.psmenu-cal tbody,.psmenu table.psmenu-cal tr,.psmenu table.psmenu-cal td{display:block;width:100%;}'
    + '.psmenu table.psmenu-cal tr{margin-bottom:1rem;border:1px solid #d8dee9;border-radius:8px;overflow:hidden;}'
    + '.psmenu table.psmenu-cal td{border:none;border-bottom:1px solid #d8dee9;}'
    + '.psmenu table.psmenu-cal td:last-child{border-bottom:none;}'
    + '.psmenu table.psmenu-cal td.psmenu-empty{display:none;}'
    + '.psmenu table.psmenu-cal td::before{content:attr(data-day);font-weight:700;color:#1a3e9c;display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.3rem;}'
    + '.psmenu .psmenu-daynum{text-align:left;}'
    + '}'
    + '@media print{.psmenu .psmenu-nav,.psmenu .psmenu-toggle{display:none !important;}}';

  function injectStyleOnce() {
    if (document.getElementById('psmenu-style')) return;
    var style = document.createElement('style');
    style.id = 'psmenu-style';
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  // ── Widget ────────────────────────────────────────────────────────────

  function Widget(el, config) {
    config = config || {};
    this.el = el;
    this.school = config.school || el.getAttribute('data-school');
    this.menutype = config.menutype || el.getAttribute('data-menutype');
    this.displayName = config.displayName || el.getAttribute('data-display-name')
      || SCHOOL_NAMES[this.school] || this.school;
    this.view = (config.view || el.getAttribute('data-view')) === 'week' ? 'week' : 'calendar';
    var today = new Date();
    this.year = today.getFullYear();
    this.month = today.getMonth() + 1;
    this.monday = getMonday(today);
  }

  Widget.prototype.init = function () {
    injectStyleOnce();
    this.el.classList.add('psmenu');
    if (!this.school || !this.menutype) {
      this.el.innerHTML = '<p class="psmenu-status">Menu embed is missing data-school / data-menutype.</p>';
      return;
    }
    // No visible heading is rendered (the host page supplies its own page
    // title), so give the region an accessible name directly instead —
    // otherwise screen reader users tabbing in would get no context at all.
    this.el.setAttribute('role', 'region');
    this.el.setAttribute('aria-label', this.displayName + ' ' + cap(this.menutype) + ' menu');
    this.render(false);
  };

  Widget.prototype.getItemMap = function () {
    return fetchRollup(this.school, this.menutype);
  };

  // moveFocus is true only for user-initiated navigation (prev/next/today/
  // view toggle), never on the initial page-load render — moving focus on
  // load would be jarring and unexpected. A blanket aria-live region on this
  // whole container would work for announcing updates too, but every
  // navigation swaps in an entire month's worth of menu items, and a
  // "polite" live region would read all of that out loud on every click.
  // Moving focus to the heading instead announces just "September 2026" via
  // the normal focus-change announcement, which is what a sighted user
  // effectively "sees" happen too.
  Widget.prototype.render = function (moveFocus) {
    this.el.innerHTML = '<p class="psmenu-status">Loading menu&hellip;</p>';
    if (this.view === 'calendar') this.renderCalendar(moveFocus);
    else this.renderWeek(moveFocus);
  };

  Widget.prototype.focusHeading = function () {
    var target = this.el.querySelector('.psmenu-announce');
    if (target) target.focus();
  };

  // ── Month / calendar view ────────────────────────────────────────────

  Widget.prototype.renderCalendar = function (moveFocus) {
    var self = this;
    this.getItemMap().then(function (itemMap) {
      self.el.innerHTML = self.buildCalendarHTML(itemMap, self.year, self.month);
      self.bindCalendarNav();
      if (moveFocus) self.focusHeading();
    });
  };

  Widget.prototype.buildCalendarHTML = function (itemMap, year, month) {
    var fetchFailed = itemMap === null;
    itemMap = itemMap || {};

    var first = new Date(year, month - 1, 1);
    var numDays = daysInMonth(year, month);
    var weekStart = getMonday(first);

    var weeks = [];
    var cur = new Date(weekStart);
    var lastOfMonth = new Date(year, month - 1, numDays);
    while (cur <= lastOfMonth) {
      var week = [];
      for (var i = 0; i < 5; i++) {
        var d = addDays(cur, i);
        week.push(d.getMonth() === month - 1 ? d : null);
      }
      weeks.push(week);
      cur = addDays(cur, 7);
    }

    var headerCells = DAYS.map(function (d) { return '<th scope="col">' + d + '</th>'; }).join('');

    var rowsHtml = weeks.map(function (week) {
      var cells = week.map(function (d, i) {
        var dayName = DAYS[i];
        if (!d) return '<td class="psmenu-empty" data-day="' + esc(dayName) + '"></td>';
        var key = dateKey(d);
        var items = itemMap[key] || [];
        var itemsHtml = items.length
          ? '<ul class="psmenu-cal-items">' + items.map(function (it) { return '<li>' + esc(it) + '</li>'; }).join('') + '</ul>'
          : '';
        return '<td data-day="' + esc(dayName) + '">'
          + '<span class="psmenu-sr-only">' + esc(fmtDateLong(d)) + ': </span>'
          + '<span class="psmenu-daynum" aria-hidden="true">' + d.getDate() + '</span>'
          + itemsHtml + '</td>';
      }).join('');
      return '<tr>' + cells + '</tr>';
    }).join('');

    var monthLabel = MONTH_NAMES[month] + ' ' + year;
    var noDataNote = fetchFailed
      ? '<p class="psmenu-status">Sorry, the menu couldn&rsquo;t be loaded right now. Please try again later.</p>'
      : '';

    return ''
      + '<p class="psmenu-sr-only psmenu-announce" tabindex="-1">' + esc(monthLabel) + '</p>'
      + '<nav class="psmenu-nav" aria-label="Month navigation">'
      + '<button type="button" data-nav="today">Today</button>'
      + '<button type="button" data-nav="prev" aria-label="Previous month">&larr;</button>'
      + '<button type="button" data-nav="next" aria-label="Next month">&rarr;</button>'
      + '<button type="button" data-nav="print" class="psmenu-print">Print</button>'
      + '</nav>'
      + noDataNote
      + '<table class="psmenu-cal"><caption>' + esc(cap(this.menutype)) + ' menu &mdash; ' + esc(this.displayName) + ' &mdash; ' + esc(monthLabel) + '</caption>'
      + '<thead><tr>' + headerCells + '</tr></thead><tbody>' + rowsHtml + '</tbody></table>'
      + '<div class="psmenu-toggle"><button type="button" data-nav="list">List View</button></div>';
  };

  Widget.prototype.bindCalendarNav = function () {
    var self = this;
    bindNav(this.el, {
      prev: function () { self.shiftMonth(-1); },
      next: function () { self.shiftMonth(1); },
      today: function () { var t = new Date(); self.year = t.getFullYear(); self.month = t.getMonth() + 1; self.render(true); },
      print: function () { window.print(); },
      list: function () { self.view = 'week'; self.render(true); }
    });
  };

  Widget.prototype.shiftMonth = function (delta) {
    var m = this.month + delta, y = this.year;
    if (m < 1) { m = 12; y -= 1; }
    if (m > 12) { m = 1; y += 1; }
    this.year = y; this.month = m;
    this.render(true);
  };

  // ── Week / list view ──────────────────────────────────────────────────

  Widget.prototype.renderWeek = function (moveFocus) {
    var self = this;
    this.getItemMap().then(function (itemMap) {
      self.el.innerHTML = self.buildWeekHTML(itemMap, self.monday);
      self.bindWeekNav();
      if (moveFocus) self.focusHeading();
    });
  };

  Widget.prototype.buildWeekHTML = function (itemMap, monday) {
    var fetchFailed = itemMap === null;
    itemMap = itemMap || {};
    var today = new Date();
    var friday = addDays(monday, 4);

    var rows = DAYS.map(function (dayName, i) {
      var d = addDays(monday, i);
      var key = dateKey(d);
      var items = itemMap[key] || [];
      var isToday = sameDay(d, today);
      var flag = isToday ? '<span class="psmenu-flag">Today</span>' : '';
      var itemsHtml = items.length
        ? '<ul class="psmenu-items">' + items.map(function (it) { return '<li>' + esc(it) + '</li>'; }).join('') + '</ul>'
        : '';
      return '<div class="psmenu-day' + (isToday ? ' today' : '') + '">'
        + '<div class="psmenu-day-head"><h3>' + esc(dayName) + flag + '</h3>'
        + '<span class="psmenu-date">' + esc(fmtDateFull(d)) + '</span></div>'
        + '<div class="psmenu-day-body">' + itemsHtml + '</div></div>';
    }).join('');

    var noDataNote = fetchFailed
      ? '<p class="psmenu-status">Sorry, the menu couldn&rsquo;t be loaded right now. Please try again later.</p>'
      : '';

    var weekLabel = fmtDate(monday) + ' – ' + fmtDate(friday) + ', ' + monday.getFullYear();

    return ''
      + '<p class="psmenu-sr-only psmenu-announce" tabindex="-1">' + esc(weekLabel) + '</p>'
      + '<nav class="psmenu-nav" aria-label="Week navigation">'
      + '<button type="button" data-nav="today">Today</button>'
      + '<button type="button" data-nav="prev" aria-label="Previous week">&larr;</button>'
      + '<button type="button" data-nav="next" aria-label="Next week">&rarr;</button>'
      + '<button type="button" data-nav="print" class="psmenu-print">Print</button>'
      + '</nav>'
      + noDataNote
      + '<div class="psmenu-daylist">' + rows + '</div>'
      + '<div class="psmenu-toggle"><button type="button" data-nav="month">Month View</button></div>';
  };

  Widget.prototype.bindWeekNav = function () {
    var self = this;
    bindNav(this.el, {
      prev: function () { self.monday = addDays(self.monday, -7); self.render(true); },
      next: function () { self.monday = addDays(self.monday, 7); self.render(true); },
      today: function () { self.monday = getMonday(new Date()); self.render(true); },
      print: function () { window.print(); },
      month: function () { self.view = 'calendar'; self.render(true); }
    });
  };

  // ── Shared nav wiring ─────────────────────────────────────────────────

  function bindNav(root, handlers) {
    Object.keys(handlers).forEach(function (key) {
      var btn = root.querySelector('[data-nav="' + key + '"]');
      if (btn) btn.addEventListener('click', handlers[key]);
    });
  }

  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

  // ── Boot ──────────────────────────────────────────────────────────────
  //
  // Two independent discovery paths, both run every boot() call so either
  // (or both) can be present on a page:
  //
  //  1. <script src="...menu-widget.js?school=X&menutype=Y"> — the
  //     recommended path for CMS "Custom HTML" blocks, since config lives in
  //     the script's own src, which sanitizers can't strip without breaking
  //     the script load itself. The script creates its own container.
  //
  //  2. <div data-psmenu data-school="X" data-menutype="Y"></div> — for
  //     contexts you fully control where data-* attributes are known to
  //     survive untouched.

  function bootFromScriptTags() {
    var scripts = document.querySelectorAll('script[src*="menu-widget.js"]');
    for (var i = 0; i < scripts.length; i++) {
      var script = scripts[i];
      if (script.hasAttribute('data-psmenu-booted')) continue;

      var params;
      try { params = new URL(script.src, window.location.href).searchParams; }
      catch (e) { continue; }

      var school = params.get('school');
      var menutype = params.get('menutype');
      if (!school || !menutype) continue;

      script.setAttribute('data-psmenu-booted', 'true');
      var container = document.createElement('div');
      script.parentNode.insertBefore(container, script.nextSibling);
      new Widget(container, {
        school: school,
        menutype: menutype,
        view: params.get('view'),
        displayName: params.get('displayName')
      }).init();
    }
  }

  function bootFromDataAttr() {
    var els = document.querySelectorAll('[data-psmenu]');
    for (var i = 0; i < els.length; i++) {
      if (!els[i].hasAttribute('data-psmenu-init')) {
        els[i].setAttribute('data-psmenu-init', 'true');
        new Widget(els[i]).init();
      }
    }
  }

  function boot() {
    bootFromScriptTags();
    bootFromDataAttr();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
