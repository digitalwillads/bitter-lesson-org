#!/usr/bin/env python3
"""Build slides.html from index.html.

The page is the source of truth. This script lifts each scene's copy and
picture out of index.html and lays them out one per slide, so the two files
never drift. Run it after any edit to index.html:

    python3 build_slides.py
"""
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "index.html"
OUT = HERE / "slides.html"

# Slide order and composition. `split` = copy left, picture right.
# `flip` = picture left, copy right. `full` = one-line copy on top, picture below.
SCENES = [
    ("lesson", "split"),
    ("meaning", "flip"),
    ("system", "full"),
    ("playbook", "split"),
    ("gate", "flip"),
    ("specialists", "split"),
    ("rounds", "flip"),
    ("people", "full"),
    ("compounds", "split"),
]


def between(text, start, end, what):
    a = text.find(start)
    b = text.find(end, a)
    if a < 0 or b < 0:
        sys.exit(f"build_slides: marker for {what} not found ({start!r} .. {end!r})")
    return text[a + len(start):b]


def section(html, sid):
    m = re.search(r'<section class="scene[^"]*" id="%s">(.*?)</section>' % re.escape(sid), html, re.S)
    if not m:
        sys.exit(f"build_slides: section #{sid} not found")
    return m.group(1)


def part(block, tag_open_re, what):
    m = re.search(tag_open_re, block, re.S)
    if not m:
        sys.exit(f"build_slides: {what} not found")
    return m.group(0)


def main():
    t0 = time.perf_counter()
    html = SRC.read_text()
    print(f"[build_slides] read {SRC.name}: {len(html):,} chars")

    tokens = between(html, "/* @tokens-start */", "/* @tokens-end */", "tokens")
    shared = between(html, "/* @shared-start */", "/* @shared-end */", "shared css")
    print(f"[build_slides] tokens {len(tokens):,} chars, shared css {len(shared):,} chars")

    slides = []
    for sid, comp in SCENES:
        block = section(html, sid)
        copy = part(block, r'<div class="copy">.*?</div>\s*(?=<figure)', f"copy for #{sid}")
        figure = part(block, r'<figure class="anim[^>]*>.*?</figure>', f"figure for #{sid}")
        table = ""
        if "<table" in block:
            table = part(block, r'<table.*?</table>', f"table for #{sid}")
            table = re.sub(r' style="grid-column:1/-1"', "", table)
        n_svg = figure.count("<svg")
        vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', figure)
        if not vb:
            sys.exit(f"build_slides: no viewBox in figure for #{sid}")
        ar = int(vb.group(1)) / int(vb.group(2))
        figure = figure.replace('<figure class="anim', f'<figure style="--ar:{ar:.4f}" class="anim', 1)
        print(f"[build_slides] slide {sid:<12} {comp:<5} copy {len(copy):>5} chars, figure {len(figure):>6} chars, svg {n_svg} ar {ar:.2f}, table {'yes' if table else 'no'}")
        slides.append((sid, comp, copy, figure, table))

    body = []
    body.append(TITLE)
    for sid, comp, copy, figure, table in slides:
        body.append(f'<section class="slide {comp}" id="{sid}">\n{copy}\n{figure}\n{table}\n</section>')
    body.append(SETUP)
    body.append(QUOTE)

    out = TEMPLATE.replace("/*TOKENS*/", tokens).replace("/*SHARED*/", shared).replace("<!--SLIDES-->", "\n\n".join(body))
    OUT.write_text(out)
    n_slides = out.count('<section class="slide')
    print(f"[build_slides] wrote {OUT.name}: {len(out):,} chars, {n_slides} slides, {1000*(time.perf_counter()-t0):.0f} ms")


TITLE = '''<section class="slide title" id="title">
  <svg class="bg" viewBox="0 0 600 600" aria-hidden="true">
    <circle cx="300" cy="300" r="250" class="ringbg"/>
    <circle id="titledot" class="dot" r="9"/>
  </svg>
  <div class="copy">
    <h1>Run the agency the way the labs run AI.</h1>
    <p class="lead">The Bitter Lesson, applied to Digital Will.</p>
    <p class="src">Rich Sutton, 2019. Six paragraphs. Read it once.</p>
    <div class="key"><span><i class="b"></i>the agents work</span><span><i class="a"></i>a person decides</span><span><i class="g"></i>the old way</span></div>
  </div>
</section>'''

