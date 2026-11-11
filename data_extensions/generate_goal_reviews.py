"""Generate synthetic goals and year-end self-reviews that agree with Echo's existing records.

Reads the built database (Agent_Echo/data/echo.db), writes three CSVs next to this script, and with
--load adds the two HR tables to that database. The existing eleven tables are never changed.

    python data_extensions/generate_goal_reviews.py --load

Output (synthetic, seeded, so every run produces the same rows):
  HR_goals.csv                  goals agreed in January, review years 2025 and 2026
  HR_self_review_items.csv      what each employee reported in December 2025
  QA_discovery_answer_key.csv   what each self-review item really is; never loaded, so the judge can't see it

2026 has goals only: its self-reviews would fall after the data ends on 30 September 2026.
"""
import argparse
import csv
import random
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATABASE = HERE.parent / 'Agent_Echo' / 'data' / 'echo.db'
SEED = 20251201
ORIGIN = 'synthetic'

# Assumptions, stated so the team can change them: how goals turn out, and how people write.
OUTCOMES = (('Met', 0.55), ('Partly met', 0.30), ('Missed', 0.15))
STYLES = (('detailed', 0.30), ('standard', 0.40), ('brief', 0.20), ('overstated', 0.10))
UNRECORDED_SHARE = 0.20

# The planted side project: six people in three teams, in no goal and no record.
PLANTED_TEAMS = ('Data Platforms', 'Customer Renewals', 'Customer Care')
PLANTED_TEXTS = {  # team -> (text, team helped) for its two people, each written differently
    'Data Platforms': (
        ('Built a small tool on my own time that flags customer accounts likely not to renew, from support tickets and usage drops', 'Customer Renewals'),
        ('Helped turn a renewal-risk alert prototype into a weekly list the renewals team can use', 'Customer Renewals')),
    'Customer Renewals': (
        ('Tested an early-warning tool for renewal risk that Data Platforms built; we now check its list every Monday', 'Data Platforms'),
        ('Used a homemade renewal-risk list to call at-risk customers early; two of those accounts renewed after we stepped in', 'Data Platforms')),
    'Customer Care': (
        ('Gave the renewals team feedback on a renewal-risk alert tool and suggested which ticket patterns to flag', 'Customer Renewals'),
        ('Tagged support tickets that hint a customer may leave, so the renewal-risk list could pick them up', 'Customer Renewals')),
}

UNRECORDED = (
    'Wrote a script that flags duplicate records in {team_s} weekly extract',
    'Trained two new starters in {team} on the tools our team maintains',
    'Rebuilt {team_s} shared tracker after it broke in {month}',
    'Answered {team_s} questions about our data and processes most weeks',
    'Documented the handoff steps {team} now follows with our team',
    'Reviewed {team_s} quarterly figures before they went to leadership',
)
INTERNAL = (
    'Covered a colleague\'s workload for {weeks} weeks in {month}',
    'Onboarded a new team member and wrote our team\'s starter guide',
    'Ran our team\'s weekly planning meeting while the lead was away',
)
DEVELOPMENT = (
    ('Build skills for my {area} role', 'Finish one course and use it on a real task'),
    ('Mentor a newer team member', 'Meet every two weeks for the year'),
    ('Present our team\'s work at a department meeting', 'One presentation'),
)
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
SUMMARY = re.compile(r'^(?P<did>.+?) for the (?P<project>.+) - (?P<team>.+) - (?P<quarter>\d{4}-Q\d) project\.$')


def possessive(team):
    return team + ("'" if team.endswith('s') else "'s")


def pick(rng, weighted):
    return rng.choices([w[0] for w in weighted], weights=[w[1] for w in weighted])[0]


