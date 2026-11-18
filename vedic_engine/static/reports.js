// Reports tab: current issues, what's wrong, full kundli, life areas, varshphal, Lal Kitab.
// Uses globals from index.html (t, T, api, esc, last, places, northChart, planetLabels, ...).
let curRep = "issues";
let BOOKS = {lalkitab: 0, bhrigu: 0};
fetch("/books/status").then(r => r.json()).then(j => BOOKS = j).catch(() => {});
const pad3 = n => String(n).padStart(3, "0");
function pageLinks(kind, pages, printedOffset) {
  if (!BOOKS[kind]) return `<span class="note">${t("books_missing")}</span>`;
  return pages.map(p => `<a href="/books/${kind}/p${pad3(p)}.jpg" target="_blank" rel="noopener" class="chip gray" style="text-decoration:none">${t("view_page")} ${kind === "lalkitab" ? (p <= 142 ? p - 20 : p - 22) : p + printedOffset}</a>`).join(" ");
}
const repCache = {};
const AREA = a => (I18N.ui["area_" + a] ? t("area_" + a) : a.replace(/_/g, " "));
const sevChip = n => `<span class="chip ${n >= 3 ? 'bad' : (n == 2 ? 'mixed' : 'gray')}">${t("severity")} ${n}</span>`;
const prioChip = p => `<span class="chip ${p === 'high' ? 'bad' : (p === 'medium' ? 'mixed' : 'gray')}">${t(p)}</span>`;

function lkChart(houses) {               // {planet: house} drawn with house 1 at the top
  const by = {}; for (let i = 0; i < 12; i++) by[i] = [];
  for (const [p, h] of Object.entries(houses)) by[h - 1].push(abbr(p));
  return northChart(0, by);
}

async function loadReport(kind) {
  curRep = kind;
  document.querySelectorAll("#subtabs button").forEach(b => b.classList.toggle("on", b.dataset.rep === kind));
  if (!last) { $("#repout").innerHTML = `<div class="empty">${t("need_chart")}</div>`; return; }
  const ep = {issues: "issues", wrong: "full", full: "full", life: "life-areas", varsh: "varshphal", lk: "lal-kitab", bhrigu: "bhrigu"}[kind];
  const year = parseInt($("#repyear").value) || new Date().getFullYear();
  const key = `${ep}|${LANG}|${year}|${JSON.stringify(last.input)}`;
  $("#repout").innerHTML = `<div class="empty">…</div>`;
  try {
    const data = repCache[key] || (repCache[key] = await api(`/report/${ep}`, {...last.input, lang: LANG, year, at: nowIn(last.input.tz)}));
    ({issues: renderIssues, wrong: renderWrong, full: renderFull, life: renderLife, varsh: renderVarsh, lk: renderLK, bhrigu: renderBhrigu})[kind](data);
  } catch (e) { $("#repout").innerHTML = `<p class="err" style="display:block">${esc(e.message)}</p>`; }
}

function headerBlock(title) {
  const c = last.chart;
  return `<h2>${title}</h2><p class="note">${esc($("#name").value || "")} · ${last.input.datetime_local.replace("T", " ")} · ${esc(places.birth?.name || "")} · ${t("lagna")}: ${T(c.lagna.sign)} · ${t("moon_sign")}: ${T(c.planets.Moon.sign)} · ${t("nakshatra")}: ${T(c.planets.Moon.nakshatra.name)}</p>`;
}

