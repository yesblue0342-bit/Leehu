(() => {
  document.querySelectorAll("[data-reader-nav]").forEach((nav) => {
    const button = nav.querySelector(".nav-toggle");
    const links = nav.querySelector(".nav-links");
    if (!button || !links || nav.hasAttribute("data-nav-ready")) return;
    const label = button.querySelector(".nav-toggle-label");
    const setOpen = (open) => {
      button.setAttribute("aria-expanded", String(open));
      button.setAttribute("aria-label", open ? "전체 메뉴 닫기" : "전체 메뉴 열기");
      label.textContent = open ? "닫기" : "메뉴";
    };
    button.addEventListener("click", () => setOpen(button.getAttribute("aria-expanded") !== "true"));
    links.addEventListener("click", (event) => {
      if (event.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && button.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        button.focus();
      }
    });
    document.addEventListener("click", (event) => {
      if (!nav.contains(event.target)) setOpen(false);
    });
    window.matchMedia("(max-width: 1024px)").addEventListener("change", () => setOpen(false));
    const currentPath = window.location.pathname.replace(/index\.html$/, "");
    links.querySelectorAll("a").forEach((link) => {
      const url = new URL(link.href, window.location.origin);
      if (!url.hash && url.pathname === currentPath) link.setAttribute("aria-current", "page");
    });
    button.hidden = false;
    nav.setAttribute("data-nav-ready", "");
  });
})();
