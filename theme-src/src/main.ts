import "./main.css";
import "./tree";

function wireSidebarTabs(root: ParentNode = document): void {
  const sidebars = root.querySelectorAll<HTMLElement>(".thdocs-sidebar");
  for (const sidebar of sidebars) {
    sidebar.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const button = target.closest<HTMLElement>("[data-tab]");
      if (!button || !sidebar.contains(button)) return;
      const tabName = button.dataset.tab;
      if (!tabName) return;
      for (const btn of sidebar.querySelectorAll<HTMLElement>("[data-tab]")) {
        btn.setAttribute(
          "aria-selected",
          btn.dataset.tab === tabName ? "true" : "false",
        );
      }
      for (const panel of sidebar.querySelectorAll<HTMLElement>("[data-panel]")) {
        if (panel.dataset.panel === tabName) {
          panel.removeAttribute("hidden");
        } else {
          panel.setAttribute("hidden", "");
        }
      }
    });
  }
}

function setupToctreeCollapse(): void {
  const contentsPanel = document.querySelector<HTMLElement>(
    ".thdocs-sidebar [data-panel='contents']"
  );
  if (!contentsPanel) return;

  // ── SVG icons ──
  const closedBookSvg =
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 13.5a2 2 0 0 1 2-2H14"/><path d="M4 1h10v13H4a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2z"/><line x1="9" y1="1" x2="9" y2="11"/></svg>';
  const openBookSvg =
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M1 2h7v12H3a2 2 0 0 1-2-2V2z"/><path d="M15 2H8v12h5a2 2 0 0 0 2-2V2z"/><line x1="8" y1="2" x2="8" y2="14"/></svg>';
  const docSvg =
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5l-3-4z"/><path d="M10 1v4h4"/><line x1="5" y1="10" x2="11" y2="10"/></svg>';

  // ── Phase 1: Strip fragment-only links (anchors within pages) ──
  for (const li of Array.from(contentsPanel.querySelectorAll<HTMLElement>("li"))) {
    const link = li.querySelector<HTMLAnchorElement>(":scope > a");
    if (!link) continue;
    const href = link.getAttribute("href") || "";
    // Link is a fragment anchor (e.g. getting-started.html#installation, or just #something)
    if (href.includes("#") && !href.endsWith("#")) {
      const parentLi = li.parentElement?.closest("li");
      li.remove();
      // Clean up empty UL in parent
      if (parentLi) {
        const parentUl = parentLi.querySelector<HTMLElement>(":scope > ul");
        if (parentUl && !parentUl.hasChildNodes()) parentUl.remove();
      }
    }
  }

  // ── Phase 2: Setup icons and collapse ──
  // Load persisted state
  const persistedSet = new Set<string>();
  const persisted = sessionStorage.getItem("thdocs-toc-expanded");
  if (persisted) {
    try {
      const parsed = JSON.parse(persisted);
      if (Array.isArray(parsed)) parsed.forEach((key) => persistedSet.add(key));
    } catch {}
  }

  // Find current page and its ancestors
  const currentAncestors = new Set<HTMLElement>();
  const currentLink = contentsPanel.querySelector<HTMLElement>("a.reference.internal.current");
  if (currentLink) {
    let ancestor: HTMLElement | null = currentLink.parentElement;
    while (ancestor && ancestor !== contentsPanel) {
      if (ancestor.tagName === "LI") currentAncestors.add(ancestor);
      ancestor = ancestor.parentElement;
    }
  }

  // Process section captions (e.g. "User Guide", "Internals")
  for (const caption of Array.from(contentsPanel.querySelectorAll<HTMLElement>("p.caption"))) {
    const nextUl = caption.nextElementSibling as HTMLElement | null;
    if (!nextUl || nextUl.tagName !== "UL") continue;

    const key = caption.textContent || "";
    const shouldExpand = persistedSet.has(key);

    const wrapper = document.createElement("div");
    wrapper.className = "thdocs-toc-section";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "thdocs-toc-toggle thdocs-toc-toggle--caption";
    btn.innerHTML = shouldExpand ? openBookSvg : closedBookSvg;
    btn.setAttribute("aria-expanded", shouldExpand ? "true" : "false");
    btn.setAttribute("aria-label", "Toggle section");

    caption.parentElement!.insertBefore(wrapper, caption);
    const row = document.createElement("div");
    row.className = "thdocs-toc-row thdocs-toc-caption-row";
    row.appendChild(btn);
    row.appendChild(caption);
    wrapper.appendChild(row);
    wrapper.appendChild(nextUl);

    if (!shouldExpand) nextUl.style.display = "none";

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const expanded = btn.getAttribute("aria-expanded") === "true";
      const newExpanded = !expanded;
      btn.setAttribute("aria-expanded", newExpanded ? "true" : "false");
      btn.innerHTML = newExpanded ? openBookSvg : closedBookSvg;
      nextUl.style.display = newExpanded ? "" : "none";
      if (newExpanded) persistedSet.add(key);
      else persistedSet.delete(key);
      sessionStorage.setItem("thdocs-toc-expanded", JSON.stringify(Array.from(persistedSet)));
    });
  }

  // Process LI items (page links)
  for (const li of Array.from(
    contentsPanel.querySelectorAll<HTMLElement>("li.toctree-l1, li.toctree-l2, li.toctree-l3, li.toctree-l4")
  )) {
    const link = li.querySelector<HTMLAnchorElement>(":scope > a");
    if (!link) continue;

    const childUl = li.querySelector<HTMLElement>(":scope > ul");
    const hasChildren = childUl !== null;

    if (hasChildren) {
      // Item with children: book icon + toggle
      const key = link.href;
      const shouldExpand = currentAncestors.has(li) || persistedSet.has(key);

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "thdocs-toc-toggle thdocs-toc-toggle--page";
      btn.innerHTML = shouldExpand ? openBookSvg : closedBookSvg;
      btn.setAttribute("aria-expanded", shouldExpand ? "true" : "false");
      btn.setAttribute("aria-label", "Toggle");

      const row = document.createElement("div");
      row.className = "thdocs-toc-row";
      li.insertBefore(row, link);
      row.appendChild(btn);
      row.appendChild(link);

      if (!shouldExpand) childUl!.style.display = "none";

      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const expanded = btn.getAttribute("aria-expanded") === "true";
        const newExpanded = !expanded;
        btn.setAttribute("aria-expanded", newExpanded ? "true" : "false");
        btn.innerHTML = newExpanded ? openBookSvg : closedBookSvg;
        childUl!.style.display = newExpanded ? "" : "none";
        if (newExpanded) persistedSet.add(key);
        else persistedSet.delete(key);
        sessionStorage.setItem("thdocs-toc-expanded", JSON.stringify(Array.from(persistedSet)));
      });
    } else {
      // Leaf page: document icon (no toggle)
      const icon = document.createElement("span");
      icon.className = "thdocs-toc-icon";
      icon.innerHTML = docSvg;

      const row = document.createElement("div");
      row.className = "thdocs-toc-row";
      li.insertBefore(row, link);
      row.appendChild(icon);
      row.appendChild(link);
    }
  }
}

