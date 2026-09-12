(() => {
  'use strict';
  const book = window.BOOK;
  const $ = id => document.getElementById(id);
  if (!book?.pages?.length) {
    $('audio-status').textContent = 'Please reload to open your book.';
    return;
  }
  const audio = $('narration');
  const pages = book.pages;
  $('page-total').textContent = `of ${pages.length}`;
  let index = -1;
  let cueIndex = -1;
  let requestId = 0;
  let nextTimer;
  let flipTimer;
  let loading = false;
  let seekInProgress = false;
  let pointerStart = null;
  const format = seconds => {
    seconds = Math.max(0, Math.floor(Number(seconds) || 0));
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  };

  function status(message, error = false) {
    $('audio-status').textContent = message;
    $('audio-status').classList.toggle('error', error);
  }
  function playState() {
    const playing = !audio.paused && !audio.ended;
    $('play').classList.toggle('is-playing', playing);
    $('play-icon').querySelector('use').setAttribute('href', playing ? '#i-pause' : '#i-play');
    $('play-label').textContent = loading ? 'Loading audio…' : playing ? 'Pause reading' : 'Play this page';
    $('play').setAttribute('aria-label', loading ? 'Loading page audio' : playing ? 'Pause reading' : `Play page ${index + 1}`);
    $('mobile-play').classList.toggle('is-playing', playing);
    $('mobile-play').querySelector('use').setAttribute('href', playing ? '#i-pause' : '#i-play');
    $('mobile-play').querySelector('span').textContent = loading ? 'Loading audio…' : playing ? 'Pause reading' : `Play page ${index + 1}`;
  }
  function updateTime() {
    const total = Number.isFinite(audio.duration) ? audio.duration : pages[index].duration;
    $('elapsed').textContent = format(audio.currentTime);
    $('duration').textContent = format(total);
    if (!seekInProgress) $('seek').value = total > 0 ? Math.round(audio.currentTime / total * 1000) : 0;
    $('seek').setAttribute('aria-valuetext', `${format(audio.currentTime)} of ${format(total)}`);
    const nextCue = pages[index].cues.findLastIndex(cue => audio.currentTime >= cue.start);
    if (nextCue !== cueIndex) {
      $('transcript').querySelector('.active')?.classList.remove('active');
      const line = $('transcript').children[nextCue];
      if (line && audio.currentTime > 0) {
        line.classList.add('active');
        // Scroll only the transcript, never the whole reading page.
        if (matchMedia('(min-width: 761px)').matches) {
          const holder = $('transcript');
          const lineTop = line.offsetTop - holder.offsetTop;
          if (lineTop < holder.scrollTop || lineTop + line.offsetHeight > holder.scrollTop + holder.clientHeight) {
            holder.scrollTo({ top: Math.max(0, lineTop - 25), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
          }
        }
      }
      cueIndex = nextCue;
    }
  }
  async function playCurrent() {
    clearTimeout(nextTimer);
    if (audio.ended) audio.currentTime = 0;
    const token = requestId;
    loading = true;
    playState();
    try {
      await audio.play();
      if (token !== requestId) return;
      loading = false;
      status($('auto-next').checked ? 'Reading together. The next page will turn for you.' : 'Listen, look, and read along.');
    } catch (error) {
      if (token !== requestId || error.name === 'AbortError') return;
      loading = false;
      status(error.name === 'NotAllowedError' ? 'Tap Play to continue reading.' : 'The audio could not load. Tap Play to try again.', true);
    }
    playState();
  }
  function showPage(next, { autoplay = false, initial = false } = {}) {
    next = Math.max(0, Math.min(pages.length - 1, next));
    if (next === index && !initial) return;
    const direction = next >= index ? 'next' : 'prev';
    requestId += 1;
    clearTimeout(nextTimer);
    clearTimeout(flipTimer);
    audio.pause();
    loading = false;
    index = next;
    cueIndex = -1;
    const page = pages[index];
    audio.src = page.audio;
    audio.defaultPlaybackRate = Number($('speed').value);
    audio.preservesPitch = true;
    audio.load();
    audio.playbackRate = Number($('speed').value);
    $('page-image').src = page.image;
    $('page-image').alt = page.alt;
    if ($('zoom-dialog').open) {
      $('zoom-image').src = page.image;
      $('zoom-image').alt = page.alt;
    }
    $('page-number').textContent = index + 1;
    $('page-counter').setAttribute('aria-label', `Page ${index + 1} of ${pages.length}. Choose a page.`);
    $('previous').disabled = index === 0;
    $('next').disabled = index === pages.length - 1;
    $('mobile-previous').disabled = index === 0;
    $('mobile-next').disabled = index === pages.length - 1;
    $('page-section').textContent = page.section;
    $('chapter-title').textContent = page.title;
    $('chapter-note').textContent = page.note;
    $('reader-tip').textContent = page.tip;
    $('duration').textContent = format(page.duration);
    $('elapsed').textContent = '0:00';
    $('seek').value = 0;
    $('seek').disabled = true;
    $('seek').setAttribute('aria-valuetext', `0:00 of ${format(page.duration)}`);
    $('audio-download').href = page.audio;
    $('audio-download').download = `${book.slug}-page-${String(page.number).padStart(2, '0')}.mp3`;
    $('transcript').replaceChildren(...page.cues.map((cue, i) => {
      const line = document.createElement('p');
      line.textContent = cue.text;
      if (i === 0) line.className = 'cue-heading';
      return line;
    }));
    $('transcript').scrollTop = 0;
    $('page-grid').querySelectorAll('button').forEach((tile, i) => {
      if (i === index) tile.setAttribute('aria-current', 'page');
      else tile.removeAttribute('aria-current');
    });
    history.replaceState(null, '', `#page-${index + 1}`);
    $('page-announcement').textContent = `Page ${index + 1} of ${pages.length}. ${page.title}.`;
    $('page-sheet').classList.remove('flip-next', 'flip-prev');
    if (!initial) {
      void $('page-sheet').offsetWidth;
      $('page-sheet').classList.add(`flip-${direction}`);
      flipTimer = setTimeout(() => $('page-sheet').classList.remove('flip-next', 'flip-prev'), 450);
    }
    status(autoplay ? 'Turning the page…' : 'Listen, look, and read along.');
    playState();
    if (pages[index + 1]) {
      const image = new Image();
      image.src = pages[index + 1].image;
    }
    if (autoplay) playCurrent();
  }
  $('play').addEventListener('click', () => {
    if (!audio.paused || loading) {
      requestId += 1;
      audio.pause();
      clearTimeout(nextTimer);
      loading = false;
      status('Paused. Take your time.');
      playState();
    } else playCurrent();
  });
  $('replay').addEventListener('click', () => { audio.currentTime = 0; cueIndex = -1; updateTime(); playCurrent(); });
  $('previous').addEventListener('click', () => showPage(index - 1));
  $('next').addEventListener('click', () => showPage(index + 1));
  $('mobile-play').addEventListener('click', () => $('play').click());
  $('mobile-previous').addEventListener('click', () => showPage(index - 1));
  $('mobile-next').addEventListener('click', () => showPage(index + 1));
  $('speed').addEventListener('change', () => { audio.defaultPlaybackRate = audio.playbackRate = Number($('speed').value); });
  $('auto-next').addEventListener('change', () => {
    clearTimeout(nextTimer);
    status($('auto-next').checked ? 'Press Play. Each page will turn when its reading finishes.' : 'You can turn each page when you are ready.');
  });
  $('seek').addEventListener('input', () => {
    if (!Number.isFinite(audio.duration)) return;
    seekInProgress = true;
    audio.currentTime = Number($('seek').value) / 1000 * audio.duration;
    updateTime();
    seekInProgress = false;
  });
  audio.addEventListener('loadedmetadata', () => { audio.playbackRate = Number($('speed').value); $('seek').disabled = !Number.isFinite(audio.duration); updateTime(); });
  audio.addEventListener('timeupdate', updateTime);
  audio.addEventListener('play', playState);
  audio.addEventListener('pause', playState);
  audio.addEventListener('error', () => { loading = false; playState(); status('The audio could not load. Tap Play to try again.', true); });
  audio.addEventListener('ended', () => {
    loading = false;
    playState();
    const token = requestId;
    if (pages[index].autoNext === false) {
      status(pages[index].stopMessage || 'Take a moment to reflect before continuing.');
    } else if ($('auto-next').checked && index < pages.length - 1) {
      status('Turning the page…');
      nextTimer = setTimeout(() => { if (token === requestId && $('auto-next').checked) showPage(index + 1, { autoplay: true }); }, 800);
    } else status(index === pages.length - 1 ? 'You have reached the end of the book.' : 'Page complete. Replay or turn the page when you are ready.');
  });
  const openPages = () => $('pages-dialog').showModal();
  $('open-pages').addEventListener('click', openPages);
  $('page-counter').addEventListener('click', openPages);
  $('close-pages').addEventListener('click', () => $('pages-dialog').close());
  $('zoom-button').addEventListener('click', () => {
    $('zoom-image').src = pages[index].image;
    $('zoom-image').alt = pages[index].alt;
    $('zoom-dialog').showModal();
  });
  $('close-zoom').addEventListener('click', () => $('zoom-dialog').close());
  for (const dialog of [$('pages-dialog'), $('zoom-dialog')]) {
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
    });
  }
  pages.forEach((page, i) => {
    const tile = document.createElement('button');
    tile.className = 'page-tile';
    tile.setAttribute('aria-label', `Page ${i + 1}: ${page.title}`);
    const image = document.createElement('img');
    image.src = page.thumbnail || page.image;
    image.loading = 'lazy';
    image.alt = '';
    image.width = 180;
    image.height = 233;
    const count = document.createElement('span'); count.textContent = `PAGE ${i + 1}`;
    const title = document.createElement('strong'); title.textContent = page.title;
    tile.append(image, count, title);
    tile.addEventListener('click', () => { showPage(i); $('pages-dialog').close(); $('page-sheet').focus({ preventScroll: true }); });
    $('page-grid').append(tile);
  });
  document.addEventListener('keydown', event => {
    if ($('pages-dialog').open || $('zoom-dialog').open || /INPUT|SELECT|TEXTAREA/.test(event.target.tagName)) return;
    if (event.key === 'ArrowRight') { event.preventDefault(); showPage(index + 1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); showPage(index - 1); }
    if (event.code === 'Space' && (event.target === document.body || event.target === $('page-sheet'))) { event.preventDefault(); $('play').click(); }
  });
  $('page-sheet').addEventListener('pointerdown', event => { if (event.pointerType === 'touch') pointerStart = { x: event.clientX, y: event.clientY }; });
  $('page-sheet').addEventListener('pointerup', event => {
    if (!pointerStart) return;
    const dx = event.clientX - pointerStart.x;
    const dy = event.clientY - pointerStart.y;
    pointerStart = null;
    if (Math.abs(dx) > 60 && Math.abs(dy) < 70) showPage(index + (dx < 0 ? 1 : -1));
  });
  $('page-sheet').addEventListener('pointercancel', () => { pointerStart = null; });
  const readHash = () => Math.max(0, Math.min(pages.length - 1, (Number(location.hash.match(/^#page-(\d+)$/)?.[1]) || 1) - 1));
  window.addEventListener('hashchange', () => showPage(readHash()));
  showPage(readHash(), { initial: true });
})();
