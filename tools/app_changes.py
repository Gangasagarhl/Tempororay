"""Apply exact text changes to the lab's page code, stopping if any target is missing."""
import pathlib

import sys
path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
changes = [
    ('''  var byId = {}, place = {}, DATA = {}, loaded = {}, waiting = {};
  var cur = null;

  C.items.forEach(function (m) { byId[m[0]] = m; });
  C.groups.forEach(function (g) {
    g.sections.forEach(function (s) {
      s.items.forEach(function (id, i) { place[id] = { g: g, s: s, i: i }; });
    });
  });
''', '''  var byId = {}, place = {}, DATA = {}, loaded = {}, waiting = {}, secByFile = {}, secWaiting = {}, searchRows = null, searchWaiting = [];
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
    var m = /^r(\\d+)_/.exec(id);
    return m && secByFile[m[1]] ? secByFile[m[1]] : null;
  }
  window.__search = function (text) {
    searchRows = text.split("\\n").map(function (line) { return { line: line, low: line.toLowerCase() }; });
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
'''),
    ('''    out = out.replace(/!\\[[^\\]]*\\]\\([^)]*\\)/g, "");
    out = out.replace(/\\[([^\\]]+)\\]\\(([^)\\s]+)\\)/g, function (_, label, url) {
      var clean = url.split("#")[0].replace(/\\.md$/, "").replace(/\\/$/, "").replace(/^https:\\/\\/(docs|reference)\\.langchain\\.com/, "");
      if (C.urls[clean]) return '<a href="#/' + C.urls[clean] + '">' + label + "</a>";
''', '''    out = out.replace(/!\\[([^\\]]*)\\]\\(([^)]*)\\)/g, function (_, alt, src) { return /^media\\//.test(src) ? '<img src="' + src + '" alt="' + alt + '" loading="lazy" style="max-width:100%;height:auto;display:block;margin:10px 0">' : "<em>[Picture: " + (alt || "no caption") + "]</em>"; });
    out = out.replace(/\\[([^\\]]+)\\]\\(([^)\\s]+)\\)/g, function (_, label, url) {
      if (url.indexOf("#/") === 0) return '<a href="' + url + '">' + label + "</a>";
'''),
    ('''      var count = g.sections.reduce(function (a, s) { return a + s.items.length; }, 0);''',
     '''      var count = g.sections.reduce(function (a, s) { return a + s.n; }, 0);'''),
    ('''var total = C.items.length, finished''', '''var total = C.total, finished'''),
    ('''    g.sections.forEach(function (s, n) {
      html += '<details class="sec" data-n="' + n + '"' + (n === 0 ? " open" : "") + "><summary>" + esc(s.title) + " <span>(" + s.items.length + ")</span></summary><ul class=list></ul></details>";
    });
''', '''    var pack = null;
    g.sections.forEach(function (s, n) {
      var cut = s.title.indexOf(" · "), head = cut > 0 ? s.title.slice(0, cut) : null;
      if (head && head !== pack) { html += '<h2 style="font:600 20px Georgia,serif;margin:22px 0 6px">' + esc(head) + "</h2>"; pack = head; }
      html += '<details class="sec" data-n="' + n + '"' + (n === 0 ? " open" : "") + "><summary>" + esc(cut > 0 ? s.title.slice(cut + 3) : s.title) + " <span>(" + s.n + ")</span></summary><ul class=list></ul></details>";
    });
'''),
    ('''      ul.innerHTML = g.sections[+d.dataset.n].items.map(function (x) {
        return '<li><a href="#/' + x + '"' + (done[x] ? ' class="done"' : "") + ">" + esc(byId[x][1]) + "</a></li>";
      }).join("");
    }
''', '''      var sec = g.sections[+d.dataset.n];
      loadSection(sec, function () {
        ul.innerHTML = sec.r.map(function (m) {
          return '<li><a href="#/' + m[0] + '"' + (done[m[0]] ? ' class="done"' : "") + ">" + esc(m[1]) + "</a></li>";
        }).join("");
      });
    }
'''),
    ('''    var hits = [];
    for (var i = 0; i < C.items.length; i++) {
      var m = C.items[i], title = m[1].toLowerCase(), hay = title + " " + String(m[3]).toLowerCase(), ok = true;
      for (var w = 0; w < words.length; w++) if (hay.indexOf(words[w]) < 0) { ok = false; break; }
      if (ok) hits.push([(title.indexOf(words[0]) === 0 ? 0 : title.indexOf(words[0]) > 0 ? 1 : 2) + (m[2] === "Simulation" ? -1 : 0) + title.length / 1000, m]);
    }
''', '''    if (!searchRows) {
      main.innerHTML = '<div class="wrap"><h1>Search</h1><p class="lead">Loading the list of every topic…</p></div>';
      return loadSearch(function () { if (q.value === text) search(text); });
    }
    var hits = [];
    for (var i = 0; i < searchRows.length; i++) {
      var row = searchRows[i], ok = true;
      for (var w = 0; w < words.length; w++) if (row.low.indexOf(words[w]) < 0) { ok = false; break; }
      if (!ok) continue;
      var m = row.line.split("\\t"), title = m[1].toLowerCase(), simple = title.split(".").pop();
      hits.push([(simple === words[0] ? -2 : title.indexOf(words[0]) === 0 ? 0 : title.indexOf(words[0]) > 0 ? 1 : 2) + (m[2] === "Simulation" ? -1 : 0) + title.length / 1000, m]);
    }
'''),
    ('''    if (!byId[id]) return home();
    main.innerHTML = '<div class="wrap"><p class="lead">Loading…</p></div>';
    load(id, function () {
      var it = DATA[id];
      cur = { id: id, it: it, seq: it.steps.slice(), i: Math.max(0, Math.min(step || 0, it.steps.length - 1)) };
      renderNav(place[id] ? place[id].g.id : null);
      draw(true);
    });
  }
''', '''    var at = sectionOf(id);
    if (!at && !byId[id]) return home();
    main.innerHTML = '<div class="wrap"><p class="lead">Loading…</p></div>';
    loadSection(at && at.s, function () {
      if (!byId[id]) return home();
      var p = place[id], following = p.g.sections[p.g.sections.indexOf(p.s) + 1];
      loadSection(following, function () {
        load(id, function () {
          var it = DATA[id];
          cur = { id: id, it: it, seq: it.steps.slice(), i: Math.max(0, Math.min(step || 0, it.steps.length - 1)) };
          renderNav(p.g.id);
          draw(true);
        });
      });
    });
  }
'''),
    ('''    if (p.i + 1 < p.s.items.length) return p.s.items[p.i + 1];
    var secs = p.g.sections, n = secs.indexOf(p.s);
    return n + 1 < secs.length ? secs[n + 1].items[0] : null;
''', '''    if (p.i + 1 < p.s.r.length) return p.s.r[p.i + 1][0];
    var secs = p.g.sections, n = secs.indexOf(p.s);
    return n + 1 < secs.length && secs[n + 1].r ? secs[n + 1].r[0][0] : null;
'''),
    ('''var body = c && typeof c === "object" ? (C.urls[c.u] ? '<a href="#/' + C.urls[c.u] + '">' + esc(c.t) + "</a>" : esc(c.t)) : esc(c);''',
     '''var body = c && typeof c === "object" ? '<a href="#/' + c.i + '">' + esc(c.t) + "</a>" : esc(c);'''),
    ('''var code = step.code != null ? step.code : it.code,''', '''var code = step.cr ? it.codes[step.cr] : step.code != null ? step.code : it.code,'''),
    ('''"</h2><div id=now>" + md(step.t) + "</div></section>";''',
     '''"</h2><div id=now>" + md(step.t) + "</div>" + (step.o ? '<p><button id="orig" type="button">Show the original wording</button></p>' : "") + "</section>";'''),
    ('''    $("#back").onclick = back;''',
     '''    var orig = $("#orig");
    if (orig) orig.onclick = function () {
      var showing = orig.dataset.on === "1";
      $("#now").innerHTML = md(showing ? step.t : step.o);
      orig.dataset.on = showing ? "0" : "1";
      orig.textContent = showing ? "Show the original wording" : "Show the simpler wording";
    };
    $("#back").onclick = back;'''),
    ('''var body = c && typeof c === "object" ? '<a href="#/' + c.i + '">' + esc(c.t) + "</a>" : esc(c);''',
     '''var body = c && typeof c === "object" ? (c.i ? '<a href="#/' + c.i + '">' + esc(c.t) + "</a>" : '<span title="' + esc(c.o) + '">' + esc(c.t) + "</span>") : esc(c);'''),
]
for old, new in changes:
    if text.count(old) != 1:
        raise SystemExit("NOT FOUND ONCE: " + old[:80])
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
print("applied", len(changes))