def first_person(summary, name, outcome, detailed):
    """'Ana Lee prepared a briefing ... for the X - Team - 2025-Q1 project.' -> 'Prepared a briefing ... for Team's X project (Q1)'."""
    match = SUMMARY.match(summary.removeprefix(name + ' '))
    if not match:
        return summary, ''
    text = f"{match['did'][0].upper()}{match['did'][1:]} for {possessive(match['team'])} {match['project'].lower()} project ({match['quarter'][-2:]})"
    return text, outcome if detailed else ''


def employees(db, year):
    return [dict(r) for r in db.execute("""
        SELECT Employee_ID, Employee_Name, Department, Team_Display_Name AS Team, Job_Title, Pilot_Manager_ID AS Manager_ID
        FROM HR_employees
        WHERE Pilot_Roster_Status LIKE 'Included%' AND Hire_Date <= :start
          AND (Termination_Date IS NULL OR Termination_Date = '' OR Termination_Date > :end)
        ORDER BY Employee_ID""", {'start': f'{year}-01-15', 'end': f'{year}-12-31'})]


def generate(db):
    rng = random.Random(SEED)
    goals, items, key = [], [], []
    teams = [r[0] for r in db.execute('SELECT DISTINCT Team_Display_Name FROM HR_employees ORDER BY 1')]
    projects = defaultdict(list)
    for r in db.execute("SELECT Project_ID, Sponsoring_Team, Business_Objective, Project_Start_Date FROM OP_projects ORDER BY Project_ID"):
        projects[(r['Sponsoring_Team'], r['Project_Start_Date'][:4])].append(dict(r))
    contributions = defaultdict(list)
    for r in db.execute("""SELECT c.Contribution_ID, c.Employee_ID, c.Contribution_Summary, c.Business_Outcome, c.Beneficiary_Team, w.Actual_Hours
        FROM OP_contributions c JOIN OP_work_requests w ON w.Work_Request_ID = c.Work_Request_ID
        WHERE c.Home_Team <> c.Beneficiary_Team AND c.Contribution_Date BETWEEN '2025-01-01' AND '2025-12-31'
        ORDER BY c.Contribution_ID"""):
        contributions[r['Employee_ID']].append(dict(r))

    for year in (2025, 2026):
        people = employees(db, year)
        planted = {p['Employee_ID'] for team in PLANTED_TEAMS for p in [p for p in people if p['Team'] == team][:2]} if year == 2025 else set()
        for person in people:
            pid = person['Employee_ID']
            style = pick(rng, STYLES)
            own = projects.get((person['Team'], str(year)), [])
            objectives = list({p['Business_Objective']: p for p in own}.values())
            chosen = rng.sample(objectives, k=min(len(objectives), rng.choice((2, 2, 3))))
            person_goals = []
            for project in chosen:
                numeric = rng.random() < 0.5
                cut = rng.choice((20, 25, 30, 40))
                person_goals.append(dict(
                    Goal_Type='Delivery', Linked_Project_ID=project['Project_ID'],
                    Goal_Text=project['Business_Objective'] + (f', cutting rework by {cut}%' if numeric else ''),
                    Target_Measure=f'Rework down {cut}%' if numeric else f'Delivered by the end of {year}'))
            text, measure = rng.choice(DEVELOPMENT)
            person_goals.append(dict(Goal_Type='Development', Linked_Project_ID='',
                                     Goal_Text=text.format(area=person['Job_Title'].lower()), Target_Measure=measure))
            for n, goal in enumerate(person_goals, start=1):
                goal_id = f'G{year}-{pid}-{n:02d}'
                goals.append({'Goal_ID': goal_id, 'Employee_ID': pid, 'Manager_ID': person['Manager_ID'], 'Review_Year': year,
                              'Set_Date': f'{year}-01-{rng.randint(6, 31):02d}', **goal, 'Data_Origin': ORIGIN})
                goal['Goal_ID'] = goal_id
            if year != 2025:
                continue

            # Year-end self-review (2025 only).
            submitted = f'2025-12-{rng.randint(1, 12):02d}'
            rows = []
            for goal in person_goals:
                outcome = pick(rng, OUTCOMES)
                quantified = '' if style == 'brief' else (
                    {'Met': 'Target reached', 'Partly met': 'About half of the target', 'Missed': 'Target not reached'}[outcome]
                    if goal['Goal_Type'] == 'Delivery' else '')
                lower = goal['Goal_Text'][0].lower() + goal['Goal_Text'][1:]
                verb = {'Met': 'Met my goal to', 'Partly met': 'Partly met my goal to', 'Missed': 'Missed my goal to'}[outcome]
                rows.append(dict(Item_Text=f"{goal['Goal_Text']}: {outcome.lower()}" if style == 'brief' else f'{verb} {lower}',
                                 Claimed_Goal_ID=goal['Goal_ID'], Goal_Outcome=outcome, Team_Helped=person['Team'],
                                 Quantified_Result=quantified, kind='goal_report', source=''))
            recorded = contributions.get(pid, [])
            limit = {'brief': 1, 'standard': 2, 'detailed': 4, 'overstated': 4}[style]
            for c in rng.sample(recorded, k=min(len(recorded), limit)):
                text, result = first_person(c['Contribution_Summary'], person['Employee_Name'], c['Business_Outcome'], style in ('detailed', 'overstated'))
                if style == 'overstated' and rng.random() < 0.5:
                    text += ', one of my biggest contributions this year'
                claim = rng.choice(person_goals)['Goal_ID'] if style == 'overstated' and rng.random() < 0.5 else ''
                rows.append(dict(Item_Text=text, Claimed_Goal_ID=claim, Goal_Outcome='', Team_Helped=c['Beneficiary_Team'],
                                 Quantified_Result=result, kind='recorded_cross_team', source=c['Contribution_ID']))
            if rng.random() < UNRECORDED_SHARE:
                other = rng.choice([t for t in teams if t != person['Team']])
                text = rng.choice(UNRECORDED).format(team=other, team_s=possessive(other), month=rng.choice(MONTHS))
                rows.append(dict(Item_Text=text, Claimed_Goal_ID='', Goal_Outcome='', Team_Helped=other,
                                 Quantified_Result='' if style == 'brief' else f'About {rng.randint(4, 30)} hours over the year',
                                 kind='unrecorded_cross_team', source=''))
            if style != 'brief' and rng.random() < 0.3:
                text = rng.choice(INTERNAL).format(weeks=rng.randint(2, 6), month=rng.choice(MONTHS))
                rows.append(dict(Item_Text=text, Claimed_Goal_ID='', Goal_Outcome='', Team_Helped=person['Team'],
                                 Quantified_Result='', kind='unplanned_own_team', source=''))
            if pid in planted:
                earlier = sum(1 for k in key if k['Kind'] == 'planted' and k['Team'] == person['Team'])
                text, helped = PLANTED_TEXTS[person['Team']][earlier]
                rows.append(dict(Item_Text=text, Claimed_Goal_ID='', Goal_Outcome='', Team_Helped=helped,
                                 Quantified_Result='', kind='planted', source=''))
            rng.shuffle(rows)
            for n, row in enumerate(rows, start=1):
                item_id = f'R2025-{pid}-{n:02d}'
                items.append({'Item_ID': item_id, 'Employee_ID': pid, 'Review_Year': 2025, 'Submitted_Date': submitted,
                              **{k: row[k] for k in ('Item_Text', 'Claimed_Goal_ID', 'Goal_Outcome', 'Team_Helped', 'Quantified_Result')},
                              'Data_Origin': ORIGIN})
                key.append({'Item_ID': item_id, 'Employee_ID': pid, 'Team': person['Team'], 'Kind': row['kind'],
                            'Source_Contribution_ID': row['source'], 'Writing_Style': style})
    return goals, items, key


