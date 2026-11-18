"""Rules engine: evaluates YAML rules (yogas, doshas, placements) against a chart.

A rule is pure data:

    - id: gajakesari
      name: Gajakesari Yoga
      category: yoga
      when: {planet_in_house: {planet: Jupiter, houses: [1, 4, 7, 10], from: Moon}}
      text: "..."
      source: "Phaladeepika 6.1"
      status: draft            # draft | reviewed  (only 'reviewed' should ship to users)
      remedy_tags: [jupiter]   # hook for the future remedies module

Conditions are built from the primitives in PRIMITIVES and combined with
`all`, `any`, `not`. Astrologers can add rules without touching Python.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

import yaml

from ..constants import EXALTATION, SIGN_LORDS

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
# Graha drishti: houses counted from the planet (7th for all + specials).
# Rahu/Ketu 5th & 9th follow a common modern convention; make configurable if needed.
ASPECTS = {"Mars": {4, 7, 8}, "Jupiter": {5, 7, 9}, "Saturn": {3, 7, 10},
           "Rahu": {5, 7, 9}, "Ketu": {5, 7, 9}}


@dataclass
class Facts:
    """Normalised chart facts the rules read. Signs are 0-11 (Aries = 0)."""
    lagna: int
    signs: dict[str, int]                      # planet -> D1 sign
    dignity: dict[str, str] = field(default_factory=dict)
    d9: dict[str, int] = field(default_factory=dict)
    flags: dict[str, bool] = field(default_factory=dict)   # e.g. {"manglik": True}

    # ---- helpers ----
    def ref_sign(self, ref: str) -> int:
        return self.lagna if ref in ("Lagna", "lagna") else self.signs[ref]

    def house_of(self, planet: str, ref: str = "Lagna") -> int:
        return (self.signs[planet] - self.ref_sign(ref)) % 12 + 1

    def sign_of_house(self, house: int, ref: str = "Lagna") -> int:
        return (self.ref_sign(ref) + house - 1) % 12

    def lord_of(self, house: int, ref: str = "Lagna") -> str:
        return SIGN_LORDS[self.sign_of_house(house, ref)]

    def planets_in_house(self, house: int, ref: str = "Lagna") -> list[str]:
        s = self.sign_of_house(house, ref)
        return [p for p, ps in self.signs.items() if ps == s]

    def aspects(self, planet: str, target_sign: int) -> bool:
        dist = (target_sign - self.signs[planet]) % 12 + 1
        return dist in ASPECTS.get(planet, {7})

    def associated(self, a: str, b: str) -> bool:
        """Parashari sambandha: conjunction, sign exchange, or mutual aspect."""
        if a == b:
            return False
        sa, sb = self.signs[a], self.signs[b]
        if sa == sb:
            return True
        if SIGN_LORDS[sa] == b and SIGN_LORDS[sb] == a:
            return True
        return self.aspects(a, sb) and self.aspects(b, sa)


def facts_from_chart(chart: dict) -> Facts:
    p = chart["planets"]
    from ..constants import SIGNS
    flags = {}
    if "doshas" in chart:
        flags = {k: v["present"] for k, v in chart["doshas"].items()}
    return Facts(
        lagna=chart["lagna"]["sign_index"] - 1,
        signs={n: v["sign_index"] - 1 for n, v in p.items()},
        dignity={n: v.get("dignity", "n/a") for n, v in p.items()},
        d9={n: SIGNS.index(v["vargas"]["D9"]) for n, v in p.items()},
        flags=flags,
    )


# ---------------- primitives ----------------
# Each takes (facts, params) and returns (matched: bool, planets_involved: list[str])

def _planets(spec) -> list[str]:
    if isinstance(spec, str):
        return {"benefics": sorted(NATURAL_BENEFICS), "malefics": sorted(NATURAL_MALEFICS),
                "all": GRAHAS, "seven": GRAHAS[:7]}.get(spec, [spec])
    return list(spec)


def p_planet_in_house(f: Facts, a: dict):
    ref = a.get("from", "Lagna")
    hits = [p for p in _planets(a["planet"]) if f.house_of(p, ref) in a["houses"]]
    need = a.get("count", "any")
    ok = (len(hits) == len(_planets(a["planet"]))) if need == "all" else bool(hits)
    return ok, hits


def p_dignity(f: Facts, a: dict):
    hits = [p for p in _planets(a["planet"]) if f.dignity.get(p) in a["is"]]
    return bool(hits), hits


def p_conjunct(f: Facts, a: dict):
    ps = _planets(a["planets"])
    ok = len({f.signs[p] for p in ps}) == 1
    return ok, ps if ok else []


def p_lord_in_house(f: Facts, a: dict):
    ref = a.get("from", "Lagna")
    lord = f.lord_of(a["lord_of"], ref)
    ok = f.house_of(lord, ref) in a["houses"]
    return ok, [lord] if ok else []


def p_lords_associated(f: Facts, a: dict):
    """Any lord of houses `a` associated with any lord of houses `b` (distinct planets)."""
    la = {f.lord_of(h) for h in a["a"]}
    lb = {f.lord_of(h) for h in a["b"]}
    for x in la:
        for y in lb:
            if f.associated(x, y):
                return True, sorted({x, y})
    return False, []


def p_owns_both(f: Facts, a: dict):
    """A single planet owning a house from group a AND one from group b (e.g. Yogakaraka)."""
    hits = sorted({f.lord_of(h) for h in a["a"]} & {f.lord_of(h) for h in a["b"]})
    return bool(hits), hits


def p_empty_houses(f: Facts, a: dict):
    ref = a.get("from", "Lagna")
    ignore = set(a.get("ignore", []))
    occ = [p for h in a["houses"] for p in f.planets_in_house(h, ref) if p not in ignore and p != ref]
    return not occ, []


def p_occupied_houses(f: Facts, a: dict):
    ref = a.get("from", "Lagna")
    ignore = set(a.get("ignore", []))
    found = []
    for h in a["houses"]:
        occ = [p for p in f.planets_in_house(h, ref) if p not in ignore and p != ref]
        if not occ:
            return False, []
        found += occ
    return True, found


def p_exchange(f: Facts, a: dict):
    for i, x in enumerate(GRAHAS[:7]):
        for y in GRAHAS[i + 1:7]:
            if SIGN_LORDS[f.signs[x]] == y and SIGN_LORDS[f.signs[y]] == x:
                return True, [x, y]
    return False, []


def p_hemmed_by_nodes(f: Facts, a: dict):
    rahu = f.signs["Rahu"]
    rel = [(f.signs[p] - rahu) % 12 for p in GRAHAS[:7]]
    # sign-level test: all strictly within one half (ties on the axis disqualify)
    ok = all(0 < r < 6 for r in rel) or all(6 < r < 12 for r in rel)
    return ok, []


def p_vargottama(f: Facts, a: dict):
    hits = [p for p in _planets(a.get("planet", "all")) if p in f.d9 and f.d9[p] == f.signs[p]]
    return bool(hits), hits


def p_neecha_bhanga(f: Facts, a: dict):
    """Debilitated planet whose debilitation-sign lord or exaltation-sign lord
    is in a kendra from Lagna or Moon (one common BPHS/Phaladeepika condition)."""
    hits = []
    for p in GRAHAS[:7]:
        if f.dignity.get(p) != "debilitated":
            continue
        deb_lord = SIGN_LORDS[f.signs[p]]
        ex_lord = SIGN_LORDS[EXALTATION[p][0]]
        for c in {deb_lord, ex_lord} - {p}:
            if f.house_of(c, "Lagna") in (1, 4, 7, 10) or f.house_of(c, "Moon") in (1, 4, 7, 10):
                hits.append(p)
                break
    return bool(hits), hits


def p_flag(f: Facts, a: dict):
    return bool(f.flags.get(a["name"])), []


def p_lagna_sign(f: Facts, a: dict):
    return f.lagna in a["in"], []


PRIMITIVES = {
    "planet_in_house": p_planet_in_house,
    "dignity": p_dignity,
    "conjunct": p_conjunct,
    "lord_in_house": p_lord_in_house,
    "lords_associated": p_lords_associated,
    "owns_both": p_owns_both,
    "empty_houses": p_empty_houses,
    "occupied_houses": p_occupied_houses,
    "exchange": p_exchange,
    "hemmed_by_nodes": p_hemmed_by_nodes,
    "vargottama": p_vargottama,
    "neecha_bhanga": p_neecha_bhanga,
    "flag": p_flag,
    "lagna_sign": p_lagna_sign,
}


def evaluate(cond: dict, f: Facts) -> tuple[bool, list[str]]:
    if len(cond) != 1:
        raise ValueError(f"condition must have exactly one key: {cond}")
    (op, arg), = cond.items()
    if op == "all":
        involved = []
        for c in arg:
            ok, ps = evaluate(c, f)
            if not ok:
                return False, []
            involved += ps
        return True, involved
    if op == "any":
        for c in arg:
            ok, ps = evaluate(c, f)
            if ok:
                return True, ps
        return False, []
    if op == "not":
        ok, _ = evaluate(arg, f)
        return not ok, []
    if op not in PRIMITIVES:
        raise ValueError(f"unknown primitive '{op}'")
    return PRIMITIVES[op](f, arg)


# ---------------- loading & running ----------------

RULES_DIR = pathlib.Path(__file__).parent / "data"
REQUIRED = {"id", "name", "category", "when", "text", "source", "status"}


def load_rules(directory: pathlib.Path = RULES_DIR) -> list[dict]:
    rules, seen = [], set()
    for path in sorted(directory.glob("*.yaml")):
        for r in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            missing = REQUIRED - r.keys()
            if missing:
                raise ValueError(f"{path.name}:{r.get('id')} missing {missing}")
            if r["id"] in seen:
                raise ValueError(f"duplicate rule id {r['id']}")
            seen.add(r["id"])
            r["_file"] = path.name
            rules.append(r)
    return rules


def interpret(f: Facts, rules: list[dict] | None = None, include_draft: bool = True,
              lang: str = "en") -> list[dict]:
    from .. import i18n
    rules = rules if rules is not None else load_rules()
    tr = i18n.load(lang)["rules"] if lang != "en" else {}
    out = []
    for r in rules:
        if r["status"] != "reviewed" and not include_draft:
            continue
        ok, involved = evaluate(r["when"], f)
        if not ok:
            continue
        loc = tr.get(r["id"], {})
        name = loc.get("name", r["name"])
        text = loc.get("text", r["text"]).strip()
        if "{" in text:  # simple templating, e.g. {lagna_lord}
            text = text.format(**_template_vars(f, lang))
        out.append({
            "id": r["id"], "name": name, "lang": lang if loc or lang == "en" else "en", "category": r["category"],
            "nature": r.get("nature", "neutral"), "text": text, "source": r["source"],
            "status": r["status"], "planets": sorted(set(involved)),
            "remedy_tags": r.get("remedy_tags", []),
        })
    return out


def _template_vars(f: Facts, lang: str = "en") -> dict:
    from .. import i18n
    ll = f.lord_of(1)
    return {"lagna_lord": i18n.term(lang, ll), "lagna_lord_house": f.house_of(ll)}
