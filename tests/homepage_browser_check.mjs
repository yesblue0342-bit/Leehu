#!/usr/bin/env node

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "laptop", width: 1366, height: 768 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "mobile", width: 390, height: 844 },
  { name: "small-mobile", width: 360, height: 800 },
];
const FIRST_PARTY_HOSTS = new Set(["127.0.0.1", "localhost"]);

function parseArgs(argv) {
  const options = {
    url: null,
    outputDir: resolve(ROOT, ".omx", "artifacts", "homepage-browser"),
    keepProfile: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--url") options.url = argv[++index];
    else if (value === "--output-dir") options.outputDir = resolve(argv[++index]);
    else if (value === "--keep-profile") options.keepProfile = true;
    else if (value === "--help") {
      console.log(
        "Usage: node tests/homepage_browser_check.mjs " +
        "[--url http://127.0.0.1:PORT/] [--output-dir PATH]",
      );
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${value}`);
    }
  }
  return options;
}

function findChrome() {
  const configured = process.env.CHROME_PATH;
  const candidates = process.platform === "win32"
    ? [
        configured,
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
      ]
    : [
        configured,
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
      ];
  const executable = candidates.find((candidate) => candidate && existsSync(candidate));
  if (!executable) {
    throw new Error("Chrome/Edge was not found. Set CHROME_PATH to an installed executable.");
  }
  return executable;
}

async function freePort() {
  return new Promise((resolvePort, reject) => {
    const server = createServer();
    server.unref();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolvePort(address.port));
    });
  });
}

async function waitForHttp(url, timeoutMs = 15_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1_000) });
      if (response.ok) return response;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  }
  throw new Error(`Timed out waiting for ${url}: ${lastError?.message || "unknown error"}`);
}

async function cleanupDirectory(path) {
  try {
    await rm(path, { recursive: true, force: true, maxRetries: 8, retryDelay: 250 });
  } catch (error) {
    console.warn(`WARN: temporary directory cleanup deferred (${path}): ${error.message}`);
  }
}

async function startLocalServer() {
  const port = await freePort();
  const dataRoot = await mkdtemp(join(tmpdir(), "leehu-browser-data-"));
  const python = process.platform === "win32" ? "python" : "python3";
  const child = spawn(python, ["server.py"], {
    cwd: ROOT,
    env: {
      ...process.env,
      PORT: String(port),
      BOARD_POSTS_DIR: join(dataRoot, "board"),
      LITERATURE_POSTS_DIR: join(dataRoot, "literature"),
    },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  let closing = false;
  const output = [];
  child.stdout.on("data", (chunk) => output.push(chunk.toString()));
  child.stderr.on("data", (chunk) => output.push(chunk.toString()));
  child.once("exit", (code) => {
    if (!closing && code && output.length) {
      process.stderr.write(`Local server exited ${code}: ${output.join("").slice(-2000)}\n`);
    }
  });
  const url = `http://127.0.0.1:${port}/`;
  try {
    await waitForHttp(url);
  } catch (error) {
    child.kill();
    await cleanupDirectory(dataRoot);
    throw error;
  }
  return {
    url,
    async close() {
      closing = true;
      await terminateProcessTree(child);
      await cleanupDirectory(dataRoot);
    },
  };
}

async function terminateProcessTree(child) {
  if (!child || child.exitCode !== null || !child.pid) return;
  if (process.platform === "win32") {
    await new Promise((resolveExit) => {
      const killer = spawn(
        "taskkill.exe",
        ["/PID", String(child.pid), "/T", "/F"],
        { stdio: "ignore", windowsHide: true },
      );
      killer.once("exit", resolveExit);
      killer.once("error", resolveExit);
      setTimeout(resolveExit, 3_000);
    });
  } else {
    child.kill("SIGTERM");
    await new Promise((resolveExit) => {
      child.once("exit", resolveExit);
      setTimeout(() => {
        if (child.exitCode === null) child.kill("SIGKILL");
        resolveExit();
      }, 2_000);
    });
  }
  child.stdout?.destroy();
  child.stderr?.destroy();
}

class Cdp {
  constructor(webSocketUrl) {
    this.socket = new WebSocket(webSocketUrl);
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = new Map();
  }

  async connect() {
    await new Promise((resolveOpen, reject) => {
      this.socket.addEventListener("open", resolveOpen, { once: true });
      this.socket.addEventListener("error", reject, { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id) {
        const request = this.pending.get(message.id);
        if (!request) return;
        this.pending.delete(message.id);
        if (message.error) request.reject(new Error(message.error.message));
        else request.resolve(message.result);
        return;
      }
      for (const listener of this.listeners.get(message.method) || []) {
        listener(message.params || {});
      }
    });
    return this;
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolveRequest, reject) => {
      this.pending.set(id, { resolve: resolveRequest, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  on(method, listener) {
    const listeners = this.listeners.get(method) || [];
    listeners.push(listener);
    this.listeners.set(method, listeners);
    return () => {
      this.listeners.set(method, (this.listeners.get(method) || []).filter(
        (candidate) => candidate !== listener,
      ));
    };
  }

  waitFor(method, timeoutMs = 15_000) {
    return new Promise((resolveEvent, reject) => {
      let remove = () => {};
      const timer = setTimeout(() => {
        remove();
        reject(new Error(`Timed out waiting for CDP event ${method}`));
      }, timeoutMs);
      remove = this.on(method, (params) => {
        clearTimeout(timer);
        remove();
        resolveEvent(params);
      });
    });
  }

  close() {
    this.socket.close();
  }
}

async function startChrome(executable) {
  const debuggingPort = await freePort();
  const profileDir = await mkdtemp(join(tmpdir(), "leehu-chrome-"));
  const child = spawn(executable, [
    "--headless=new",
    `--remote-debugging-port=${debuggingPort}`,
    `--user-data-dir=${profileDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-sync",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-features=Translate,MediaRouter",
    "--force-color-profile=srgb",
    "--mute-audio",
    "about:blank",
  ], {
    stdio: "ignore",
    windowsHide: true,
  });
  const endpoint = `http://127.0.0.1:${debuggingPort}`;
  await waitForHttp(`${endpoint}/json/version`);
  const targetResponse = await fetch(`${endpoint}/json/new?about:blank`, { method: "PUT" });
  if (!targetResponse.ok) throw new Error(`Could not create Chrome target: ${targetResponse.status}`);
  const target = await targetResponse.json();
  const cdp = await new Cdp(target.webSocketDebuggerUrl).connect();
  return {
    cdp,
    profileDir,
    async close(keepProfile = false) {
      cdp.close();
      await terminateProcessTree(child);
      if (!keepProfile) await cleanupDirectory(profileDir);
    },
  };
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  });
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || "Runtime.evaluate failed");
  }
  return result.result?.value;
}

async function navigate(cdp, url) {
  const loaded = cdp.waitFor("Page.loadEventFired");
  await cdp.send("Page.navigate", { url });
  await loaded;
  await evaluate(cdp, `
    new Promise(resolve => {
      const done = () => requestAnimationFrame(() => requestAnimationFrame(resolve));
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(done, done);
      else done();
    })
  `);
}

function pageMetricsExpression(width) {
  return `(() => {
    const visible = element => {
      if (!element) return false;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" &&
        Number(style.opacity) > 0 && rect.width > 0 && rect.height > 0;
    };
    const detail = selector => {
      const element = document.querySelector(selector);
      if (!element) return { selector, exists:false, visible:false, width:0, height:0 };
      const rect = element.getBoundingClientRect();
      return {
        selector, exists:true, visible:visible(element),
        width:Math.round(rect.width * 100) / 100,
        height:Math.round(rect.height * 100) / 100,
        top:Math.round(rect.top * 100) / 100,
        left:Math.round(rect.left * 100) / 100,
      };
    };
    const required = [
      ".hero h1",
      '.hero-actions a[href="#works"]',
      '.hero-actions a[href="#about"]',
      ${width <= 768 ? '"#mobileNavToggle"' : '"#primaryNav"'}
    ];
    const touchSelectors = ${width <= 768 ? JSON.stringify([
      "#mobileNavToggle",
      '.hero-actions a[href="#works"]',
      '.hero-actions a[href="#about"]',
      "#stellaButton",
    ]) : "[]"};
    const controls = ${width <= 768 ? '["#mobileNavToggle", "#stellaButton"].map(detail)' : "[]"};
    const controlsOverlap = controls.length === 2 &&
      controls.every(item => item.visible) &&
      !(
        controls[0].left + controls[0].width <= controls[1].left ||
        controls[1].left + controls[1].width <= controls[0].left ||
        controls[0].top + controls[0].height <= controls[1].top ||
        controls[1].top + controls[1].height <= controls[0].top
      );
    return {
      viewportWidth:document.documentElement.clientWidth,
      scrollWidth:document.documentElement.scrollWidth,
      overflow:document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      required:required.map(detail),
      touchTargets:touchSelectors.map(detail).filter(item => item.visible),
      controls,
      controlsOverlap,
      staticImageCount:document.querySelectorAll("body > img, main img, header img, footer img").length,
    };
  })()`;
}

async function inspectKeyboardNavigation(cdp) {
  await evaluate(cdp, `document.activeElement?.blur()`);
  const stops = [];
  for (let index = 0; index < 24; index += 1) {
    await cdp.send("Input.dispatchKeyEvent", {
      type: "keyDown",
      key: "Tab",
      code: "Tab",
      windowsVirtualKeyCode: 9,
    });
    await cdp.send("Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "Tab",
      code: "Tab",
      windowsVirtualKeyCode: 9,
    });
    stops.push(await evaluate(cdp, `(() => {
      const active = document.activeElement;
      if (!active) return "";
      return active.id || active.getAttribute("href") || active.tagName.toLowerCase();
    })()`));
  }
  return {
    stops,
    reachesStella:stops.includes("stellaButton"),
    reachesWorks:stops.includes("#works"),
    reachesAbout:stops.includes("#about"),
  };
}

async function inspectStella(cdp, seeded) {
  await evaluate(cdp, `
    (() => {
      const button = document.getElementById("stellaButton");
      if (!button) throw new Error("Missing #stellaButton");
      button.click();
    })()
  `);
  await new Promise((resolveWait) => setTimeout(resolveWait, 150));
  const opened = await evaluate(cdp, `(() => {
    const visible = element => {
      if (!element) return false;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" &&
        Number(style.opacity) > 0 && rect.width > 0 && rect.height > 0;
    };
    const panel = document.getElementById("stella");
    const auth = document.getElementById("authScreen");
    const app = document.getElementById("stellaApp");
    const close = document.getElementById(${seeded ? '"closeStellaBtn"' : '"closeStellaAuthBtn"'});
    const rect = close?.getBoundingClientRect();
    return {
      panelVisible:visible(panel),
      authVisible:visible(auth),
      appVisible:visible(app),
      expanded:document.getElementById("stellaButton")?.getAttribute("aria-expanded"),
      dialogRole:panel?.getAttribute("role"),
      ariaModal:panel?.getAttribute("aria-modal"),
      homepageInert:document.getElementById("homepageMain")?.hasAttribute("inert") || false,
      navigationInert:document.querySelector(".site-nav")?.hasAttribute("inert") || false,
      userName:document.getElementById("userName")?.textContent?.trim() || "",
      closeTouchTarget:rect ? { width:rect.width, height:rect.height } : null,
    };
  })()`);
  await evaluate(cdp, `document.getElementById(${seeded ? '"closeStellaBtn"' : '"closeStellaAuthBtn"'})?.click()`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  const closed = await evaluate(cdp, `(() => ({
    panelVisible:(() => {
      const panel = document.getElementById("stella");
      if (!panel) return false;
      const style = getComputedStyle(panel);
      const rect = panel.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" &&
        Number(style.opacity) > 0 && rect.width > 0 && rect.height > 0;
    })(),
    expanded:document.getElementById("stellaButton")?.getAttribute("aria-expanded"),
    focusReturned:document.activeElement?.id === "stellaButton",
    homepageInert:document.getElementById("homepageMain")?.hasAttribute("inert") || false,
    navigationInert:document.querySelector(".site-nav")?.hasAttribute("inert") || false,
    currentUser:localStorage.getItem("stella_current_user_v3"),
  }))()`);
  return { seeded, opened, closed };
}

async function seedCompatibleSession(cdp) {
  return evaluate(cdp, `(() => {
    const user = { name:"브라우저 검증", email:"browser-check@example.invalid" };
    localStorage.setItem("stella_current_user_v3", JSON.stringify(user));
    localStorage.setItem("stella_rooms_v3", JSON.stringify([{
      id:"room_browser_check", owner:user.email, projectId:null,
      name:"상태 복원 검증", messages:[{ role:"ai", text:"저장 상태" }]
    }]));
    localStorage.setItem("stella_projects_v1", JSON.stringify([]));
    localStorage.setItem("stella_posts_v3", JSON.stringify([]));
    return true;
  })()`);
}

async function inspectLegacyLogin(cdp) {
  const credentials = {
    email: "legacy-browser-check@example.invalid",
    password: "browser-password",
  };
  await evaluate(cdp, `(async () => {
    const password = ${JSON.stringify(credentials.password)};
    const digest = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(password),
    );
    const passwordHash = Array.from(new Uint8Array(digest))
      .map(value => value.toString(16).padStart(2, "0"))
      .join("");
    localStorage.removeItem("stella_current_user_v3");
    localStorage.setItem("stella_users_v3", JSON.stringify([{
      name:"기존 사용자",
      email:${JSON.stringify(credentials.email)},
      passwordHash,
      createdAt:"2024-01-01T00:00:00.000Z",
    }]));
    document.getElementById("stellaButton")?.click();
  })()`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  await evaluate(cdp, `(() => {
    const email = document.getElementById("authEmail");
    const password = document.getElementById("authPassword");
    email.value = ${JSON.stringify(credentials.email)};
    password.value = ${JSON.stringify(credentials.password)};
    email.dispatchEvent(new Event("input", { bubbles:true }));
    password.dispatchEvent(new Event("input", { bubbles:true }));
    document.getElementById("authForm")?.requestSubmit();
  })()`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 250));
  const result = await evaluate(cdp, `(() => {
    const users = JSON.parse(localStorage.getItem("stella_users_v3") || "[]");
    const current = JSON.parse(localStorage.getItem("stella_current_user_v3") || "null");
    const expectedHash = btoa(unescape(encodeURIComponent(${JSON.stringify(credentials.password)})));
    const panel = document.getElementById("stella");
    const app = document.getElementById("stellaApp");
    return {
      panelVisible:!!panel && getComputedStyle(panel).display !== "none",
      appVisible:!!app && getComputedStyle(app).display !== "none",
      currentEmail:current?.email || "",
      passwordMigrated:users[0]?.passwordHash === expectedHash,
    };
  })()`);
  await evaluate(cdp, `document.getElementById("closeStellaBtn")?.click()`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  return result;
}

async function inspectSignup(cdp) {
  const email = "signup-browser-check@example.invalid";
  await evaluate(cdp, `(() => {
    localStorage.removeItem("stella_current_user_v3");
    localStorage.setItem("stella_users_v3", "[]");
    document.getElementById("stellaButton")?.click();
    document.getElementById("signupTab")?.click();
    document.getElementById("authName").value = "신규 사용자";
    document.getElementById("authEmail").value = ${JSON.stringify(email)};
    document.getElementById("authPassword").value = "new-browser-password";
    document.getElementById("authForm")?.requestSubmit();
  })()`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 250));
  const result = await evaluate(cdp, `(() => {
    const users = JSON.parse(localStorage.getItem("stella_users_v3") || "[]");
    const current = JSON.parse(localStorage.getItem("stella_current_user_v3") || "null");
    const app = document.getElementById("stellaApp");
    return {
      appVisible:!!app && getComputedStyle(app).display !== "none",
      currentEmail:current?.email || "",
      userStored:users.some(user =>
        user.email === ${JSON.stringify(email)} &&
        user.name === "신규 사용자" &&
        typeof user.passwordHash === "string" &&
        user.passwordHash.length > 0
      ),
    };
  })()`);
  await evaluate(cdp, `document.getElementById("closeStellaBtn")?.click()`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  return result;
}

async function inspectEscapeClose(cdp) {
  await evaluate(cdp, `document.getElementById("stellaButton")?.click()`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyDown",
    key: "Escape",
    code: "Escape",
    windowsVirtualKeyCode: 27,
  });
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyUp",
    key: "Escape",
    code: "Escape",
    windowsVirtualKeyCode: 27,
  });
  await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  return evaluate(cdp, `(() => ({
    panelActive:document.getElementById("stella")?.classList.contains("active") || false,
    expanded:document.getElementById("stellaButton")?.getAttribute("aria-expanded"),
    focusReturned:document.activeElement?.id === "stellaButton",
    homepageInert:document.getElementById("homepageMain")?.hasAttribute("inert") || false,
  }))()`);
}

async function inspectBoard(cdp) {
  await evaluate(cdp, `location.hash = "#board"`);
  await new Promise((resolveWait) => setTimeout(resolveWait, 350));
  const result = await evaluate(cdp, `(() => {
    const panel = document.querySelector(".board-panel");
    const search = document.getElementById("publicBoardSearch");
    const status = document.getElementById("publicBoardStatus");
    const rect = panel?.getBoundingClientRect();
    return {
      panelVisible:!!panel && getComputedStyle(panel).display !== "none" &&
        rect.width > 0 && rect.height > 0,
      searchVisible:!!search && search.getBoundingClientRect().width > 0,
      statusText:status?.textContent?.trim() || "",
      overflow:document.documentElement.scrollWidth >
        document.documentElement.clientWidth + 1,
    };
  })()`);
  await evaluate(cdp, `history.replaceState(null, "", location.pathname + location.search)`);
  return result;
}

async function inspectMobileNavigation(cdp, width) {
  if (width > 768) return { applicable: false };
  const opened = await evaluate(cdp, `(() => {
    const toggle = document.getElementById("mobileNavToggle");
    toggle?.click();
    const nav = document.getElementById("primaryNav");
    const rect = nav?.getBoundingClientRect();
    return {
      expanded:toggle?.getAttribute("aria-expanded"),
      navVisible:!!nav && getComputedStyle(nav).display !== "none" &&
        rect.width > 0 && rect.height > 0,
    };
  })()`);
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyDown",
    key: "Escape",
    code: "Escape",
    windowsVirtualKeyCode: 27,
  });
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyUp",
    key: "Escape",
    code: "Escape",
    windowsVirtualKeyCode: 27,
  });
  const escapeClosed = await evaluate(cdp, `(() => ({
    expanded:document.getElementById("mobileNavToggle")?.getAttribute("aria-expanded"),
    navOpen:document.getElementById("primaryNav")?.classList.contains("mobile-open") || false,
    focusReturned:document.activeElement?.id === "mobileNavToggle",
  }))()`);
  const closed = await evaluate(cdp, `(() => {
    document.getElementById("mobileNavToggle")?.click();
    document.querySelector('#primaryNav a[href="#about"]')?.click();
    const toggle = document.getElementById("mobileNavToggle");
    const nav = document.getElementById("primaryNav");
    return {
      expanded:toggle?.getAttribute("aria-expanded"),
      navOpen:nav?.classList.contains("mobile-open") || false,
    };
  })()`);
  return { applicable: true, opened, escapeClosed, closed };
}

