# RetrofitPlanner.co.uk - Project Context

> This file gives Claude Code (or any AI tool) complete context to build pages for this site.
> Read this entire file before creating or editing any page.

---

## Site Overview

**Domain:** www.retrofitplanner.co.uk
**Hosting:** Netlify (auto-deploys from GitHub on push to main)
**Repo:** github.com/nateminn/retrofit-planner
**Stack:** Static HTML, shared CSS, client-side JavaScript. No build process, no framework.
**Purpose:** Free home energy calculators and guides for UK homeowners. Monetised through affiliate installer referrals and energy product recommendations (not yet active).

---

## ABSOLUTE RULES (never break these)

1. **No em dashes anywhere.** Not in HTML, not in alt text, not in schema markup, not in comments. Use commas, full stops, or rewrite the sentence. The character `—` must never appear in any file.

2. **No emojis anywhere.** Use inline SVG icons instead. Every icon on the site is an inline SVG in the Feather icon style (24x24 viewBox, stroke-based, 2px stroke width, round caps and joins).

3. **Ampersand (&) only in code.** Never use `&` in visible copy. Always spell out "and" in body text, headings, and meta descriptions.

4. **Every page must reference the shared CSS:** `<link rel="stylesheet" href="/css/style.css">`

5. **Every page must include favicon links in the `<head>`:**
```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
```

6. **Canonical URLs always use `www.`:** `https://www.retrofitplanner.co.uk/page-name/`

7. **All pages use trailing slashes** in URLs and internal links: `/heat-pump-calculator/` not `/heat-pump-calculator`

---

## Design System

### Fonts
- **Display:** Fraunces (serif) - used for h1, h2, h3, result values, brand name
- **Body:** Plus Jakarta Sans (sans-serif) - used for everything else

Include in every `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,400&display=swap" rel="stylesheet">
```

### Colours (defined in CSS custom properties)
- `--color-bg: #FAFAF7` (warm off-white background)
- `--color-surface: #FFFFFF` (cards, nav, footer)
- `--color-surface-alt: #F3F1EC` (secondary backgrounds)
- `--color-border: #E2DFD6` (borders)
- `--color-text: #1A1A17` (primary text)
- `--color-text-secondary: #6B6960` (body text)
- `--color-text-tertiary: #9C9888` (helper text, captions)
- `--color-accent: #2D6A4F` (forest green - primary action colour)
- `--color-accent-light: #40916C` (hover states)
- `--color-accent-bg: #EDF6F0` (green tinted backgrounds)
- `--color-accent-border: #B7E4C7` (green borders)
- `--color-highlight: #D4A843` (gold - grants, savings, key numbers)
- `--color-highlight-bg: #FFF8E7` (gold tinted backgrounds)
- `--color-highlight-border: #F0D78C` (gold borders)
- `--color-danger: #C1453B` (warnings, current system cost bars)
- `--color-danger-bg: #FFF0EE`

### Layout
- Max content width: 1080px
- Calculator pages: 2-column grid (main content + 380px sidebar)
- Guide pages: single column, max 720px for article text
- Padding: 24px horizontal on all containers
- Mobile breakpoint: 800px (single column, hide nav links)

---

## SEO Requirements (Critical)

### Every page MUST have:

1. **Unique `<title>` tag** - include primary keyword, location (UK), year (2026), and a value proposition. Max 60 characters. Example: `Heat Pump Cost Calculator UK 2026 | Free Estimate with Grant Deduction`

2. **Unique `<meta name="description">`** - include primary keyword, specific numbers where possible, call to action. Max 155 characters. Example: `Calculate the true cost of a heat pump for your home. See installation costs, the £7,500 government grant, annual running costs vs gas, and your payback period.`

3. **`<meta name="robots" content="index, follow">`**

4. **`<link rel="canonical">` with full www URL**

5. **Open Graph tags:**
```html
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:url" content="...">
<meta property="og:type" content="website"> <!-- or "article" for guides -->
<meta property="og:site_name" content="Retrofit Planner">
```

6. **BreadcrumbList schema** (JSON-LD):
```html
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Home","item":"https://www.retrofitplanner.co.uk/"},
  {"@type":"ListItem","position":2,"name":"Guides","item":"https://www.retrofitplanner.co.uk/guides/"},
  {"@type":"ListItem","position":3,"name":"Page Name"}
]}
</script>
```

