# Wilkins Media – Military Proposal Builder

A CRM-style tool for the Wilkins military division. Pick installations by state or by base, tick the
media options you want to propose, and export a client-facing and an internal Excel proposal in the
house "Military Media Plan" format.

```
military/
├── index.html                                 the app (static page, no build step)
├── Wilkins Military Rate Card - MASTER.xlsx   the standardized rate card David's team maintains
├── data/
│   ├── rate_card.csv                          same data, one row per media option (source of truth for the build)
│   ├── rate_card.js                           generated copy embedded in the app
│   └── source_master_export_12.2.25.json      raw export of the old Box master (traceability only)
├── tools/
│   ├── standardize.py                         one-time: raw Box export -> rate_card.csv
│   └── build_rate_card.py                     rate_card.csv -> MASTER.xlsx + rate_card.js
└── assets/                                    Wilkins logos
```

## Where the data came from

* **Rate card**: Box > Military > Master Grid > `MasterMilitaryOnBaseList 12.2.25 NS.xlsx`
  (1,238 media options across ~100 domestic installations). Vendor (base) cost at 1 / 3 / 6 / 12
  months plus production, cleaned and categorized.
* **Base populations (reference)**: Box > Military > `Military - National Digital Inventory Master 6.3.26.xlsx`.
* **Pricing rules**: David's Sep 18 / 22 / 23 / 24 2026 calls with Jon and Chelsea (Fireflies).

## Pricing rules baked into the app

| Rule | Where it comes from |
|---|---|
| Default flight is 3 months | "A one-month campaign is not as effective." (David, Sep 18) |
| Standard price = 1-month vendor rate × months, not the discounted term price | "I'll use the monthly price, multiply it times three… then I can divide it out." (David, Sep 18). Switch to *Rate-card term price* for competitive bids. |
| Items sold only at 3 / 6 / 12 months use that minimum, scaled to the flight | Rate-card columns are totals per term. |
| Markup checkbox, default 50% margin on price (vendor × 2), rounded to $25 | "Normally it's 50 on this media." (Sep 18) / "you did it times two, so everything has a 50% margin" (Chelsea, Sep 23). A *markup on cost* basis is available if David means × 1.5. |
| Production is never included unless checked; standard $100 poster (22×28) / $350 banner (3×6); other sizes "inquire" | David, Sep 22 |
| Client file is hard-coded prices only; internal file adds vendor cost, profit, margin | David, Sep 18 |
| All columns width 20 (units columns narrower), wrapped headers, zeros left as zeros | David, Sep 24 |
| Rate cards older than 2025 flagged "reconfirm" | "If the card is from 25 or 26, it's good." (Sep 18) |

Footnotes on every client export: rates based on an N-month flight; subject to base approval;
contracts non-cancellable; production not included, sizes vary by installation.

## Keeping the rate card current

1. Edit **Wilkins Military Rate Card - MASTER.xlsx** (Rate Card tab: vendor costs, year of the rate card
   used, notes). Client prices are formulas driven by the Settings tab.
2. In the app, click **Load rate card** and pick the edited file. The app re-reads it in the browser;
   nothing else needs to run.
3. To bake the new data into the app permanently, export the Rate Card tab to `data/rate_card.csv`
   and run `python3 tools/build_rate_card.py` (needs `pip install openpyxl`), then commit.

Proposals autosave in the browser; **Save proposal** downloads a `.json` you can reopen later or hand
to someone else.

## Known gaps / follow-ups

* 63 options are listed by a base with no cost on file (shown as *inquire*; a manual price can be typed in).
* Most rows in the old master had no rate-card year recorded, so they show *year unverified* rather than a warning.
* Screen counts per network live in the description text, not a numeric field; the *Qty* box is manual.
* International installations are not included (the old master only listed names for them).
* Base populations are the old inventory numbers; Chelsea/David are re-sourcing them from Military OneSource and the DoD demographics report.
