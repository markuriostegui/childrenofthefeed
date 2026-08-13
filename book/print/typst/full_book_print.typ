#import "../../../apps/templates/book_print_template.typ": *
        #set document(title: "Children of the Feed. Servants of the AI God", author: "Mark Uriostegui")
        #set page(
          width: 6in,
          height: 9in,
          fill: page-paper,
          header: context print-header("Children of the Feed. Servants of the AI God", visible-from: 5),
          footer: context print-footer(visible-from: 5),
        )
        #full-bleed-cover(image("../assets/images/book_master_cover.jpg", width: 100%, height: 100%, fit: "cover"))
        #book-imprint-page(
          title-line-1: "Children of the Feed. Servants",
          title-line-2: "of the AI God",
          subtitle: "How technofeudalism raised us as digital serfs",
          author: "Mark Uriostegui",
          adaptation-line: "A trade-book adaptation of the AI Empire research program.",
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
        #toc-page(title: "Contents", target: heading.where(level: 1))
        = Before the Machine Could Speak
#let chapter_meta_00 = (
  id: "00",
  title: "Before the Machine Could Speak",
  deck: "The opening wound: how humanity was turned into signal before AI could be sold as destiny.",
  cover: image("../assets/images/00_before-the-machine-could-speak_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "Before the Machine Could Speak",
)
#chapter-cover-page(chapter_meta_00)
#include "../manuscripts/chapters/00_opening-framework.typ"
#pagebreak()

= The Free Trap
#let chapter_meta_01 = (
  id: "01",
  title: "The Free Trap",
  deck: "How the platforms taught us to confuse participation with payment while they harvested the map of our behavior.",
  cover: image("../assets/images/01_the-free-trap_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "The Free Trap",
)
#chapter-cover-page(chapter_meta_01)
#include "../manuscripts/chapters/01_the-free-trap.typ"
#pagebreak()

= Raised by the Algorithm
#let chapter_meta_02 = (
  id: "02",
  title: "Raised by the Algorithm",
  deck: "A generation did not simply lose attention. Attention was farmed.",
  cover: image("../assets/images/02_raised-by-the-algorithm_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "Raised by the Algorithm",
)
#chapter-cover-page(chapter_meta_02)
#include "../manuscripts/chapters/02_raised-by-the-algorithm.typ"
#pagebreak()

= Lockdown and the Great Acceleration
#let chapter_meta_03 = (
  id: "03",
  title: "Lockdown and the Great Acceleration",
  deck: "The world went inside. The platforms were waiting.",
  cover: image("../assets/images/03_lockdown-and-the-great-acceleration_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "Lockdown and the Great Acceleration",
)
#chapter-cover-page(chapter_meta_03)
#include "../manuscripts/chapters/03_lockdown-and-the-great-acceleration.typ"
#pagebreak()

= We Were the Dataset
#let chapter_meta_04 = (
  id: "04",
  title: "We Were the Dataset",
  deck: "First they captured what we made. Then they captured how we think.",
  cover: image("../assets/images/04_we-were-the-dataset_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "We Were the Dataset",
)
#chapter-cover-page(chapter_meta_04)
#include "../manuscripts/chapters/04_we-were-the-dataset.typ"
#pagebreak()

= The Layoff Ritual
#let chapter_meta_05 = (
  id: "05",
  title: "The Layoff Ritual",
  deck: "The machine did not only learn from workers. It was used to discipline them.",
  cover: image("../assets/images/05_the-layoff-ritual_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "The Layoff Ritual",
)
#chapter-cover-page(chapter_meta_05)
#include "../manuscripts/chapters/05_the-layoff-ritual.typ"
#pagebreak()

= The Dual-Use Gospel
#let chapter_meta_06 = (
  id: "06",
  title: "The Dual-Use Gospel",
  deck: "How the same system is sold as miracle, weapon, tutor, oracle, and dependency engine.",
  cover: image("../assets/images/06_the-dual-use-gospel_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "The Dual-Use Gospel",
)
#chapter-cover-page(chapter_meta_06)
#include "../manuscripts/chapters/06_the-dual-use-gospel.typ"
#pagebreak()

= The Gates of Intelligence
#let chapter_meta_07 = (
  id: "07",
  title: "The Gates of Intelligence",
  deck: "Compute, export controls, and defense alignments decide who may approach the new oracle.",
  cover: image("../assets/images/07_the-gates-of-intelligence_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "The Gates of Intelligence",
)
#chapter-cover-page(chapter_meta_07)
#include "../manuscripts/chapters/07_the-gates-of-intelligence.typ"
#pagebreak()

= The Legitimacy Machine
#let chapter_meta_08 = (
  id: "08",
  title: "The Legitimacy Machine",
  deck: "The empire does not survive by code alone. It survives by praise, access, prestige, and institutional blessing.",
  cover: image("../assets/images/08_the-legitimacy-machine_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "The Legitimacy Machine",
)
#chapter-cover-page(chapter_meta_08)
#include "../manuscripts/chapters/08_the-legitimacy-machine.typ"
#pagebreak()

= If No One Acts
#let chapter_meta_09 = (
  id: "09",
  title: "If No One Acts",
  deck: "What comes next if dependence, enclosure, and state-corporate fusion harden into infrastructure.",
  cover: image("../assets/images/09_if-no-one-acts_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "If No One Acts",
)
#chapter-cover-page(chapter_meta_09)
#include "../manuscripts/chapters/09_if-no-one-acts.typ"
#pagebreak()

= The Three Reforms
#let chapter_meta_10 = (
  id: "10",
  title: "The Three Reforms",
  deck: "The response is no longer a mood. It is a program.",
  cover: image("../assets/images/10_the-three-reforms_cover.jpg", width: 100%, height: 2.7in, fit: "cover"),
  running: "The Three Reforms",
)
#chapter-cover-page(chapter_meta_10)
#include "../manuscripts/chapters/10_the-three-reforms.typ"
