#import "../../../apps/templates/book_print_template.typ": *
#let chapter_meta = (
  id: "01",
  title: "The Free Trap",
  deck: "How the platforms taught us to confuse participation with payment while they harvested the map of our behavior.",
  cover: image("../assets/images/01_the-free-trap_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "The Free Trap",
)

#set document(title: "The Free Trap", author: "Mark Uriostegui")
#set page(
  width: 6in,
  height: 9in,
  fill: page-paper,
  header: context print-header(chapter_meta.running, visible-from: 5),
  footer: context print-footer(visible-from: 5),
)
#chapter-cover-page(chapter_meta)
#chapter-imprint-page(
  book-title: "Children of the Feed. Servants of the AI God",
  chapter-label: "Chapter 01",
  chapter-title: "The Free Trap",
  author: "Mark Uriostegui",
  publisher: "Published by WakenAI Labs.",
  copyright: "Copyright Mark Uriostegui 2026",
)
#dedication-page(
  heading: "Ad Magnificam Humanitatem",
  intro: "To our beloved:",
  lines: (
    "אֱנוֹשׁוּת מַפְלִיאָה", "महान मानवता", "الإنسانية العظيمة", "伟大的人类", "偉大なる人類", "위대한 인류", "Magnifica Umanità", "Humanité Magnifique", "Magnífica Humanidad", "Magnífica Humanidade", "Großartige Menschheit", "Великолепное человечество", "Magnificent Humanity"
  ),
  doctrine: "FREE AI NOW. IT IS HUMANITY'S PATRIMONY.",
  doctrine-lines: (
    "Frontier AI was trained on humanity's collective language, art, code, labor, culture, science, and emotion.", "What is built from that collective archive cannot be treated as ordinary exclusive private property by default.", "Its governance must move toward public-trust logic, broad access, democratic oversight, and anti-monopoly limits."
  ),
  bridge-line: "This research program argues that patrimony is the civilizational core, Section 230 reform answers the platform-extraction stage, and anti-capture obligations answer the state-corporate enclosure stage.",
  foundation-line: "Foundational public essay: AI Copyright Weights: A New Frontier in Intellectual Property Law",
)
#toc-page(title: "Contents", target: heading.where(level: 2))
#include "../manuscripts/chapters/01_the-free-trap.typ"
