# What the Energy Saving Trust tool gives, and what it does not

Sourced from the two banks that white label it, in their own words, rather than from
running a fabricated property through their systems.

## Lloyds Bank, Eco Home Tool page

"you'll be able to see your:
- current and estimated (after improvements) energy bills
- current and estimated Energy Performance Certificate (EPC) rating
- estimated savings after improvements (and how much they'll cost)
- current and estimated CO2 emissions"

Inputs it asks for: postcode, year built, how you heat your home, what insulation you
have, what your walls and roof are made of. Address required. Nine steps. Lloyds states
"Estimated time: six minutes".

## Nationwide, Home Energy Efficiency Tool page

"Your plan will show:
- what your energy bill savings could be after improvements
- your current Energy Performance Certificate (EPC) rating and what it could be
- how much you could save and how much improvements might cost
- what your CO2 emission savings could be after improvements"

Nationwide adds a goal and budget step: "You can also set a goal, such as lowering your
energy costs, and choose a budget. We'll then guide you through suggested improvements."

## The difference, stated conservatively

Both official descriptions list the same four outputs, and neither mentions two things:

1. A PAYBACK PERIOD. Both give a saving and a cost. Neither says the tool divides one by
   the other and tells the household how many years the money takes to come back. That is
   the number a person deciding whether to spend five figures actually needs.

2. A STATED METHOD. Neither page, nor the tool, publishes how the estimate is produced or
   what data it rests on. RetrofitPlanner publishes its method at /methodology/ and its
   model table at /js/heat-model.js, and enforces both with two automated checks.

Be careful not to overclaim. Nationwide's goal and budget step does order suggestions, so
"no prioritisation at all" would be wrong. The defensible claim is about payback and
published method, not about sequencing.

Also fair to EST, and worth conceding in the application: their tool covers the whole of
Great Britain and produces an EPC estimate and a CO2 figure. RetrofitPlanner does neither
of the latter two, and its model is fitted to gas heated homes in England and Wales.

## Why this was not tested by running a property through it

The Lloyds tool requires an address and stores what you enter: "As you use the tool, we
save the property information you enter." Submitting a fabricated address would create a
false record inside the systems of the organisation being applied to. The official
descriptions are better evidence anyway, because they are the bank's own words rather
than one person's screenshot.