GOAL_COLUMNS = ('Goal_ID', 'Employee_ID', 'Manager_ID', 'Review_Year', 'Set_Date', 'Goal_Text', 'Goal_Type', 'Target_Measure', 'Linked_Project_ID', 'Data_Origin')
ITEM_COLUMNS = ('Item_ID', 'Employee_ID', 'Review_Year', 'Submitted_Date', 'Item_Text', 'Claimed_Goal_ID', 'Goal_Outcome', 'Team_Helped', 'Quantified_Result', 'Data_Origin')
KEY_COLUMNS = ('Item_ID', 'Employee_ID', 'Team', 'Kind', 'Source_Contribution_ID', 'Writing_Style')
SCHEMA = {
    'HR_goals': """CREATE TABLE HR_goals (Goal_ID TEXT NOT NULL PRIMARY KEY,
        Employee_ID TEXT NOT NULL REFERENCES HR_employees (Employee_ID), Manager_ID TEXT NOT NULL REFERENCES HR_managers (Manager_ID),
        Review_Year INTEGER NOT NULL, Set_Date TEXT NOT NULL, Goal_Text TEXT NOT NULL, Goal_Type TEXT NOT NULL, Target_Measure TEXT,
        Linked_Project_ID TEXT REFERENCES OP_projects (Project_ID), Data_Origin TEXT NOT NULL)""",
    'HR_self_review_items': """CREATE TABLE HR_self_review_items (Item_ID TEXT NOT NULL PRIMARY KEY,
        Employee_ID TEXT NOT NULL REFERENCES HR_employees (Employee_ID), Review_Year INTEGER NOT NULL, Submitted_Date TEXT NOT NULL,
        Item_Text TEXT NOT NULL, Claimed_Goal_ID TEXT REFERENCES HR_goals (Goal_ID), Goal_Outcome TEXT, Team_Helped TEXT,
        Quantified_Result TEXT, Data_Origin TEXT NOT NULL)""",
}


