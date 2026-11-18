"""Build and verify the discovery_v1 pack (T1.7). Run from Agent_Echo: python -m data_discovery.build_discovery_v1

Runs the generator, then the importer, then QA checks against the database and CSVs. Writes a public report
(files_discovery_v1/QA_build_report.md) and a private one (files_discovery_v1_private/QA_build_report_private.md).
Standard library only; makes no model or API calls; never loads the private files into a database.
"""
import csv
import hashlib
import re
import sqlite3
import statistics
import subprocess
import sys
import time
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

from . import common
from .text import VERDICT_TERMS, _VERDICT_RES, scan

HERE = common.FINAL / "Agent_Echo"
DB = HERE / "data" / "echo_discovery_v1.db"
LEGACY_DB = HERE / "data" / "echo.db"
MANIFEST = common.PACK / "QA_manifest.csv"
KEY = common.PRIVATE / "QA_discovery_v1_answer_key.csv"
LAST_INT, LAST_CON = "INT042542", "CON077333"
FILLED = "({c} IS NOT NULL AND {c}<>'')"

PUBLIC, PRIVATE = [], []  # (status, name, detail)


def chk(report, name, ok, detail=""):
    report.append(("PASS" if ok else "FAIL", name, detail))
    return ok


def warn(report, name, detail):
    report.append(("WARN", name, detail))


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hash(folder):
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(folder)).encode() + sha(path).encode())
    return digest.hexdigest()