7. **Page-type specific schema:**
   - Calculator pages: `WebApplication` schema
   - Guide pages: `Article` schema with `datePublished` and `dateModified`
   - ALL guides and calculators: `FAQPage` schema with 4-6 questions matching Google's "People Also Ask" for that topic

8. **Minimum 15 internal links per page** spread across:
   - Hero paragraph (1-2 links to related calculators)
   - Body content (contextual links where natural)
   - "Related links" card grid (4 cards with SVG icons)
   - "Next steps" section after calculator results
   - Sidebar tool links
   - Footer (all calculators, all guides, all company pages)

9. **2-4 external links per page** to authoritative sources. Always use `target="_blank" rel="noopener"`. Link to these when citing their data:
   - Ofgem: `https://www.ofgem.gov.uk/check-if-energy-price-cap-affects-you`
   - Energy Saving Trust: `https://energysavingtrust.org.uk/`
   - GOV.UK BUS: `https://www.gov.uk/apply-boiler-upgrade-scheme`
   - GOV.UK EPC: `https://www.gov.uk/find-energy-certificate`
   - GOV.UK ECO4: `https://www.gov.uk/energy-company-obligation`
   - MCS installers: `https://mcscertified.com/find-an-installer/`
   - BRE SAP: `https://bregroup.com/sap/`
   - PVGIS: `https://re.jrc.ec.europa.eu/pvg_tools/`
   - Open Government Licence: `https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/`

10. **Data source attribution** at the bottom of every page, before the footer.

### Guide Content Standards

- **Answer the primary query in the first paragraph.** Lead with the number or fact the searcher wants. Do not bury the answer.
- **Include a "key-number" span** for the most important figure: `<span class="key-number">£7,500</span>` (styled as Fraunces bold, accent green)
- **Minimum 1,500 words** per guide. Target 2,000-2,500 for competitive queries.
- **Data tables** for any comparative data. Use the `.data-table` class. Always include a `.note` paragraph below with source attribution.
- **FAQ section** at the bottom with 4-6 questions. Each answer should link to a relevant calculator or other guide. These are also marked up with FAQPage schema.
- **Table of contents** for guides over 1,500 words using the `.toc` class with anchor links.
- **Callout boxes** for key information:
  - Green callout (`.callout`): links to calculators, positive actions
  - Gold callout (`.warning-callout .callout`): deadlines, important warnings
- **No fluff.** Every sentence must contain information or link to a tool. Delete filler phrases like "it's worth noting that" or "it goes without saying."
- **Use specific numbers, not vague language.** Write "£300 to £600" not "a few hundred pounds." Write "2 to 5 years" not "several years."

---

## Data Sources (use these numbers)

### Energy Prices (Ofgem Q1 2026 Price Cap)
- Electricity: 24.5p per kWh
- Gas: 6.76p per kWh
- Electricity standing charge: 61.64p per day
- Gas standing charge: 31.65p per day

### Other Fuel Prices
- Heating oil (kerosene): 6.8p per kWh
- LPG: 9.5p per kWh

### Heat Pump Data
- COP by insulation: Good = 3.2, Average = 2.9, Poor = 2.6
- Installation cost: £7,000 to £13,000 (air source)
- BUS grant: £7,500 (air source), £6,000 (ground source)
- BUS runs until April 2028

### Insulation Savings (EST data, gas heating)
| Measure | Detached | Semi | Mid-terrace | End-terrace | Bungalow | Flat |
|---------|----------|------|-------------|-------------|----------|------|
| Loft (from zero) | £355 | £215 | £135 | £175 | £280 | £100 |
| Cavity wall | £395 | £215 | £105 | £160 | £250 | £100 |
| Solid wall | £590 | £340 | £200 | £270 | £370 | £160 |

### Grant Schemes
- ECO4: runs until December 2026. Benefits required (main route). ECO4 Flex available through local councils.
- GBIS: CLOSED to new applications January 31, 2026.
- BUS: £7,500 air source, £6,000 ground source. Until April 2028.
- Home Upgrade Grant (HUG): off-gas-grid homes, EPC D-G. Local authority managed.
- 0% VAT on solar, heat pumps, insulation: until March 2027.

