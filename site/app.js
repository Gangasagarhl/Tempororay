(function () {
  "use strict";
  var C = window.CATALOG, G = window.GLOSSARY || {};
  var $ = function (s) { return document.querySelector(s); };
  var main = $("#main"), nav = $("#nav"), q = $("#q"), tip = $("#tip");
  var byId = {}, place = {}, DATA = {}, loaded = {}, waiting = {}, secByFile = {}, secWaiting = {}, searchRows = null, searchWaiting = [];
  var cur = null;

  function indexSection(g, s) { s.r.forEach(function (m, i) { byId[m[0]] = m; place[m[0]] = { g: g, s: s, i: i }; }); }
  C.groups.forEach(function (g) {
    g.sections.forEach(function (s) {
      if (s.r) indexSection(g, s); else secByFile[s.f] = { g: g, s: s };
    });
  });
  window.__sec = function (f, rows) {
    var at = secByFile[f];
    at.s.r = rows;
    indexSection(at.g, at.s);
    (secWaiting[f] || []).forEach(function (cb) { cb(); });
    delete secWaiting[f];
  };
  function loadSection(s, cb) {
    if (!s || s.r) return cb();
    if (secWaiting[s.f]) return secWaiting[s.f].push(cb);
    secWaiting[s.f] = [cb];
    var el = document.createElement("script");
    el.src = "data/sec/" + s.f + ".js";
    document.head.appendChild(el);
  }
  function sectionOf(id) {
    var m = /^r(\d+)_/.exec(id);
    return m && secByFile[m[1]] ? secByFile[m[1]] : null;
  }
  window.__search = function (text) {
    searchRows = text.split("\n").map(function (line) { return { line: line, low: line.toLowerCase() }; });
    searchWaiting.splice(0).forEach(function (cb) { cb(); });
  };
  function loadSearch(cb) {
    if (searchRows) return cb();
    searchWaiting.push(cb);
    if (searchWaiting.length > 1) return;
    var el = document.createElement("script");
    el.src = "data/search.js";
    document.head.appendChild(el);
  }

  function store(k, v) {
    try {
      if (v === undefined) return JSON.parse(localStorage.getItem(k) || "null");
      localStorage.setItem(k, JSON.stringify(v));
    } catch (e) { return null; }
  }
  var done = store("lab-done") || {};
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  window.__chunk = function (n, obj) {
    Object.keys(obj).forEach(function (k) { DATA[k] = obj[k]; });
    loaded[n] = true;
    (waiting[n] || []).forEach(function (f) { f(); });
    delete waiting[n];
  };
  function load(id, cb) {
    var n = byId[id][4];
    if (loaded[n]) return cb();
    if (waiting[n]) return waiting[n].push(cb);
    waiting[n] = [cb];
    var s = document.createElement("script");
    s.src = "data/chunks/" + n + ".js";
    s.onerror = function () { main.innerHTML = '<div class="wrap"><h1>This topic could not load</h1><p class="lead">The data file is missing. Run the build again.</p></div>'; };
    document.head.appendChild(s);
  }

  function inline(t) {
    var out = esc(t);
    out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
    out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    out = out.replace(/!\[([^\]]*)\]\(([^)]*)\)/g, function (_, alt, src) { return /^media\//.test(src) ? '<img src="' + src + '" alt="' + alt + '" loading="lazy" style="max-width:100%;height:auto;display:block;margin:10px 0">' : "<em>[Picture: " + (alt || "no caption") + "]</em>"; });
    out = out.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (_, label, url) {
      if (url.indexOf("#/") === 0) return '<a href="' + url + '">' + label + "</a>";
      if (/^https?:/.test(url)) return '<a href="' + url + '" target="_blank" rel="noopener">' + label + "</a>";
      return label;
    });
    return out;
  }
  function md(text) {
    var lines = String(text || "").split(/\r?\n/), html = "", i = 0;
    function para(buf) { if (buf.length) html += "<p>" + inline(buf.join(" ")) + "</p>"; }
    var buf = [];
    while (i < lines.length) {
      var l = lines[i], m;
      if (!l.trim()) { para(buf); buf = []; i++; continue; }
      if ((m = l.match(/^(#{1,6})\s+(.*)/))) { para(buf); buf = []; html += "<h4>" + inline(m[2]) + "</h4>"; i++; continue; }
      if (/^\s*\|.*\|\s*$/.test(l)) {
        para(buf); buf = []; var rows = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { rows.push(lines[i]); i++; }
        var cells = function (r) { return r.trim().replace(/^\||\|$/g, "").split("|"); };
        html += '<div class="tablewrap"><table>';
        rows.forEach(function (r, n) {
          if (/^[\s|:-]+$/.test(r)) return;
          html += "<tr>" + cells(r).map(function (c) { return (n ? "<td>" : "<th>") + inline(c.trim()) + (n ? "</td>" : "</th>"); }).join("") + "</tr>";
        });
        html += "</table></div>"; continue;
      }
      if (/^\s*([-*+]|\d+\.)\s+/.test(l)) {
        para(buf); buf = []; var ord = /^\s*\d+\./.test(l), items = [];
        while (i < lines.length && /^\s*([-*+]|\d+\.)\s+/.test(lines[i])) { items.push(lines[i].replace(/^\s*([-*+]|\d+\.)\s+/, "")); i++; }
        html += (ord ? "<ol>" : "<ul>") + items.map(function (x) { return "<li>" + inline(x) + "</li>"; }).join("") + (ord ? "</ol>" : "</ul>"); continue;
      }
      if (/^>/.test(l)) {
        para(buf); buf = []; var qs = [];
        while (i < lines.length && /^>/.test(lines[i])) { qs.push(lines[i].replace(/^>\s?/, "").replace(/^\[!(\w+)\]\s*$/, "**$1**")); i++; }
        html += "<blockquote>" + inline(qs.filter(Boolean).join(" ")) + "</blockquote>"; continue;
      }
      buf.push(l.trim()); i++;
    }
    para(buf);
    return html;
  }

  var termRe = null, termKey = {};
  (function () {
    var keys = Object.keys(G).sort(function (a, b) { return b.length - a.length; });
    keys.forEach(function (k) { termKey[k.toLowerCase()] = k; });
    if (keys.length) termRe = new RegExp("\\b(" + keys.map(function (k) { return k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("|") + ")\\b", "i");
  })();
  function addTerms(root) {
    if (!termRe) return;
    var seen = {}, walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT), nodes = [], n;
    while ((n = walker.nextNode())) if (!n.parentNode.closest("code,a,.term,h2")) nodes.push(n);
    nodes.forEach(function (node) {
      var text = node.nodeValue, frag = null, m;
      while (text && (m = text.match(termRe))) {
        var key = m[1].toLowerCase();
        if (seen[key]) {
          var cut = m.index + m[1].length;
          frag = frag || document.createDocumentFragment();
          frag.appendChild(document.createTextNode(text.slice(0, cut)));
          text = text.slice(cut); continue;
        }
        seen[key] = true;
        frag = frag || document.createDocumentFragment();
        frag.appendChild(document.createTextNode(text.slice(0, m.index)));
        var s = document.createElement("span");
        s.className = "term"; s.tabIndex = 0; s.textContent = m[1]; s.dataset.def = G[termKey[key]];
        frag.appendChild(s);
        text = text.slice(m.index + m[1].length);
      }
      if (frag) { frag.appendChild(document.createTextNode(text)); node.parentNode.replaceChild(frag, node); }
    });
  }
  function showTip(e) {
    var t = e.target.closest && e.target.closest(".term");
    if (!t) return;
    tip.textContent = t.dataset.def; tip.hidden = false;
    var r = t.getBoundingClientRect();
    tip.style.left = Math.max(8, Math.min(r.left, innerWidth - 350)) + "px";
    tip.style.top = (r.bottom + 6 + tip.offsetHeight > innerHeight ? r.top - tip.offsetHeight - 6 : r.bottom + 6) + "px";
  }
  function hideTip(e) { if (e.target.closest && e.target.closest(".term")) tip.hidden = true; }
  document.addEventListener("mouseover", showTip); document.addEventListener("focusin", showTip);
  document.addEventListener("mouseout", hideTip); document.addEventListener("focusout", hideTip);

  function highlight(line, lang) {
    var s = esc(line);
    if (lang === "python" || lang === "py") {
      var parts = s.split(/(&quot;.*?&quot;|'.*?'|#.*$)/);
      return parts.map(function (p) {
        if (/^(&quot;|')/.test(p)) return '<span class="str">' + p + "</span>";
        if (p[0] === "#" && !/^#\d/.test(p)) return '<span class="com">' + p + "</span>";
        return p.replace(/\b(from|import|def|class|return|if|else|elif|for|while|in|not|and|or|try|except|with|as|await|async|yield|raise|None|True|False|lambda|pass)\b/g, '<span class="kw">$1</span>');
      }).join("");
    }
    return s;
  }
  function codeHTML(code, lang, title, hits) {
    var a = hits ? hits[0] : 0, b = hits ? hits[1] : 0;
    var body = String(code).split("\n").map(function (l, i) {
      var n = i + 1;
      return '<span class="ln' + (hits && n >= a && n <= b ? " hit" : "") + '"><b>' + n + "</b>" + highlight(l, lang) + "</span>";
    }).join("");
    return '<section class="box codebox"><h3>' + esc(title || "Code") + '</h3><pre class="code" tabindex="0">' + body + "</pre></section>";
  }
  function fmt(v) { return typeof v === "string" ? v : JSON.stringify(v, null, 2); }

  function renderNav(active) {
    var html = "", last = null;
    C.groups.forEach(function (g) {
      if (g.band !== last) { html += "<h2>" + esc(g.band) + "</h2>"; last = g.band; }
      var count = g.sections.reduce(function (a, s) { return a + s.n; }, 0);
      html += '<a href="#/g/' + g.id + '"' + (g.id === active ? ' class="on"' : "") + ">" + esc(g.title) + "<span>" + count + "</span></a>";
    });
    nav.innerHTML = html;
  }
  function home() {
    renderNav();
    var total = C.total, finished = Object.keys(done).length;
    var band = "", cards = "";
    C.groups.forEach(function (g) {
      if (g.band !== band) { if (band) cards += "</div>"; band = g.band; cards += "<h2 style='font:600 24px Georgia,serif;margin:26px 0 0'>" + esc(band) + '</h2><div class="grid">'; }
      cards += '<a class="card" href="#/g/' + g.id + '"><strong>' + esc(g.title) + "</strong><small>" + esc(g.desc) + "</small></a>";
    });
    main.innerHTML = '<div class="wrap"><h1>Every part of LangChain, one Next press at a time</h1><p class="lead">Nothing here calls a real service. Every topic is a simulation: press Next and watch what moves, which line runs, and what changes in memory. ' + total.toLocaleString() + " topics, " + finished.toLocaleString() + ' finished so far.</p><p><a class="top-next" href="#/' + C.start + '">Start at the first simulation →</a></p><p class="keys">Keyboard: <kbd>→</kbd> or <kbd>Space</kbd> for Next, <kbd>←</kbd> for Back. Dotted words explain themselves when you point at them.</p>' + cards + "</div></div>";
    main.scrollTop = 0;
  }
  function group(id) {
    var g = C.groups.filter(function (x) { return x.id === id; })[0];
    if (!g) return home();
    renderNav(id);
    var html = '<div class="wrap"><h1>' + esc(g.title) + '</h1><p class="lead">' + esc(g.desc) + "</p>";
    var pack = null;
    g.sections.forEach(function (s, n) {
      var cut = s.title.indexOf(" · "), head = cut > 0 ? s.title.slice(0, cut) : null;
      if (head && head !== pack) { html += '<h2 style="font:600 20px Georgia,serif;margin:22px 0 6px">' + esc(head) + "</h2>"; pack = head; }
      html += '<details class="sec" data-n="' + n + '"' + (n === 0 ? " open" : "") + "><summary>" + esc(cut > 0 ? s.title.slice(cut + 3) : s.title) + " <span>(" + s.n + ")</span></summary><ul class=list></ul></details>";
    });
    main.innerHTML = html + "</div>";
    function fill(d) {
      var ul = d.querySelector("ul");
      if (ul.children.length) return;
      var sec = g.sections[+d.dataset.n];
      loadSection(sec, function () {
        ul.innerHTML = sec.r.map(function (m) {
          return '<li><a href="#/' + m[0] + '"' + (done[m[0]] ? ' class="done"' : "") + ">" + esc(m[1]) + "</a></li>";
        }).join("");
      });
    }
    main.querySelectorAll("details").forEach(function (d) { if (d.open) fill(d); d.addEventListener("toggle", function () { if (d.open) fill(d); }); });
    main.scrollTop = 0;
  }
  function search(text) {
    visit++;
    var words = text.toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return route();
    if (!searchRows) {
      main.innerHTML = '<div class="wrap"><h1>Search</h1><p class="lead">Loading the list of every topic…</p></div>';
      return loadSearch(function () { if (q.value === text) search(text); });
    }
    var hits = [];
    for (var i = 0; i < searchRows.length; i++) {
      var row = searchRows[i], ok = true;
      for (var w = 0; w < words.length; w++) if (row.low.indexOf(words[w]) < 0) { ok = false; break; }
      if (!ok) continue;
      var m = row.line.split("\t"), title = m[1].toLowerCase(), simple = title.split(".").pop();
      hits.push([(simple === words[0] ? -2 : title.indexOf(words[0]) === 0 ? 0 : title.indexOf(words[0]) > 0 ? 1 : 2) + (m[2] === "Simulation" ? -1 : 0) + title.length / 1000, m]);
    }
    hits.sort(function (a, b) { return a[0] - b[0]; });
    main.innerHTML = '<div class="wrap"><h1>Search</h1><p class="lead">' + hits.length.toLocaleString() + ' results for “' + esc(text) + '”</p><ul class="hits">' + hits.slice(0, 80).map(function (h) {
      return '<li><a href="#/' + h[1][0] + '">' + esc(h[1][1]) + "</a><small>" + esc(h[1][2]) + " · " + esc(h[1][3]) + "</small></li>";
    }).join("") + "</ul></div>";
    main.scrollTop = 0;
  }

  function openItem(id, step) {
    var at = sectionOf(id);
    if (!at && !byId[id]) return home();
    main.innerHTML = '<div class="wrap"><p class="lead">Loading…</p></div>';
    var mine = visit;  // if the reader moves on before this finishes loading, drop it
    loadSection(at && at.s, function () {
      if (mine !== visit) return;
      if (!byId[id]) return home();
      var p = place[id], following = p.g.sections[p.g.sections.indexOf(p.s) + 1];
      loadSection(following, function () {
        load(id, function () {
          if (mine !== visit) return;
          var it = DATA[id];
          cur = { id: id, it: it, seq: it.steps.slice(), i: Math.max(0, Math.min(step || 0, it.steps.length - 1)) };
          renderNav(p.g.id);
          draw(true);
        });
      });
    });
  }
  function nextId() {
    var p = place[cur.id];
    if (!p) return null;
    if (p.i + 1 < p.s.r.length) return p.s.r[p.i + 1][0];
    var secs = p.g.sections, n = secs.indexOf(p.s);
    return n + 1 < secs.length && secs[n + 1].r ? secs[n + 1].r[0][0] : null;
  }
  function stateAt() {
    var st = {}, order = [];
    for (var n = 0; n <= cur.i; n++) {
      var set = cur.seq[n].s;
      if (!set) continue;
      Object.keys(set).forEach(function (k) {
        if (set[k] === null) { delete st[k]; order = order.filter(function (x) { return x !== k; }); }
        else { if (!(k in st)) order.push(k); st[k] = set[k]; }
      });
    }
    return { st: st, order: order, changed: cur.seq[cur.i].s || {} };
  }
  function draw(fresh) {
    var it = cur.it, step = cur.seq[cur.i], total = cur.seq.length, end = cur.i === total - 1;
    if (end) { done[cur.id] = 1; store("lab-done", done); }
    var html = '<div class="wrap"><div class="badges">' + (it.kind.indexOf("Saved docs") < 0 ? '<span class="badge sim">Simulation</span>' : "") + '<span class="badge">' + esc(it.kind) + "</span>" + (it.beta ? '<span class="badge">Beta product</span>' : "") + "</div><h1>" + esc(it.title) + "</h1>";
    if (it.intro && cur.i === 0) html += '<p class="lead">' + inline(it.intro) + "</p>";
    html += '<div class="bar"><i style="width:' + Math.round((cur.i + 1) / total * 100) + '%"></i></div>';
    if (it.actors && it.actors.length) {
      html += '<div id="stage">' + it.actors.map(function (a) { return '<div class="actor" data-a="' + esc(a) + '">' + esc(a) + "</div>"; }).join("") + "</div>";
    }
    html += '<section class="now" aria-live="polite"><div class="eyebrow">What happens now · step ' + (cur.i + 1) + "</div><h2>" + esc(step.h) + "</h2><div id=now>" + md(step.t) + "</div>" + (step.o ? '<p><button id="orig" type="button">Show the original wording</button></p>' : "") + "</section>";
    if (step.table) {
      html += '<section class="box" style="margin-bottom:16px"><div class="tablewrap" style="padding:0 14px"><table><tr>' + step.table.head.map(function (h) { return "<th>" + esc(h) + "</th>"; }).join("") + "</tr>" + step.table.rows.map(function (r) { return "<tr>" + r.map(function (c, n) { var body = c && typeof c === "object" ? (c.i ? '<a href="#/' + c.i + '">' + esc(c.t) + "</a>" : '<span title="' + esc(c.o) + '">' + esc(c.t) + "</span>") : esc(c); return "<td" + (n === 0 ? ' class="mono"' : "") + ">" + body + "</td>"; }).join("") + "</tr>"; }).join("") + "</table></div></section>";
    }
    if (step.choices) {
      html += '<div class="choices"><strong>What if something different happens?</strong>' + step.choices.map(function (c, n) { return '<button data-c="' + n + '">' + esc(c.label) + "</button>"; }).join("") + "</div>";
    }
    var code = step.cr ? it.codes[step.cr] : step.code != null ? step.code : it.code, lang = step.lang || it.lang || "python", mem = stateAt(), hasMem = mem.order.length > 0 || it.mem;
    if (code || hasMem) {
      html += '<div class="cols' + (code && hasMem ? "" : " one") + '">';
      if (code) html += codeHTML(code, lang, step.codeTitle || it.codeTitle || "Code", step.l || null);
      if (hasMem) {
        html += '<section class="box"><h3>Memory right now</h3><div class="mem">' + (mem.order.length ? mem.order.map(function (k) { return "<div" + (k in mem.changed ? ' class="changed"' : "") + "><b>" + esc(k) + "</b> = " + esc(fmt(mem.st[k])) + "</div>"; }).join("") : '<div class="empty">Empty</div>') + "</div></section>";
      }
      html += "</div>";
    }
    if (end && it.quiz) {
      html += '<section class="quiz"><h3>Check yourself</h3><p>' + inline(it.quiz.q) + "</p>" + it.quiz.a.map(function (a, n) { return '<button data-q="' + n + '">' + esc(a) + "</button>"; }).join("") + '<p id="why" aria-live="polite"></p></section>';
    }
    var nx = end ? nextId() : null;
    if (nx) html += '<p><a class="top-next" href="#/' + nx + '">Next topic: ' + esc(byId[nx][1]) + " →</a></p>";
    html += '</div><div id="controls"><button id="back"' + (cur.i === 0 ? " disabled" : "") + '>Back</button><span>Step ' + (cur.i + 1) + " of " + total + '</span><button id="next" class="next"' + (end && !nx ? " disabled" : "") + ">" + (end ? (nx ? "Next topic" : "Finished") : "Next: what happens?") + "</button></div>";
    main.innerHTML = html;
    addTerms($("#now"));
    if (fresh) main.scrollTop = 0;
    var hit = main.querySelector(".ln.hit"), pre = main.querySelector("pre.code");
    if (hit && pre) pre.scrollTop = Math.max(0, hit.offsetTop - pre.offsetTop - 70);
    var orig = $("#orig");
    if (orig) orig.onclick = function () {
      var showing = orig.dataset.on === "1";
      $("#now").innerHTML = md(showing ? step.t : step.o);
      orig.dataset.on = showing ? "0" : "1";
      orig.textContent = showing ? "Show the original wording" : "Show the simpler wording";
    };
    $("#back").onclick = back;
    $("#next").onclick = advance;
    main.querySelectorAll("[data-c]").forEach(function (b) {
      b.onclick = function () {
        var c = step.choices[+b.dataset.c];
        cur.seq = cur.seq.slice(0, cur.i + 1).concat(it.paths[c.path]);
        cur.i++; draw(false); sync();
      };
    });
    main.querySelectorAll("[data-q]").forEach(function (b) {
      b.onclick = function () {
        var right = +b.dataset.q === it.quiz.c;
        b.classList.add(right ? "right" : "wrong");
        $("#why").innerHTML = (right ? "<strong>Right.</strong> " : "<strong>Not quite.</strong> ") + inline(it.quiz.why);
      };
    });
    animate(step);
  }
  function animate(step) {
    var stage = $("#stage");
    if (!stage || !step.a) return;
    var f = stage.querySelector('[data-a="' + cssq(step.a[0]) + '"]'), t = stage.querySelector('[data-a="' + cssq(step.a[1]) + '"]');
    if (f) f.classList.add("from");
    if (t) t.classList.add("to");
    if (!f || !t || !step.a[2]) return;
    var p = document.createElement("div");
    p.id = "packet"; p.textContent = step.a[2]; stage.appendChild(p);
    var w = p.offsetWidth, W = stage.clientWidth;
    var pos = function (el) { return Math.max(0, Math.min(W - w, el.offsetLeft + el.offsetWidth / 2 - w / 2)); };
    var x0 = pos(f), x1 = pos(t);
    p.style.left = x1 + "px";
    if (p.animate && !matchMedia("(prefers-reduced-motion:reduce)").matches) {
      p.animate([{ transform: "translateX(" + (x0 - x1) + "px)" }, { transform: "translateX(0)" }], { duration: 650, easing: "ease-in-out" });
    }
  }
  function cssq(s) { return String(s).replace(/["\\]/g, "\\$&"); }
  // Update the address once the reader pauses: Chrome ignores pages that change it hundreds of times a second.
  var syncTimer = null;
  function sync() {
    clearTimeout(syncTimer);
    var at = "#/" + cur.id + "/" + cur.i, mine = visit;
    syncTimer = setTimeout(function () { if (mine === visit) history.replaceState(null, "", at); }, 250);
  }
  function advance() {
    if (!cur) return;
    if (cur.i < cur.seq.length - 1) { cur.i++; draw(false); sync(); }
    else { var n = nextId(); if (n) location.hash = "#/" + n; }
  }
  function back() { if (cur && cur.i > 0) { cur.i--; draw(false); sync(); } }

  var visit = 0;
  function route() {
    var parts = location.hash.replace(/^#\/?/, "").split("/");
    visit++;
    cur = null;
    if (!parts[0]) return home();
    if (parts[0] === "g") return group(parts[1]);
    openItem(parts[0], parseInt(parts[1], 10) || 0);
  }
  window.addEventListener("hashchange", route);
  var timer = null;
  q.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { cur = null; search(q.value); }, 140); });
  document.addEventListener("keydown", function (e) {
    if (!cur || /INPUT|TEXTAREA|BUTTON/.test(e.target.tagName) && e.key === " " || e.target === q) return;
    if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); advance(); }
    if (e.key === "ArrowLeft") { e.preventDefault(); back(); }
  });
  route();
})();
