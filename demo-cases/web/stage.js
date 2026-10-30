'use strict';
// Case stage (Claude Code, 2026-10-29): a looping carousel of cases, kept at the top of the page while scrolling. The
// current case sits in the middle with its neighbours faded at both sides. Each card carries its category, the question in
// a read-only chat-style box and the Replay button. Choosing a card sets #case=<id>; showcase.js loads it in place and the
// recorded run starts replaying.
(function () {
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const COPIES = 3;  // the track holds three copies of the cases, so there is always a neighbour on each side
  let cases = [], current = 0, pos = 0, settle = null;
  const root = document.createElement('section');
  root.id = 'stage-cases';
  root.setAttribute('aria-label', 'Examples');
  const workspace = document.getElementById('workspace');
  workspace.parentNode.insertBefore(root, workspace);
  const n = () => cases.length;

  function idFromHash() {
    const m = location.hash.match(/^#case=([a-z0-9-]+)$/);
    return m ? m[1] : null;
  }

  function slideHtml(c, i, k) {
    return '<article class="stage-slide" data-pos="' + k + '">' +
      '<div class="card-top"><span>' + esc(c.category) + '</span><span>' + String(i + 1).padStart(2, '0') + ' / ' +
      String(n()).padStart(2, '0') + '</span></div>' +
      '<div class="stage-ask" aria-label="Question"><p>' + esc(c.question) + '</p>' +
      '<button class="button primary stage-replay" type="button" tabindex="-1" aria-label="Play" title="Play">▶</button></div></article>';
  }

  // start the replay once showcase.js has loaded the chosen case
  let autoplayToken = 0;
  function autoplay() {
    const token = ++autoplayToken, run = cases[current].run, started = Date.now();
    window.lamuirHoldFollow = false;
    (function wait() {
      if (token !== autoplayToken) return;
      const meta = document.getElementById('case-meta'), watch = document.getElementById('watch');
      if (meta && watch && meta.textContent.indexOf(run) >= 0) { noteMissingData(); return void watch.click(); }
      if (Date.now() - started < 8000) setTimeout(wait, 120);
    })();
  }

  function render() {
    let slides = '';
    for (let copy = 0; copy < COPIES; copy++) cases.forEach((c, i) => { slides += slideHtml(c, i, copy * n() + i); });
    root.innerHTML =
      '<div class="stage-viewport"><button class="stage-arrow prev" aria-label="Previous example">‹</button>' +
      '<div class="stage-track">' + slides + '</div><button class="stage-arrow next" aria-label="Next example">›</button></div>';
    root.querySelectorAll('.stage-slide').forEach(el => el.addEventListener('click', () => step(+el.dataset.pos - pos)));
    root.querySelectorAll('.stage-replay').forEach(el => el.addEventListener('click', e => {
      const slide = el.closest('.stage-slide');
      if (+slide.dataset.pos !== pos) return;  // on a side card the click only brings that case to the middle
      e.stopPropagation();
      togglePlay();
    }));
    root.querySelector('.prev').addEventListener('click', () => step(-1));
    root.querySelector('.next').addEventListener('click', () => step(1));
    pos = n() + current;
    place(false);
  }

  // The card button plays and pauses. showcase.js keeps the hidden #play button's label in step with the replay
  // ("Pause" while playing, "Resume" when paused, "Replay code" / "Replay again" before and after a run).
  function togglePlay() {
    const play = document.getElementById('play'), watch = document.getElementById('watch');
    const label = play ? play.textContent : '';
    if (/Pause|Resume/.test(label)) play.click();
    else if (watch) watch.click();
  }

  function showPlayState() {
    const play = document.getElementById('play');
    const playing = !!play && /Pause/.test(play.textContent);
    root.querySelectorAll('.stage-slide.current .stage-replay').forEach(b => {
      b.textContent = playing ? '❚❚' : '▶';
      b.setAttribute('aria-label', playing ? 'Pause' : 'Play');
      b.title = playing ? 'Pause' : 'Play';
    });
    root.querySelectorAll('.stage-slide:not(.current) .stage-replay').forEach(b => { b.textContent = '▶'; });
  }

  function place(animate) {
    const track = root.querySelector('.stage-track'), slide = track && track.children[pos];
    if (!slide) return;
    track.style.transition = animate ? '' : 'none';
    const viewport = root.querySelector('.stage-viewport');
    track.style.transform = 'translateX(' + (viewport.clientWidth / 2 - (slide.offsetLeft + slide.offsetWidth / 2)) + 'px)';
    if (!animate) { void track.offsetWidth; requestAnimationFrame(() => { track.style.transition = ''; }); }
    track.querySelectorAll('.stage-slide').forEach((s, k) => {
      s.classList.toggle('current', k === pos);
      s.setAttribute('aria-hidden', String(k !== pos));
      const b = s.querySelector('.stage-replay');
      if (b) b.tabIndex = k === pos ? 0 : -1;
    });
    showPlayState();
  }

  function step(delta) {
    if (!delta) return;
    pos += delta;
    current = ((pos % n()) + n()) % n();
    place(true);
    clearTimeout(settle);
    // after the slide, jump back to the middle copy so the loop never runs out of neighbours
    settle = setTimeout(() => { if (pos < n() || pos >= 2 * n()) { pos = n() + current; place(false); } }, 480);
    const id = cases[current].id;
    if (idFromHash() !== id) {
      history.replaceState(null, '', '#case=' + id);
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    }
    autoplay();
  }

  function goTo(i) {
    let delta = i - current;  // take the shorter way round the loop
    if (delta > n() / 2) delta -= n();
    if (delta < -n() / 2) delta += n();
    step(delta);
  }

  function stickBelowHeader() {
    const header = document.querySelector('header'), h = header ? header.getBoundingClientRect().height : 0;
    root.style.setProperty('--stage-top', h + 'px');
    document.documentElement.style.setProperty('--pinned-bottom', h + root.getBoundingClientRect().height + 'px');
  }

  // the four step tabs join the pinned stage, so they stay in view during a replay
  function pinStepTabs() {
    const steps = document.querySelector('#workspace .tabs');
    if (steps && steps.parentNode !== root) root.appendChild(steps);
  }

  // a case without data files says so on the data tab, before the full task text
  function noteMissingData() {
    const previews = document.getElementById('previews'), files = document.getElementById('input-files');
    if (!previews) return;
    let note = document.getElementById('stage-no-data');
    const empty = !previews.children.length && !(files && files.children.length);
    if (empty && !note) {
      note = document.createElement('p');
      note.id = 'stage-no-data';
      note.className = 'stage-note';
      note.textContent = 'This case has no data file: every input is a parameter stated in the task below.';
      previews.parentNode.insertBefore(note, previews);
    } else if (!empty && note) note.remove();
  }

  // the reader scrolling the notebook pauses the replay's auto-follow until another case is chosen
  window.lamuirHoldFollow = false;
  ['wheel', 'touchstart', 'pointerdown', 'keydown'].forEach(type => document.addEventListener(type, e => {
    if (e.target.closest && e.target.closest('#notebook')) window.lamuirHoldFollow = true;
  }, {passive: true}));

  window.addEventListener('hashchange', () => {
    const i = cases.findIndex(c => c.id === idFromHash());
    if (i >= 0 && i !== current) goTo(i);
  });
  window.addEventListener('resize', () => { place(false); stickBelowHeader(); });
  window.addEventListener('load', () => { place(false); stickBelowHeader(); });
  if (window.ResizeObserver) {
    new ResizeObserver(() => place(false)).observe(root.parentNode);
    new ResizeObserver(stickBelowHeader).observe(root);
  }
  document.addEventListener('keydown', e => {
    if (e.target.closest && e.target.closest('textarea, input, select')) return;
    if (e.key === 'ArrowLeft') step(-1);
    if (e.key === 'ArrowRight') step(1);
  });

  fetch('coverage-cases.json').then(r => r.json()).then(data => {
    cases = data;
    const i = cases.findIndex(c => c.id === idFromHash());
    current = i >= 0 ? i : 0;
    render();
    const play = document.getElementById('play');
    if (play) new MutationObserver(showPlayState).observe(play, {childList: true, characterData: true, subtree: true});
    pinStepTabs();
    stickBelowHeader();
    autoplay();
  });
})();
