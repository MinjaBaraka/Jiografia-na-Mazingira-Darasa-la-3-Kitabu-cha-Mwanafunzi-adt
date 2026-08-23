// Synchronize the visible book TOC with the current ADT reading-order spine.
// Section IDs are stable content destinations; positions and hrefs are derived.
(() => {
  const links = [...document.querySelectorAll("[data-toc-section]")]
  if (links.length === 0) return

  Promise.all([
    fetch("./content/pages.json").then((response) => response.json()),
    fetch("./content/toc.json").then((response) => response.json()),
  ])
    .then(([pages, toc]) => {
      const spine = new Map(
        pages.map((entry, index) => [entry.section_id, { entry, position: index + 1 }]),
      )
      const tocDestinations = new Set(toc.map((entry) => entry.section_id))

      for (const link of links) {
        const sectionId = link.dataset.tocSection
        const destination = spine.get(sectionId)
        const positionNode = link.querySelector("[data-toc-position]")

        if (!destination || !tocDestinations.has(sectionId)) {
          link.removeAttribute("href")
          link.setAttribute("aria-disabled", "true")
          continue
        }

        const { entry, position } = destination
        link.href = entry.href
        link.dataset.adtPage = String(position)
        link.removeAttribute("aria-disabled")
        if (positionNode) positionNode.textContent = String(position)

        const label = link.querySelector("[data-id]")?.textContent?.trim() || ""
        link.setAttribute("aria-label", `${label}, ${position}/${pages.length}`)
      }
    })
    .catch(() => {
      // The page remains readable if data loading fails; disabled placeholders
      // avoid sending a reader to an incorrect hardcoded destination.
      for (const link of links) {
        link.removeAttribute("href")
        link.setAttribute("aria-disabled", "true")
      }
    })
})()
