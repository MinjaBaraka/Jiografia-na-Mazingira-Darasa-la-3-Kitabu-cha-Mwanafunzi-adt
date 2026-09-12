(function () {
  "use strict";

  if (window.__adtIndependentMediaInstalled) return;
  window.__adtIndependentMediaInstalled = true;

  var mediaPrototype = window.HTMLMediaElement && window.HTMLMediaElement.prototype;
  if (!mediaPrototype) return;

  var nativePlay = mediaPrototype.play;
  var nativePause = mediaPrototype.pause;
  var observedNarrationAudios = new Set();
  var explicitVideoPauses = new WeakSet();

  function mediaSource(media) {
    return String(media.currentSrc || media.getAttribute("src") || media.src || "");
  }

  function isNarrationAudio(media) {
    return media instanceof window.HTMLAudioElement &&
      /\/content\/i18n\/[^/]+\/audio\//i.test(mediaSource(media));
  }

  function isSignLanguageVideo(media) {
    if (!(media instanceof window.HTMLVideoElement)) return false;
    if (/\/content\/i18n\/[^/]+\/video\//i.test(mediaSource(media))) return true;
    return Boolean(
      media.closest("[data-sign-language-player]") ||
      media.parentElement && media.parentElement.querySelector('[aria-label="Drag sign language video"]')
    );
  }

  function videoForCloseButton(target) {
    if (!(target instanceof window.Element)) return null;
    var button = target.closest("button");
    if (!button) return null;
    var player = button.closest("[data-sign-language-player]") || button.parentElement;
    var isDragHandle = button.matches('[aria-label="Drag sign language video"]') ||
      button.hasAttribute("data-sign-language-drag-handle");
    var video = player && player.querySelector && player.querySelector("video");
    return video && !isDragHandle && isSignLanguageVideo(video) ? video : null;
  }

  function narrationIsActive() {
    // play() sets paused=false while audio buffers. Keep protecting the video
    // until narration pauses or ends, regardless of how long loading takes.
    return Array.from(observedNarrationAudios).some(function (audio) {
      return !audio.paused && !audio.ended;
    });
  }

  function setPlaybackState(kind, state) {
    document.documentElement.setAttribute("data-" + kind + "-playback", state);
  }

  function observeNarrationAudio(audio) {
    if (observedNarrationAudios.has(audio)) return;
    observedNarrationAudios.add(audio);
    audio.addEventListener("play", function () { setPlaybackState("read-aloud", "starting"); });
    audio.addEventListener("playing", function () { setPlaybackState("read-aloud", "playing"); });
    audio.addEventListener("waiting", function () { setPlaybackState("read-aloud", "buffering"); });
    audio.addEventListener("pause", function () { setPlaybackState("read-aloud", "paused"); });
    audio.addEventListener("ended", function () { setPlaybackState("read-aloud", "ended"); });
    audio.addEventListener("error", function () { setPlaybackState("read-aloud", "error"); });
    audio.addEventListener("emptied", function () {
      if (!audio.getAttribute("src")) setPlaybackState("read-aloud", "stopped");
    });
  }

  mediaPrototype.play = function () {
    if (isNarrationAudio(this)) {
      observeNarrationAudio(this);
      setPlaybackState("read-aloud", "starting");
    }
    return nativePlay.apply(this, arguments);
  };

  mediaPrototype.pause = function () {
    if (
      isSignLanguageVideo(this) &&
      narrationIsActive() &&
      !explicitVideoPauses.has(this)
    ) {
      // The compiled reader pauses its video when TTS becomes active. Ignore
      // that arbitration; native video controls still use the browser's pause.
      return;
    }
    explicitVideoPauses.delete(this);
    // stopAndClear() immediately calls load(), which can cancel a queued
    // pause event. Keep the observed state accurate for that path as well.
    if (isNarrationAudio(this)) setPlaybackState("read-aloud", "paused");
    return nativePause.apply(this, arguments);
  };

  function allowExplicitVideoClose(event) {
    var video = videoForCloseButton(event.target);
    if (!video) return;
    explicitVideoPauses.add(video);
    // Scope permission to this player's current input event. Closing one
    // player must not let a later TTS start pause a newly opened player.
    window.setTimeout(function () { explicitVideoPauses.delete(video); }, 0);
  }

  window.addEventListener("pointerdown", allowExplicitVideoClose, true);
  window.addEventListener("click", allowExplicitVideoClose, true);
  window.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") allowExplicitVideoClose(event);
  }, true);

  window.addEventListener("play", function (event) {
    if (!isSignLanguageVideo(event.target)) return;
    event.target.setAttribute("data-independent-media-playback", "");
    setPlaybackState("sign-language", "playing");
    event.stopPropagation();
  }, true);

  window.addEventListener("pause", function (event) {
    if (isSignLanguageVideo(event.target)) setPlaybackState("sign-language", "paused");
  }, true);
  window.addEventListener("ended", function (event) {
    if (isSignLanguageVideo(event.target)) setPlaybackState("sign-language", "ended");
  }, true);

  document.documentElement.setAttribute("data-independent-media-playback", "");
})();