SETUP = '''<section class="slide setup" id="setup">
  <div class="copy">
    <h2>What we set up</h2>
    <ol>
      <li><b>Everyone works in Claude Code inside CMUX.</b> Barbara is the hub for clients, email, meetings, tasks and Slack.</li>
      <li><b>One playbook folder.</b> One MD per SOP. One MD per client. One exceptions log.</li>
      <li><b>The hook and the leadership channel.</b> Exceptions in. SOP updates out. Approved in Slack. Live on the next round.</li>
    </ol>
  </div>
</section>'''

QUOTE = '''<section class="slide quote" id="quote">
  <blockquote>We want AI agents that can discover like we can, not which contain what we have discovered.<footer>Rich Sutton, The Bitter Lesson</footer></blockquote>
</section>'''

TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>The Loop, slides</title>
<meta name="description" content="Slides: how Digital Will runs the agency as one learning loop. The Bitter Lesson, applied.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
/*TOKENS*/
  *{box-sizing:border-box}
  html,body{height:100%;margin:0;overflow:hidden}
  body{background:var(--bg);color:var(--ink);font:18px/1.5 Inter,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
  a{color:var(--blue)}
  button:focus-visible{outline:2px solid var(--focus);outline-offset:3px}

  /* deck */
  .deck{height:100dvh;overflow-y:auto;scroll-snap-type:y mandatory;scroll-behavior:smooth;-webkit-overflow-scrolling:touch}
  .slide{height:100dvh;scroll-snap-align:start;overflow:hidden;position:relative;isolation:isolate;display:grid;grid-template-columns:minmax(0,4fr) minmax(0,8fr);gap:clamp(24px,4vw,64px);align-items:center;padding:clamp(24px,5vh,56px) clamp(24px,6vw,96px)}
  .slide.flip{grid-template-columns:minmax(0,8fr) minmax(0,4fr)}
  .slide.flip .copy{order:2}
  .slide.full{grid-template-columns:1fr;grid-template-rows:auto minmax(0,1fr);align-items:start;align-content:start;gap:clamp(12px,2vh,24px)}
  .slide.full .copy{display:flex;gap:6px clamp(16px,3vw,48px);align-items:baseline;flex-wrap:wrap}
  .slide.full .copy h2{margin:0}
  .slide.full .copy p{margin:0}
  .slide.full .copy p:not(.lede){display:none}
  .slide.full{--fh:calc(100dvh - 190px)}
  #people{grid-template-rows:auto minmax(0,1fr) auto;--fh:calc(100dvh - 420px)}
  @media (max-width:860px){
    .slide,.slide.flip{grid-template-columns:1fr;grid-template-rows:auto minmax(0,1fr);align-items:start;gap:16px;padding:20px 16px 40px}
    .slide.flip .copy{order:0}
  }

  /* copy */
  .copy h1{font-size:clamp(40px,6.4vw,96px);line-height:1.02;letter-spacing:-.03em;font-weight:800;margin:0 0 .35em;max-width:14ch;text-wrap:balance}
  .copy h2{font-size:clamp(28px,3.6vw,52px);line-height:1.1;letter-spacing:-.02em;font-weight:700;margin:0 0 .5em;text-wrap:balance}
  .copy p{margin:0 0 .7em;max-width:40ch;text-wrap:pretty}
  .copy .lede{font-weight:600;font-size:clamp(20px,2.3vw,32px);line-height:1.3;color:var(--ink)}
  .copy p:not(.lede){font-size:clamp(16px,1.6vw,22px);color:var(--ink2);line-height:1.5}
  .copy .lead{font-size:clamp(20px,2.4vw,34px);color:var(--ink);font-weight:500;max-width:32ch}
  .copy .src{font-size:clamp(14px,1.3vw,18px);color:var(--ink2)}
  .key{display:flex;flex-wrap:wrap;gap:8px 22px;font-size:clamp(14px,1.3vw,18px);color:var(--ink2);margin-top:1.2em}
  .key span{display:inline-flex;align-items:center;gap:8px}
  .key i{display:inline-block;width:.8em;height:.8em;border-radius:50%}
  .key .b{background:var(--blue)}.key .a{background:var(--amber)}.key .g{background:var(--grey)}

  /* pictures */
  .slide{--fh:calc(100dvh - 160px)} /* room for a picture: viewport minus padding, legend and caption */
  figure{margin:0;position:relative;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:clamp(10px,1.4vw,18px);min-width:0;max-width:100%;width:fit-content;justify-self:center;display:flex;flex-direction:column}
  .frame{min-height:0}
  figure svg{display:block;height:auto;font-family:inherit;aspect-ratio:var(--ar);width:min(calc(100vw - 200px),calc(var(--fh) * var(--ar)))}
  .slide.split figure svg,.slide.flip figure svg{width:min(calc((100vw - 200px) * .66),calc(var(--fh) * var(--ar)))}
  figcaption{font-size:clamp(13px,1.2vw,17px);color:var(--ink2);margin:8px 4px 0;text-wrap:pretty;flex:none}
  .replay{position:absolute;top:10px;right:10px;z-index:2;font:inherit;font-size:13px;font-weight:500;color:var(--ink2);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 11px;cursor:pointer;opacity:0;transition:opacity .2s}
  figure.played .replay{opacity:1}
  .replay:hover{color:var(--ink);border-color:var(--line2)}
  .legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:clamp(12px,1.1vw,15px);color:var(--ink2);margin:2px 4px 8px;flex:none}
  .legend span{display:inline-flex;align-items:center;gap:7px}
  .legend i{display:inline-block;width:18px;height:0;border-top:2.5px solid var(--c);border-radius:2px}

