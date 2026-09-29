# Wilkins Media – Military Proposal Builder

A CRM-style tool for the Wilkins military division. Pick installations by state or by base, tick the
media options you want to propose, and export a client-facing and an internal Excel proposal in the
house "Military Media Plan" format.

```
military/
├── index.html                                 the app (static page, no build step)
├── dist/Wilkins Military Proposal Builder.html one-file copy of the app (data + logos inlined) - save this in Box
├── Wilkins Military Rate Card - MASTER.xlsx   the standardized rate card David's team maintains
├── DESIGN.md                                  design tokens and component rules the app follows
├── audit/                                     Box folders vs. rate card audit (xlsx + README + raw listing)
├── data/
│   ├── rate_card.csv                          same data, one row per media option (source of truth for the build)
│   ├── rate_card.js                           generated copy embedded in the app
│   ├── source_master_export_12.2.25.json      raw export of the old Box master (traceability only)
│   ├── source_digital_inventory_6.3.26.txt    raw export of the June 2026 digital inventory master
│   └── source_publication_inventory_june2026.txt  raw export of the June 2026 publication inventory master
├── tools/
│   ├── standardize.py                         step 1: raw Box master export -> rate_card.csv
│   ├── merge_inventory.py                     step 1b: fold the June 2026 inventory masters into rate_card.csv
│   ├── build_rate_card.py                     step 2: rate_card.csv -> MASTER.xlsx + rate_card.js
│   ├── build_standalone.py                    index.html + data + logos -> dist/ one-file app
│   └── box_audit.py                           audit/box_listing_<date>.json + rate_card.csv -> audit workbook
└── assets/                                    Wilkins logos
```

## Where the data came from

* **Rate card**: Box > Military > Master Grid > `MasterMilitaryOnBaseList 12.2.25 NS.xlsx`
  (1,238 media options across ~100 domestic installations). Vendor (base) cost at 1 / 3 / 6 / 12
  months plus production, cleaned and categorized.
* **June 2026 inventory masters**: Box > Military > `Military - National Digital Inventory Master 6.3.26.xlsx`
  and `Military - National Publication Inventory Master_June 2026.xlsx`. They are newer than the
  12.2.25 master and cover ~60 more bases; 296 options were added from them (source column says which)
  and 204 existing rows carry a note where the inventory price differs.
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

## Keeping the rate card current (no technical steps)

Rate cards change every year, so the app has an **Update pricing** mode built for whoever is
onboarding:

1. Pick the installation on the left (or *add a new installation*).
2. Click **Update pricing**. Type the vendor costs from the base's new rate card into the
   1 / 3 / 6 / 12-month boxes, set the rate card year, add a note if a price is per unit or has a minimum.
   Edits save in the browser as you type; client prices are always calculated, never typed.
3. Click **Download rate card (Excel)** and save the file over the master in Box. Every edit is listed
   on the Change Log tab with the date.
4. Anyone else clicks **Load rate card** and picks that file. Their proposals now use the new prices.

The Excel file is the shared source of truth; the app is just the editor and the proposal builder.
`Reset to built-in data` throws away local edits. The developer path (`tools/build_rate_card.py`)
still exists for baking a new rate card into the app itself.

## Where the files live

Jon asked that this not live in the shared Box > Military folder. Box folder **Military Rate Card Tool**
(Jon's own drive) holds the master rate card and the one-file app; the code lives in this repo.

## Box folders vs. the rate card

`audit/` holds a comparison of every per-base folder in Box > Military > 2 Military Installations
against the rate card (listing pulled Sep 28, 2026). Rebuild with `python3 tools/box_audit.py <date>`
after saving a fresh listing. See `audit/README.md` for the verdicts.

## Where each price came from

Every row carries the installation's Box folder and the newest rate-card file in it ("Rate card in Box"
link on each base card, `Link to rate card file` column in the workbook, `Source (Box)` column on the
internal export). When someone prices a base from a new file, they paste that file's Box link in Update
pricing and it travels with the row. Edits are stamped with the editor's name (asked once, stored in the
browser) on the Change Log tab.

## Deployment and sync

**Hosting**: GitHub Pages from this repo (`.github/workflows/pages.yml` publishes the repo root, so the
calculator stays at `/` and the builder is at `/military/`). Enable it once in the repo settings
(Settings > Pages > Source: GitHub Actions). No server, no login, nothing to install; the app is a static
page and proposals are saved as files.

**Box → app (automatic)**: `.github/workflows/sync-rate-card.yml` runs hourly. It downloads
`Wilkins Military Rate Card - MASTER.xlsx` from Jon's Box folder "Military Rate Card Tool"
(folder 422333003231), and if the file changed it rebuilds `data/rate_card.js`, the repo copy of the
workbook and `dist/`, then commits. Pages redeploys on the commit. So an edit to the master in Box shows
up in the builder within the hour without anyone touching the repo. One-time setup:

1. In Box Developer Console create a Custom App, authentication "Server Authentication (Client
   Credentials Grant)", application scope "Read all files and folders". Submit it for authorization and
   have a Box admin approve it (Admin Console > Apps > Custom Apps Manager).
2. Share the "Military Rate Card Tool" folder with the app's service-account e-mail (shown on the app's
   General Settings tab) as Viewer.
3. In GitHub (Settings > Secrets and variables > Actions) add secrets `BOX_CLIENT_ID`,
   `BOX_CLIENT_SECRET`, `BOX_SUBJECT_ID` (the enterprise ID) and, optionally, variables
   `BOX_SUBJECT_TYPE` (`enterprise`) and `BOX_FOLDER_ID`.
4. Run the workflow once by hand (Actions > Sync rate card from Box > Run workflow).

**App → Box (one click)**: after editing prices in the app, "Download rate card (Excel)" produces the
master workbook; save it over the file in the Box folder. Box keeps every version and who uploaded it,
which is the "who last worked on it" record. The next hourly sync pulls it back into the app, so the
loop closes: Box is the system of record, the app is the editor and the proposal builder.

**Proposals in flight** are not affected by a rate-card sync: a proposal keeps the prices it was built
with until you re-check the item, and the internal export records which rate-card file it used.

## Known gaps / follow-ups

* 63 options are listed by a base with no cost on file (shown as *inquire*; a manual price can be typed in).
* Most rows in the old master had no rate-card year recorded, so they show *year unverified* rather than a warning.
* Screen counts per network live in the description text, not a numeric field; the *Qty* box is manual.
* International installations are not included (the old master only listed names for them).
* Base populations are the old inventory numbers; Chelsea/David are re-sourcing them from Military OneSource and the DoD demographics report.