async function screenshot(cdp, path) {
  const result = await cdp.send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
    fromSurface: true,
  });
  await writeFile(path, Buffer.from(result.data, "base64"));
}

function firstParty(url, baseUrl) {
  try {
    const parsed = new URL(url, baseUrl);
    return FIRST_PARTY_HOSTS.has(parsed.hostname) ||
      parsed.origin === new URL(baseUrl).origin;
  } catch {
    return true;
  }
}

async function safeHttpChecks(baseUrl) {
  const checks = [];
  for (const path of ["/", "/robots.txt", "/sitemap.xml", "/literature/", "/api/board/posts?q=browser-check-no-match"]) {
    try {
      const response = await fetch(new URL(path, baseUrl), {
        headers: { Accept: path.includes("/api/") ? "application/json" : "*/*" },
        signal: AbortSignal.timeout(10_000),
      });
      checks.push({
        path,
        status: response.status,
        contentType: response.headers.get("content-type") || "",
        ok: response.ok,
      });
    } catch (error) {
      checks.push({ path, status: null, contentType: "", ok: false, error: error.message });
    }
  }
  return checks;
}

function validateReport(report) {
  const failures = [];
  for (const check of report.http) {
    if (!check.ok) failures.push(`HTTP ${check.path}: ${check.status || check.error}`);
  }
  for (const viewport of report.viewports) {
    if (viewport.metrics.overflow) failures.push(`${viewport.name}: document overflow`);
    if (viewport.metrics.staticImageCount !== 0) {
      failures.push(`${viewport.name}: static person/image surface exists`);
    }
    for (const item of viewport.metrics.required) {
      if (!item.exists || !item.visible) failures.push(`${viewport.name}: hidden ${item.selector}`);
    }
    for (const target of viewport.metrics.touchTargets) {
      if (target.width < 44 || target.height < 44) {
        failures.push(
          `${viewport.name}: touch target ${target.selector} is ` +
          `${target.width}x${target.height}`,
        );
      }
    }
    if (viewport.metrics.controlsOverlap) {
      failures.push(`${viewport.name}: mobile menu and Stella controls overlap`);
    }
    if (!viewport.keyboard.reachesStella ||
        !viewport.keyboard.reachesWorks ||
        !viewport.keyboard.reachesAbout) {
      failures.push(`${viewport.name}: keyboard navigation did not reach key controls`);
    }
    if (!viewport.board.panelVisible || !viewport.board.searchVisible || viewport.board.overflow) {
      failures.push(`${viewport.name}: board read/search layout failed`);
    }
    if (viewport.mobileNavigation.applicable &&
        (!viewport.mobileNavigation.opened.navVisible ||
         viewport.mobileNavigation.opened.expanded !== "true" ||
         viewport.mobileNavigation.escapeClosed.navOpen ||
         viewport.mobileNavigation.escapeClosed.expanded !== "false" ||
         !viewport.mobileNavigation.escapeClosed.focusReturned ||
         viewport.mobileNavigation.closed.navOpen ||
         viewport.mobileNavigation.closed.expanded !== "false")) {
      failures.push(`${viewport.name}: mobile navigation open/close contract failed`);
    }
    const anonymous = viewport.stella.anonymous;
    if (!anonymous.opened.panelVisible || !anonymous.opened.authVisible ||
        anonymous.opened.appVisible || anonymous.opened.expanded !== "true" ||
        anonymous.opened.dialogRole !== "dialog" ||
        anonymous.opened.ariaModal !== "true" ||
        !anonymous.opened.homepageInert || !anonymous.opened.navigationInert) {
      failures.push(`${viewport.name}: anonymous Stella entry did not show auth`);
    }
    if (anonymous.closed.panelVisible || anonymous.closed.expanded !== "false" ||
        !anonymous.closed.focusReturned || anonymous.closed.homepageInert ||
        anonymous.closed.navigationInert) {
      failures.push(`${viewport.name}: Stella close/focus contract failed`);
    }
    const seeded = viewport.stella.seeded;
    if (!seeded.opened.panelVisible || seeded.opened.authVisible ||
        !seeded.opened.appVisible || seeded.opened.userName !== "브라우저 검증") {
      failures.push(`${viewport.name}: seeded Stella session was not restored`);
    }
    if (seeded.closed.currentUser === null) {
      failures.push(`${viewport.name}: Stella close removed stored current user`);
    }
    const legacyLogin = viewport.stella.legacyLogin;
    if (!legacyLogin.panelVisible || !legacyLogin.appVisible ||
        legacyLogin.currentEmail !== "legacy-browser-check@example.invalid" ||
        !legacyLogin.passwordMigrated) {
      failures.push(`${viewport.name}: legacy Stella login compatibility failed`);
    }
    const signup = viewport.stella.signup;
    if (!signup.appVisible ||
        signup.currentEmail !== "signup-browser-check@example.invalid" ||
        !signup.userStored) {
      failures.push(`${viewport.name}: Stella signup flow failed`);
    }
    const escapeClose = viewport.stella.escapeClose;
    if (escapeClose.panelActive || escapeClose.expanded !== "false" ||
        !escapeClose.focusReturned || escapeClose.homepageInert) {
      failures.push(`${viewport.name}: Stella Escape close contract failed`);
    }
    if (viewport.width <= 768) {
      const closeTarget = seeded.opened.closeTouchTarget;
      if (!closeTarget || closeTarget.width < 44 || closeTarget.height < 44) {
        failures.push(`${viewport.name}: Stella close target is below 44x44`);
      }
    }
    for (const error of viewport.firstPartyErrors) {
      failures.push(`${viewport.name}: ${error.kind}: ${error.message}`);
    }
  }
  return failures;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  await mkdir(options.outputDir, { recursive: true });
  let localServer = null;
  let chrome = null;
  try {
    if (!options.url) localServer = await startLocalServer();
    const baseUrl = new URL(options.url || localServer.url).toString();
    const report = {
      generatedAt: new Date().toISOString(),
      baseUrl,
      chrome: basename(findChrome()),
      http: await safeHttpChecks(baseUrl),
      viewports: [],
    };
    chrome = await startChrome(findChrome());
    const { cdp } = chrome;
    await Promise.all([
      cdp.send("Page.enable"),
      cdp.send("Runtime.enable"),
      cdp.send("Log.enable"),
      cdp.send("Network.enable"),
    ]);

    let activeErrors = [];
    cdp.on("Runtime.exceptionThrown", ({ exceptionDetails }) => {
      activeErrors.push({
        kind: "exception",
        message: exceptionDetails?.exception?.description ||
          exceptionDetails?.text || "Uncaught exception",
        url: exceptionDetails?.url || baseUrl,
      });
    });
    cdp.on("Runtime.consoleAPICalled", ({ type, args }) => {
      if (type !== "error" && type !== "assert") return;
      activeErrors.push({
        kind: `console.${type}`,
        message: args?.map((arg) => arg.value || arg.description || "").join(" "),
        url: baseUrl,
      });
    });
    cdp.on("Log.entryAdded", ({ entry }) => {
      if (entry?.level !== "error") return;
      activeErrors.push({
        kind: "log.error",
        message: entry.text || "Browser log error",
        url: entry.url || baseUrl,
      });
    });
    cdp.on("Network.loadingFailed", (failure) => {
      if (failure.canceled || failure.blockedReason === "inspector") return;
      activeErrors.push({
        kind: "resource",
        message: failure.errorText || "Network loading failed",
        url: failure.url || "",
      });
    });

    for (const viewport of VIEWPORTS) {
      activeErrors = [];
      await cdp.send("Emulation.setDeviceMetricsOverride", {
        width: viewport.width,
        height: viewport.height,
        deviceScaleFactor: 1,
        mobile: viewport.width <= 768,
        screenWidth: viewport.width,
        screenHeight: viewport.height,
      });
      await cdp.send("Network.clearBrowserCache");
      console.log(`Checking ${viewport.name} ${viewport.width}x${viewport.height}...`);
      await navigate(cdp, `${baseUrl}?browser-check=${viewport.name}`);
      await evaluate(cdp, `localStorage.clear()`);
      await navigate(cdp, `${baseUrl}?browser-check=${viewport.name}-anonymous`);
      const metrics = await evaluate(cdp, pageMetricsExpression(viewport.width));
      const keyboard = await inspectKeyboardNavigation(cdp);
      const anonymous = await inspectStella(cdp, false);
      const legacyLogin = await inspectLegacyLogin(cdp);
      const signup = await inspectSignup(cdp);
      const escapeClose = await inspectEscapeClose(cdp);
      await seedCompatibleSession(cdp);
      await navigate(cdp, `${baseUrl}?browser-check=${viewport.name}-seeded`);
      const seeded = await inspectStella(cdp, true);
      const mobileNavigation = await inspectMobileNavigation(cdp, viewport.width);
      await evaluate(cdp, `(() => {
        history.replaceState(null, "", location.pathname + location.search);
        document.body.classList.remove("board-mode");
        document.getElementById("primaryNav")?.classList.remove("mobile-open");
        const toggle = document.getElementById("mobileNavToggle");
        toggle?.setAttribute("aria-expanded", "false");
        window.scrollTo(0, 0);
      })()`);
      const screenshotPath = join(options.outputDir, `${viewport.name}.png`);
      await screenshot(cdp, screenshotPath);
      const board = await inspectBoard(cdp);
      const boardScreenshotPath = join(options.outputDir, `${viewport.name}-board.png`);
      await screenshot(cdp, boardScreenshotPath);
      await evaluate(cdp, `history.replaceState(null, "", location.pathname + location.search)`);
      const firstPartyErrors = activeErrors.filter((error) => {
        if (!firstParty(error.url, baseUrl)) return false;
        try {
          return new URL(error.url, baseUrl).pathname !== "/favicon.ico";
        } catch {
          return true;
        }
      });
      const thirdPartyErrors = activeErrors.filter((error) => !firstParty(error.url, baseUrl));
      report.viewports.push({
        ...viewport,
        metrics,
        keyboard,
        board,
        mobileNavigation,
        stella: { anonymous, legacyLogin, signup, escapeClose, seeded },
        firstPartyErrors,
        thirdPartyErrors,
        screenshot: screenshotPath,
        boardScreenshot: boardScreenshotPath,
      });
    }

    report.failures = validateReport(report);
    const reportPath = join(options.outputDir, "report.json");
    await writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    for (const viewport of report.viewports) {
      console.log(
        `${viewport.name.padEnd(12)} ${viewport.width}x${viewport.height} ` +
        `overflow=${viewport.metrics.overflow ? "FAIL" : "PASS"} ` +
        `firstPartyErrors=${viewport.firstPartyErrors.length} ` +
        `screenshot=${viewport.screenshot}`,
      );
    }
    console.log(`HTTP safe-read: ${report.http.filter((item) => item.ok).length}/${report.http.length}`);
    console.log(`Report: ${reportPath}`);
    if (report.failures.length) {
      for (const failure of report.failures) console.error(`FAIL: ${failure}`);
      process.exitCode = 1;
    } else {
      console.log("PASS: five-viewport homepage browser contract");
    }
  } finally {
    if (chrome) await chrome.close(options.keepProfile);
    if (localServer) await localServer.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