def run(args):
    start = time.time()
    done = subprocess.run([sys.executable, *args], cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    return done, time.time() - start


def dist(values):
    values = sorted(values)
    pick = lambda p: values[round(p * (len(values) - 1))]
    return [round(x, 2) for x in (values[0], pick(.1), statistics.median(values), pick(.9), values[-1])]


def main():
    began = time.time()
    protected = {"data/echo.db": sha(LEGACY_DB), "files_update": tree_hash(common.LEGACY),
                 "data_extensions": tree_hash(common.EXTENSIONS)}

    global DB
    if "--db" in sys.argv:  # re-run QA on an existing database (generator and importer skipped)
        DB = Path(sys.argv[sys.argv.index("--db") + 1])
        gen_time = imp_time = 0
        imp = subprocess.CompletedProcess([], 0, "", "")
    else:
        gen, gen_time = run(["-m", "data_discovery.generate_discovery_v1"])
        if gen.returncode:
            sys.exit(f"Generator failed:\n{gen.stderr[-2000:]}")
        imp, imp_time = run(["import_data.py", "--profile", "discovery_v1", "--replace"])
    chk(PUBLIC, "Importer passes (--profile discovery_v1 --replace)", imp.returncode == 0,
        f"exit {imp.returncode}; {imp_time:.0f}s" + ("" if imp.returncode == 0 else f"\n{(imp.stderr or imp.stdout)[-1500:]}"))
    if imp.returncode:
        write_reports(began, gen_time, imp_time, protected)
        sys.exit("Importer failed; see QA_build_report.md")

    db = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    one = lambda sql, *a: db.execute(sql, a).fetchone()[0]
    dictionary = common.read_csv(common.PACK / "QA_data_dictionary.csv")
    manifest = common.read_csv(MANIFEST)
    tables = [m["File"].removesuffix(".csv") for m in manifest]
    pk = {r["File"].removesuffix(".csv"): r["Column"] for r in dictionary if r["Primary_Key"] == "Yes"}
    columns = defaultdict(list)
    for r in dictionary:
        columns[r["File"].removesuffix(".csv")].append(r)

    # ---- row counts ----
    counts, bad = {}, []
    for m, table in zip(manifest, tables):
        counts[table] = one(f"SELECT COUNT(*) FROM {table}")
        with (common.PACK / m["File"]).open(encoding="utf-8", newline="") as stream:
            csv_rows = sum(1 for _ in csv.reader(stream)) - 1
        if csv_rows != counts[table]:
            bad.append(f"{table}: csv {csv_rows} vs db {counts[table]}")
    chk(PUBLIC, "Row counts: database equals CSV for all tables", not bad, f"{len(tables)} tables; " + "; ".join(bad))
    chk(PUBLIC, "Table count", len(tables) == 27 and len(counts) == 27, f"{len(tables)} tables in manifest")
    drift = {t: (m["Rows"], counts[t]) for m, t in zip(manifest, tables) if int(m["Rows"]) != counts[t]}
    warn(PUBLIC, "Manifest Rows differed from generated counts (updated below)", f"{len(drift)} tables: {drift}")

    # ---- integrity ----
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    chk(PUBLIC, "PRAGMA foreign_key_check", not fk, f"{len(fk)} violations" + (f"; e.g. {fk[:3]}" if fk else ""))
    integrity = db.execute("PRAGMA integrity_check").fetchall()
    chk(PUBLIC, "PRAGMA integrity_check", integrity == [("ok",)], str(integrity[:3]))

    # ---- variance ----
    def variance(label, values):
        d = dist(values)
        chk(PUBLIC, f"Variance: {label}", len(set(values)) > 1, f"n={len(values)} min/p10/median/p90/max = {d}")

    employees = [r[0] for r in db.execute("SELECT Employee_ID FROM HR_employees")]
    def per_person(sql):
        found = dict(db.execute(sql).fetchall())
        return [found.get(e, 0) for e in employees]
    variance("messages authored per person", per_person(
        "SELECT Author_Employee_ID, COUNT(*) FROM OP_collab_messages WHERE Author_Employee_ID<>'' GROUP BY 1"))
    variance("threads helped per person (messages in threads they did not open)", per_person(
        "SELECT m.Author_Employee_ID, COUNT(DISTINCT m.Thread_ID) FROM OP_collab_messages m JOIN OP_collab_threads t "
        "ON t.Thread_ID=m.Thread_ID WHERE m.Author_Employee_ID<>'' AND m.Author_Employee_ID<>t.Requester_Employee_ID GROUP BY 1"))
    variance("after-hours minutes per person (sum of weekly)", per_person(
        "SELECT Employee_ID, SUM(After_Hours_Minutes) FROM OP_activity_weekly GROUP BY 1"))
    variance("cross-team hours per person (sum of weekly)", per_person(
        "SELECT Employee_ID, SUM(Cross_Team_Hours) FROM OP_activity_weekly GROUP BY 1"))
    teams = [r[0] for r in db.execute(
        "SELECT AVG(p.Pulse_Score) FROM HR_employee_performance p JOIN HR_employees e USING(Employee_ID) GROUP BY e.Pilot_Manager_ID")]
    variance("mean pulse per team", teams)

    # ---- generic checks the importer does not do ----
    n = one(f"SELECT COUNT(*) FROM HR_recognition_feedback WHERE NOT ((Author_Type IN ('partner_manager','home_manager') "
            f"AND {FILLED.format(c='Author_Manager_ID')} AND NOT {FILLED.format(c='Author_Employee_ID')}) OR (Author_Type='partner_employee' "
            f"AND {FILLED.format(c='Author_Employee_ID')} AND NOT {FILLED.format(c='Author_Manager_ID')}))")
    chk(PUBLIC, "Feedback Author_Type matches the filled author column", n == 0, f"{n} violations of {counts['HR_recognition_feedback']}")
    n = one("SELECT COUNT(*) FROM HR_recognition_feedback WHERE Interaction_Date<>substr(Interaction_At,1,10)")
    chk(PUBLIC, "Interaction_Date equals date part of Interaction_At", n == 0, f"{n} violations")

    cap = db.execute(
        "SELECT COUNT(*), SUM(a.Employee_ID IS NULL), SUM(a.Employee_ID IS NOT NULL AND ABS(c.After_Hours-a.After_Hours_Minutes/60.0)>0.001), "
        "SUM(a.Employee_ID IS NOT NULL AND ABS(c.Cross_Team_Hours-a.Cross_Team_Hours)>0.001) FROM OP_capacity c "
        "LEFT JOIN OP_activity_weekly a ON a.Employee_ID=c.Employee_ID AND a.Week_Start=c.Week_Start WHERE c.Week_Start>='2025-09-29'").fetchone()
    chk(PUBLIC, "OP_capacity After_Hours / Cross_Team_Hours equal OP_activity_weekly (minutes/60 for after-hours) from 2025-09-29 (tol 0.001)",
        cap[1] == 0 and cap[2] == 0 and cap[3] == 0,
        f"{cap[0]} capacity rows; no activity row {cap[1]}; after-hours mismatches {cap[2]}; cross-team mismatches {cap[3]}")
    extra = one("SELECT COUNT(*) FROM OP_activity_weekly a LEFT JOIN OP_capacity c ON a.Employee_ID=c.Employee_ID AND a.Week_Start=c.Week_Start WHERE c.Employee_ID IS NULL")
    chk(PUBLIC, "Every OP_activity_weekly row has a capacity row", extra == 0, f"{extra} without")

    term_specs = [("OP_collab_messages", "Author_Employee_ID", "Sent_At", None), ("OP_collab_threads", "Requester_Employee_ID", "Opened_At", None),
                  ("OP_dependency_blockers", "Resolved_By_Employee_ID", "Resolved_At", None),
                  ("OP_meeting_mentions", "Mentioned_Employee_ID", "Meeting_Date", None),
                  ("HR_recognition_events", "Employee_ID", "Recognized_At", None), ("OP_activity_weekly", "Employee_ID", "Week_Start", None),
                  ("HR_employee_performance", "Employee_ID", "Recorded_At", None), ("HR_one_on_ones", "Employee_ID", "Meeting_Date", None),
                  ("HR_review_notes", "Employee_ID", "Note_Date", None),
                  ("HR_recognition_feedback", "Employee_ID", "Interaction_At", f"Interaction_ID>'{LAST_INT}'"),
                  ("HR_recognition_feedback", "Author_Employee_ID", "Interaction_At", f"Interaction_ID>'{LAST_INT}'"),
                  ("OP_contributions", "Employee_ID", "Contribution_Date", f"Contribution_ID>'{LAST_CON}'")]
    late = {}
    for table, who, when, where in term_specs:
        sql = (f"SELECT t.{pk[table]}, t.{who}, t.{when}, e.Termination_Date FROM {table} t JOIN HR_employees e ON e.Employee_ID=t.{who} "
               f"WHERE e.Termination_Date<>'' AND substr(t.{when},1,10)>e.Termination_Date" + (f" AND {where.replace('Interaction_ID', 't.Interaction_ID').replace('Contribution_ID', 't.Contribution_ID')}" if where else ""))
        late[f"{table}.{who}"] = db.execute(sql).fetchall()
    for r in db.execute("SELECT t.Incident_ID, t.Responder_Employee_IDs, t.Started_At FROM OP_incident_handoffs t"):
        for emp in filter(None, r[1].split(";")):
            term = one("SELECT Termination_Date FROM HR_employees WHERE Employee_ID=?", emp)
            if term and r[2][:10] > term:
                late.setdefault("OP_incident_handoffs.Responder_Employee_IDs", []).append((r[0], emp, r[2], term))
    total_late = sum(map(len, late.values()))
    chk(PUBLIC, "No new-table row dated after the employee's termination date", total_late == 0,
        f"{total_late} violations across {len(term_specs) + 1} employee columns" + "".join(f"; {k}: {len(v)} e.g. {v[0]}" for k, v in late.items() if v))

    # ---- verdict-like columns ----
    verdict_cols = re.compile(r"hidden|recogni[sz]ed_flag|expected|verdict|planted|decoy|prohibited", re.I)
    hits = [(t, c["Column"]) for t in tables for c in columns[t] if verdict_cols.search(c["Column"])
            and (t, c["Column"]) != ("OP_work_requests", "Expected_Deliverable")]  # legacy planning field
    chk(PUBLIC, "No column named like a verdict (*Hidden*, *Recognized_Flag*, *Expected*, ...)", not hits,
        f"{sum(len(v) for v in columns.values())} columns checked" + (f"; {hits}" if hits else ""))
    key_header = next(csv.reader(KEY.open(encoding="utf-8-sig", newline="")))
    story_header = next(csv.reader(common.STORY_ROWS.open(encoding="utf-8-sig", newline="")))
    generic = {"Manager_ID", "Employee_ID", "Beneficiary_Team", "Notes", "Origin", "Kind", "Table", "Window", "Date_Or_At"}
    forbidden = (set(key_header) | set(story_header)) - generic
    db_columns = {c["Column"] for t in tables for c in columns[t]}
    chk(PUBLIC, "No pack column shares a name with an answer-key or story-file column", not (forbidden & db_columns),
        f"{len(forbidden)} private column names compared; overlap {sorted(forbidden & db_columns)}")
    actual = {r[1] for t in tables for r in db.execute(f"PRAGMA table_info({t})")}
    chk(PUBLIC, "No database column named Expected_Result (checked against live schema)", not (actual & forbidden), f"{len(actual)} distinct columns")
    private_names = [p.name for p in common.PRIVATE.iterdir() if p.suffix == ".csv"]
    manifest_text = MANIFEST.read_text(encoding="utf-8-sig")
    pack_files = [p.name for p in common.PACK.iterdir()]
    chk(PUBLIC, "Answer-key and story files not referenced in the manifest and not copied into the pack folder",
        not any(n in manifest_text for n in private_names + ["answer_key", "story_rows", "story_worksheet", "files_discovery_v1_private"])
        and not any(n in pack_files for n in private_names), f"{len(private_names)} private csv files")

    # ---- leakage scan ----
    text_cols = re.compile(r"(Message|Text|Notes?|Description|Citation|Summary|Outcome|Evidence|Resolution|Topic|Quantified)", re.I)
    textual = {t: [c["Column"] for c in columns[t] if c["Type"] == "TEXT" and text_cols.search(c["Column"]) and not c["Column"].endswith("_ID")
                   and c["Column"] not in ("Goal_Outcome_ID", "Metric_Name", "Evidence_IDs", "Team_Helped")] for t in tables}
    union = re.compile("|".join(p.pattern for _, p in _VERDICT_RES), re.I)
    scope_of = lambda t, i: ("legacy/copied" if t == "HR_self_review_items" or (t == "HR_recognition_feedback" and i <= LAST_INT)
                             or (t == "OP_contributions" and i <= LAST_CON) else "new/added")
    leaks, hit_rows, scanned = Counter(), defaultdict(set), Counter()
    for t in tables:
        legacy_copy = t in ("HR_employees", "HR_managers", "HR_survey_summary", "HR_survey_comments", "HR_program_participation",
                            "OP_projects", "OP_work_requests", "OP_capacity", "OP_priority_decisions", "HR_goals")
        if legacy_copy or not textual[t]:
            continue
        cols = textual[t]
        for row in db.execute(f"SELECT {pk[t]}, {', '.join(cols)} FROM {t}"):
            sc = scope_of(t, row[0])
            for value in row[1:]:
                if value and union.search(value):
                    for term in scan(value):
                        leaks[(t, sc, term)] += 1
                        hit_rows[(t, row[0])].add(term)
        scanned[t] = counts[t]
    warn(PUBLIC, "Leakage scan: tables scanned (text columns)", "; ".join(f"{t} [{', '.join(textual[t])}]" for t in scanned))
    per_table = defaultdict(Counter)
    for (t, sc, term), k in leaks.items():
        per_table[(t, sc)][term] += k
    for (t, sc), c in sorted(per_table.items()):
        warn(PUBLIC, f"Leakage hits {t} ({sc} rows)", f"{sum(c.values())} hits; " + ", ".join(f"{k}: {v}" for k, v in c.most_common()))
    if not per_table:
        warn(PUBLIC, "Leakage hits", "none")

    # ---- coverage (public: counts only) ----
    cov = one("SELECT COUNT(*) FROM OP_source_coverage")
    part = db.execute("SELECT Coverage_ID, Source_Table, Home_Manager_ID, Quarter FROM OP_source_coverage WHERE Coverage_Status='partial'").fetchall()
    chk(PUBLIC, "OP_source_coverage has 1,680 rows and exactly one partial", cov == 1680 and len(part) == 1, f"{cov} rows; {len(part)} partial")
    chk(PRIVATE, "Named partial row is M41, HR_recognition_feedback, 2026-Q3", len(part) == 1 and part[0][1:] == ("HR_recognition_feedback", "M41", "2026-Q3"), str(part))

    # ---- private: story presence, answer key ----
    prefix_map = defaultdict(list)
    for t in tables:
        first = db.execute(f"SELECT {pk[t]} FROM {t} LIMIT 1").fetchone()
        prefix_map[re.match(r"[A-Za-z]+", first[0]).group()].append(t)
    exists = lambda t, i: db.execute(f"SELECT 1 FROM {t} WHERE {pk[t]}=? LIMIT 1", (i,)).fetchone() is not None
    story = common.story_rows()
    reserved = common.reserved_ids()
    story_only = [r for r in story if r["Row_ID"] in reserved]
    missing = [(r["Table"], r["Row_ID"]) for r in story_only if not exists(r["Table"], r["Row_ID"])]
    chk(PRIVATE, "Every story-only ID in the story-rows file exists in its table", not missing,
        f"{len(story_only)} story-only rows ({len(reserved)} distinct IDs); missing {len(missing)}: {missing[:5]}")
    pinned = [r for r in story if r["Row_ID"].startswith(common.PINNED_PREFIXES)]
    miss_pin = [(r["Table"], r["Row_ID"]) for r in pinned if not exists(r["Table"], r["Row_ID"])]
    chk(PRIVATE, "Every pinned background row (PRF/AWK/COV) exists", not miss_pin, f"{len(pinned)} pinned rows; missing {miss_pin[:5]}")

    # reserved IDs: appear only in their declared table, once (PK), and in no other table's key column
    declared = defaultdict(set)
    for r in story_only:
        declared[r["Row_ID"]].add(r["Table"])
    stray = []
    for rid, owner in declared.items():
        for t in tables:
            if t not in owner and t != "HR_self_review_items" and exists(t, rid):
                stray.append((rid, t))
    chk(PRIVATE, "No background row uses a story-only reserved ID (IDs live only in their declared table)", not stray,
        f"{len(reserved)} reserved IDs; stray {len(stray)}: {stray[:5]}")
    dup = [(t, i, k) for t in tables if t != "HR_self_review_items" for i, k in db.execute(f"SELECT {pk[t]}, COUNT(*) FROM {t} GROUP BY 1 HAVING COUNT(*)>1 LIMIT 3")]
    chk(PRIVATE, "No duplicate primary keys", not dup, str(dup))

    key = common.read_csv(KEY)
    origin = Counter(r["Origin"] for r in key)
    chk(PRIVATE, "Answer key has 194 rows (14 hand_built + 180 automatic)",
        len(key) == 194 and origin == {"hand_built": 14, "automatic": 180}, f"{len(key)} rows; {dict(origin)}")
    chk(PRIVATE, "Answer key Case_IDs unique", len({r["Case_ID"] for r in key}) == len(key), "")
    absent, int_rows = [], defaultdict(set)
    n_ids = 0
    for r in key:
        for i in filter(None, r["Evidence_IDs"].split(";")):
            n_ids += 1
            tabs = prefix_map.get(re.match(r"[A-Za-z]+", i).group(), []) if re.match(r"[A-Za-z]+", i) else []
            if not any(exists(t, i) for t in tabs):
                absent.append((r["Case_ID"], i))
            if i.startswith("INT"):
                int_rows[r["Case_ID"]].add(i)
    chk(PRIVATE, "Every answer-key Evidence_ID exists in the database", not absent, f"{n_ids} ids checked; missing {len(absent)}: {absent[:5]}")
    refs_bad = []
    for r in key:
        for ref in filter(None, r["Work_Refs"].split(";")):
            kind, _, i = ref.partition(":")
            t = {"contribution": "OP_contributions", "thread": "OP_collab_threads", "blocker": "OP_dependency_blockers", "incident": "OP_incident_handoffs"}.get(kind)
            if not t or not exists(t, i):
                refs_bad.append((r["Case_ID"], ref))
    chk(PRIVATE, "Every answer-key Work_Ref exists", not refs_bad, f"missing {len(refs_bad)}: {refs_bad[:5]}")

    cov_of = dict(db.execute("SELECT Interaction_ID, Record_Coverage FROM HR_recognition_feedback WHERE Interaction_ID>?", (LAST_INT,)))
    cov_of.update(dict(db.execute("SELECT Interaction_ID, Record_Coverage FROM HR_recognition_feedback WHERE Interaction_ID<=?", (LAST_INT,))))
    wrong = [(c, i, cov_of.get(i)) for c, ids in int_rows.items() for i in sorted(ids)
             if cov_of.get(i) != ("partial" if c == "D5" else "complete")]
    d5 = sorted(int_rows.get("D5", ()))
    cited = sum(map(len, int_rows.values()))
    chk(PRIVATE, "Cited feedback rows are complete (D5's rows partial)", not wrong and len(d5) == 2,
        f"{cited} cited INT rows over {len(int_rows)} cases; D5 rows {d5}; wrong {len(wrong)}: {wrong[:5]}")

    cited_ids = {i for ids in int_rows.values() for i in ids}
    for r in key:
        cited_ids.update(i for i in r["Evidence_IDs"].split(";") if i)
    leaky = [(t, i, sorted(terms)) for (t, i), terms in hit_rows.items() if i in cited_ids]
    chk(PRIVATE, "Leakage: no story or plant Evidence_ID row has a verdict-term hit", not leaky,
        f"{len(cited_ids)} evidence ids; {len(leaky)} with hits: {leaky[:5]}")

    db.close()
    after = {"data/echo.db": sha(LEGACY_DB), "files_update": tree_hash(common.LEGACY), "data_extensions": tree_hash(common.EXTENSIONS)}
    chk(PUBLIC, "data/echo.db, files_update/ and data_extensions/ unchanged", after == protected,
        f"echo.db sha256 before = after = {after['data/echo.db']}" if after == protected else f"before {protected}\nafter {after}")

    update_manifest(tables, counts)
    write_reports(began, gen_time, imp_time, protected)
    failed = [n for s, n, _ in PUBLIC + PRIVATE if s == "FAIL"]
    print(f"{len(PUBLIC) + len(PRIVATE)} checks; FAIL: {failed or 'none'}; {time.time() - began:.0f}s")
    sys.exit(1 if failed else 0)


def update_manifest(tables, counts):
    raw = MANIFEST.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    eol = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(text.splitlines()))
    rows[0:1] = [rows[0]]
    col = rows[0].index("Rows")
    for r in rows[1:]:
        r[col] = str(counts[r[0].removesuffix(".csv")])
    import io
    out = io.StringIO()
    csv.writer(out, lineterminator=eol).writerows(rows)
    MANIFEST.write_bytes((b"\xef\xbb\xbf" if bom else b"") + out.getvalue().encode("utf-8"))


