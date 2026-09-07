EDITS = {
 'index.html': [
  ('Updated March 2026 with latest Ofgem rates', 'Updated September 2026 with Ofgem October to December 2026 rates'),
  ('Updated quarterly with each new price cap. Currently using Q1 2026 rates.',
   'Updated with each new price cap. Currently using Ofgem rates for October to December 2026.'),
  ('Energy prices from Ofgem (Q1 2026 price cap).', 'Energy prices from Ofgem (October to December 2026 price cap).'),
 ],
 'about/index.html': [
  ('Energy prices from Ofgem (Q1 2026 price cap).', 'Energy prices from Ofgem (October to December 2026 price cap).'),
  ('We update our calculators within days of each new price cap taking effect.',
   'We update our calculators when Ofgem announces each new price cap.'),
 ],
 'methodology/index.html': [
  ('Our current rates are from the Q1 2026 price cap:',
   'Our current rates are from the price cap for 1 October to 31 December 2026, announced on 26 August 2026:'),
  ('<li>Electricity: 24.5p per kWh</li>', '<li>Electricity: 26.32p per kWh, standing charge 54.83p per day</li>'),
  ('<li>Gas: 6.76p per kWh</li>',
   '<li>Gas: 7.97p per kWh, standing charge 29.68p per day</li>\n            <li>Heating oil: 9.0p per kWh (September 2026 kerosene market price)</li>\n            <li>LPG: 9.5p per kWh (typical bulk contract)</li>\n            <li>Heat pump tariff: 18p per kWh effective, assuming a well-scheduled time-of-use tariff such as Octopus Cosy with around 60% of heating shifted into the cheap windows</li>'),
  ('We update our calculators within one week of each new price cap taking effect (January, April, July, October).',
   'We update our calculators when Ofgem announces each new price cap (usually late February, May, August and November), so the figures cover the coming quarter.'),
 ],
 'guides/index.html': [
  ('What UK households actually pay for gas and electricity. Ofgem Q1 2026 data',
   'What UK households actually pay for gas and electricity. Ofgem October to December 2026 data'),
  ('Council Tax A to D. Closes 31 March 2026', 'Council Tax A to D. Closed 31 March 2026'),
 ],
 'CONTEXT.md': [
  ('### Energy Prices (Ofgem Q1 2026 Price Cap)', '### Energy Prices (Ofgem Price Cap, 1 October to 31 December 2026, announced 26 August 2026)'),
  ('- Electricity: 24.5p per kWh', '- Electricity: 26.32p per kWh'),
  ('- Gas: 6.76p per kWh', '- Gas: 7.97p per kWh'),
  ('- Electricity standing charge: 61.64p per day', '- Electricity standing charge: 54.83p per day'),
  ('- Gas standing charge: 31.65p per day',
   '- Gas standing charge: 29.68p per day\n- Ofgem typical consumption from 1 July 2026: 2,500 kWh electricity, 9,500 kWh gas (typical dual-fuel bill £1,723)\n- Heat pump tariff effective rate used in all tables: 18p per kWh (well-scheduled Octopus Cosy). OVO Heat Pump Plus closed to new customers February 2026.\n- Refresh recipe: run docs/superpowers/tools/verify_model.py, then update the constants in the four calculators and the tables listed in docs/superpowers/plans/2026-09-06-fix-and-freshen.md'),
  ('- Heating oil (kerosene): 6.8p per kWh', '- Heating oil (kerosene): 9.0p per kWh (September 2026, about 93p per litre including VAT)'),
  ('- BUS runs until April 2028', '- BUS runs to 2030 (extended 28 April 2026). £9,000 for homes replacing oil or LPG (from July 2026). £2,500 for air-to-air.'),
  ('- BUS: £7,500 air source, £6,000 ground source. Until April 2028.',
   '- BUS: £7,500 air source or ground source, £9,000 if replacing oil or LPG, £2,500 air-to-air. Runs to 2030.'),
 ],
}
