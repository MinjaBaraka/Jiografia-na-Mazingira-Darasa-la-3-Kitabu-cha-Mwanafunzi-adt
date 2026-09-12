(function () {
  "use strict";

  if (window.__adtMobileSheetDragInstalled) return;
  window.__adtMobileSheetDragInstalled = true;

  var mobile = window.matchMedia("(max-width: 639px)");
  var sheets = new WeakMap();
  var scheduled = false;

  function restore(sheet, state) {
    state.pointerId = null;
    sheet.removeAttribute("data-mobile-sheet-dragging");
    sheet.style.removeProperty("--mobile-sheet-offset");
  }

  function closeSheet(sheet, handle) {
    if (!sheet.isConnected || !sheet.hasAttribute("data-open")) return;
    // Let the reader close its own dialog and restore focus. Dismissing a
    // menu must never change narration or sign-language playback state.
    handle.dispatchEvent(new KeyboardEvent("keydown", {
      key: "Escape", code: "Escape", bubbles: true, cancelable: true
    }));
  }

  function enhance(sheet) {
    if (sheets.has(sheet)) return;
    var handle = sheet.firstElementChild;
    if (!handle || handle.tagName !== "DIV" ||
        handle.getAttribute("aria-hidden") !== "true" ||
        !handle.nextElementSibling ||
        handle.nextElementSibling.getAttribute("data-slot") !== "sheet-title") return;

    var label = document.documentElement.lang.indexOf("sw") === 0
      ? "Buruta chini kufunga" : "Drag down to close";
    var state = { pointerId: null, startX: 0, startY: 0, dx: 0, dy: 0, moved: false };
    sheets.set(sheet, state);
    sheet.setAttribute("data-mobile-sheet-draggable", "");
    handle.setAttribute("data-mobile-sheet-drag-handle", "");
    handle.removeAttribute("aria-hidden");
    handle.setAttribute("role", "button");
    handle.setAttribute("tabindex", "0");
    handle.setAttribute("aria-label", label);
    handle.setAttribute("title", label);

    handle.addEventListener("pointerdown", function (event) {
      if (!mobile.matches || !event.isPrimary || event.button !== 0) return;
      state.pointerId = event.pointerId;
      state.startX = event.clientX;
      state.startY = event.clientY;
      state.dx = state.dy = 0;
      state.moved = false;
      handle.setPointerCapture(event.pointerId);
    });

    handle.addEventListener("pointermove", function (event) {
      if (state.pointerId !== event.pointerId) return;
      state.dx = Math.abs(event.clientX - state.startX);
      state.dy = Math.max(0, event.clientY - state.startY);
      state.moved = state.moved || state.dx > 6 || state.dy > 6;
      sheet.setAttribute("data-mobile-sheet-dragging", "");
      sheet.style.setProperty("--mobile-sheet-offset", state.dy + "px");
      event.preventDefault();
    });

    handle.addEventListener("pointerup", function (event) {
      if (state.pointerId !== event.pointerId) return;
      state.dx = Math.abs(event.clientX - state.startX);
      state.dy = Math.max(0, event.clientY - state.startY);
      state.moved = state.moved || state.dx > 6 || state.dy > 6;
      var threshold = Math.min(120, sheet.getBoundingClientRect().height / 4);
      var dismiss = state.dy >= threshold && state.dy > state.dx;
      restore(sheet, state);
      if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId);
      if (dismiss) closeSheet(sheet, handle);
    });

    function cancel(event) {
      if (state.pointerId !== event.pointerId) return;
      state.moved = true;
      restore(sheet, state);
    }
    handle.addEventListener("pointercancel", cancel);
    handle.addEventListener("lostpointercapture", cancel);

    handle.addEventListener("click", function (event) {
      if (state.moved && event.detail !== 0) {
        event.preventDefault();
        return;
      }
      closeSheet(sheet, handle);
    });
    handle.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      closeSheet(sheet, handle);
    });
  }

  function install() {
    scheduled = false;
    if (!mobile.matches) return;
    document.querySelectorAll('[data-slot="sheet-content"][data-side="bottom"]').forEach(enhance);
  }
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(install);
  }

  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  mobile.addEventListener("change", function () {
    document.querySelectorAll("[data-mobile-sheet-draggable]").forEach(function (sheet) {
      var state = sheets.get(sheet);
      if (state) restore(sheet, state);
    });
    schedule();
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", schedule, { once: true });
  else schedule();
})();
