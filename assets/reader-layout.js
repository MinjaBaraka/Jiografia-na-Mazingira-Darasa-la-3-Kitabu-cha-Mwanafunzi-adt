// Apply book-reading defaults and content-layout classes before ADT starts.
// Navigation itself is owned exclusively by the default ADT runtime.
(() => {
  try {
    localStorage.setItem("stateMode", "false")
    localStorage.setItem("easyReadMode", "false")
    localStorage.setItem("wordHighlightMode", "true")
  } catch {
    // Runtime defaults remain available in restricted file:// contexts.
  }

  const sectionId = document.querySelector('meta[name="title-id"]')?.content
  const content = document.getElementById("content")
  if (!content || !sectionId) return

  const sectionType = content.querySelector(":scope > section")?.dataset.sectionType
  const frontMatterTypes = new Set([
    "inside_cover",
    "table_of_contents",
    "credits",
    "foreword",
  ])

  // The spine distinguishes unnumbered front matter from textbook content.
  // This remains correct when sections are inserted, removed, or reordered.
  fetch("./content/pages.json")
    .then((response) => response.json())
    .then((pages) => {
      const entryIndex = pages.findIndex((entry) => entry.section_id === sectionId)
      if (entryIndex < 0) return

      if (sectionType === "front_cover") {
        content.classList.add("source-cover-page")
      } else if (frontMatterTypes.has(sectionType)) {
        content.classList.add("source-front-page")
      } else if (entryIndex > 0 && sectionType !== "cover") {
        content.classList.add("source-book-page")
      }
    })
    .catch(() => {
      // Base runtime still loads the semantic page if manifest lookup fails.
    })
})()
