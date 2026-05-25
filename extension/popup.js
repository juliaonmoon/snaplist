// SnapList popup — fetches draft listings from local backend and sends one to the active FB tab.

const API_BASE = "http://localhost:8000";
const $ = (id) => document.getElementById(id);

async function init() {
  $("api-url").textContent = API_BASE;

  // 1. Verify backend reachable
  let drafts;
  try {
    const resp = await fetch(`${API_BASE}/listings/?status_filter=draft`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    drafts = await resp.json();
    $("status").textContent = "connected";
    $("status").className = "status ok";
  } catch (err) {
    $("status").textContent = "offline";
    $("status").className = "status bad";
    showError(
      `Can't reach <code>${API_BASE}</code>.<br>Start the backend:<br>` +
      `<code>uvicorn backend.main:app --port 8000</code>`
    );
    return;
  }

  // 2. Verify we're on a FB Marketplace create page
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const onFbMarketplace = tab?.url?.startsWith("https://www.facebook.com/marketplace/create");
  if (!onFbMarketplace) {
    showHint(
      `Open <a href="https://www.facebook.com/marketplace/create/item" target="_blank">` +
      `facebook.com/marketplace/create/item</a> first, then click a listing below.`
    );
  }

  // 3. Render drafts
  if (!drafts.length) {
    $("empty").classList.remove("hidden");
    return;
  }

  const list = $("list");
  for (const d of drafts) {
    const photoUrl = d.photos?.[0]
      ? (d.photos[0].startsWith("http") ? d.photos[0] : `${API_BASE}${d.photos[0]}`)
      : "";
    const price = d.ai_analysis?.suggested_price
      ?? d.ai_analysis?.price
      ?? d.ai_analysis?.estimated_price;

    const card = document.createElement("div");
    card.className = "item";
    card.innerHTML = `
      <img src="${photoUrl}" onerror="this.style.opacity=0.3" />
      <div class="meta">
        <div class="title"></div>
        <div class="sub"></div>
        ${price ? `<div class="price">C$${Number(price).toFixed(2)}</div>` : ""}
      </div>
    `;
    card.querySelector(".title").textContent = d.title || "(untitled)";
    card.querySelector(".sub").textContent =
      [d.category, d.condition].filter(Boolean).join(" · ") || "no category";

    card.addEventListener("click", () => fillIntoTab(tab, d, onFbMarketplace));
    list.appendChild(card);
  }
}

async function fillIntoTab(tab, listing, onFbMarketplace) {
  if (!onFbMarketplace) {
    // Open FB Marketplace and stash the listing; user re-clicks once page loads.
    await chrome.storage.local.set({ pendingListing: listing });
    chrome.tabs.create({ url: "https://www.facebook.com/marketplace/create/item" });
    window.close();
    return;
  }

  // Resolve photo URLs to absolute
  const photos = (listing.photos || []).map(p =>
    p.startsWith("http") ? p : `${API_BASE}${p}`
  );

  // Ask backend to map our category → exact FB Marketplace leaf path
  let fb_category_path = null;
  try {
    const catResp = await fetch(`${API_BASE}/analyze/category`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: listing.title || "",
        category: listing.category || null,
        keywords: listing.keywords || [],
      }),
    });
    if (catResp.ok) {
      const data = await catResp.json();
      fb_category_path = data.path;
      console.log("[SnapList popup] fb category path:", fb_category_path);
    } else {
      console.log("[SnapList popup] category mapper:", catResp.status);
    }
  } catch (e) {
    console.warn("[SnapList popup] category mapper failed:", e);
  }

  const payload = { ...listing, photos, fb_category_path };

  try {
    await chrome.tabs.sendMessage(tab.id, { action: "fillListing", listing: payload });
    showHint("✅ Filling form — review and click Publish.");
    setTimeout(() => window.close(), 800);
  } catch (err) {
    showError(
      `Couldn't reach the page script. Refresh the Facebook tab and try again.<br>` +
      `<small>${err.message}</small>`
    );
  }
}

function showHint(html) {
  const h = $("hint");
  h.classList.remove("hidden", "error");
  h.innerHTML = html;
}
function showError(html) {
  const h = $("hint");
  h.classList.remove("hidden");
  h.classList.add("error");
  h.innerHTML = html;
}

init();
