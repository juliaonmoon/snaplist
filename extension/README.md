# SnapList — Facebook Marketplace Autofill

A Chrome/Edge/Brave extension that auto-fills the Facebook Marketplace "Create
listing" form using your SnapList drafts.

This avoids Facebook's lack of any public listing API. The extension acts as
your hands: it reads your draft from `localhost:8000` and types into the form
for you. One click, then you review and publish.

## Install (dev / unpacked)

1. Make sure your SnapList backend is running:
   ```
   uvicorn backend.main:app --port 8000
   ```
2. Open Chrome and visit `chrome://extensions`
3. Toggle **Developer mode** (top right)
4. Click **Load unpacked**
5. Select this folder: `C:\Users\jules\snaplist\extension`
6. Pin the SnapList icon to your toolbar (puzzle-piece menu → pin)

## Use

1. In SnapList, snap a photo and save the listing as a draft (don't publish).
2. Open `https://www.facebook.com/marketplace/create/item`
3. Click the SnapList toolbar icon → pick the draft → it fills the form
4. Review the filled fields (especially Category and Condition — FB's taxonomy
   doesn't always match ours)
5. Click Facebook's **Publish** button yourself

## What it fills

| Field       | Source                              | Notes                                  |
| ----------- | ----------------------------------- | -------------------------------------- |
| Title       | `listing.title`                     | always works                           |
| Price       | `ai_analysis.suggested_price`       | always works                           |
| Description | `listing.description`               | always works                           |
| Location    | `pickup_location` or `location`     | picks the first autocomplete result    |
| Photos      | `listing.photos[]`                  | downloaded from your backend           |
| Category    | `listing.category`                  | best-effort dropdown match             |
| Condition   | `listing.condition`                 | best-effort dropdown match             |

## Why dropdowns are "best-effort"

Facebook uses a fixed taxonomy (e.g. "Home & Garden > Furniture > Tables")
while SnapList stores a free-text category. We do a substring match on the
visible dropdown options, which works ~80% of the time. When it can't match,
the toast at the bottom will tell you which fields it skipped — fill those
in manually.

## Why selectors might break

Facebook ships UI changes constantly. We use `aria-label` and `role="..."`
attributes (the most stable hooks they have), but if FB re-labels a field
the extension will silently skip it. If something stops working, check the
DevTools Console for `SnapList:` warnings — usually a one-line selector
update fixes it.

## Permissions explained

- `host_permissions: http://localhost:8000/*` — fetch drafts from your backend
- `host_permissions: https://www.facebook.com/*` — read/write the Marketplace form
- `activeTab` — send the "fill" message to the current FB tab
- `storage` — temporarily stash a listing if we need to open FB in a new tab first
- `scripting` — required for content script messaging on MV3
