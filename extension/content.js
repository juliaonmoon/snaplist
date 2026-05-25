// SnapList content script
// Runs on facebook.com/marketplace/create/* and fills the listing form on command.

(() => {
  if (window.__SNAPLIST_INJECTED__) return;
  window.__SNAPLIST_INJECTED__ = true;

  const LOG = (...a) => console.log("[SnapList]", ...a);

  // ── React-aware setters ───────────────────────────────────────────────────
  // FB's React-controlled inputs ignore plain `el.value = "x"`. We must:
  //   1. Reset React's internal _valueTracker so it knows the value changed
  //   2. Call the native HTMLInputElement value setter (not the React-shadowed one)
  //   3. Dispatch an InputEvent React's SyntheticEvent system can read
  function setNativeInputValue(element, value) {
    const proto = element.tagName === "TEXTAREA"
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;

    // CRITICAL: tell React's value tracker the previous value was empty,
    // otherwise React sees value === lastValue and skips the change handler.
    const tracker = element._valueTracker;
    if (tracker) tracker.setValue("");

    if (setter) setter.call(element, value);
    else element.value = value;

    // InputEvent (not plain Event) so React's beforeinput/input handlers fire correctly
    element.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // Wait for an element to appear in the DOM, up to `timeout` ms.
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

  // Find an input by ANY of: aria-label, placeholder, OR a nearby label text node.
  // FB Marketplace renders field names as <span> siblings rather than aria-labels,
  // so we walk up the DOM and look for matching label text.
  function findByLabel(labels, kind = "input,textarea") {
    const lc = labels.map(l => l.toLowerCase());
    const els = Array.from(document.querySelectorAll(kind))
      .filter(e => e.offsetParent !== null);   // visible only

    // 1. Direct match on aria-label / placeholder / name / id
    let match = els.find(e => {
      const haystack = [
        e.getAttribute("aria-label"),
        e.getAttribute("placeholder"),
        e.getAttribute("name"),
        e.getAttribute("id"),
      ].filter(Boolean).join(" ").toLowerCase();
      return lc.some(l => haystack.includes(l));
    });
    if (match) return match;

    // 2. Walk up 6 ancestors and check their text content for a label
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

  // ── Field fillers ─────────────────────────────────────────────────────────
  async function fillField(labels, value, kind = "input,textarea") {
    if (value == null || value === "") return false;
    const el = findByLabel(labels, kind);
    if (!el) { LOG("  not found:", labels); return false; }
    LOG("  filling", labels[0], "→", String(value).slice(0, 60),
        "| tag=", el.tagName, "aria=", el.getAttribute("aria-label"));
    el.focus();
    await sleep(80);
    setNativeInputValue(el, String(value));
    await sleep(220);   // let React flush
    return true;
  }

  const fillTitle       = (v) => fillField(["title"], v);
  const fillPrice       = (v) => fillField(["price"], v);
  // FB's description field is sometimes <textarea>, sometimes <input>, sometimes contenteditable.
  const fillDescription = async (v) => {
    if (!v) return false;
    // Try textarea first, then any input, then any contenteditable
    if (await fillField(["description", "what makes"], v, "textarea")) return true;
    if (await fillField(["description", "what makes"], v, "input")) return true;
    const ce = Array.from(document.querySelectorAll('[contenteditable="true"]'))
      .find(e => {
        let n = e;
        for (let i = 0; i < 6 && n; i++) {
          if ((n.innerText || "").toLowerCase().includes("description")) return true;
          n = n.parentElement;
        }
        return false;
      });
    if (ce) {
      ce.focus();
      ce.innerText = v;
      ce.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: v }));
      LOG("  filled description via contenteditable");
      return true;
    }
    LOG("  description: not found anywhere");
    return false;
  };

  async function fillLocation(value) {
    if (!value) { LOG("  location: no value"); return false; }
    // FB uses different labels in different layouts: "location", "city", "address", "where"
    const el = findByLabel(["location", "city", "where is", "address", "pickup"]);
    if (!el) { LOG("  location: input not found (tried: location/city/where/address/pickup)"); return false; }
    LOG("  filling location →", value, "| tag=", el.tagName);
    el.focus();
    await sleep(80);
    setNativeInputValue(el, value);
    await sleep(1500);
    const firstOption = document.querySelector('[role="option"]');
    if (firstOption) { LOG("  location: clicking first autocomplete option"); firstOption.click(); }
    else { LOG("  location: no autocomplete options appeared"); }
    return true;
  }

  // Categories and Conditions use FB's custom dropdowns (role="combobox" / haspopup).
  async function pickDropdown(buttonLabel, optionText) {
    if (!optionText) { LOG("  ", buttonLabel, ": no value"); return false; }

    // Prefer REAL trigger elements (combobox, listbox-popup buttons) over plain labels.
    // Fall back to any [role="button"] only if no real trigger has the label nearby.
    const realTriggers = Array.from(document.querySelectorAll(
      '[role="combobox"], [aria-haspopup="listbox"], [aria-haspopup="menu"], [aria-haspopup="dialog"], [aria-haspopup="true"]'
    )).filter(b => b.offsetParent !== null);

    const labelLC = buttonLabel.toLowerCase();
    // For each real trigger, check itself AND its ancestors for the label text.
    let trigger = realTriggers.find(b => {
      let node = b;
      for (let i = 0; i < 6 && node; i++) {
        if ((node.innerText || "").toLowerCase().includes(labelLC)) return true;
        node = node.parentElement;
      }
      return false;
    });

    // Fallback: any visible button-ish element whose own text contains the label
    if (!trigger) {
      const anyButtons = Array.from(document.querySelectorAll('[role="button"], button'))
        .filter(b => b.offsetParent !== null);
      trigger = anyButtons.find(b => (b.innerText || "").toLowerCase().includes(labelLC));
    }

    if (!trigger) { LOG("  ", buttonLabel, ": trigger not found"); return false; }
    LOG("  ", buttonLabel, ": opening trigger →", (trigger.innerText || "").slice(0, 60), "| role=", trigger.getAttribute("role"));

    // FB's React popovers ignore plain .click() — they listen for the full pointer sequence.
    const fireMouse = (el, type) => el.dispatchEvent(new MouseEvent(type, {
      bubbles: true, cancelable: true, view: window, button: 0,
    }));
    const firePointer = (el, type) => el.dispatchEvent(new PointerEvent(type, {
      bubbles: true, cancelable: true, pointerType: "mouse", isPrimary: true,
    }));
    trigger.scrollIntoView({ block: "center" });
    trigger.focus();
    firePointer(trigger, "pointerdown");
    fireMouse(trigger, "mousedown");
    firePointer(trigger, "pointerup");
    fireMouse(trigger, "mouseup");
    trigger.click();
    await sleep(250);
    try {
      await waitFor('[role="option"]', { timeout: 3000 });
      await sleep(200);
      const options = Array.from(document.querySelectorAll('[role="option"]'));
      LOG("  ", buttonLabel, ":", options.length, "options visible");
      const wanted = options.find(o =>
        (o.innerText || "").toLowerCase().includes(optionText.toLowerCase())
      );
      if (wanted) { LOG("  ", buttonLabel, ": picking →", wanted.innerText.slice(0, 60)); wanted.click(); return true; }
      LOG("  ", buttonLabel, ": no option matched", optionText, "— first 5:", options.slice(0, 5).map(o => o.innerText.slice(0, 30)));
      document.body.click();
      return false;
    } catch (e) {
      LOG("  ", buttonLabel, ": dropdown never opened");
      return false;
    }
  }

  // ── FB Category modal — navigate a known leaf path step-by-step ──────────
  // FB renders Category as a modal tree (Home & Garden → Furniture → Chairs → Lounge Chairs).
  // Each level renders new clickable rows; we click each one in turn.
  async function pickCategoryByPath(path) {
    if (!path?.length) { LOG("  category: no path provided"); return false; }
    LOG("  category: navigating path →", path.join(" > "));

    // Pointer event helpers (FB's React popovers ignore plain .click())
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

    // 1. Open the Category combobox
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
    trigger.focus();
    realClick(trigger);

    // 2. Walk each path step
    for (let i = 0; i < path.length; i++) {
      const step = path[i];
      const stepLC = step.toLowerCase();
      let found = null;
      // Poll for the option to appear (FB renders levels async)
      for (let attempt = 0; attempt < 12 && !found; attempt++) {
        await sleep(200);
        // FB uses role="option" for tree leaves, role="button" / div[role="menuitem"] for branches
        const candidates = Array.from(document.querySelectorAll(
          '[role="option"], [role="menuitem"], [role="treeitem"], div[role="button"], li[role="button"]'
        )).filter(e => e.offsetParent !== null);
        found = candidates.find(o => {
          const t = (o.innerText || "").trim().toLowerCase();
          // Match if option text starts with or equals the step (avoids matching "Furniture Polish" for "Furniture")
          return t === stepLC || t.startsWith(stepLC + "\n") || t.startsWith(stepLC + " ");
        }) || candidates.find(o => (o.innerText || "").toLowerCase().includes(stepLC));
      }
      if (!found) {
        LOG("  category: step", i + 1, `"${step}"`, "not found — closing modal");
        document.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        return false;
      }
      LOG("  category: step", i + 1, "→ clicking", `"${step}"`);
      realClick(found);
      await sleep(300);
    }
    LOG("  category: done");
    return true;
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
      } catch (e) {
        console.warn("SnapList: failed to fetch photo", url, e);
      }
    }
    if (added > 0) {
      fileInput.files = dt.files;
      fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
    return added;
  }

  // ── Main orchestrator ─────────────────────────────────────────────────────
  async function fillListing(listing) {
    LOG("fillListing called with:", listing);
    showToast("📦 SnapList: filling form…");
    // Give FB's form a moment to settle before poking it
    await sleep(400);

    const results = {};
    LOG("→ title");       results.title       = await fillTitle(listing.title);
    LOG("→ price");       results.price       = await fillPrice(listing.ai_analysis?.suggested_price ?? listing.ai_analysis?.price ?? "");
    LOG("→ description"); results.description = await fillDescription(listing.description);
    LOG("→ location");    results.location    = await fillLocation(listing.pickup_location || listing.location || "Surrey");
    // Category uses path-based tree navigation when popup pre-mapped it; falls back to flat dropdown.
    LOG("→ category");
    if (listing.fb_category_path?.length) {
      results.category = await pickCategoryByPath(listing.fb_category_path);
    } else {
      LOG("  category: no fb_category_path on payload, falling back to flat dropdown");
      results.category = await pickDropdown("Category", listing.category);
    }
    LOG("→ condition");
    results.condition   = await pickDropdown("Condition", listing.condition);
    const photoCount    = await attachPhotos(listing.photos);

    const filled = Object.entries(results).filter(([, v]) => v).map(([k]) => k);
    const skipped = Object.entries(results).filter(([, v]) => !v).map(([k]) => k);
    const summary = `✅ Filled: ${filled.join(", ")}${photoCount ? `, ${photoCount} photo${photoCount > 1 ? "s" : ""}` : ""}` +
                    (skipped.length ? ` · ⚠️ skipped: ${skipped.join(", ")}` : "");
    showToast(summary, 6000);
    return { ok: true, filled, skipped, photoCount };
  }

  // ── Floating toast UI ─────────────────────────────────────────────────────
  function showToast(text, duration = 3000) {
    let el = document.getElementById("__snaplist_toast__");
    if (!el) {
      el = document.createElement("div");
      el.id = "__snaplist_toast__";
      el.style.cssText = `
        position: fixed; bottom: 24px; right: 24px; z-index: 2147483647;
        background: #0f172a; color: white; padding: 12px 18px;
        border-radius: 10px; font: 500 13px -apple-system, system-ui;
        box-shadow: 0 8px 24px rgba(0,0,0,.25); max-width: 360px;
      `;
      document.body.appendChild(el);
    }
    el.textContent = text;
    el.style.opacity = "1";
    clearTimeout(el.__timer);
    el.__timer = setTimeout(() => { el.style.transition = "opacity .4s"; el.style.opacity = "0"; }, duration);
  }

  // ── Message bridge ────────────────────────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.action === "fillListing") {
      fillListing(msg.listing).then(sendResponse).catch(err => {
        showToast(`❌ SnapList error: ${err.message}`, 5000);
        sendResponse({ ok: false, error: err.message });
      });
      return true; // async response
    }
  });

  // ── Auto-resume: if popup stashed a listing while we were navigating ──────
  chrome.storage.local.get("pendingListing", ({ pendingListing }) => {
    if (pendingListing) {
      chrome.storage.local.remove("pendingListing");
      // Give FB a moment to render the form before we start poking it.
      setTimeout(() => fillListing(pendingListing).catch(() => {}), 1500);
    }
  });

  console.log("SnapList content script loaded");
})();