### Solar Data
- Generation: 810-950 kWh per kW installed per year (Scotland to South England)
- Self-use: 45% without battery, 80% with battery
- SEG export rate: 8p/kWh (conservative average)
- System cost: 3kW £4,000-5,500, 4kW £5,000-7,000, 5kW £6,500-8,500, 6kW £7,000-9,000
- Battery cost: £2,500-5,000
- Panel degradation: 0.5% per year

---

## Page Structure Templates

### Guide Page Structure
```
<nav> (sticky, shared across all pages)
<breadcrumbs>
<div class="page-content">
  <p class="article-meta"> (date, data sources with external links)
  <h1> (primary keyword in title)
  <p class="lead"> (answer the query, include key-number span)
  <div class="callout"> (link to relevant calculator)
  <div class="toc"> (table of contents with anchor links)
  <h2 id="..."> (sections matching TOC)
    <p> (content with internal links)
    <table class="data-table"> (where data comparison needed)
    <div class="callout"> (mid-article callouts)
  <div class="related-links"> (4 card grid linking to calculators/guides)
  <h2>Frequently asked questions</h2>
    <h3> / <p> (4-6 FAQs with internal links)
  <h2>Data sources</h2>
    <p> (external links to sources)
</div>
<footer> (shared across all pages)
```

### Guide Page Inline Styles (add to `<head>`)
These supplement the shared CSS for guide-specific elements:
```css
.data-table { width: 100%; border-collapse: collapse; margin: 24px 0; font-size: 0.9rem; }
.data-table th { background: var(--color-surface-alt); font-weight: 600; text-align: left; padding: 12px 16px; border-bottom: 2px solid var(--color-border); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--color-text-secondary); }
.data-table td { padding: 12px 16px; border-bottom: 1px solid var(--color-surface-alt); }
.data-table tr:last-child td { border-bottom: none; }
.data-table .highlight-cell { color: var(--color-accent); font-weight: 600; }
.data-table .note { font-size: 0.78rem; color: var(--color-text-tertiary); margin-top: 8px; }
.callout { background: var(--color-accent-bg); border: 1px solid var(--color-accent-border); border-radius: var(--radius-md); padding: 20px 24px; margin: 28px 0; }
.callout h4 { font-family: var(--font-display); font-size: 1rem; font-weight: 600; color: var(--color-accent); margin-bottom: 8px; }
.callout p { font-size: 0.9rem; color: var(--color-text-secondary); margin: 0; }
.callout a { color: var(--color-accent); font-weight: 600; }
.warning-callout { background: var(--color-highlight-bg); border-color: var(--color-highlight-border); }
.warning-callout h4 { color: var(--color-highlight); }
.key-number { display: inline-block; font-family: var(--font-display); font-weight: 700; font-size: 1.1rem; color: var(--color-accent); }
.article-meta { font-size: 0.85rem; color: var(--color-text-tertiary); margin-bottom: 24px; }
.toc { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 24px; margin: 24px 0; }
.toc h4 { font-family: var(--font-display); font-size: 1rem; font-weight: 600; margin-bottom: 12px; }
.toc a { display: block; font-size: 0.88rem; color: var(--color-text-secondary); text-decoration: none; padding: 6px 0; border-bottom: 1px solid var(--color-surface-alt); }
.toc a:last-child { border-bottom: none; }
.toc a:hover { color: var(--color-accent); }
```

---

## Navigation (consistent across all pages)

```html
<nav class="nav"><div class="nav-inner"><a href="/" class="nav-logo">Retrofit Planner</a><ul class="nav-links">
  <li><a href="/heat-pump-calculator/">Heat Pump</a></li>
  <li><a href="/insulation-calculator/">Insulation</a></li>
  <li><a href="/epc-calculator/">EPC Rating</a></li>
  <li><a href="/solar-calculator/">Solar Panels</a></li>
  <li><a href="/grants/">Grants</a></li>
  <li><a href="/guides/">Guides</a></li>
</ul></div></nav>
```

Add `class="active"` to the current section's nav link.

---

## Footer (consistent across all pages)