function remedyBoxes(rem) {
  let h = `<div class="rem">`;
  const lk = rem.lal_kitab || [];
  h += `<div class="box"><h5>${t("lk_upay")}</h5>` + (lk.length ? lk.map(x => `<div><b>${T(x.planet)} – ${t("house")} ${x.house}</b> (${x.kind === 'annual' ? t("this_year") : t("natal")}) <span class="note">“${esc(x.title_hi)}”</span><ul>${x.upay.map(u => `<li>${esc(u)}</li>`).join("")}</ul><div class="note">${esc(x.source)}</div></div>`).join("") : `<p class="note">${t("upay_pending")}</p>`) + `</div>`;
  if (rem.lal_kitab_quick) h += `<div class="box"><h5>${t("lk_quick")}</h5><b>${esc(rem.lal_kitab_quick.text)}</b><div class="note">${esc(rem.lal_kitab_quick.source)}</div>${rem.lal_kitab_help ? `<hr style="border:0;border-top:1px solid var(--line)"><h5>${t("lk_help")}</h5>${esc(rem.lal_kitab_help.text)}<div class="note">${esc(rem.lal_kitab_help.source)}</div>` : ""}</div>`;
  const a = rem.pvr_arudha;
  h += `<div class="box"><h5>${t("pvr_arudha")}</h5>${t("fast_on")}: <b>${esc(a.fast_day)}</b><br>${t("worship")}: <b>${esc(a.deity)}</b> (${esc(a.avatar)})<div class="note">${esc(a.source)}</div></div>`;
  const d = rem.pvr_deity, p = rem.parashari;
  h += `<div class="box"><h5>${t("pvr_deity")}</h5>${T(d.planet)}: <b>${esc(d.deity)}</b> · ${esc(d.avatar)}<div class="note">${esc(d.source)}</div></div>`;
  h += `<div class="box"><h5>${t("parashari")}</h5><b>${esc(p.mantra)}</b><br>${p.japa.toLocaleString()} ${t("japa")} · ${t("on_day")}: ${esc(p.day)}<br>${t("daana")}: ${esc(p.daana)}<br><span class="note">${esc(p.practice)}</span></div>`;
  return h + `</div>`;
}

function afflList(list) {
  if (!list.length) return `<p class="note">${t("no_afflictions")}</p>`;
  let h = "";
  for (const cat of ["dosha", "yuti", "position"]) {
    const xs = list.filter(a => a.category === cat); if (!xs.length) continue;
    h += `<h3>${t("cat_" + cat)} (${xs.length})</h3>` + xs.map(a => `<div class="finding ${a.severity >= 3 ? 'challenging' : (a.severity == 2 ? 'mixed' : '')}"><h4>${esc(a.text)} ${sevChip(a.severity)}</h4>
      <div class="src">${t("house")}: ${a.houses.join(", ")} · ${t("affects")}: ${a.areas.map(AREA).join(", ")}</div></div>`).join("");
  }
  return h;
}

function rinBlock(rin, rules) {
  let h = `<h2>${t("rin")}</h2>`;
  h += rin.length ? rin.map(x => `<div class="finding challenging"><h4>${esc(x.name)}</h4>
     <p><b>${t("rin_trigger")}:</b> ${x.trigger.map(T).join(", ")} → ${t("house")} ${x.houses.join("/")}</p>
     <p><b>${t("rin_sign")}:</b> ${esc(x.sign)}</p><p><b>${t("family_upay")}:</b> ${esc(x.upay)}</p><div class="src">${esc(x.source)}</div></div>`).join("")
     : `<p class="note">${t("no_rin")}</p>`;
  if (rules && rules.length) h += `<h3>${t("upay_rules")}</h3><ul>${rules.map(r => `<li>${esc(r.text)} <span class="note">(${esc(r.source)})</span></li>`).join("")}</ul>`;
  return h;
}

