import "./main.css";

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

  const allLis = contentsPanel.querySelectorAll<HTMLElement>(
    "li.toctree-l1, li.toctree-l2, li.toctree-l3, li.toctree-l4"
  );

  // Find current page and its ancestors
  const currentAncestors = new Set<HTMLElement>();
  const currentLink = contentsPanel.querySelector<HTMLElement>(
    "a.reference.internal.current"
  );
  if (currentLink) {
    let ancestor: HTMLElement | null = currentLink.parentElement;
    while (ancestor && ancestor !== contentsPanel) {
      if (ancestor.tagName === "LI") {
        currentAncestors.add(ancestor);
      }
      ancestor = ancestor.parentElement;
    }
  }

  // Load persisted state from sessionStorage
  const persistedSet = new Set<string>();
  const persisted = sessionStorage.getItem("thdocs-toc-expanded");
  if (persisted) {
    try {
      const parsed = JSON.parse(persisted);
      if (Array.isArray(parsed)) {
        parsed.forEach((key) => persistedSet.add(key));
      }
    } catch {}
  }

  // Chevron SVG icon
  const chevronSvg =
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 4l4 4-4 4"/></svg>';

  // Make section captions (e.g. "User Guide", "Internals") collapsible
  const captions = contentsPanel.querySelectorAll<HTMLElement>("p.caption");
  for (const caption of captions) {
    const nextUl = caption.nextElementSibling as HTMLElement | null;
    if (!nextUl || nextUl.tagName !== "UL") continue;

    const key = caption.textContent || "";
    const shouldExpand = persistedSet.has(key);

    // Wrap caption + ul together
    const wrapper = document.createElement("div");
    wrapper.className = "thdocs-toc-section";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "thdocs-toc-toggle";
    btn.setAttribute("aria-label", "Toggle section");
    btn.innerHTML = chevronSvg;
    btn.setAttribute("aria-expanded", shouldExpand ? "true" : "false");

    // Insert wrapper before caption while caption is still in its original parent
    caption.parentElement!.insertBefore(wrapper, caption);

    const row = document.createElement("div");
    row.className = "thdocs-toc-row thdocs-toc-caption-row";
    row.appendChild(btn);
    row.appendChild(caption);

    wrapper.appendChild(row);
    wrapper.appendChild(nextUl);

    if (!shouldExpand) {
      nextUl.style.display = "none";
    }

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isExpanded = btn.getAttribute("aria-expanded") === "true";
      const newExpanded = !isExpanded;
      btn.setAttribute("aria-expanded", newExpanded ? "true" : "false");
      nextUl.style.display = newExpanded ? "" : "none";
      if (newExpanded) {
        persistedSet.add(key);
      } else {
        persistedSet.delete(key);
      }
      sessionStorage.setItem(
        "thdocs-toc-expanded",
        JSON.stringify(Array.from(persistedSet))
      );
    });
  }

  // Initialize toggles on each LI that has a child UL
  for (const li of allLis) {
    const childUl = li.querySelector<HTMLElement>(":scope > ul");
    if (!childUl) continue;

    const link = li.querySelector<HTMLAnchorElement>(":scope > a");
    if (!link) continue;

    // Create toggle button
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "thdocs-toc-toggle";
    btn.setAttribute("aria-label", "Toggle");
    btn.innerHTML = chevronSvg;

    // Determine if should be expanded
    const key = link.href;
    const shouldExpand =
      currentAncestors.has(li) || persistedSet.has(key);

    btn.setAttribute("aria-expanded", shouldExpand ? "true" : "false");

    // Create a flex row wrapper for toggle + link
    const row = document.createElement("div");
    row.className = "thdocs-toc-row";

    // Move the link into the row, and insert the row where the link was
    li.insertBefore(row, link);
    row.appendChild(btn);
    row.appendChild(link);

    // Wire toggle handler
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isExpanded = btn.getAttribute("aria-expanded") === "true";
      const newExpanded = !isExpanded;
      btn.setAttribute("aria-expanded", newExpanded ? "true" : "false");
      childUl.style.display = newExpanded ? "" : "none";

      // Persist to sessionStorage
      if (newExpanded) {
        persistedSet.add(key);
      } else {
        persistedSet.delete(key);
      }
      sessionStorage.setItem(
        "thdocs-toc-expanded",
        JSON.stringify(Array.from(persistedSet))
      );
    });

    // Apply initial collapsed state
    if (!shouldExpand) {
      childUl.style.display = "none";
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

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    wireSidebarTabs();
    setupScrollspy();
    setupToctreeCollapse();
    setupToctreeNavMemory();
    setupMobileSidebar();
  });
} else {
  wireSidebarTabs();
  setupScrollspy();
  setupToctreeCollapse();
  setupToctreeNavMemory();
  setupMobileSidebar();
}