function setupScrollspy(): void {
  const toc = document.querySelector(".thdocs-page-toc");
  if (!toc) return;

  const headings = Array.from(
    document.querySelectorAll<HTMLElement>("main h2[id], main h3[id]")
  );
  if (headings.length === 0) return;

  const intersecting = new Set<string>();

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        const id = entry.target.id;
        if (entry.isIntersecting) {
          intersecting.add(id);
        } else {
          intersecting.delete(id);
        }
      }

      const active = Array.from(intersecting).pop();
      for (const link of toc.querySelectorAll<HTMLAnchorElement>("a")) {
        if (link.href.endsWith(`#${active}`)) {
          link.classList.add("thdocs-toc-active");
        } else {
          link.classList.remove("thdocs-toc-active");
        }
      }
    },
    { rootMargin: "0px 0px -60% 0px" }
  );

  for (const heading of headings) {
    observer.observe(heading);
  }
}

function setupToctreeNavMemory(): void {
  const contentsPanel = document.querySelector<HTMLElement>(
    ".thdocs-sidebar [data-panel='contents']"
  );
  if (!contentsPanel) return;

  // Capture scroll position and focus on link click
  contentsPanel.addEventListener("click", (e) => {
    if (!(e.target instanceof Element)) return;
    const link = e.target.closest<HTMLAnchorElement>("a");
    if (!link) return;

    sessionStorage.setItem("thdocs:tocScroll", String(contentsPanel.scrollTop));

    // Only capture focus if the link was focused when clicked
    if (document.activeElement === link) {
      sessionStorage.setItem("thdocs:tocFocusHref", link.href);
    } else {
      sessionStorage.removeItem("thdocs:tocFocusHref");
    }
  });

  // Also capture on Enter keydown for keyboard navigation
  contentsPanel.addEventListener("keydown", (e) => {
    if (!(e.target instanceof Element)) return;
    const link = e.target.closest<HTMLAnchorElement>("a");
    if (!link || e.key !== "Enter") return;

    sessionStorage.setItem("thdocs:tocScroll", String(contentsPanel.scrollTop));

    if (document.activeElement === link) {
      sessionStorage.setItem("thdocs:tocFocusHref", link.href);
    }
  });

  // Restore scroll position and focus on page load
  const savedScroll = sessionStorage.getItem("thdocs:tocScroll");
  if (savedScroll !== null) {
    contentsPanel.scrollTop = parseInt(savedScroll, 10);
  }

  const focusHref = sessionStorage.getItem("thdocs:tocFocusHref");
  if (focusHref) {
    const normalize = (h: string) => h.replace(/#$/, "");
    const target = normalize(focusHref);
    const links = Array.from(
      contentsPanel.querySelectorAll<HTMLAnchorElement>("a")
    );
    const targetLink = links.find((link) => normalize(link.href) === target);

    if (targetLink) {
      // Ensure ancestors are expanded
      let parent = targetLink.closest<HTMLElement>("li");
      while (parent && parent !== contentsPanel) {
        const parentLi = parent.closest<HTMLElement>("li.toctree-l1, li.toctree-l2, li.toctree-l3, li.toctree-l4");
        if (!parentLi || parentLi === parent) break;

        const toggle = parentLi.querySelector<HTMLButtonElement>(
          ".thdocs-toc-toggle"
        );
        if (toggle && toggle.getAttribute("aria-expanded") === "false") {
          toggle.setAttribute("aria-expanded", "true");
        }

        parent = parentLi.parentElement as HTMLElement | null;
      }

      // Restore focus on next macrotask after Sphinx scripts finish claiming focus.
      // Use setTimeout with 0 delay to defer past both DOMContentLoaded handlers and
      // any other microtasks. Also set tabindex to ensure the element can receive focus.
      setTimeout(() => {
        targetLink.focus({ preventScroll: true });
      }, 0);
    }

    sessionStorage.removeItem("thdocs:tocFocusHref");
  }
}

function setupMobileSidebar(): void {
  const btn = document.querySelector<HTMLButtonElement>(".thdocs-header-menu-btn");
  const sidebar = document.querySelector<HTMLElement>("div.sphinxsidebar");
  if (!btn || !sidebar) return;

  btn.addEventListener("click", () => {
    const isOpen = sidebar.classList.contains("thdocs-sidebar--visible");
    if (isOpen) {
      sidebar.classList.remove("thdocs-sidebar--visible");
      btn.setAttribute("aria-expanded", "false");
    } else {
      sidebar.classList.add("thdocs-sidebar--visible");
      btn.setAttribute("aria-expanded", "true");
    }
  });
}

function setupSidebarIndex(): void {
  const indexPanel = document.querySelector<HTMLElement>('[data-panel="index"]');
  if (!indexPanel) return;

  let loaded = false;

  function loadIndex(): void {
    if (loaded) return;
    if ((globalThis as any).THINDEX_DATA) {
      renderIndex();
      loaded = true;
      return;
    }
    const contentRoot = document.documentElement.dataset.content_root || "./";
    const script = document.createElement("script");
    script.src = contentRoot + "_static/index_entries.js";
    script.onload = () => {
      loaded = true;
      renderIndex();
    };
    document.body.appendChild(script);
  }

  function resolveHref(href: string | boolean): string {
    if (href === false) return "#";
    const baseUrl = document.documentElement.dataset.content_root || "./";
    return baseUrl + href;
  }

  function renderIndex(): void {
    const data = (globalThis as any).THINDEX_DATA;
    const container = indexPanel.querySelector<HTMLElement>(".thdocs-index-content");
    if (!container) return;

    if (!data || !Array.isArray(data) || data.length === 0) {
      container.innerHTML = '<p class="thdocs-index-empty">No index entries.</p>';
      return;
    }

    let html = "";

    // Jump nav
    html += '<div class="thdocs-index__jump">';
    for (const group of data) {
      html += `<button type="button" class="thdocs-index__jump-btn" data-letter="${esc(group.letter)}">${esc(group.letter)}</button>`;
    }
    html += "</div>";

    // Sections
    for (const group of data) {
      html += `<div class="thdocs-index__section">`;
      html += `<h3 class="thdocs-index__letter" id="thindex-${group.letter}">${esc(group.letter)}</h3>`;
      html += '<ul class="thdocs-index__list">';
      for (const entry of group.entries) {
        if (entry.url) {
          html += `<li><a class="thdocs-index__link" href="${resolveHref(entry.url)}">${esc(entry.name)}</a>`;
        } else {
          html += `<li><span class="thdocs-index__link thdocs-index__link--no-href">${esc(entry.name)}</span>`;
        }
        if (entry.subitems && entry.subitems.length > 0) {
          html += '<ul class="thdocs-index__list">';
          for (const sub of entry.subitems) {
            if (sub.url) {
              html += `<li><a class="thdocs-index__link" href="${resolveHref(sub.url)}">${esc(sub.name)}</a></li>`;
            } else {
              html += `<li><span class="thdocs-index__link thdocs-index__link--no-href">${esc(sub.name)}</span></li>`;
            }
          }
          html += "</ul>";
        }
        html += "</li>";
      }
      html += "</ul>";
      html += "</div>";
    }

    container.innerHTML = html;

    // Wire up jump buttons
    for (const btn of container.querySelectorAll<HTMLButtonElement>(".thdocs-index__jump-btn")) {
      const letter = btn.dataset.letter;
      if (letter) {
        btn.addEventListener("click", () => {
          const section = document.getElementById(`thindex-${letter}`);
          if (section) section.scrollIntoView({ behavior: "smooth" });
        });
      }
    }
  }

  function esc(text: string): string {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
  }

  // Lazy-load when panel becomes visible
  const observer = new MutationObserver(() => {
    if (!indexPanel.hasAttribute("hidden")) loadIndex();
  });
  observer.observe(indexPanel, { attributes: true, attributeFilter: ["hidden"] });
}

function setupSidebarSearch(): void {
  const searchInput = document.querySelector<HTMLInputElement>("#thdocs-search-input");
  const searchPanel = document.querySelector<HTMLElement>('[data-panel="search"]');
  if (!searchInput || !searchPanel) return;

  let indexLoaded = false;

  function loadSearchIndex(): void {
    if (indexLoaded) return;
    const contentRoot = document.documentElement.dataset.content_root || "./";
    const script = document.createElement("script");
    script.src = contentRoot + "searchindex.js";
    script.onload = () => { indexLoaded = true; };
    document.body.appendChild(script);
  }

  const panelObserver = new MutationObserver(() => {
    if (!searchPanel.hasAttribute("hidden")) loadSearchIndex();
  });
  panelObserver.observe(searchPanel, { attributes: true, attributeFilter: ["hidden"] });

  let debounceTimer: number | undefined;
  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();
    const container = document.getElementById("search-results");
    if (!container) return;
    if (!query) {
      container.innerHTML = "";
      return;
    }
    debounceTimer = window.setTimeout(() => {
      container.innerHTML = "";
      if (Search.hasIndex()) {
        Search.performSearch(query);
      } else {
        Search.deferQuery(query);
        loadSearchIndex();
      }
    }, 200);
  });
}

declare const Search: {
  _index: unknown;
  hasIndex: () => boolean;
  performSearch: (query: string) => void;
  deferQuery: (query: string) => void;
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    wireSidebarTabs();
    setupScrollspy();
    setupMobileSidebar();
    setupSidebarSearch();
    setupSidebarIndex();
  });
} else {
  wireSidebarTabs();
  setupScrollspy();
  setupMobileSidebar();
  setupSidebarSearch();
  setupSidebarIndex();
}