function renderIssues(r) {
  let h = headerBlock(t("rep_issues"));
  const tp = r.tithi_pravesha, ss = r.sade_sati;
  h += `<div class="summary"><div class="stat"><span>${t("as_of")}</span><b>${fmtD(r.as_of)}</b></div>
    <div class="stat"><span>${t("running_now")}</span><b>${r.dasha_now.map(T).join(" / ")}</b></div>
    <div class="stat"><span>${t("age_running")}</span><b>${r.age_running}</b></div>
    ${tp ? `<div class="stat"><span>${t("tp")}</span><b>${fmtD(tp.moment)} → ${fmtD(tp.valid_until)}</b><span>${t("vara_lord")}: ${T(tp.vara_lord)} · ${t("hora_lord")}: ${T(tp.hora_lord)}</span></div>` : ''}
    <div class="stat"><span>${t("tab_sade")}</span><b>${ss.sade_sati ? T(ss.phase) : (ss.dhaiya ? T(ss.dhaiya) : t("no"))}</b></div></div>`;
  h += r.issues.map(i => `<div class="issue"><div class="head"><div class="rank">${i.rank}</div><h3 style="margin:0">${esc(i.area_name)}</h3>${prioChip(i.priority)}<span class="note">${t("key_planet")}: <b>${T(i.key_planet)}</b> · ${LANG==="hi"?"अंक":"score"} ${i.score}</span></div>
     <div class="bar" style="margin:8px 0"><i style="width:${Math.min(100, i.score * 7)}%"></i></div>
     <b>${t("why")}:</b><ul>${i.evidence.map(e => `<li>${esc(e.text)} <span class="note">(${esc(e.source)})</span></li>`).join("")}</ul>
     <b>${t("remedies")}:</b>${remedyBoxes(i.remedies)}</div>`).join("");
  h += rinBlock(r.rin, r.upay_rules);
  h += `<h2>${t("natal_afflictions")}</h2>` + afflList(r.natal_afflictions);
  h += `<p class="note">${esc(r.disclaimer)}</p>`;
  $("#repout").innerHTML = h;
}

function renderWrong(r) {
  const bad = r.interpretation.filter(f => f.nature === 'challenging' || f.category === 'dosha');
  $("#repout").innerHTML = headerBlock(t("rep_wrong")) + afflList(r.afflictions) +
    (bad.length ? `<h2>${t("cat_dosha")} / ${t("cat_yoga")}</h2>` + bad.map(f => `<div class="finding challenging"><h4>${esc(f.name)}</h4><p>${esc(f.text)}</p><div class="src">${t("source")}: ${esc(f.source)}</div></div>`).join("") : "");
}

function renderFull(r) {
  const c = r.chart, j = r.jaimini, av = r.ashtakavarga;
  const vargas = Object.keys(c.vargas);
  let h = headerBlock(t("rep_full"));
  const d1 = Object.fromEntries(Object.entries(c.planets).map(([p, v]) => [p, v.sign_index - 1]));
  const vchart = D => { const m = Object.fromEntries(Object.entries(c.vargas[D].planets).map(([p, s]) => [p, SIGNS.indexOf(s)])); return northChart(SIGNS.indexOf(c.vargas[D].lagna), planetLabels(m)); };
  h += `<div class="mini">` + ["D1", "D9", "D10", "D2", "D4", "D7", "D12", "D24", "D60"].map(D => `<div class="chartbox"><div class="cap">${D}</div>${D === "D1" ? northChart(c.lagna.sign_index - 1, planetLabels(d1)) : vchart(D)}</div>`).join("") + `</div>`;
  h += `<h3>${t("positions")}</h3><div style="overflow:auto"><table><tr><th>${t("graha")}</th><th>${t("sign")}</th><th>${t("degree")}</th><th>${t("nakshatra")}</th><th>${t("house")}</th><th>${t("dignity")}</th></tr>` +
    Object.entries(c.planets).map(([p, v]) => `<tr><td><b>${T(p)}</b></td><td>${T(v.sign)}</td><td>${v.degree_in_sign}</td><td>${T(v.nakshatra.name)} (${v.nakshatra.pada})</td><td>${v.house}</td><td>${v.dignity === 'n/a' ? '—' : T(v.dignity)}</td></tr>`).join("") + `</table></div>`;
  h += `<h3>${t("vargas_all")}</h3><div style="overflow:auto"><table><tr><th>${t("graha")}</th>${vargas.map(D => `<th>${D}</th>`).join("")}</tr>` +
    [["Lagna", D => c.vargas[D].lagna], ...Object.keys(c.planets).map(p => [p, D => c.vargas[D].planets[p]])]
      .map(([p, f]) => `<tr><td><b>${T(p)}</b></td>${vargas.map(D => `<td>${LANG === 'en' ? f(D).slice(0, 3) : T(f(D))}</td>`).join("")}</tr>`).join("") + `</table></div>`;
  h += `<div class="grid2"><div><h3>${t("karakas")}</h3><table>${Object.entries(j.karakas).map(([k, v]) => `<tr><td><b>${k}</b></td><td>${T(v.planet)}</td><td class="note">${esc(v.meaning)}</td></tr>`).join("")}</table></div>
        <div><h3>${t("arudhas")}</h3><table>${Object.entries(j.arudhas).map(([k, v]) => `<tr><td><b>${k}</b></td><td>${T(v)}</td><td>${t("house")} ${j.arudha_houses[k]}</td></tr>`).join("")}</table></div></div>`;
  h += `<h3>${t("sav")}</h3><div style="overflow:auto"><table><tr>${av.signs.map(s => `<th>${LANG === 'en' ? s.slice(0, 3) : T(s)}</th>`).join("")}<th>Σ</th></tr><tr>${av.sav.map(x => `<td style="${x >= 30 ? 'color:var(--good);font-weight:700' : (x < 25 ? 'color:var(--bad);font-weight:700' : '')}">${x}</td>`).join("")}<td><b>${av.sav.reduce((a, b) => a + b, 0)}</b></td></tr></table></div>`;
  h += `<h3>${t("dasha_ad")}</h3><table><tr><th>${t("mahadasha")}</th><th>${t("start")}</th><th>${t("end")}</th><th>AD</th></tr>` + r.dasha.mahadashas.map(md => `<tr class="${isCurrent(md) ? 'cur' : ''}"><td><b>${T(md.lord)}</b></td><td>${fmtD(md.start)}</td><td>${fmtD(md.end)}</td><td class="note">${md.sub.map(a => `${T(a.lord)} ${a.start.slice(0, 7)}`).join(" · ")}</td></tr>`).join("") + `</table>`;
  h += `<h2>${t("tab_interp")}</h2>` + r.interpretation.map(f => `<div class="finding ${f.nature}"><h4>${esc(f.name)}</h4><p>${esc(f.text)}</p><div class="src">${t("source")}: ${esc(f.source)}</div></div>`).join("");
  h += `<h2>${t("natal_afflictions")}</h2>` + afflList(r.afflictions);
  $("#repout").innerHTML = h;
}

