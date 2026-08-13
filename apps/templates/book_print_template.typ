#let page-paper = rgb("#f7f2e8")
#let page-ink = rgb("#18130f")
#let page-muted = rgb("#6d6256")
#let page-rule = rgb("#c6b18a")
#let page-ember = rgb("#9e3d23")
#let page-gold = rgb("#b8872b")
#let page-night = rgb("#0c1118")
#let default-page-margin = (
  inside: 1.04in,
  outside: 0.9in,
  top: 1.0in,
  bottom: 1.08in,
)

#set page(
  width: 6in,
  height: 9in,
  margin: default-page-margin,
  fill: page-paper,
)

#set text(
  font: "Source Serif 4",
  size: 11.2pt,
  fill: page-ink,
  lang: "en",
)

#set par(
  justify: true,
  leading: 0.98em,
  spacing: 0.94em,
)

#set heading(numbering: none)

#show link: set text(fill: page-ember)
#show emph: set text(style: "italic")
#show strong: set text(weight: "semibold")
#show heading.where(level: 1): it => []

#show heading.where(level: 2): it => [
  #v(1.45em)
  #set text(font: "Source Sans 3", size: 9.2pt, fill: page-ember)
  #set par(justify: false)
  #text(tracking: 0.08em)[#upper(it.body)]
  #v(0.32em)
  #line(length: 100%, stroke: (paint: page-rule, thickness: 0.6pt))
  #v(0.56em)
]

#show heading.where(level: 3): it => [
  #v(1.05em)
  #set text(font: "Source Sans 3", size: 9.3pt, fill: page-gold)
  #set par(justify: false)
  #it.body
  #v(0.26em)
]

#show figure: set block(above: 1.35em, below: 1.4em)
#show figure.caption: set text(font: "Source Sans 3", size: 8.2pt, fill: page-muted)

#show quote: set block(
  inset: (left: 0.18in, right: 0.08in, top: 0.08in, bottom: 0.08in),
  stroke: (left: (paint: page-ember, thickness: 2pt)),
  fill: rgb("#efe7d9"),
)

#show raw.where(block: true): set block(
  inset: 0.14in,
  radius: 6pt,
  fill: rgb("#efe7d9"),
)
#show raw: set text(font: "Source Sans 3", size: 8.5pt)

#show table: set block(above: 1.05em, below: 1.05em)

#let dedication-font(index) = {
  if index == 0 {
    "Noto Sans Hebrew"
  } else if index == 1 {
    "Noto Sans Devanagari"
  } else if index == 2 {
    "Noto Naskh Arabic"
  } else if index == 3 {
    "Noto Sans CJK SC"
  } else if index == 4 {
    "Noto Sans CJK JP"
  } else if index == 5 {
    "Noto Sans CJK KR"
  } else {
    "Source Sans 3"
  }
}

#let print-header(running, visible-from: 5) = context {
  let n = counter(page).get().first()
  if n >= visible-from [
    #box(
      width: 100%,
      inset: (bottom: 0.03in),
      [
        #set text(font: "Source Sans 3", size: 8pt, fill: page-muted)
        #align(left + horizon)[#running]
      ],
    )
  ]
}

#let print-footer(visible-from: 5) = context {
  let n = counter(page).get().first()
  if n >= visible-from [
    #box(
      width: 100%,
      inset: (top: 0.03in),
      [
        #set text(font: "Source Sans 3", size: 8pt, fill: page-muted)
        #align(center + horizon)[#n]
      ],
    )
  ]
}

#let full-bleed-cover(cover) = [
  #set page(
    margin: 0pt,
    fill: page-night,
    header: [],
    footer: [],
  )
  #cover
  #pagebreak()
  #set page(
    margin: default-page-margin,
    fill: page-paper,
  )
]

#let book-imprint-page(
  title-line-1: "",
  title-line-2: "",
  subtitle: "",
  author: "",
  publisher: "",
  copyright: "",
  adaptation-line: "",
) = [
  #set par(justify: false)
  #v(1.55in)
  #align(center)[
    #set text(font: "Oswald", size: 23pt, fill: page-ink)
    #upper(title-line-1)
    #linebreak()
    #upper(title-line-2)
  ]
  #v(0.24in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 11pt, fill: page-ember)
    #subtitle
  ]
  #v(0.28in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 11pt, fill: page-ink)
    #author
  ]
  #v(0.45in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 9.3pt, fill: page-muted)
    #adaptation-line
  ]
  #v(0.22in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 9.2pt, fill: page-muted)
    #publisher
  ]
  #v(0.08in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 9.2pt, fill: page-muted)
    #copyright
  ]
  #pagebreak()
]

#let chapter-imprint-page(
  book-title: "",
  chapter-label: "",
  chapter-title: "",
  author: "",
  publisher: "",
  copyright: "",
) = [
  #set par(justify: false)
  #v(1.4in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 8.8pt, fill: page-gold)
    #upper(book-title)
  ]
  #v(0.2in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 9.1pt, fill: page-ember)
    #upper(chapter-label)
  ]
  #v(0.08in)
  #align(center)[
    #set text(font: "Oswald", size: 22pt, fill: page-ink)
    #chapter-title
  ]
  #v(0.28in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 10.5pt, fill: page-ink)
    #author
  ]
  #v(0.42in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 9.2pt, fill: page-muted)
    #publisher
  ]
  #v(0.08in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 9.2pt, fill: page-muted)
    #copyright
  ]
  #pagebreak()
]

#let dedication-page(
  heading: "",
  intro: "",
  lines: (),
  doctrine: "",
  doctrine-lines: (),
  bridge-line: "",
  foundation-line: "",
) = [
  #set par(justify: false)
  #v(0.72in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 10pt, fill: page-gold)
    #upper(heading)
  ]
  #v(0.24in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 11pt, fill: page-ink)
    #intro
    #for (index, line) in lines.enumerate() [
      #linebreak()
      #set text(font: dedication-font(index), size: 11pt, fill: page-ink)
      #line
    ]
  ]
  #v(0.34in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 9.2pt, fill: page-ember)
    #strong[#doctrine]
  ]
  #v(0.16in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 8.95pt, fill: page-ink)
    #for line in doctrine-lines [
      #line
      #linebreak()
    ]
  ]
  #v(0.12in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 8.15pt, fill: page-muted)
    #bridge-line
  ]
  #v(0.1in)
  #align(center)[
    #set text(font: "Source Sans 3", size: 7.9pt, fill: page-muted)
    #foundation-line
  ]
  #pagebreak()
]

#let toc-page(title: "Contents", target: none) = [
  #set par(justify: false)
  #v(0.5in)
  #align(center)[
    #set text(font: "Oswald", size: 20pt, fill: page-ink)
    #title
  ]
  #v(0.18in)
  #line(length: 100%, stroke: (paint: page-rule, thickness: 0.8pt))
  #v(0.2in)
  #set text(font: "Source Sans 3", size: 9.1pt, fill: page-ink)
  #outline(title: none, target: target)
  #pagebreak()
]

#let chapter-cover-page(meta, label: "CHAPTER") = [
  #figure(meta.cover)
  #v(0.24in)
  #set text(font: "Source Sans 3", size: 9pt, fill: page-ember)
  #text(tracking: 0.08em)[#label #meta.id]
  #v(0.12in)
  #set text(font: "Oswald", size: 24pt, fill: page-ink)
  #meta.title
  #v(0.12in)
  #set text(font: "Source Sans 3", size: 10pt, fill: page-muted)
  #meta.deck
  #v(0.22in)
  #line(length: 100%, stroke: (paint: page-rule, thickness: 0.8pt))
  #pagebreak()
]
