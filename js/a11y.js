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
        // focus() scrolls the element into view and carries the screen reader with it.
        box.focus();
    };
})();
