/*
 * Make image descriptions part of Read Aloud from a learner's first visit.
 * The reader remembers a learner's later choice in localStorage, so turning
 * the option off in Settings still works normally.
 */
(function () {
  try {
    // Apply this new book default once, including for learners who opened an
    // earlier version before image narration was enabled. Afterwards their
    // Settings choice remains untouched.
    if (localStorage.getItem("imageNarrationDefault") !== "v1") {
      localStorage.setItem("describeImagesMode", "true");
      localStorage.setItem("imageNarrationDefault", "v1");
    }
  } catch (_) {
    // The reader continues with its built-in setting when storage is blocked.
  }
})();