def write_csv(path, columns, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def load(database, goals, items):
    """Adds (or replaces) only the two new tables; the eleven existing tables are left as they are."""
    db = sqlite3.connect(database)
    try:
        db.execute('PRAGMA foreign_keys = ON')
        db.execute('BEGIN')
        db.execute('DROP TABLE IF EXISTS HR_self_review_items')
        db.execute('DROP TABLE IF EXISTS HR_goals')
        for sql in SCHEMA.values():
            db.execute(sql)
        nulls = lambda row, cols: [row[c] if row[c] != '' else None for c in cols]
        db.executemany(f'INSERT INTO HR_goals VALUES ({",".join("?" * len(GOAL_COLUMNS))})', [nulls(g, GOAL_COLUMNS) for g in goals])
        db.executemany(f'INSERT INTO HR_self_review_items VALUES ({",".join("?" * len(ITEM_COLUMNS))})', [nulls(i, ITEM_COLUMNS) for i in items])
        db.execute('CREATE INDEX idx_HR_goals_period ON HR_goals (Employee_ID, Review_Year)')
        db.execute('CREATE INDEX idx_HR_self_review_items_period ON HR_self_review_items (Employee_ID, Review_Year)')
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise ValueError('Foreign-key check failed; nothing was saved.')
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--database', type=Path, default=DATABASE)
    parser.add_argument('--load', action='store_true', help='also add the two tables to the database')
    args = parser.parse_args()
    db = sqlite3.connect(f'{args.database.resolve().as_uri()}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    goals, items, key = generate(db)
    db.close()
    write_csv(HERE / 'HR_goals.csv', GOAL_COLUMNS, goals)
    write_csv(HERE / 'HR_self_review_items.csv', ITEM_COLUMNS, items)
    write_csv(HERE / 'QA_discovery_answer_key.csv', KEY_COLUMNS, key)
    print(f'HR_goals: {len(goals):,} rows · HR_self_review_items: {len(items):,} rows · answer key: {len(key):,} rows')
    if args.load:
        load(args.database, goals, items)
        print(f'Loaded both tables into {args.database}')


if __name__ == '__main__':
    main()
