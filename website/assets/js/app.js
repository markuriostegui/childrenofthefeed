(() => {
  const BOOK_TITLE = "Children of the Feed. Servants of the AI God";
  const STORAGE_KEY = "ai_empire_reader_state";
  const STATE_VERSION = 1;
  const AUTOPLAY_SHORT_WORDS_MAX = 18;
  const AUTOPLAY_MEDIUM_WORDS_MAX = 48;
  const AUTOPLAY_SHORT_WORDS_PER_MINUTE = 260;
  const AUTOPLAY_MEDIUM_WORDS_PER_MINUTE = 225;
  const AUTOPLAY_LONG_WORDS_PER_MINUTE = 190;
  const AUTOPLAY_SHORT_PAUSE_MS = 300;
  const AUTOPLAY_MEDIUM_PAUSE_MS = 700;
  const AUTOPLAY_LONG_PAUSE_MS = 1200;
  const AUTOPLAY_MIN_MS = 2200;
  const AUTOPLAY_MAX_MS = 18000;
  const appRoot = document.getElementById("app");
  const noteDialog = document.getElementById("note-dialog");
  const noteForm = document.getElementById("note-form");
  const noteInput = document.getElementById("note-input");
  const noteTitle = document.getElementById("note-dialog-title");
  const noteContext = document.getElementById("note-context");
  const noteCancel = document.getElementById("note-cancel");
  const noteDelete = document.getElementById("note-delete");
  const navLinks = Array.from(document.querySelectorAll(".bottom-nav a"));

  let chapters = [];
  let hooks = [];
  let state = createDefaultState();
  let activeNoteContext = null;
  let touchStart = null;
  let fitTimer = null;
  let fitFrame = null;
  let isAutoplaying = false;
  let autoplayTimerId = null;
  let autoplayGeneration = 0;
  let readerFitObserver = null;

  function createDefaultState() {
    return {
      version: STATE_VERSION,
      lastPosition: { chapterIndex: 0, blockIndex: 0 },
      chapterProgress: {},
      favorites: [],
      notes: [],
    };
  }

  function safeInt(value, fallback = 0) {
    return Number.isInteger(value) && value >= 0 ? value : fallback;
  }

  function normalizeState(raw) {
    if (!raw || typeof raw !== "object") {
      return createDefaultState();
    }
    const base = createDefaultState();
    const lastPosition = raw.lastPosition || {};
    base.lastPosition = {
      chapterIndex: safeInt(lastPosition.chapterIndex, 0),
      blockIndex: safeInt(lastPosition.blockIndex, 0),
    };
    if (raw.chapterProgress && typeof raw.chapterProgress === "object") {
      for (const [key, value] of Object.entries(raw.chapterProgress)) {
        if (!value || typeof value !== "object") continue;
        const completedBlocks = Array.isArray(value.completedBlocks)
          ? value.completedBlocks.filter((item) => Number.isInteger(item) && item >= 0).sort((a, b) => a - b)
          : [];
        base.chapterProgress[key] = {
          lastBlockIndex: safeInt(value.lastBlockIndex, 0),
          completedBlocks,
          progressPercent: safeInt(value.progressPercent, 0),
          completed: Boolean(value.completed),
          updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : "",
        };
      }
    }
    base.favorites = Array.isArray(raw.favorites) ? raw.favorites.filter((item) => item && typeof item === "object") : [];
    base.notes = Array.isArray(raw.notes) ? raw.notes.filter((item) => item && typeof item === "object") : [];
    return base;
  }

  function loadState() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      state = normalizeState(parsed);
    } catch {
      state = createDefaultState();
    }
    saveState();
  }

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function wordCount(text) {
    return String(text).trim().split(/\s+/).filter(Boolean).length;
  }

  function getAutoplayDelay(text) {
    const words = wordCount(text);
    let wordsPerMinute = AUTOPLAY_LONG_WORDS_PER_MINUTE;
    let pauseMs = AUTOPLAY_LONG_PAUSE_MS;
    if (words <= AUTOPLAY_SHORT_WORDS_MAX) {
      wordsPerMinute = AUTOPLAY_SHORT_WORDS_PER_MINUTE;
      pauseMs = AUTOPLAY_SHORT_PAUSE_MS;
    } else if (words <= AUTOPLAY_MEDIUM_WORDS_MAX) {
      wordsPerMinute = AUTOPLAY_MEDIUM_WORDS_PER_MINUTE;
      pauseMs = AUTOPLAY_MEDIUM_PAUSE_MS;
    }
    const unclamped = Math.round((words / wordsPerMinute) * 60000 + pauseMs);
    return Math.min(AUTOPLAY_MAX_MS, Math.max(AUTOPLAY_MIN_MS, unclamped));
  }

  function clearAutoplayTimer() {
    if (autoplayTimerId !== null) {
      window.clearTimeout(autoplayTimerId);
      autoplayTimerId = null;
    }
  }

  function stopAutoplay() {
    isAutoplaying = false;
    autoplayGeneration += 1;
    clearAutoplayTimer();
    resetAutoplayIndicator();
  }

  function setReaderRouteState(isActive) {
    const isCompact = isActive && window.innerHeight <= 520;
    document.documentElement.classList.toggle("reader-route", isActive);
    document.body.classList.toggle("reader-route", isActive);
    document.documentElement.classList.toggle("reader-compact", isCompact);
    document.body.classList.toggle("reader-compact", isCompact);
  }

  function clearReaderFitObserver() {
    if (readerFitObserver) {
      readerFitObserver.disconnect();
      readerFitObserver = null;
    }
  }

  function scheduleReaderFit() {
    if (routeInfo().name === "read") {
      setReaderRouteState(true);
    }
    if (fitFrame) {
      window.cancelAnimationFrame(fitFrame);
    }
    fitFrame = window.requestAnimationFrame(() => {
      fitFrame = null;
      fitReaderText();
    });
  }

  function resetAutoplayIndicator() {
    const progress = document.getElementById("autoplay-progress");
    const fill = document.getElementById("autoplay-progress-fill");
    if (!progress || !fill) return;
    progress.classList.remove("active");
    fill.style.transition = "none";
    fill.style.transform = "scaleX(1)";
  }

  function startAutoplayIndicator(durationMs) {
    const progress = document.getElementById("autoplay-progress");
    const fill = document.getElementById("autoplay-progress-fill");
    if (!progress || !fill) return;
    progress.classList.add("active");
    fill.style.transition = "none";
    fill.style.transform = "scaleX(1)";
    void fill.offsetWidth;
    window.requestAnimationFrame(() => {
      fill.style.transition = `transform ${durationMs}ms linear`;
      fill.style.transform = "scaleX(0)";
    });
  }

  function favoriteId(chapterIndex, blockIndex) {
    return `fav-${chapterIndex}-${blockIndex}`;
  }

  function noteId(chapterIndex, blockIndex) {
    return `note-${chapterIndex}-${blockIndex}`;
  }

  function chapterProgressEntry(chapterIndex) {
    return state.chapterProgress[String(chapterIndex)] || {
      lastBlockIndex: 0,
      completedBlocks: [],
      progressPercent: 0,
      completed: false,
      updatedAt: "",
    };
  }

  function updateProgress(chapterIndex, blockIndex) {
    const totalBlocks = chapters[chapterIndex]?.blocks.length || 1;
    const key = String(chapterIndex);
    const entry = chapterProgressEntry(chapterIndex);
    const completedBlocks = new Set(entry.completedBlocks);
    completedBlocks.add(blockIndex);
    state.chapterProgress[key] = {
      lastBlockIndex: blockIndex,
      completedBlocks: Array.from(completedBlocks).sort((a, b) => a - b),
      progressPercent: Math.round((completedBlocks.size / totalBlocks) * 100),
      completed: blockIndex >= totalBlocks - 1,
      updatedAt: nowIso(),
    };
    state.lastPosition = { chapterIndex, blockIndex };
    saveState();
  }

  function getFavorite(chapterIndex, blockIndex) {
    const id = favoriteId(chapterIndex, blockIndex);
    return state.favorites.find((favorite) => favorite.id === id) || null;
  }

  function toggleFavorite(chapterIndex, blockIndex) {
    const chapter = chapters[chapterIndex];
    const block = chapter.blocks[blockIndex];
    const id = favoriteId(chapterIndex, blockIndex);
    const existing = getFavorite(chapterIndex, blockIndex);
    if (existing) {
      state.favorites = state.favorites.filter((favorite) => favorite.id !== id);
    } else {
      state.favorites.push({
        id,
        chapterIndex,
        blockIndex,
        chapterTitle: chapter.title,
        text: block.text,
        image: block.image,
        createdAt: nowIso(),
      });
    }
    saveState();
  }

  function getNote(chapterIndex, blockIndex) {
    const id = noteId(chapterIndex, blockIndex);
    return state.notes.find((note) => note.id === id) || null;
  }

  function upsertNote(chapterIndex, blockIndex, comment) {
    const chapter = chapters[chapterIndex];
    const block = chapter.blocks[blockIndex];
    const id = noteId(chapterIndex, blockIndex);
    const existing = getNote(chapterIndex, blockIndex);
    const timestamp = nowIso();
    if (existing) {
      existing.comment = comment;
      existing.updatedAt = timestamp;
      existing.chapterTitle = chapter.title;
      existing.blockText = block.text;
      existing.image = block.image;
    } else {
      state.notes.push({
        id,
        chapterIndex,
        blockIndex,
        chapterTitle: chapter.title,
        blockText: block.text,
        comment,
        image: block.image,
        createdAt: timestamp,
        updatedAt: timestamp,
      });
    }
    saveState();
  }

  function deleteNote(id) {
    state.notes = state.notes.filter((note) => note.id !== id);
    saveState();
  }

  function deriveHooks(chaptersList) {
    const embeddedHooks = readJsonScript("hook-data");
    if (Array.isArray(embeddedHooks) && embeddedHooks.length) {
      return embeddedHooks;
    }
    const candidates = [];
    const seen = new Set();
    for (const chapter of chaptersList) {
      for (const block of chapter.blocks.slice(0, 4)) {
        const firstSentence = String(block.text).split(/(?<=[.!?])\s+/)[0].trim();
        const candidate = firstSentence.endsWith("?") ? firstSentence : String(block.text).trim();
        const wordTotal = candidate.split(/\s+/).filter(Boolean).length;
        if (wordTotal >= 5 && wordTotal <= 18 && !seen.has(candidate)) {
          seen.add(candidate);
          candidates.push(candidate);
        }
      }
    }
    return candidates.length ? candidates : [chaptersList[0]?.blocks[0]?.text || "Start reading."];
  }

  function hookOfTheMoment() {
    if (!hooks.length) return "Start reading.";
    const day = Math.floor(Date.now() / 86400000);
    return hooks[day % hooks.length];
  }

  function readJsonScript(id) {
    const node = document.getElementById(id);
    if (!node) return null;
    try {
      return JSON.parse(node.textContent || "null");
    } catch {
      return null;
    }
  }

  async function loadChapters() {
    try {
      const response = await fetch("data/chapters.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`Unexpected status ${response.status}`);
      return await response.json();
    } catch {
      const embedded = readJsonScript("chapters-data");
      if (Array.isArray(embedded)) {
        return embedded;
      }
      throw new Error("Unable to load chapters.json");
    }
  }

  function clampPosition(chapterIndex, blockIndex) {
    const safeChapterIndex = Math.min(Math.max(chapterIndex, 0), Math.max(chapters.length - 1, 0));
    const blocks = chapters[safeChapterIndex]?.blocks || [];
    const safeBlockIndex = Math.min(Math.max(blockIndex, 0), Math.max(blocks.length - 1, 0));
    return { chapterIndex: safeChapterIndex, blockIndex: safeBlockIndex };
  }

  function routeInfo() {
    const hash = window.location.hash || "#/home";
    const trimmed = hash.replace(/^#\/?/, "");
    const segments = trimmed.split("/").filter(Boolean);
    const primary = segments[0] || "home";
    if (primary === "read") {
      return {
        name: "read",
        chapterIndex: safeInt(Number(segments[1]), 0),
        blockIndex: safeInt(Number(segments[2]), 0),
      };
    }
    return { name: primary };
  }

  function navigateTo(hash) {
    window.location.hash = hash;
  }

  function setActiveNav(name) {
    for (const link of navLinks) {
      link.classList.toggle("active", link.dataset.nav === name);
    }
  }

  function progressBar(percent) {
    return `
      <div class="progress-row">
        <div class="progress-bar" aria-hidden="true"><div class="progress-fill" style="width: ${percent}%"></div></div>
        <span>${percent}%</span>
      </div>
    `;
  }

  function renderBrandHeader() {
    return `
      <header class="brand-header">
        <a class="brand-link" href="https://wakenai.com" aria-label="WakenAI">
          <img
            src="assets/images/waken-ai-black.webp"
            alt="WakenAI"
            onerror="this.onerror=null;this.src='../assets/brand/waken-ai-black.webp';"
          >
        </a>
      </header>
    `;
  }

  function renderHome() {
    const last = clampPosition(state.lastPosition.chapterIndex, state.lastPosition.blockIndex);
    const lastChapter = chapters[last.chapterIndex];
    const currentBlock = lastChapter.blocks[last.blockIndex];
    const entry = chapterProgressEntry(last.chapterIndex);
    const hook = hookOfTheMoment();
    appRoot.innerHTML = `
      <section class="screen">
        <div class="screen-stack">
          ${renderBrandHeader()}
          <article class="hero-card home-card" style="background-image: url('${escapeAttribute(currentBlock.image)}')">
            <div class="hero-copy">
              <p class="eyebrow">Story reader</p>
              <h1 class="hero-title">${escapeHtml(BOOK_TITLE)}</h1>
              <p class="hero-subtitle">A chapter-based story reader built from the editorial book source</p>
              <p class="hero-hook">${escapeHtml(hook)}</p>
              <p class="resume-meta">Resume with ${escapeHtml(lastChapter.title)} · ${entry.progressPercent || 0}% complete</p>
              <div class="button-row">
                <a class="button primary" href="#/read/${last.chapterIndex}/${last.blockIndex}">Continue reading</a>
                <a class="button" href="#/index">Choose a chapter</a>
                <a class="button" href="../book/index.html">HTML book</a>
                <a class="button" href="../papers/html/11_children-of-the-feed-servants-of-the-ai-god_paper.html">Research paper</a>
              </div>
            </div>
          </article>
        </div>
      </section>
    `;
    setActiveNav("home");
  }

  function renderIndex() {
    const cards = chapters.map((chapter, chapterIndex) => {
      const entry = chapterProgressEntry(chapterIndex);
      const actionLabel = entry.progressPercent > 0 ? "Continue" : "Start";
      const blockIndex = Math.min(entry.lastBlockIndex || 0, chapter.blocks.length - 1);
      return `
        <article class="chapter-card">
          <div class="chapter-cover" style="background-image: url('${escapeAttribute(chapter.blocks[0].image)}')"></div>
          <div class="chapter-body">
            <p class="meta-label">Chapter ${String(chapterIndex).padStart(2, "0")}</p>
            <h2>${escapeHtml(chapter.title)}</h2>
            <p>${escapeHtml(chapter.blocks[0].text)}</p>
            ${progressBar(entry.progressPercent)}
            <div class="button-row">
              <a class="button primary" href="#/read/${chapterIndex}/${blockIndex}">${actionLabel}</a>
            </div>
          </div>
        </article>
      `;
    }).join("");
    appRoot.innerHTML = `
      <section class="screen">
        ${renderBrandHeader()}
        <div class="section-head">
          <div>
            <p class="eyebrow">Index</p>
            <h1>Read out of order.</h1>
          </div>
          <p>Each chapter tracks its own progress, so the reader can move by mood, topic, or urgency.</p>
        </div>
        <div class="chapter-grid">${cards}</div>
      </section>
    `;
    setActiveNav("index");
  }

  function renderFavorites() {
    const favorites = [...state.favorites].sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
    if (!favorites.length) {
      appRoot.innerHTML = renderEmptyState("Favorites", "Save the blocks you want to revisit later.");
      setActiveNav("favorites");
      return;
    }
    const cards = favorites.map((favorite) => `
      <article class="saved-card">
        <div class="saved-thumb" style="background-image: url('${escapeAttribute(favorite.image)}')"></div>
        <div class="saved-body">
          <p class="saved-meta">${escapeHtml(favorite.chapterTitle)} · Block ${favorite.blockIndex + 1}</p>
          <p class="saved-snippet">${escapeHtml(favorite.text)}</p>
          <div class="saved-actions">
            <a class="button primary" href="#/read/${favorite.chapterIndex}/${favorite.blockIndex}">Return to block</a>
          </div>
        </div>
      </article>
    `).join("");
    appRoot.innerHTML = `
      <section class="screen">
        ${renderBrandHeader()}
        <div class="section-head">
          <div>
            <p class="eyebrow">Favorites</p>
            <h1>Saved fragments.</h1>
          </div>
          <p>Every saved block keeps its chapter title, exact location, and image context.</p>
        </div>
        <div class="saved-grid">${cards}</div>
      </section>
    `;
    setActiveNav("favorites");
  }

  function renderNotes() {
    const notes = [...state.notes].sort((a, b) => String(b.updatedAt || b.createdAt).localeCompare(String(a.updatedAt || a.createdAt)));
    if (!notes.length) {
      appRoot.innerHTML = renderEmptyState("Notes", "Add a private note from any reading block.");
      setActiveNav("notes");
      return;
    }
    const cards = notes.map((note) => `
      <article class="saved-card">
        <div class="saved-thumb" style="background-image: url('${escapeAttribute(note.image)}')"></div>
        <div class="saved-body">
          <p class="saved-meta">${escapeHtml(note.chapterTitle)} · Block ${note.blockIndex + 1} · ${formatDate(note.updatedAt || note.createdAt)}</p>
          <p class="saved-snippet">${escapeHtml(note.blockText)}</p>
          <p>${escapeHtml(note.comment)}</p>
          <div class="saved-actions">
            <a class="button primary" href="#/read/${note.chapterIndex}/${note.blockIndex}">Return to block</a>
            <button data-edit-note="${note.id}">Edit note</button>
            <button class="danger" data-delete-note="${note.id}">Delete</button>
          </div>
        </div>
      </article>
    `).join("");
    appRoot.innerHTML = `
      <section class="screen">
        ${renderBrandHeader()}
        <div class="section-head">
          <div>
            <p class="eyebrow">Notes</p>
            <h1>Private annotations.</h1>
          </div>
          <p>Notes stay local to this browser and always jump back to the exact block that prompted them.</p>
        </div>
        <div class="saved-grid">${cards}</div>
      </section>
    `;
    bindNotesScreenActions();
    setActiveNav("notes");
  }

  function renderEmptyState(label, message) {
    return `
      <section class="screen">
        ${renderBrandHeader()}
        <div class="section-head">
          <div>
            <p class="eyebrow">${escapeHtml(label)}</p>
            <h1>Nothing here yet.</h1>
          </div>
        </div>
        <article class="panel empty-state">
          <h2>${escapeHtml(message)}</h2>
          <p>Use the reader to save favorites or capture private notes as you move through the book.</p>
        </article>
      </section>
    `;
  }

  function renderReader(chapterIndex, blockIndex) {
    const safe = clampPosition(chapterIndex, blockIndex);
    const chapter = chapters[safe.chapterIndex];
    const block = chapter.blocks[safe.blockIndex];
    clearAutoplayTimer();
    updateProgress(safe.chapterIndex, safe.blockIndex);
    const entry = chapterProgressEntry(safe.chapterIndex);
    const favorite = getFavorite(safe.chapterIndex, safe.blockIndex);
    const note = getNote(safe.chapterIndex, safe.blockIndex);
    appRoot.innerHTML = `
      <section class="screen reader-screen">
        <article class="reader-stage" style="background-image: url('${escapeAttribute(block.image)}')">
          <div class="reader-copy">
            <div class="reader-frame">
              <div class="reader-header">
                <div class="reader-topline">
                  <span class="reader-chapter">${escapeHtml(chapter.title)}</span>
                  <span class="reader-progress">${entry.progressPercent}%</span>
                </div>
                <div class="reader-progress-bar" aria-hidden="true">
                  <div class="progress-fill" style="width: ${entry.progressPercent}%"></div>
                </div>
              </div>
              <div class="reader-main">
                  <div class="reader-fit-area">
                    <div class="reader-text-panel">
                      <div class="reader-text-body">
                        <p class="reader-text">${escapeHtml(block.text)}</p>
                      </div>
                    </div>
                  </div>
              </div>
              <div class="reader-footer">
                <div class="reader-autoplay-progress ${isAutoplaying ? "active" : ""}" id="autoplay-progress" aria-hidden="true">
                  <div class="reader-autoplay-fill" id="autoplay-progress-fill"></div>
                </div>
                <div class="reader-actions">
                  <button
                    class="icon-button ${favorite ? "active" : ""}"
                    id="favorite-toggle"
                    type="button"
                    aria-label="${favorite ? "Remove favorite" : "Save favorite"}"
                    aria-pressed="${favorite ? "true" : "false"}"
                    title="${favorite ? "Remove favorite" : "Save favorite"}"
                  >
                    <span class="reader-icon" aria-hidden="true">${favorite ? "favorite" : "favorite_border"}</span>
                    <span class="sr-only">${favorite ? "Remove favorite" : "Save favorite"}</span>
                  </button>
                  <button
                    class="icon-button ${note ? "active" : ""}"
                    id="note-toggle"
                    type="button"
                    aria-label="${note ? "Edit note" : "Add note"}"
                    aria-pressed="${note ? "true" : "false"}"
                    title="${note ? "Edit note" : "Add note"}"
                  >
                    <span class="reader-icon" aria-hidden="true">edit_note</span>
                    <span class="sr-only">${note ? "Edit note" : "Add note"}</span>
                  </button>
                  <button
                    class="icon-button ${isAutoplaying ? "active" : ""}"
                    id="autoplay-toggle"
                    type="button"
                    aria-label="${isAutoplaying ? "Pause autoplay" : "Start autoplay"}"
                    aria-pressed="${isAutoplaying ? "true" : "false"}"
                    title="${isAutoplaying ? "Pause autoplay" : "Start autoplay"}"
                  >
                    <span class="reader-icon" aria-hidden="true">${isAutoplaying ? "pause" : "play_arrow"}</span>
                    <span class="sr-only">${isAutoplaying ? "Pause autoplay" : "Start autoplay"}</span>
                  </button>
                  <button
                    class="icon-button"
                    id="next-toggle"
                    type="button"
                    aria-label="Next block"
                    title="Next block"
                  >
                    <span class="reader-icon" aria-hidden="true">skip_next</span>
                    <span class="sr-only">Next block</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </article>
      </section>
    `;
    document.getElementById("autoplay-toggle")?.addEventListener("click", (event) => {
      event.stopPropagation();
      if (isAutoplaying) {
        stopAutoplay();
      } else {
        isAutoplaying = true;
        autoplayGeneration += 1;
      }
      renderCurrentRoute();
    });
    document.getElementById("favorite-toggle")?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleFavorite(safe.chapterIndex, safe.blockIndex);
      renderCurrentRoute();
    });
    document.getElementById("note-toggle")?.addEventListener("click", (event) => {
      event.stopPropagation();
      openNoteDialog(safe.chapterIndex, safe.blockIndex);
    });
    document.getElementById("next-toggle")?.addEventListener("click", (event) => {
      event.stopPropagation();
      advanceReader(safe.chapterIndex, safe.blockIndex, 1, { preserveAutoplay: isAutoplaying });
    });
    bindReaderGestures(safe.chapterIndex, safe.blockIndex);
    bindReaderFitObserver();
    scheduleReaderFit();
    if (document.fonts?.ready) {
      document.fonts.ready.then(() => scheduleReaderFit()).catch(() => scheduleReaderFit());
    }
    if (isAutoplaying) {
      scheduleAutoplay(safe.chapterIndex, safe.blockIndex);
    } else {
      resetAutoplayIndicator();
    }
    setActiveNav("");
  }

  function bindReaderFitObserver() {
    clearReaderFitObserver();
    const stage = document.querySelector(".reader-stage");
    const fitArea = document.querySelector(".reader-fit-area");
    const textPanel = document.querySelector(".reader-text-panel");
    if (!stage || !fitArea || !textPanel || typeof ResizeObserver !== "function") return;
    readerFitObserver = new ResizeObserver(() => {
      setReaderRouteState(routeInfo().name === "read");
      scheduleReaderFit();
    });
    readerFitObserver.observe(stage);
    readerFitObserver.observe(fitArea);
    readerFitObserver.observe(textPanel);
  }

  function fitReaderText() {
    const textBody = document.querySelector(".reader-text-body");
    const text = document.querySelector(".reader-text");
    if (!textBody || !text) return;
    const isDesktop = window.matchMedia("(min-width: 760px)").matches && window.innerHeight >= 640;
    const minSize = isDesktop ? 16 : 14;
    const maxSize = isDesktop ? 60 : 46;
    let low = minSize;
    let high = maxSize;
    let best = minSize;
    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      text.style.setProperty("--reader-font-size", `${mid}px`);
      if (textBody.scrollHeight <= textBody.clientHeight && textBody.scrollWidth <= textBody.clientWidth) {
        best = mid;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }
    text.style.setProperty("--reader-font-size", `${best}px`);
  }

  function bindReaderGestures(chapterIndex, blockIndex) {
    const stage = document.querySelector(".reader-stage");
    if (!stage) return;
    stage.addEventListener("click", (event) => {
      if (event.target.closest("button")) return;
      const bounds = stage.getBoundingClientRect();
      const relativeX = event.clientX - bounds.left;
      if (relativeX > bounds.width / 2) {
        stepReader(chapterIndex, blockIndex, 1);
      } else {
        stepReader(chapterIndex, blockIndex, -1);
      }
    });
    stage.addEventListener("touchstart", (event) => {
      const touch = event.changedTouches[0];
      touchStart = { x: touch.clientX, y: touch.clientY };
    }, { passive: true });
    stage.addEventListener("touchend", (event) => {
      if (!touchStart) return;
      const touch = event.changedTouches[0];
      const dx = touch.clientX - touchStart.x;
      const dy = touch.clientY - touchStart.y;
      touchStart = null;
      if (Math.abs(dx) < 24 && Math.abs(dy) < 24) return;
      if (Math.abs(dx) > Math.abs(dy)) {
        stepReader(chapterIndex, blockIndex, dx < 0 ? 1 : -1);
      } else {
        stepReader(chapterIndex, blockIndex, dy < 0 ? 1 : -1);
      }
    }, { passive: true });
  }

  function scheduleAutoplay(chapterIndex, blockIndex) {
    clearAutoplayTimer();
    if (!isAutoplaying) return;
    const chapter = chapters[chapterIndex];
    const block = chapter?.blocks?.[blockIndex];
    if (!chapter || !block) {
      stopAutoplay();
      return;
    }
    if (blockIndex >= chapter.blocks.length - 1) {
      stopAutoplay();
      renderCurrentRoute();
      return;
    }
    const delay = getAutoplayDelay(block.text);
    const generation = autoplayGeneration;
    startAutoplayIndicator(delay);
    autoplayTimerId = window.setTimeout(() => {
      autoplayTimerId = null;
      if (!isAutoplaying || generation !== autoplayGeneration) return;
      const route = routeInfo();
      if (route.name !== "read") {
        stopAutoplay();
        return;
      }
      if (route.chapterIndex !== chapterIndex || route.blockIndex !== blockIndex) {
        scheduleAutoplay(route.chapterIndex, route.blockIndex);
        return;
      }
      if (blockIndex >= chapter.blocks.length - 1) {
        stopAutoplay();
        renderCurrentRoute();
        return;
      }
      navigateTo(`#/read/${chapterIndex}/${blockIndex + 1}`);
    }, delay);
  }

  function nextReaderPosition(chapterIndex, blockIndex, direction) {
    const chapter = chapters[chapterIndex];
    const nextBlockIndex = blockIndex + direction;
    if (nextBlockIndex >= 0 && nextBlockIndex < chapter.blocks.length) {
      return { chapterIndex, blockIndex: nextBlockIndex };
    }
    const nextChapterIndex = chapterIndex + direction;
    if (nextChapterIndex >= 0 && nextChapterIndex < chapters.length) {
      return {
        chapterIndex: nextChapterIndex,
        blockIndex: direction > 0 ? 0 : chapters[nextChapterIndex].blocks.length - 1,
      };
    }
    return null;
  }

  function advanceReader(chapterIndex, blockIndex, direction, options = {}) {
    const target = nextReaderPosition(chapterIndex, blockIndex, direction);
    if (!target) {
      if (options.preserveAutoplay) {
        stopAutoplay();
        renderCurrentRoute();
      }
      return;
    }
    if (options.preserveAutoplay) {
      autoplayGeneration += 1;
      clearAutoplayTimer();
      resetAutoplayIndicator();
    }
    navigateTo(`#/read/${target.chapterIndex}/${target.blockIndex}`);
  }

  function stepReader(chapterIndex, blockIndex, direction) {
    advanceReader(chapterIndex, blockIndex, direction);
  }

  function openNoteDialog(chapterIndex, blockIndex) {
    if (isAutoplaying) {
      stopAutoplay();
      renderCurrentRoute();
    }
    const chapter = chapters[chapterIndex];
    const block = chapter.blocks[blockIndex];
    const existing = getNote(chapterIndex, blockIndex);
    activeNoteContext = { chapterIndex, blockIndex, noteId: existing?.id || null };
    noteTitle.textContent = existing ? "Edit note" : "Add a note";
    noteContext.textContent = `${chapter.title} · Block ${blockIndex + 1}`;
    noteInput.value = existing?.comment || "";
    noteDelete.hidden = !existing;
    if (typeof noteDialog.showModal === "function") {
      noteDialog.showModal();
    }
  }

  function closeNoteDialog() {
    activeNoteContext = null;
    if (noteDialog.open) {
      noteDialog.close();
    }
  }

  function bindNotesScreenActions() {
    document.querySelectorAll("[data-edit-note]").forEach((button) => {
      button.addEventListener("click", () => {
        const note = state.notes.find((entry) => entry.id === button.getAttribute("data-edit-note"));
        if (!note) return;
        openNoteDialog(note.chapterIndex, note.blockIndex);
      });
    });
    document.querySelectorAll("[data-delete-note]").forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.getAttribute("data-delete-note");
        if (!id) return;
        deleteNote(id);
        renderCurrentRoute();
      });
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replace(/`/g, "&#96;");
  }

  function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return "Saved locally";
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function renderCurrentRoute() {
    const route = routeInfo();
    setReaderRouteState(route.name === "read");
    if (route.name !== "read") {
      clearReaderFitObserver();
    }
    if (route.name !== "read") {
      stopAutoplay();
    }
    switch (route.name) {
      case "home":
        renderHome();
        break;
      case "index":
        renderIndex();
        break;
      case "favorites":
        renderFavorites();
        break;
      case "notes":
        renderNotes();
        break;
      case "read":
        renderReader(route.chapterIndex, route.blockIndex);
        break;
      default:
        navigateTo("#/home");
    }
  }

  async function init() {
    chapters = await loadChapters();
    hooks = deriveHooks(chapters);
    loadState();
    if (!window.location.hash) {
      navigateTo("#/home");
      return;
    }
    renderCurrentRoute();
  }

  noteForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!activeNoteContext) return;
    const comment = noteInput.value.trim();
    if (!comment) {
      closeNoteDialog();
      return;
    }
    upsertNote(activeNoteContext.chapterIndex, activeNoteContext.blockIndex, comment);
    closeNoteDialog();
    renderCurrentRoute();
  });

  noteCancel.addEventListener("click", () => {
    closeNoteDialog();
    if (routeInfo().name === "read") {
      renderCurrentRoute();
    }
  });
  noteDelete.addEventListener("click", () => {
    if (!activeNoteContext?.noteId) return;
    deleteNote(activeNoteContext.noteId);
    closeNoteDialog();
    renderCurrentRoute();
  });

  window.addEventListener("hashchange", () => renderCurrentRoute());
  window.addEventListener("resize", () => {
    setReaderRouteState(routeInfo().name === "read");
    if (fitTimer) window.clearTimeout(fitTimer);
    fitTimer = window.setTimeout(() => {
      if (routeInfo().name === "read") {
        scheduleReaderFit();
      }
    }, 60);
  });
  window.addEventListener("orientationchange", () => {
    setReaderRouteState(routeInfo().name === "read");
    if (routeInfo().name === "read") {
      scheduleReaderFit();
    }
  });
  window.addEventListener("keydown", (event) => {
    const route = routeInfo();
    if (route.name !== "read" || noteDialog.open) return;
    if (["ArrowRight", "ArrowDown"].includes(event.key)) {
      event.preventDefault();
      stepReader(route.chapterIndex, route.blockIndex, 1);
    }
    if (["ArrowLeft", "ArrowUp"].includes(event.key)) {
      event.preventDefault();
      stepReader(route.chapterIndex, route.blockIndex, -1);
    }
  });

  init().catch((error) => {
    appRoot.innerHTML = `
      <section class="screen">
        <article class="panel empty-state">
          <p class="eyebrow">Reader unavailable</p>
          <h2>Unable to load the story reader.</h2>
          <p>${escapeHtml(error.message || "Unknown error")}</p>
        </article>
      </section>
    `;
  });
})();