def write_reports(began, gen_time, imp_time, protected):
    sizes = {p.name: p.stat().st_size for p in common.PACK.glob("*.csv")}
    head = (f"- Generated: {datetime.now():%Y-%m-%d %H:%M}\n- Generator seed: {common.SEED}\n"
            f"- Build runtime: generator {gen_time:.0f}s, importer {imp_time:.0f}s, total {time.time() - began:.0f}s\n"
            f"- Database: `{DB}` ({(DB.stat().st_size / 1e6 if DB.exists() else 0):.1f} MB; {'built' if DB.exists() else 'NOT BUILT'})\n"
            f"- Pack CSVs: {len(sizes)} files, {sum(sizes.values()) / 1e6:.1f} MB; largest "
            + ", ".join(f"{k} {v / 1e6:.1f} MB" for k, v in sorted(sizes.items(), key=lambda kv: -kv[1])[:3]) + "\n")
    for path, title, rows, note in ((common.PACK / "QA_build_report.md", "discovery_v1 build report", PUBLIC,
                                     "Public report: counts, integrity, variance, generic checks and leakage warning counts."),
                                    (common.PRIVATE / "QA_build_report_private.md", "discovery_v1 private build report", PRIVATE,
                                     "Private. Story presence, coverage of cited rows and answer-key checks. Never load or quote.")):
        lines = [f"# {title}", "", note, "", head, f"Result: {sum(s == 'PASS' for s, _, _ in rows)} PASS, "
                 f"{sum(s == 'FAIL' for s, _, _ in rows)} FAIL, {sum(s == 'WARN' for s, _, _ in rows)} WARN", "",
                 "| Status | Check | Detail |", "| --- | --- | --- |"]
        lines += [f"| {s} | {n} | {d.replace(chr(10), ' ').replace('|', '/')} |" for s, n, d in rows]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
