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

  // Initialize toggles on each LI that has a child UL
  for (const li of allLis) {
    const childUl = li.querySelector<HTMLElement>(":scope > ul");
    if (!childUl) continue;

    // Create toggle button
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "thdocs-toc-toggle";
    btn.setAttribute("aria-label", "Toggle");

    // Determine if should be expanded
    const link = li.querySelector<HTMLElement>("a");
    const key = link ? link.href : li.textContent || "";
    const shouldExpand =
      currentAncestors.has(li) || persistedSet.has(key);

    btn.setAttribute("aria-expanded", shouldExpand ? "true" : "false");

    // Insert button before the link
    const firstChild = li.firstChild;
    if (firstChild) {
      li.insertBefore(btn, firstChild);
    } else {
      li.insertBefore(btn, childUl);
    }

    // Wire toggle handler
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isExpanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", isExpanded ? "false" : "true");

      // Persist to sessionStorage
      const newExpanded = !isExpanded;
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

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    wireSidebarTabs();
    setupScrollspy();
    setupToctreeCollapse();
  });
} else {
  wireSidebarTabs();
  setupScrollspy();
  setupToctreeCollapse();
}
