/* Shared accessibility helpers for the calculators.
   Two problems this solves:
   1. Results were injected with no announcement and no focus move, so a screen reader user
      completed an eleven-field form and was told nothing had happened.
   2. Validation was a generic alert() that named no field, so a visitor with one gap had to
      rescan every control to find it. A suppressed dialog also left the button silently dead. */
(function () {
    'use strict';

    function liveRegion() {
        var el = document.getElementById('rp-live');
        if (!el) {
            el = document.createElement('div');
            el.id = 'rp-live';
            el.className = 'sr-only';
            el.setAttribute('aria-live', 'polite');
            el.setAttribute('role', 'status');
            document.body.appendChild(el);
        }
        return el;
    }

    function say(message) {
        var el = liveRegion();
        el.textContent = '';
        // A fresh text node in the next frame is what makes the announcement fire reliably.
        window.setTimeout(function () { el.textContent = message; }, 60);
    }

    function labelFor(node) {
        var l = node.id && document.querySelector('label[for="' + node.id + '"]');
        var text = l ? l.textContent : (node.getAttribute('aria-label') || node.id || 'this answer');
        return text.replace(/\s+/g, ' ').replace(/[:?]\s*$/, '').trim().toLowerCase();
    }

    function clearError(node) {
        node.removeAttribute('aria-invalid');
        var msg = document.getElementById(node.id + '-err');
        if (msg) { msg.parentNode.removeChild(msg); }
        var d = node.getAttribute('aria-describedby');
        if (d) {
            d = d.split(/\s+/).filter(function (x) { return x !== node.id + '-err'; }).join(' ');
            if (d) { node.setAttribute('aria-describedby', d); } else { node.removeAttribute('aria-describedby'); }
        }
    }

    function markError(node, text) {
        node.setAttribute('aria-invalid', 'true');
        if (!document.getElementById(node.id + '-err')) {
            var msg = document.createElement('p');
            msg.id = node.id + '-err';
            msg.className = 'field-error';
            msg.textContent = text;
            node.parentNode.insertBefore(msg, node.nextSibling);
            var d = node.getAttribute('aria-describedby');
            node.setAttribute('aria-describedby', d ? d + ' ' + msg.id : msg.id);
        }
    }

    function listOf(names) {
        if (names.length === 1) { return names[0]; }
        return names.slice(0, -1).join(', ') + ' and ' + names[names.length - 1];
    }

    /* Checks every select inside the calculator card, skipping any id in skipIds.
       Marks the empty ones, moves focus to the first, and names them out loud. */
    window.rpRequire = function (skipIds) {
        skipIds = skipIds || [];
        var card = document.querySelector('.calc-card, .calculator, main') || document;
        var controls = Array.prototype.slice.call(card.querySelectorAll('select'));
        var missing = [];
        controls.forEach(function (node) {
            if (!node.id || skipIds.indexOf(node.id) !== -1) { return; }
            if (node.offsetParent === null && node.type !== 'hidden') { return; } // not currently shown
            clearError(node);
            if (node.value === '') { missing.push(node); }
        });
        if (!missing.length) { return true; }
        missing.forEach(function (node) { markError(node, 'Choose an option to continue.'); });
        var names = missing.map(labelFor);
        say(missing.length === 1
            ? 'One answer is still needed: ' + names[0] + '.'
            : missing.length + ' answers are still needed: ' + listOf(names) + '.');
        missing[0].focus();
        return false;
    };

    /* Same, for a single control that only becomes required in some branches. */
    window.rpRequireOne = function (id, text) {
        var node = document.getElementById(id);
        if (!node) { return true; }
        clearError(node);
        if (node.value !== '') { return true; }
        markError(node, text || 'Choose an option to continue.');
        say('One answer is still needed: ' + labelFor(node) + '.');
        node.focus();
        return false;
    };

    /* Reads an optional number field. The min and max attributes on these inputs never
       fire, because the calculators submit through a button rather than a form, so a
       visitor could enter 0, a negative, or nine digits and get a result built on it.
       Returns null when the field is empty (use your own estimate), a number when it is
       valid, and false when it is present but out of range, having marked the field. */
    window.rpNumber = function (id) {
        var node = document.getElementById(id);
        if (!node) { return null; }
        clearError(node);
        var raw = String(node.value).trim();
        if (raw === '') { return null; }
        var v = Number(raw);
        var min = node.hasAttribute('min') ? Number(node.getAttribute('min')) : -Infinity;
        var max = node.hasAttribute('max') ? Number(node.getAttribute('max')) : Infinity;
        var lo = min > 0 ? min : 1;
        // data-unit="kWh" (or "litres", "p") words the message for fields that are not money
        var unit = node.getAttribute('data-unit');
        var amt = function (n) { return unit ? n.toLocaleString('en-GB') + (unit === 'p' ? 'p' : ' ' + unit) : '£' + n.toLocaleString('en-GB'); };
        if (!isFinite(v) || v < lo || v > max) {
            markError(node, 'Enter an amount between ' + amt(lo) + ' and ' + amt(max)
                            + (node.hasAttribute('data-required') ? '.' : ', or leave it blank and we will estimate it.'));
            say('Check ' + labelFor(node) + ': enter an amount between ' + amt(lo)
                + ' and ' + amt(max) + (node.hasAttribute('data-required') ? '.' : ', or leave it blank.'));
            node.focus();
            return false;
        }
        return v;
    };

    /* Carries the answers a visitor has already given across to the next calculator, so
       they are not asked the same questions twice. Property type, bedrooms, insulation and
       tenure share a vocabulary across the tools and travel safely. Fuel does not: the EPC
       calculator needs to know whether a gas boiler is over or under 15 years old, which
       the other tools never ask, so gas is deliberately NOT carried there. Carrying a wrong
       answer is worse than carrying none. */
    var FUEL_IN = {
        'old-gas': 'gas', 'new-gas': 'gas', 'gas-boiler': 'gas', 'gas': 'gas',
        'oil': 'oil', 'oil-boiler': 'oil', 'lpg': 'lpg', 'lpg-boiler': 'lpg',
        'electric': 'electric', 'electricity': 'electric',
        'electric-storage': 'electric', 'electric-direct': 'electric',
        'heat-pump': 'heat-pump', 'heatpump': 'heat-pump'
    };
    var FUEL_OUT = {
        '/heat-pump-calculator/': { field: 'currentHeating',
            map: { gas: 'gas-boiler', oil: 'oil-boiler', lpg: 'lpg-boiler', electric: 'electric-storage' } },
        '/insulation-calculator/': { field: 'heatingFuel',
            map: { gas: 'gas', oil: 'oil', lpg: 'lpg', electric: 'electricity' } },
        '/grants/': { field: 'heating',
            map: { gas: 'gas', oil: 'oil', lpg: 'lpg', electric: 'electric', 'heat-pump': 'heatpump' } },
        '/epc-calculator/': { field: 'heating',
            map: { oil: 'oil', lpg: 'lpg', electric: 'electric', 'heat-pump': 'heat-pump' } },
        '/energy-bill-calculator/': { field: 'heatingFuel',
            map: { gas: 'gas', oil: 'oil', lpg: 'lpg', electric: 'electric', 'heat-pump': 'heatpump' } },
        '/landlord-epc-calculator/': { field: 'heating',
            map: { oil: 'oil', lpg: 'lpg', electric: 'electric', 'heat-pump': 'heat-pump' } },
        '/heat-pump-running-cost-calculator/': { field: 'currentHeating',
            map: { gas: 'gas', oil: 'oil', lpg: 'lpg', electric: 'electric' } }
    };
    var TYPE_FIELD = { '/epc-calculator/': 'propType', '/boiler-vs-heat-pump/': 'propType',
                       '/heat-pump-calculator/': 'propertyType', '/insulation-calculator/': 'propertyType',
                       '/energy-bill-calculator/': 'propertyType', '/heat-pump-running-cost-calculator/': 'propertyType',
                       '/landlord-epc-calculator/': 'propType' };
    var TAKES_BEDS = { '/heat-pump-calculator/': 1, '/insulation-calculator/': 1, '/boiler-vs-heat-pump/': 1,
                       '/energy-bill-calculator/': 1, '/heat-pump-running-cost-calculator/': 1 };
    var TAKES_INS  = { '/heat-pump-calculator/': 1, '/boiler-vs-heat-pump/': 1,
                       '/energy-bill-calculator/': 1, '/heat-pump-running-cost-calculator/': 1 };
    var TAKES_TEN  = { '/epc-calculator/': 1, '/grants/': 1 };

    function val(id) {
        var n = document.getElementById(id);
        return n && n.value ? n.value : null;
    }

    window.rpCarry = function () {
        var here = {
            type: val('propType') || val('propertyType'),
            beds: val('bedrooms'),
            ins: val('insulation'),
            fuel: FUEL_IN[val('heating') || val('currentHeating') || val('heatingFuel') || ''] || null,
            tenure: val('tenure')
        };
        var links = document.querySelectorAll('a.next-step-link, a.tool-link, .related-links a');
        Array.prototype.forEach.call(links, function (a) {
            var href = a.getAttribute('href') || '';
            if (href.charAt(0) !== '/' || href.indexOf('?') !== -1) { return; }
            var dest = href.split('#')[0];
            var q = [];
            if (here.type && TYPE_FIELD[dest]) { q.push(TYPE_FIELD[dest] + '=' + here.type); }
            if (here.beds && TAKES_BEDS[dest]) { q.push('bedrooms=' + here.beds); }
            if (here.ins && TAKES_INS[dest]) { q.push('insulation=' + here.ins); }
            if (here.tenure && TAKES_TEN[dest]) { q.push('tenure=' + here.tenure); }
            var f = FUEL_OUT[dest];
            if (here.fuel && f && f.map[here.fuel]) { q.push(f.field + '=' + f.map[here.fuel]); }
            if (q.length) { a.setAttribute('href', dest + '?' + q.join('&')); }
        });
    };

    /* Reveals a results block so assistive technology announces it and keyboard focus
       follows the visitor to the answer instead of being stranded on the button. */
    window.rpReveal = function (id) {
        var box = document.getElementById(id || 'results');
        if (!box) { return; }
        box.classList.add('visible');
        box.setAttribute('tabindex', '-1');
        box.setAttribute('role', 'region');
        var heading = box.querySelector('h2, h3, .result-title');
        if (heading) {
            if (!heading.id) { heading.id = (id || 'results') + '-heading'; }
            box.setAttribute('aria-labelledby', heading.id);
        } else {
            box.setAttribute('aria-label', 'Your result');
        }
        var first = box.querySelector('.result-item');
        var label = first && first.querySelector('.label');
        var value = first && first.querySelector('.value');
        say(label && value
            ? 'Result ready. ' + label.textContent.replace(/\s+/g, ' ').trim() + ': ' + value.textContent.replace(/\s+/g, ' ').trim() + '. Full breakdown follows.'
            : 'Your result is ready below.');
        // Answers already given travel to whatever the visitor opens next.
        try { window.rpCarry(); } catch (e) {}
        // Count that a result was shown, naming the calculator only, never the answers (js/analytics.js).
        try { if (typeof window.gtag === 'function') { window.gtag('event', 'calculate', { calculator: window.location.pathname }); } } catch (e) {}
        // focus() scrolls the element into view and carries the screen reader with it.
        box.focus();
    };
})();