```html
<footer class="footer">
  <div class="footer-inner">
    <div><div class="footer-brand">Retrofit Planner</div><p class="footer-about">Free tools to help UK homeowners plan energy-efficient home improvements.</p></div>
    <div class="footer-col"><h4>Calculators</h4>
      <a href="/heat-pump-calculator/">Heat Pump Cost Calculator</a>
      <a href="/insulation-calculator/">Insulation Savings Calculator</a>
      <a href="/epc-calculator/">EPC Improvement Planner</a>
      <a href="/solar-calculator/">Solar Panel ROI Calculator</a>
      <a href="/boiler-vs-heat-pump/">Boiler vs Heat Pump</a>
      <a href="/grants/">Grant Eligibility Checker</a>
    </div>
    <div class="footer-col"><h4>Guides</h4>
      <!-- Include 5 most relevant guides here -->
    </div>
    <div class="footer-col"><h4>Company</h4>
      <a href="/about/">About Us</a>
      <a href="/methodology/">Our Methodology</a>
      <a href="/privacy/">Privacy Policy</a>
      <a href="/terms/">Terms of Use</a>
      <a href="/contact/">Contact</a>
    </div>
  </div>
  <div class="attribution">
    <!-- Data source credits with external links -->
  </div>
</footer>
```

---

## Existing Pages (do not overwrite unless asked)

### Calculators (6)
- `/heat-pump-calculator/` - installation cost, grant, running costs, payback
- `/insulation-calculator/` - loft, cavity, solid wall savings by property type
- `/epc-calculator/` - cheapest path to target EPC band
- `/solar-calculator/` - generation, savings, SEG income, 25-year ROI
- `/boiler-vs-heat-pump/` - 15-year total cost comparison
- `/grants/` - eligibility checker for BUS, ECO4, GB Energy, HUG

### Guides (8 published)
- `/guides/heat-pump-running-costs/`
- `/guides/how-to-improve-epc-rating/`
- `/guides/is-cavity-wall-insulation-worth-it/`
- `/guides/boiler-upgrade-scheme-guide/`
- `/guides/are-solar-panels-worth-it-uk/`
- `/guides/heat-pump-cost-by-house-type/`
- `/guides/free-loft-insulation-uk/`
- `/guides/average-energy-bills-uk/`

### Supporting Pages (7)
- `/` - homepage with calculator cards
- `/guides/` - guide index
- `/about/`
- `/methodology/`
- `/privacy/`
- `/terms/`
- `/contact/`

---

## Deployment Workflow

1. Create files in the correct directory under the repo root
2. Update `sitemap.xml` at the repo root with new URLs
3. Run: `git add . && git commit -m "description" && git push`
4. Netlify auto-deploys within 60 seconds

---

## Keyword Strategy

Target long-tail, low-competition queries that funnel readers to calculators. Every guide should target a specific search query and include that query (or close variation) in the title, H1, meta description, and first paragraph.

Google "People Also Ask" questions for each target keyword should be included as H3 headings in the FAQ section AND marked up with FAQPage schema.

Prioritise queries where:
- The searcher has commercial intent (they want to buy/install something)
- Existing results are from low-authority sites (DR below 50)
- The query naturally leads to one of our calculators
- We can provide specific data that competitors don't (tables, calculations)

---

## Quality Checklist (run before every commit)

- [ ] No em dashes (`—`) anywhere in the file
- [ ] No emojis anywhere in the file
- [ ] No ampersands in visible text (only in HTML entities and code)
- [ ] `<link rel="stylesheet" href="/css/style.css">` present
- [ ] All 6 favicon/manifest links in `<head>`
- [ ] `<link rel="canonical">` with www URL
- [ ] Unique `<title>` under 60 characters
- [ ] Unique `<meta name="description">` under 155 characters
- [ ] Open Graph tags present
- [ ] BreadcrumbList schema present
- [ ] Article or WebApplication schema present
- [ ] FAQPage schema with 4-6 questions
- [ ] Minimum 15 internal links
- [ ] 2-4 external links to authoritative sources
- [ ] Data tables have source attribution
- [ ] Footer matches current site footer
- [ ] Nav matches current site nav
- [ ] Mobile responsive (check 800px breakpoint)
- [ ] All internal links use trailing slashes
- [ ] `sitemap.xml` updated with new URL
