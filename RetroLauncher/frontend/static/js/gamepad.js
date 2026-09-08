// Spatial (grid-aware) focus navigation shared by keyboard and gamepad input,
// plus a Gamepad API poll loop that drives the same navigation functions.
(function () {
  const FOCUSABLE_SELECTOR = ".card, .nav-item, .btn, input, [data-nav]";
  const FOCUS_CLASS = "gamepad-focus";

  function isVisible(el) {
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }

  function getScope() {
    const modal = document.getElementById("modal-backdrop");
    if (modal && !modal.hidden) return modal;
    return document;
  }

  function getFocusable() {
    const scope = getScope();
    return Array.from(scope.querySelectorAll(FOCUSABLE_SELECTOR)).filter(
      (el) => isVisible(el) && !el.disabled
    );
  }

  function setFocus(el) {
    document
      .querySelectorAll("." + FOCUS_CLASS)
      .forEach((e) => e.classList.remove(FOCUS_CLASS));
    if (!el) return;
    el.classList.add(FOCUS_CLASS);
    el.focus({ preventScroll: false });
    if (el.scrollIntoView) el.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function currentFocused() {
    const scope = getScope();
    const active = document.activeElement;
    if (active && scope.contains(active) && active.matches(FOCUSABLE_SELECTOR)) {
      return active;
    }
    return null;
  }

  // Direction: "up" | "down" | "left" | "right"
  function moveFocus(direction) {
    const items = getFocusable();
    if (items.length === 0) return;

    const current = currentFocused() || items[0];
    if (!currentFocused()) {
      setFocus(current);
      return;
    }

    const from = current.getBoundingClientRect();
    const fromCenter = { x: from.left + from.width / 2, y: from.top + from.height / 2 };

    let best = null;
    let bestScore = Infinity;

    for (const el of items) {
      if (el === current) continue;
      const rect = el.getBoundingClientRect();
      const center = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
      const dx = center.x - fromCenter.x;
      const dy = center.y - fromCenter.y;

      let primary, perpendicular, aligned;
      if (direction === "up") {
        aligned = dy < -1;
        primary = -dy;
        perpendicular = Math.abs(dx);
      } else if (direction === "down") {
        aligned = dy > 1;
        primary = dy;
        perpendicular = Math.abs(dx);
      } else if (direction === "left") {
        aligned = dx < -1;
        primary = -dx;
        perpendicular = Math.abs(dy);
      } else {
        aligned = dx > 1;
        primary = dx;
        perpendicular = Math.abs(dy);
      }

      if (!aligned) continue;

      // Favor items close in the travel direction, penalize sideways drift.
      const score = primary + perpendicular * 2;
      if (score < bestScore) {
        bestScore = score;
        best = el;
      }
    }

    if (best) setFocus(best);
  }

  function activate() {
    const el = currentFocused();
    if (el) el.click();
  }

  function ensureInitialFocus() {
    if (!currentFocused()) {
      const items = getFocusable();
      if (items.length) setFocus(items[0]);
    }
  }

  const RetroNav = {
    moveFocus,
    activate,
    setFocus,
    getFocusable,
    ensureInitialFocus,
    onBack: null, // app.js assigns a handler (e.g. close modal)
  };
  window.RetroNav = RetroNav;

  // ---------------- Keyboard fallback (also drives spatial nav) ----------------

  document.addEventListener("keydown", (e) => {
    const tag = (document.activeElement && document.activeElement.tagName) || "";
    const typing = tag === "INPUT" || tag === "TEXTAREA";

    if (e.key === "/" && !typing) {
      const search = document.getElementById("search");
      if (search) {
        e.preventDefault();
        search.focus();
      }
      return;
    }

    if (typing && e.key !== "Escape") return;

    switch (e.key) {
      case "ArrowUp":
        e.preventDefault();
        moveFocus("up");
        break;
      case "ArrowDown":
        e.preventDefault();
        moveFocus("down");
        break;
      case "ArrowLeft":
        e.preventDefault();
        moveFocus("left");
        break;
      case "ArrowRight":
        e.preventDefault();
        moveFocus("right");
        break;
      case "Enter":
        activate();
        break;
      case "Escape":
        if (RetroNav.onBack) RetroNav.onBack();
        break;
    }
  });

  // ---------------- Gamepad API poll loop ----------------

  const AXIS_DEADZONE = 0.5;
  const REPEAT_DELAY_MS = 380; // delay before a held direction starts repeating
  const REPEAT_RATE_MS = 150;

  const BUTTON_A = 0;
  const BUTTON_B = 1;
  const DPAD_UP = 12;
  const DPAD_DOWN = 13;
  const DPAD_LEFT = 14;
  const DPAD_RIGHT = 15;

  let lastDirection = null;
  let lastDirectionAt = 0;
  let prevButtons = {};
  let connected = false;

  function setConnected(isConnected) {
    if (isConnected === connected) return;
    connected = isConnected;
    const dot = document.getElementById("gamepad-indicator");
    const label = document.getElementById("gamepad-status");
    if (dot) dot.classList.toggle("connected", isConnected);
    if (label) label.textContent = isConnected ? "Controller connected" : "No controller";
  }

  function readDirection(gp) {
    if (gp.buttons[DPAD_UP] && gp.buttons[DPAD_UP].pressed) return "up";
    if (gp.buttons[DPAD_DOWN] && gp.buttons[DPAD_DOWN].pressed) return "down";
    if (gp.buttons[DPAD_LEFT] && gp.buttons[DPAD_LEFT].pressed) return "left";
    if (gp.buttons[DPAD_RIGHT] && gp.buttons[DPAD_RIGHT].pressed) return "right";

    const x = gp.axes[0] || 0;
    const y = gp.axes[1] || 0;
    if (Math.abs(y) > Math.abs(x)) {
      if (y < -AXIS_DEADZONE) return "up";
      if (y > AXIS_DEADZONE) return "down";
    } else {
      if (x < -AXIS_DEADZONE) return "left";
      if (x > AXIS_DEADZONE) return "right";
    }
    return null;
  }

  function pollGamepads() {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    const gp = pads && pads[0];

    setConnected(!!gp);

    if (gp) {
      const now = performance.now();
      const direction = readDirection(gp);

      if (direction) {
        if (direction !== lastDirection) {
          moveFocus(direction);
          lastDirection = direction;
          lastDirectionAt = now;
        } else if (now - lastDirectionAt > REPEAT_DELAY_MS) {
          moveFocus(direction);
          lastDirectionAt = now - REPEAT_DELAY_MS + REPEAT_RATE_MS;
        }
      } else {
        lastDirection = null;
      }

      const aPressed = gp.buttons[BUTTON_A] && gp.buttons[BUTTON_A].pressed;
      if (aPressed && !prevButtons[BUTTON_A]) activate();
      prevButtons[BUTTON_A] = aPressed;

      const bPressed = gp.buttons[BUTTON_B] && gp.buttons[BUTTON_B].pressed;
      if (bPressed && !prevButtons[BUTTON_B] && RetroNav.onBack) RetroNav.onBack();
      prevButtons[BUTTON_B] = bPressed;
    }

    requestAnimationFrame(pollGamepads);
  }

  window.addEventListener("gamepadconnected", () => setConnected(true));
  window.addEventListener("gamepaddisconnected", () => setConnected(false));

  requestAnimationFrame(pollGamepads);
})();