function renderLife(r) {
  $("#repout").innerHTML = headerBlock(t("rep_life")) + r.areas.map(a => `<div class="issue"><div class="head"><h3 style="margin:0">${esc(a.title)}</h3>
     <span class="chip ${a.verdict_key === 'strong' ? 'good' : (a.verdict_key === 'moderate' ? 'mixed' : 'bad')}">${esc(a.verdict)}</span>
     <span class="note">${t("house")} ${a.house} (${T(a.sign)}, ${T(a.lord)}) · ${a.varga} · ${T(a.karaka)}${a.chara_karaka ? ` · ${T(a.chara_karaka)}` : ''}</span></div>
     <ul>${a.points.map(p => `<li>${esc(p.text)}</li>`).join("")}</ul>
     ${a.periods.length ? `<b>${t("periods")}:</b> <span class="note">${a.periods.map(w => `${T(w.md)}–${T(w.ad)} (${w.start.slice(0, 7)} → ${w.end.slice(0, 7)})`).join(" · ")}</span>` : ''}</div>`).join("") +
    `<p class="note">${esc(r.areas[0]?.source || "")}</p>`;
}

function lkPlanetRows(list, annual) {
  return list.map(e => {
    const x = annual ? e.annual : e;
    return `<div class="finding"><h4>${T(e.planet)} – ${t("house")} ${x.house} <span class="note">“${esc(x.title_hi)}”</span> ${x.pakka_ghar ? `<span class="chip good">${t("pakka")}</span>` : ''}</h4>
     ${x.theme ? `<p>${esc(x.theme)}</p>` : ''}${x.upay.length ? `<b>${t("lk_upay")}:</b><ul>${x.upay.map(u => `<li>${esc(u)}</li>`).join("")}</ul>` : `<p class="note">${t("upay_pending")}</p>`}
     <div class="src">Lal Kitab (Arun Sanhita), p. ${x.book_page} · ${t("read_in_book")}: ${pageLinks("lalkitab", x.pdf_pages || [], -20)}</div></div>`;
  }).join("");
}