/*SHARED*/

  /* title slide */
  .slide.title{grid-template-columns:1fr;align-items:center}
  .slide.title .bg{position:absolute;right:-12vmin;top:50%;transform:translateY(-50%);width:80vmin;height:80vmin;z-index:-1;opacity:.9}
  .ringbg{fill:none;stroke:var(--line);stroke-width:2;stroke-dasharray:6 10}
  .slide.title.play #titledot{offset-path:path("M300 50 A250 250 0 1 1 299.99 50");offset-rotate:0deg;animation:loop 14s linear infinite}
  .slide.title #titledot{opacity:0}
  .slide.title.play #titledot{opacity:1}
  .slide.title .copy{max-width:min(92vw,1100px)}

  /* setup and quote */
  .slide.setup{grid-template-columns:1fr;align-items:center}
  .slide.setup .copy{max-width:min(92vw,1000px)}
  .slide.setup ol{margin:0;padding-left:1.2em;font-size:clamp(18px,2.2vw,30px);line-height:1.4;max-width:34ch}
  .slide.setup li{margin:0 0 .8em;text-wrap:pretty;color:var(--ink2)}
  .slide.setup li b{color:var(--ink);font-weight:600}
  .slide.quote{grid-template-columns:1fr;place-items:center}
  .slide.quote blockquote{margin:0;padding:0 0 0 clamp(18px,2vw,32px);border-left:4px solid var(--amber);max-width:26ch;font-size:clamp(26px,3.4vw,52px);line-height:1.25;letter-spacing:-.015em;font-weight:500;text-wrap:pretty}
  .slide.quote footer{font-size:clamp(14px,1.4vw,20px);color:var(--ink2);margin-top:.8em;font-weight:400}

  /* people table on its slide */
  table{border-collapse:collapse;width:100%;font-size:clamp(13px,1.35vw,19px);background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
  th,td{padding:.45em .8em;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
  th{font-weight:600;color:var(--ink2);background:var(--grey-soft)}
  tr:last-child td{border-bottom:0}
  td:first-child{font-weight:600;white-space:nowrap}
  td.hu{color:var(--amber);font-weight:600}

  /* chrome */
  .deck-progress{position:fixed;top:0;left:0;height:3px;background:var(--blue);z-index:100;transition:width .3s ease;pointer-events:none}
  .deck-dots{position:fixed;right:clamp(10px,1.5vw,20px);top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:8px;z-index:100}
  .deck-dot{width:8px;height:8px;border-radius:50%;background:var(--muted);opacity:.35;border:0;padding:0;cursor:pointer;transition:opacity .2s,transform .2s}
  .deck-dot:hover{opacity:.7}
  .deck-dot.active{opacity:1;transform:scale(1.5);background:var(--blue)}
  .deck-counter{position:fixed;bottom:clamp(10px,2vh,20px);right:clamp(12px,2vw,24px);font-size:13px;color:var(--muted);z-index:100;font-variant-numeric:tabular-nums}
  .deck-hints{position:fixed;bottom:clamp(10px,2vh,20px);left:50%;transform:translateX(-50%);font-size:13px;color:var(--muted);z-index:100;transition:opacity .5s;white-space:nowrap}
  .deck-hints.faded{opacity:0;pointer-events:none}
  @media (max-width:860px){.deck-dots{display:none}}

  @media (prefers-reduced-motion: reduce){
    .deck{scroll-behavior:auto}
    .play *{animation-duration:.01ms!important;animation-delay:0ms!important;animation-iteration-count:1!important}
    .js figure.anim:not(.play) .a1,.js figure.anim:not(.play) .draw{opacity:1;stroke-dashoffset:0}
    svg .dot,svg .sp,#trackdot,#rounddot,#titledot{display:none}
    .replay{display:none}
  }
</style>
<noscript><style>.dot{display:none}</style></noscript>
</head>
<body>
<div class="deck">

<!--SLIDES-->

</div>
<script>
(function(){
  document.documentElement.classList.add('js');
  var t0 = performance.now();
  var deck = document.querySelector('.deck');
  var slides = [].slice.call(document.querySelectorAll('.slide'));
  var current = 0;
  console.log('[slides] init', slides.length, 'slides');

  function play(f, why){
    f.classList.remove('play');
    void f.offsetWidth;
    f.classList.add('play');
    f.classList.add('played');
    console.log('[slides] play', f.id || f.dataset.name, why, Math.round(performance.now()-t0)+'ms');
  }
  function playSlide(s, why){
    if (s.classList.contains('title')) play(s, why);
    var f = s.querySelector('figure.anim');
    if (f) play(f, why);
  }

  // chrome
  var bar = document.createElement('div'); bar.className = 'deck-progress'; document.body.appendChild(bar);
  var dots = document.createElement('div'); dots.className = 'deck-dots';
  slides.forEach(function(s, i){
    var d = document.createElement('button'); d.className = 'deck-dot'; d.type = 'button';
    d.title = 'Slide ' + (i+1) + ': ' + (s.querySelector('h1,h2,blockquote') || {textContent:''}).textContent.trim().slice(0,60);
    d.addEventListener('click', function(){ goTo(i); });
    dots.appendChild(d);
  });
  document.body.appendChild(dots);
  var dotEls = [].slice.call(dots.children);
  var counter = document.createElement('div'); counter.className = 'deck-counter'; document.body.appendChild(counter);
  var hints = document.createElement('div'); hints.className = 'deck-hints'; hints.textContent = '← → to move, r to replay, f for full screen'; document.body.appendChild(hints);
  var hintTimer = setTimeout(function(){ hints.classList.add('faded'); }, 5000);
  function fadeHints(){ clearTimeout(hintTimer); hints.classList.add('faded'); }

  function update(){
    bar.style.width = ((current+1)/slides.length*100) + '%';
    dotEls.forEach(function(d, i){ d.classList.toggle('active', i === current); });
    counter.textContent = (current+1) + ' / ' + slides.length;
    try { history.replaceState(null, '', '#' + (slides[current].id || (current+1))); } catch(e){}
  }
  function goTo(i){
    i = Math.max(0, Math.min(i, slides.length-1));
    slides[i].scrollIntoView({behavior:'smooth'});
    console.log('[slides] goTo', i+1, slides[i].id);
  }
  function next(){ goTo(current+1); }
  function prev(){ goTo(current-1); }

  document.addEventListener('keydown', function(e){
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target.closest('input, textarea, [contenteditable]')) return;
    if (['ArrowDown','ArrowRight',' ','PageDown'].indexOf(e.key) >= 0){ e.preventDefault(); next(); }
    else if (['ArrowUp','ArrowLeft','PageUp'].indexOf(e.key) >= 0){ e.preventDefault(); prev(); }
    else if (e.key === 'Home'){ e.preventDefault(); goTo(0); }
    else if (e.key === 'End'){ e.preventDefault(); goTo(slides.length-1); }
    else if (e.key === 'r'){ playSlide(slides[current], 'key'); }
    else if (e.key === 'f'){
      if (document.fullscreenElement) document.exitFullscreen && document.exitFullscreen();
      else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
      else if (document.documentElement.webkitRequestFullscreen) document.documentElement.webkitRequestFullscreen();
    }
    else return;
    fadeHints();
  });
  var touchY;
  deck.addEventListener('touchstart', function(e){ touchY = e.touches[0].clientY; }, {passive:true});
  deck.addEventListener('touchend', function(e){ var dy = touchY - e.changedTouches[0].clientY; if (Math.abs(dy) > 50){ dy > 0 ? next() : prev(); } });

  // a slide plays its picture every time it comes into view
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      var i = slides.indexOf(e.target);
      if (e.isIntersecting){ current = i; update(); playSlide(e.target, 'enter'); }
    });
  }, {threshold:.6});
  slides.forEach(function(s){ io.observe(s); });

  slides.forEach(function(s){
    var b = s.querySelector('.replay');
    if (b) b.addEventListener('click', function(){ playSlide(s, 'replay'); });
  });

  // deep link: #playbook or ?slide=4
  var want = -1;
  var q = new URLSearchParams(location.search).get('slide');
  if (q) want = parseInt(q, 10) - 1;
  else if (location.hash) want = slides.findIndex(function(s){ return '#' + s.id === location.hash; });
  if (want > 0){ deck.style.scrollBehavior = 'auto'; slides[want].scrollIntoView(); deck.style.scrollBehavior = ''; console.log('[slides] deep link to', want+1); }
  update();
})();
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
