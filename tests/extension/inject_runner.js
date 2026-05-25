// Self-contained SnapList runner — pastes everything inline so we can drive
// the fillListing pipeline from the page context (no extension required).
// Used by autonomous test on real Facebook Marketplace.

(async () => {
  const API = "http://localhost:8000";

  // 1. Fetch the seed draft listing
  let listing;
  try {
    const drafts = await fetch(`${API}/listings/?status_filter=draft`).then(r => r.json());
    listing = drafts.find(d => /Eames/i.test(d.title)) || drafts[0];
    if (!listing) { console.log("[runner] no draft listings"); return; }
  } catch (e) { console.log("[runner] cannot reach backend:", e.message); return; }

  // 2. Get FB category path
  try {
    const cat = await fetch(`${API}/analyze/category`, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        title: listing.title, category: listing.category, keywords: listing.keywords || []
      })
    }).then(r => r.json());
    if (cat?.path) listing.fb_category_path = cat.path;
    console.log("[runner] category path:", listing.fb_category_path);
  } catch (e) { console.log("[runner] category mapper failed:", e.message); }

  // 3. Resolve photo URLs
  listing.photos = (listing.photos || []).map(p =>
    p.startsWith("http") ? p : `${API}${p}`
  );

  // ── Inlined fillListing logic (copy of extension/content.js) ──────────────
  const LOG = (...a) => console.log("[SnapList]", ...a);
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  function setNativeInputValue(element, value) {
    const proto = element.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    const tracker = element._valueTracker;
    if (tracker) tracker.setValue("");
    if (setter) setter.call(element, value);
    else element.value = value;
    element.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function waitFor(selector, { root = document, timeout = 5000 } = {}) {
    return new Promise((resolve, reject) => {
      const found = root.querySelector(selector);
      if (found) return resolve(found);
      const obs = new MutationObserver(() => {
        const el = root.querySelector(selector);
        if (el) { obs.disconnect(); resolve(el); }
      });
      obs.observe(root, { childList: true, subtree: true });
      setTimeout(() => { obs.disconnect(); reject(new Error(`timeout: ${selector}`)); }, timeout);
    });
  }

  function findByLabel(labels, kind = "input,textarea") {
    const lc = labels.map(l => l.toLowerCase());
    const els = Array.from(document.querySelectorAll(kind)).filter(e => e.offsetParent !== null);
    let match = els.find(e => {
      const haystack = [e.getAttribute("aria-label"), e.getAttribute("placeholder"),
                       e.getAttribute("name"), e.getAttribute("id")].filter(Boolean).join(" ").toLowerCase();
      return lc.some(l => haystack.includes(l));
    });
    if (match) return match;
    match = els.find(e => {
      let node = e;
      for (let i = 0; i < 6 && node; i++) {
        const txt = (node.innerText || "").toLowerCase();
        if (lc.some(l => txt.includes(l)) && txt.length < 120) return true;
        node = node.parentElement;
      }
      return false;
    });
    return match;
  }

  async function fillField(labels, value, kind = "input,textarea") {
    if (value == null || value === "") return false;
    const el = findByLabel(labels, kind);
    if (!el) { LOG("  not found:", labels); return false; }
    LOG("  filling", labels[0], "→", String(value).slice(0, 60), "| tag=", el.tagName);
    el.focus(); await sleep(80);
    setNativeInputValue(el, String(value));
    await sleep(220);
    return true;
  }

  const fireMouse = (el, type) => el.dispatchEvent(new MouseEvent(type, {
    bubbles: true, cancelable: true, view: window, button: 0,
  }));
  const firePointer = (el, type) => el.dispatchEvent(new PointerEvent(type, {
    bubbles: true, cancelable: true, pointerType: "mouse", isPrimary: true,
  }));
  const realClick = (el) => {
    el.scrollIntoView({ block: "center" });
    firePointer(el, "pointerdown"); fireMouse(el, "mousedown");
    firePointer(el, "pointerup");   fireMouse(el, "mouseup");
    el.click();
  };

  async function pickCategoryByPath(path) {
    if (!path?.length) { LOG("  category: no path"); return false; }
    LOG("  category: navigating", path.join(" > "));
    const triggers = Array.from(document.querySelectorAll(
      '[role="combobox"], [aria-haspopup="listbox"], [aria-haspopup="menu"], [aria-haspopup="dialog"], [aria-haspopup="true"]'
    )).filter(b => b.offsetParent !== null);
    const trigger = triggers.find(b => {
      let n = b;
      for (let i = 0; i < 6 && n; i++) {
        if ((n.innerText || "").toLowerCase().includes("category")) return true;
        n = n.parentElement;
      }
      return false;
    });
    if (!trigger) { LOG("  category: trigger not found"); return false; }
    trigger.focus(); realClick(trigger);
    for (let i = 0; i < path.length; i++) {
      const step = path[i]; const stepLC = step.toLowerCase();
      let found = null;
      for (let attempt = 0; attempt < 12 && !found; attempt++) {
        await sleep(200);
        const candidates = Array.from(document.querySelectorAll(
          '[role="option"], [role="menuitem"], [role="treeitem"], div[role="button"], li[role="button"]'
        )).filter(e => e.offsetParent !== null);
        found = candidates.find(o => {
          const t = (o.innerText || "").trim().toLowerCase();
          return t === stepLC || t.startsWith(stepLC + "\n") || t.startsWith(stepLC + " ");
        }) || candidates.find(o => (o.innerText || "").toLowerCase().includes(stepLC));
      }
      if (!found) {
        LOG("  category: step", i+1, `"${step}"`, "not found");
        document.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        return false;
      }
      LOG("  category: step", i+1, "→", `"${step}"`);
      realClick(found); await sleep(400);
    }
    LOG("  category: done");
    return true;
  }

  async function pickDropdown(buttonLabel, optionText) {
    if (!optionText) return false;
    const realTriggers = Array.from(document.querySelectorAll(
      '[role="combobox"], [aria-haspopup="listbox"], [aria-haspopup="menu"]'
    )).filter(b => b.offsetParent !== null);
    const labelLC = buttonLabel.toLowerCase();
    let trigger = realTriggers.find(b => {
      let n = b;
      for (let i = 0; i < 6 && n; i++) {
        if ((n.innerText || "").toLowerCase().includes(labelLC)) return true;
        n = n.parentElement;
      }
      return false;
    });
    if (!trigger) { LOG("  ", buttonLabel, ": trigger not found"); return false; }
    LOG("  ", buttonLabel, ": opening", (trigger.innerText||"").slice(0,40));
    trigger.focus(); realClick(trigger); await sleep(250);
    try {
      await waitFor('[role="option"]', { timeout: 3000 });
      await sleep(200);
      const options = Array.from(document.querySelectorAll('[role="option"]'));
      const wanted = options.find(o => (o.innerText||"").toLowerCase().includes(optionText.toLowerCase()));
      if (wanted) { realClick(wanted); LOG("  ", buttonLabel, ": picked", wanted.innerText.slice(0,30)); return true; }
      LOG("  ", buttonLabel, ": no option matched");
      document.body.click();
      return false;
    } catch { LOG("  ", buttonLabel, ": never opened"); return false; }
  }

  async function attachPhotos(urls) {
    if (!urls?.length) return 0;
    const fileInput = document.querySelector('input[type="file"][accept*="image"]');
    if (!fileInput) return 0;
    const dt = new DataTransfer();
    let added = 0;
    for (const url of urls) {
      try {
        const resp = await fetch(url);
        if (!resp.ok) continue;
        const blob = await resp.blob();
        const name = url.split("/").pop().split("?")[0] || "photo.jpg";
        dt.items.add(new File([blob], name, { type: blob.type || "image/jpeg" }));
        added++;
      } catch (e) {}
    }
    if (added > 0) {
      fileInput.files = dt.files;
      fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
    return added;
  }

  // ── Run ───────────────────────────────────────────────────────────────────
  LOG("starting on", location.href);
  await sleep(400);
  const results = {};
  LOG("→ title");       results.title       = await fillField(["title"], listing.title);
  LOG("→ price");       results.price       = await fillField(["price"], listing.ai_analysis?.suggested_price);
  LOG("→ description"); results.description = await fillField(["description","what makes"], listing.description, "textarea") || await fillField(["description","what makes"], listing.description, "input");
  LOG("→ category");    results.category    = await pickCategoryByPath(listing.fb_category_path);
  LOG("→ condition");   results.condition   = await pickDropdown("Condition", listing.condition);
  const photoCount    = await attachPhotos(listing.photos);
  LOG("DONE results:", JSON.stringify(results), "photos:", photoCount);
  window.__SNAPLIST_RESULTS__ = { ...results, photoCount };
})();
