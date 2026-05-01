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
  });
} else {
  wireSidebarTabs();
  setupScrollspy();
}
