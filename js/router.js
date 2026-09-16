/* Start-here router. Three questions, then straight to the right tool with the answers
   already filled in. The presets ride on the query string that /js/results.js reads, so
   no calculator needed changing for this. */
(function () {
  // router heating value -> the field and value each destination expects
  var HEAT = {
    'gas-old':          { hp: 'gas-boiler',      ins: 'gas',         epc: 'old-gas',   grants: 'gas' },
    'gas-new':          { hp: 'gas-boiler',      ins: 'gas',         epc: 'new-gas',   grants: 'gas' },
    'oil':              { hp: 'oil-boiler',      ins: 'oil',         epc: 'oil',       grants: 'oil' },
    'lpg':              { hp: 'lpg-boiler',      ins: 'lpg',         epc: '',          grants: 'lpg' },
    'electric-storage': { hp: 'electric-storage', ins: 'electricity', epc: 'electric', grants: 'electric' },
    'electric-direct':  { hp: 'electric-direct', ins: 'electricity', epc: 'electric',  grants: 'electric' },
    'heat-pump':        { hp: '',                ins: 'electricity', epc: 'heat-pump', grants: '' }
  };
  var FOSSIL = { 'gas-old': 1, 'gas-new': 1, 'oil': 1, 'lpg': 1 };

  function go(path, params) {
    var q = [];
    for (var k in params) if (params[k]) q.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
    location.href = path + (q.length ? '?' + q.join('&') : '');
  }

  window.rpRoute = function (e) {
    if (e && e.preventDefault) e.preventDefault();
    var heat = document.getElementById('r-heat').value;
    var goal = document.getElementById('r-goal').value;
    var who = document.getElementById('r-who').value;
    var map = HEAT[heat] || {};
    var out = document.getElementById('r-out');

    if (who === 'tenant') {
      out.innerHTML = '<h3>What a tenant can actually do</h3>' +
        '<p>Most of these tools price work only an owner can commission, so here is the part that is yours. ' +
        'Some grants are open to private tenants with the landlord’s written permission, and your landlord has duties of their own: ' +
        'a rented home cannot legally be let below EPC band E today, and every rented home has to reach the new band C standard by 1 October 2030.</p>' +
        '<p><a href="/grants/?tenure=tenant' + (map.grants ? '&heating=' + encodeURIComponent(map.grants) : '') + '">Check which grants you could qualify for</a><br>' +
        '<a href="/guides/epc-rating-landlords/">What your landlord has to do about the EPC rating</a><br>' +
        '<a href="/guides/energy-bills-by-epc-rating/">What a home in each EPC band costs to run</a></p>';
      out.hidden = false;
      out.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      return false;
    }

    var landlord = who === 'landlord';

    // A heat pump owner who wants lower bills needs a tariff, not a calculator.
    if (goal === 'bills' && heat === 'heat-pump') { location.href = '/guides/best-heat-pump-tariffs/'; return false; }
    // Storage heaters are the one case where changing the heating beats insulating first.
    if (goal === 'bills' && heat === 'electric-storage') { location.href = '/guides/storage-heaters-vs-heat-pump/'; return false; }

    if (goal === 'heating') {
      if (FOSSIL[heat]) return go('/boiler-vs-heat-pump/', {});
      return go('/heat-pump-calculator/', { currentHeating: map.hp });
    }
    if (goal === 'solar')      return go('/solar-calculator/', {});
    if (goal === 'epc')        return go('/epc-calculator/', { heating: map.epc, tenure: landlord ? 'landlord' : 'owner' });
    if (goal === 'grants')     return go('/grants/', { tenure: landlord ? 'landlord' : 'owner', heating: map.grants });
    // bills and insulation both start with the fabric
    return go('/insulation-calculator/', { heatingFuel: map.ins });
  };
})();
