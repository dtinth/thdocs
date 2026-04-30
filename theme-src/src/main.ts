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

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => wireSidebarTabs());
} else {
  wireSidebarTabs();
}