function renderVarsh(r) {
  const tp = r.tithi_pravesha, tc = tp.chart;
  const d1 = Object.fromEntries(Object.entries(tc.planets).map(([p, v]) => [p, v.sign_index - 1]));
  let h = headerBlock(`${t("rep_varsh")} ${r.year}`);
  h += `<h3>${t("tp")}</h3><div class="summary"><div class="stat"><span>${t("start")}</span><b>${tp.moment.replace("T", " ")}</b></div><div class="stat"><span>${t("valid_until")}</span><b>${tp.valid_until.replace("T", " ")}</b></div>
    <div class="stat"><span>${t("vara_lord")}</span><b>${T(tp.vara_lord)}</b></div><div class="stat"><span>${t("hora_lord")}</span><b>${T(tp.hora_lord)}</b></div><div class="stat"><span>${t("lagna")}</span><b>${T(tc.lagna.sign)}</b></div></div>`;
  h += `<div class="mini"><div class="chartbox"><div class="cap">${t("tp")}</div>${northChart(tc.lagna.sign_index - 1, planetLabels(d1))}</div>
        <div class="chartbox"><div class="cap">${t("lk_annual")} (${t("year")} ${r.age})</div>${lkChart(r.lal_kitab.varshphal.annual_houses)}</div></div>`;
  h += `<table><tr><th>${t("graha")}</th><th>${t("house")} (TP)</th><th>${t("dignity")}</th></tr>${Object.entries(tc.planets).map(([p, v]) => `<tr><td>${T(p)}</td><td>${v.house}</td><td>${v.dignity === 'n/a' ? '—' : T(v.dignity)}</td></tr>`).join("")}</table>`;
  h += `<h3>${t("lk_annual")}</h3>` + lkPlanetRows(r.lal_kitab.planets, true);
  $("#repout").innerHTML = h;
}

function renderLK(r) {
  let h = headerBlock(t("rep_lk")) + `<p class="note">${t("lk_note")}</p>`;
  h += `<div class="mini"><div class="chartbox"><div class="cap">${t("lk_chart")}</div>${lkChart(r.varshphal.natal_houses)}</div>
        <div class="chartbox"><div class="cap">${t("lk_annual")} (${t("age_running")} ${r.age})</div>${lkChart(r.varshphal.annual_houses)}</div></div>`;
  h += `<p><b>${t("empty_houses")}:</b> ${r.empty_houses.join(", ")}</p>`;
  h += lkPlanetRows(r.planets, false);
  h += `<h3>${t("lk_quick")}</h3><ul>${r.quick.filter(Boolean).map(q => `<li><b>${T(q.planet)}:</b> ${esc(q.text)}</li>`).join("")}</ul><p class="note">${esc(r.quick.find(Boolean)?.source || "")}</p>`;
  h += rinBlock(r.rin, r.rules);
  $("#repout").innerHTML = h;
}

function renderBhrigu(r) {
  let h = headerBlock(t("rep_bhrigu")) + `<p class="note">${t("ocr_note")}</p><h3>${t("bhrigu_lagna")}: ${T(r.lagna)}</h3>`;
  h += r.readings.map(x => `<div class="finding"><h4>${T(x.planet)} – ${t("house")} ${x.house} <span class="note">(p. ${x.printed_page})</span></h4>
     ${x.found ? `<p lang="hi">${esc(x.text_hi)}</p><div class="src">${pageLinks("bhrigu", [x.pdf_page], 8)}</div>`
               : `<p class="note">${t("not_split")}</p><div class="src">${pageLinks("bhrigu", x.block_pdf_pages, 8)}</div>`}</div>`).join("");
  h += `<p class="note">${esc(r.source)}</p>`;
  $("#repout").innerHTML = h;
}

// wiring
$("#subtabs").addEventListener("click", e => { const b = e.target.closest("button"); if (b) loadReport(b.dataset.rep); });
document.querySelector('#tabs button[data-tab="reports"]').addEventListener("click", () => loadReport(curRep));
$("#repyear").value = new Date().getFullYear();
$("#repyear").addEventListener("change", () => loadReport(curRep));
const _setLangBase = setLang;
setLang = async function (l) {
  await _setLangBase(l);
  if (document.getElementById("tab-reports").classList.contains("on")) loadReport(curRep);
};
