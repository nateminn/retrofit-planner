/* Shareable and printable calculator results.
   One script for every calculator on the site. It writes the inputs into the URL so a
   result can be sent to someone or kept, reads them back when that link is opened, and
   adds a copy-link and print row under the results. Configured per page with data
   attributes on the script tag, so no page needs its own JavaScript.

   <script src="/js/results.js" data-fields="a,b,c" data-calc="calculate" defer></script>

   Values arriving from a URL are only ever used to set a form control, and only after
   they are matched against that control's own options, so a crafted link cannot put
   anything on the page. */
(function () {
  var cfg = document.currentScript;
  if (!cfg) return;
  var FIELDS = (cfg.getAttribute('data-fields') || '').split(',').filter(Boolean);
  var CALC = cfg.getAttribute('data-calc') || 'calculate';
  var TITLE = cfg.getAttribute('data-title') || document.title;
  if (!FIELDS.length) return;

  function el(id) { return document.getElementById(id); }

  function allowed(node, v) {
    if (node.tagName === 'SELECT') {
      for (var i = 0; i < node.options.length; i++) if (node.options[i].value === v) return true;
      return false;
    }
    if (node.type === 'number') return /^\d{1,7}(\.\d{1,2})?$/.test(v);
    return false;
  }

  function currentUrl() {
    var parts = [];
    FIELDS.forEach(function (id) {
      var node = el(id);
      if (node && node.value !== '') parts.push(encodeURIComponent(id) + '=' + encodeURIComponent(node.value));
    });
    return location.origin + location.pathname + (parts.length ? '?' + parts.join('&') : '');
  }

  function restore() {
    var q = location.search.replace(/^\?/, '');
    if (!q) return false;
    var found = false;
    q.split('&').forEach(function (pair) {
      var i = pair.indexOf('='); if (i < 0) return;
      var k = decodeURIComponent(pair.slice(0, i));
      var v = decodeURIComponent(pair.slice(i + 1).replace(/\+/g, ' '));
      if (FIELDS.indexOf(k) < 0) return;
      var node = el(k);
      if (node && allowed(node, v)) { node.value = v; found = true; }
    });
    return found;
  }

  /* A printed sheet has to say what was entered, or the numbers mean nothing. */
  function inputSummary() {
    var bits = [];
    FIELDS.forEach(function (id) {
      var node = el(id);
      if (!node || node.value === '') return;
      var label = document.querySelector('label[for="' + id + '"]');
      var name = label ? label.textContent.replace(/\s*\(optional\)\s*/i, '').replace(/:$/, '').trim() : id;
      var value = node.tagName === 'SELECT' ? node.options[node.selectedIndex].textContent.trim() : node.value;
      bits.push(name + ': ' + value);
    });
    return bits.join('   |   ');
  }

  function build() {
    var box = el('results');
    if (!box) return;

    var head = document.createElement('div');
    head.className = 'print-head';
    head.innerHTML = '<strong></strong><span class="ph-inputs"></span><span class="ph-url"></span>';
    head.querySelector('strong').textContent = TITLE;
    box.insertBefore(head, box.firstChild);

    var row = document.createElement('div');
    row.className = 'result-share';
    var label = document.createElement('span');
    label.className = 'rs-label'; label.textContent = 'Keep this result';
    var copy = document.createElement('button');
    copy.type = 'button'; copy.className = 'rs-btn'; copy.textContent = 'Copy link';
    var print = document.createElement('button');
    print.type = 'button'; print.className = 'rs-btn'; print.textContent = 'Print or save as PDF';
    row.appendChild(label); row.appendChild(copy); row.appendChild(print);

    copy.addEventListener('click', function () {
      var u = currentUrl();
      function done() { copy.textContent = 'Link copied'; setTimeout(function () { copy.textContent = 'Copy link'; }, 2000); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(u).then(done, function () { prompt('Copy this link', u); });
      else prompt('Copy this link', u);
    });
    print.addEventListener('click', function () { window.print(); });

    var anchor = box.querySelector('.next-steps') || box.querySelector('.cta-box');
    if (anchor) box.insertBefore(row, anchor); else box.appendChild(row);
    return { head: head, row: row };
  }

  function ready() {
    var parts = build();
    if (!parts) return;
    var box = el('results');

    function afterCalc() {
      if (!box.classList.contains('visible')) return;      // validation failed, nothing to share
      var u = currentUrl();
      try { history.replaceState(null, '', u.replace(location.origin, '')); } catch (e) {}
      parts.head.querySelector('.ph-inputs').textContent = inputSummary();
      parts.head.querySelector('.ph-url').textContent = u;
    }

    var original = window[CALC];
    if (typeof original === 'function') {
      /* Hide the old answer and its quote form first. A calculator only reveals them when
         the new inputs pass its checks, so a half-filled form can never sit above the
         previous result. */
      window[CALC] = function () {
        box.classList.remove('visible');
        var band = el('quoteBand'); if (band) band.hidden = true;   // each calculator re-shows it when the new result earns it
        var r = original.apply(this, arguments); afterCalc(); return r;
      };
    }

    /* Only calculate straight away when the link carries a complete answer. A full result
       link always does. A preset link from the start-here router fills in what it knows
       and leaves the rest, and running that would only produce a validation alert. A select
       marked data-optional may be left blank. */
    function complete() {
      for (var i = 0; i < FIELDS.length; i++) {
        var node = el(FIELDS[i]);
        if (node && node.tagName === 'SELECT' && node.value === '' && !node.hasAttribute('data-optional')) return false;
      }
      return true;
    }
    if (restore() && complete() && typeof window[CALC] === 'function') window[CALC]();
  }

  /* Wait for the whole page, not just the HTML. A calculator's own functions, and the
     helpers it calls from a11y.js, are deferred scripts too; running before they have loaded
     opened every shared link with the form filled in and no result. */
  if (document.readyState === 'complete') ready();
  else window.addEventListener('load', ready);
})();
