"""Hand-built stories P1-P6 and decoys D1-D8 for discovery_v1 (T1.5, plan v10 §5.6).

Runs after ops.generate and hr.generate. The frozen private rows file (common.STORY_ROWS) is the
specification: IDs, dates, authors, anchors and share fields are read from it; this module adds the
text and the few values the file leaves open (metric units, clock times inside a given day). Pinned
PRF/AWK/COV rows and the copied P5 self-review items are written by hr; this module only checks them.
Expected answers go to ctx.answer_key only.

Run `python -m data_discovery.stories` from Agent_Echo for the self-check (ops + hr + stories in memory).
"""
import csv
import re
from collections import Counter
from datetime import date, datetime, time, timedelta

from . import common, text
from .ops import People, iso, message_row, thread_row, work_time

ORIGIN = "Synthetic"
WINDOW = (common.ANALYSIS[0].isoformat(), f"{common.AS_OF.isoformat()}T23:59:59")
FOLLOW_END = f"{common.FOLLOW_UP[1].isoformat()}T23:59:59"
ANCHOR_COLUMNS = {"contribution": "Contribution_ID", "thread": "Thread_ID", "blocker": "Blocker_ID", "incident": "Incident_ID"}
KEYS = {"OP_team_goals": "Team_Goal_ID", "OP_goal_outcomes": "Goal_Outcome_ID", "OP_collab_threads": "Thread_ID",
        "OP_collab_messages": "Message_ID", "OP_dependency_blockers": "Blocker_ID", "OP_incident_handoffs": "Incident_ID",
        "OP_meeting_mentions": "Mention_ID", "OP_contributions": "Contribution_ID",
        "HR_recognition_feedback": "Interaction_ID", "HR_recognition_events": "Recognition_ID",
        "HR_one_on_ones": "One_On_One_ID", "HR_self_review_items": "Item_ID"}
TEXT_COLUMNS = {"OP_team_goals": ("Goal_Text",), "OP_goal_outcomes": ("Measurement_Note",),
                "OP_collab_threads": ("Topic",), "OP_collab_messages": ("Message_Text",),
                "OP_dependency_blockers": ("Blocker_Description", "Resolution_Note"),
                "OP_incident_handoffs": ("Incident_Notes",), "OP_meeting_mentions": ("Note_Text",),
                "OP_contributions": ("Project_Name", "Contribution_Summary", "Business_Outcome", "Evidence_Description"),
                "HR_recognition_feedback": ("Message",), "HR_recognition_events": ("Citation_Text",),
                "HR_one_on_ones": ("Notes",)}
P5_SELF_REVIEWS = ("R2025-E0001-06", "R2025-E0046-06", "R2025-E0051-05", "R2025-E0066-07", "R2025-E0074-03", "R2025-E0085-04")


class Tpl:
    """A text.render request; `need` are substrings the rendered text must contain (the story fact)."""

    def __init__(self, family, need=(), **slots):
        self.family, self.need, self.slots = family, tuple(need), slots


# ---- Values the rows file leaves open -------------------------------------------------------------------------------
# Team_Goal_ID: (Metric_Name, Metric_Unit, Target_Direction, Target_Value, Goal_Text)
GOALS = {
    "TGL000372": ("renewal forecast accuracy", "percent", "increase", 95.0,
                  "Renewal forecast accuracy for enterprise accounts at or above 95% by 2026-06-30."),
    "TGL000040": ("sales dashboards verified after the migration", "percent", "increase", 100.0,
                  "Complete the reporting database migration with every sales dashboard verified by 2025-12-19."),
    "TGL000190": ("business-application accounts reviewed", "percent", "increase", 100.0,
                  "Review 100% of business-application accounts in the quarterly access recertification by 2026-03-27."),
    "TGL000340": ("nightly report job failures per week", "count", "decrease", 2.0,
                  "Cut nightly report job failures to under 2 per week by 2026-06-26."),
    "TGL000377": ("gross renewal rate for mid-market accounts", "percent", "increase", 90.0,
                  "Gross renewal rate for mid-market accounts at or above 90% by 2026-06-30."),
    "TGL000224": ("accounts with mismatched owners", "count", "decrease", 20.0,
                  "Fewer than 20 accounts with mismatched owners by 2026-03-31."),
    "TGL000222": ("QBR packs delivered on time", "count", "increase", 40.0,
                  "Quarterly business review packs for the top 40 enterprise accounts delivered on time by 2026-03-27."),
    "TGL000353": ("order-to-activation time for renewal orders", "business days", "decrease", 5.0,
                  "Order-to-activation time for renewal orders under 5 business days by 2026-06-30."),
    "TGL000344": ("win-loss survey responses", "count", "increase", 300.0,
                  "Win-loss survey reaches 300 responses by 2026-06-19."),
}
# Goal_Outcome_ID: (Measured_Value, Numerator, Denominator, Measurement_Note)
OUTCOMES = {
    "GOC001238": (86.0, 215, 250, ""), "GOC001428": (93.2, 233, 250, ""),
    "GOC001692": (96.4, 241, 250, "The renewal-date mapping correction was in place for the whole quarter-end cycle."),
    "GOC000499": (100.0, "", "", ""), "GOC001118": (100.0, "", "", ""), "GOC001693": (1.0, "", "", ""),
    "GOC001333": (88.2, "", "", ""),
    "GOC001694": (91.8, "", "", "Includes 5 renewals closed after early outreach to accounts on the weekly risk list."),
    "GOC001144": (14.0, "", "", ""), "GOC001119": (40.0, "", "", ""),
    "GOC001515": (6.8, "", "", ""), "GOC001695": (6.4, "", "", ""), "GOC001649": (318.0, "", "", ""),
}
# Blocker_ID: (Blocking_Manager_ID, Raised clock, Resolved clock, Blocker_Description, Resolution_Note)
BLOCKERS = {
    "BLK003068": ("M15", "09:40", "10:05",
                  "Enterprise Accounts' renewal forecast is waiting on the CRM forecast export from Business Systems: "
                  "renewal dates in the export differ from contract dates.",
                  "Isabel Nguyen corrected the renewal-date mapping in the forecast extract; forecast lines match contract dates."),
    "BLK002406": ("M15", "09:30", "09:30",
                  "QBR packs for the top enterprise accounts are waiting on the usage extract from Business Systems: "
                  "usage tables are empty for 12 accounts.",
                  "Robin Vargas corrected the usage extract filter for accounts with a parent-child link; "
                  "all 12 accounts have usage data."),
    "BLK003179": ("M32", "11:00", None,
                  "Renewal orders arrive without an activation contact, so activation cannot start; "
                  "waiting on the renewal order form from Sales Operations.", ""),
}
INCIDENT = {"Incident_ID": "INC001840", "Incident_Type": "handoff", "Severity": "sev2", "Owning_Manager_ID": "M03",
            "Started_At": "2026-05-21T22:40:00", "Ended_At": "2026-05-22T02:15:00", "Responder_Employee_IDs": "E0426;E0728",
            "Incident_Notes": "Severity sev2 escalation for a large customer: contract entitlement data in the escalation "
                              "console was wrong. Kian Martinez (on call) brought in Remy Khan from Sales Operations, who "
                              "pulled the correct entitlement from the sales records overnight. Handed back to Escalation "
                              "Services at 02:15."}
# Contribution_ID: (Project label, Contribution topic, Business_Outcome)
CONTRIBUTIONS = {
    "CON077372": ("Reporting database migration", "the sales dashboard check against the migrated database (7 mismatches listed)",
                  "The Infrastructure team used the mismatch list to fix the dashboards before cutover."),
    "CON077385": ("Reporting database migration", "two pipeline report filters that broke in the migration",
                  "The Infrastructure team used the rebuilt filters in the migrated reports."),
    "CON077435": ("Quarterly access recertification", "the access recertification review of 140 sales user accounts",
                  "The Infrastructure team used the reviewed account list in the recertification."),
    "CON077468": ("Nightly report job stability", "the two report jobs failing on quarter-end volumes, with a proposed schedule",
                  "The Infrastructure team used the proposed schedule for the nightly jobs."),
    "CON077496": ("Nightly report job stability", "the test of the new nightly schedule against the Monday pipeline reports",
                  "The Infrastructure team used the test results to keep the new schedule."),
    "CON077433": ("Territory review owner reconciliation", "the account-owner reconciliation",
                  "Owner list delivered to Regional Accounts for the territory review."),
    "CON077446": ("Renewal queue coverage", "the renewal queue of a teammate on leave",
                  "Renewal queue kept current during the leave."),
    "CON077452": ("Renewal queue coverage", "the close-out of the covered renewal accounts before the quarter end",
                  "Covered renewal accounts closed out before the quarter end."),
    "CON077466": ("Win-loss survey", "the closed-lost contact list for the win-loss survey",
                  "Contact list handed over to Customer Insights."),
    "CON077413": ("Quote approval onboarding", "a walkthrough of the quote approval steps for two new reps, with a one-page checklist",
                  "Checklist shared in the Sales Operations workspace."),
    "CON077430": ("Renewal checklist update", "the shared renewal checklist update after a pricing change",
                  "Updated checklist shared in the Sales Operations workspace."),
}
# Template verbs that would misstate what the work was.
CONTRIBUTION_VERBS_AVOIDED = ("trained", "walked", "reran", "advised", "consulted", "troubleshooting", "explained")
EFFORT_DEFAULT = {"CON077446": 6, "CON077452": 4, "CON077413": 3, "CON077430": 2}  # the rows file gives no effort for these
RECOGNITION = {"REC003025": ("written_commendation", "11:00", Tpl("recognition_citation", ("Isabel Nguyen", "the forecast export fix"),
                                                                  employee="Isabel Nguyen", work="the forecast export fix")),
               "REC002068": ("written_commendation", "15:30", Tpl("recognition_citation", ("Robin Vargas", "the QBR usage extract fix"),
                                                                  employee="Robin Vargas", work="the QBR usage extract fix"))}


def _fb(employee, team, work, outcome):
    return Tpl("feedback_partner", (employee, outcome), employee=employee, beneficiary_team=team, work=work, outcome=outcome)


def _thanks(helper, team, topic, outcome):
    return Tpl("message_thanks", (helper,), helper=helper, beneficiary_team=team, topic=topic, outcome=outcome)


# Texts for the planted rows that have one (P2 and D2 threads are built in _thread_texts).
TEXTS = {
    # P1
    "MSG061384": "Does anyone in Sales Operations know why renewal dates move in the forecast export? Several enterprise "
                 "renewals show dates that differ from the contracts.",
    "MSG061807": "I'll trace the field mapping in the export and report back.",
    "MSG064011": "Found it: the renewal-date field in the forecast export was mapped from the order date, not the contract "
                 "end date. The extract is corrected. Check steps: compare ten renewal lines with their contracts, confirm "
                 "the date column reads the contract end date, and rerun the export after any mapping change.",
    "MSG064242": _thanks("Isabel Nguyen", "Enterprise Accounts", "the forecast export", "the forecast lines up with the contracts now"),
    "INT042680": _fb("Isabel Nguyen", "Enterprise Accounts", "tracing the renewal-date mapping in the forecast export",
                     "the forecast review could go ahead"),
    "INT042693": "The check steps Isabel Nguyen left for the forecast export are now part of our routine every week before "
                 "the forecast call.",
    "INT042713": "Mid-June note for Isabel Nguyen: the June forecast review came in on target and the renewal-date fix held.",
    # P4
    "MSG020044": "Could someone in Sales Operations check the quota report totals after the cutover? We want to confirm "
                 "they match before the old database is retired.",
    "MSG020114": "Quota report totals match the old database for every region except two reps whose territory changed in "
                 "November. List with the corrected totals attached.",
    "MSG020338": _thanks("Iris Ross", "Infrastructure", "the quota report totals", "the totals are confirmed"),
    "MSG041477": "For the access recertification: which sales roles still need CRM admin rights?",
    "MSG041571": "Only the Sales Operations admins and the two regional leads still need CRM admin rights; the other nine "
                 "roles can move to standard access. List attached.",
    "MSG041806": _thanks("Amira Bryant", "Infrastructure", "the CRM admin list", "the recertification list is updated"),
    "MSG050943": "Can Sales Operations confirm the list of departed sales users before we remove their access?",
    "MSG051029": "Confirmed: 23 departed sales users on the list, plus 2 more who left last week. Updated list attached.",
    "MSG051277": _thanks("Celia Campos", "Infrastructure", "the departed-user list", "access removal can go ahead"),
    "MSG070542": "A nightly report job has been failing since the weekend. Can someone in Sales Operations look at the "
                 "sales reports it runs?",
    "MSG070594": "The job fails on a saved filter that points to a retired field. I updated the filter; tonight's run "
                 "should go through.",
    "MSG070859": _thanks("Iris Ross", "Infrastructure", "the nightly report job", "last night's run went through"),
    "INT042602": "Thank you, Amira Bryant. Your check of the sales dashboards let the reporting database migration close on time.",
    "INT042665": _fb("Iris Ross", "Infrastructure", "the sales user account review",
                     "the access recertification finished a week early"),
    "INT042667": "Thanks, Celia Campos, for confirming the departed-user list before we removed access.",
    "INT042682": "Amira Bryant's proposal for the report job schedule is now our plan of record.",
    "INT042697": _fb("Iris Ross", "Infrastructure", "the saved-filter fix", "the nightly failure stopped"),
    "INT042712": _fb("Celia Campos", "Infrastructure", "testing the new nightly schedule",
                     "failures are down to about one a week"),
    "MTM004125": "Migration retro: thanks to Amira Bryant from Sales Operations for verifying the sales dashboards.",
    "MTM004122": "Migration retro: thanks to Iris Ross from Sales Operations for checking the quota report totals.",
    "MTM004126": "Migration retro: thanks to Celia Campos from Sales Operations for rebuilding the pipeline report filters.",
    "MTM010475": "Ops review: the nightly report schedule worked out with Amira Bryant from Sales Operations is in place.",
    # P3
    "MTM009368": "Thanks to Remy Khan from Sales Operations for staying on the call overnight during the entitlement escalation.",
    "MTM009922": "The large-customer escalation is closed with the customer; the entitlement check Remy Khan used is now in "
                 "the runbook.",
    # P5
    "MSG041796": "Hi Jonah Meyer, could the weekly at-risk account list also include accounts renewing in the next 90 days? "
                 "We would like them on the Monday list.",
    "MSG042225": "The 90-day renewal filter is added. The list runs Monday at 7:00.",
    "MSG042456": "Moved the job to the shared schedule, so it runs when Jonah Meyer is out.",
    "MSG042809": "Support ticket tags now include 'cancellation question'.",
    "MSG043706": "First list: 11 accounts, 6 called so far. Test notes for Data Platforms: two accounts were already in "
                 "renewal talks and one had a wrong contact.",
    "MSG059477": "These accounts were flagged only because of a seasonal usage dip: a ski school, a tax preparer and a "
                 "campus bookstore. Can the list allow for that?",
    "MSG059854": "Suggest ignoring tickets tagged as billing-address changes; they are not a cancellation signal.",
    "MSG060231": "Usage-drop threshold adjusted; accounts with a seasonal pattern are excluded from the list.",
    "MSG063576": "False alarms dropped on the latest list, and two accounts from it renewed after early calls.",
    "MTM006605": "The Monday at-risk list from Jonah Meyer in Data Platforms flagged 11 accounts; 4 are already saved this quarter.",
    "MTM008266": "Dana Flores in Customer Renewals tests the risk list each Monday and sends back false alarms.",
    "MTM008263": "Quinn Okafor's list of seasonal accounts fixed most false alarms.",
    "MTM009093": "Customer Care's ticket tags from Aria Adams now feed the risk list.",
    # P6 (the word for a repeated record is avoided on purpose: E0107's own self-review uses it)
    "MSG039594": "Can Sales Operations run the account-owner reconciliation before the territory review?",
    "MSG039922": "I'll log it. Looping in Paola Ward, who built the owner-to-territory mapping last time.",
    "MSG044743": "Paola Ward's mapping caught accounts still assigned to departed reps in the Midwest territory.",
    "MSG046858": "The owner list is clean for the review. Thanks, Paola Ward, for the mapping.",
    "INT042647": "Thanks for the account-owner reconciliation. Paola Ward's owner-to-territory mapping was the piece that "
                 "let us close the territory review.",
    "INT042669": "The mapping approach Paola Ward set up is now how we check new territory assignments.",
    # D1
    "MSG048102": "Why are the usage tables empty for 12 accounts in the QBR packs?",
    "MSG048525": "I'll trace the usage extract and come back to you.",
    "MSG050734": "The usage extract filtered out accounts with a parent-child link. Corrected; the 12 accounts now have usage data.",
    "MSG050976": _thanks("Robin Vargas", "Enterprise Accounts", "the QBR packs", "the packs are complete"),
    "INT042652": _fb("Robin Vargas", "Enterprise Accounts", "the QBR usage extract", "the QBR packs are unblocked"),
    "INT042660": _fb("Robin Vargas", "Enterprise Accounts", "the QBR packs", "every pack went out on time"),
    "INT042670": _fb("Robin Vargas", "Enterprise Accounts", "the usage extract fix", "the fix held for the April refresh"),
    # D4
    "OOO000814": "Khalil Foster is covering a teammate's renewal accounts during a leave through the end of March. "
                 "Agreed to revisit coverage at the next 1:1.",
    # D5
    "INT042683": _fb("Sana Young", "Customer Insights", "the closed-lost contact list", "the survey went out a week early"),
    "INT042706": _fb("Sana Young", "Customer Insights", "the contact list", "the response target is within reach"),
    # D8
    "MTM008816": "Priya Hughes from Sales Operations showed us how reps log into the quote tool on the road, which pointed "
                 "to the VPN timeout behind the login loop.",
}
P2_FIXES = {
    "THR006935": "The quote was still linked to the 2025 price book. I switched it to the 2026 book and re-priced the lines; "
                 "please regenerate the PDF.",
    "THR008315": "Multi-year discounts up to 10% need the regional sales director; above that it goes to the deal desk. "
                 "I added the approval step to your quote.",
    "THR009700": "Create one renewal on the parent account and add both subsidiaries as lines with the same end date. "
                 "I set up the first one as an example.",
    "THR011080": "The tax ID field is switched off on the renewal layout. I turned it on for your profile; it shows under billing details.",
    "THR012463": "The uplift cap clause is in the contract terms library: pick 'Renewal uplift cap' and it fills the limit "
                 "from the original contract.",
    "THR013379": "Clone the renewal onto the new billing account and close the old one as replaced. I moved the open quote for you.",
    "THR014233": "The approval queue was routed to a manager who is out. I reassigned the six pending quotes to the backup approver.",
    "THR014369": "Use the amendment quote type and set the new seat count; the credit is prorated. The draft is in your queue.",
    "THR014693": "All three were created from an old template. I pointed them to the current price book and the totals match now.",
    "THR015158": "Add the new product as its own line with its own start date and keep the renewal lines as they are. "
                 "I updated the quote.",
    "THR015289": "I extended the validity date and reissued the quote; the new version is attached to the opportunity.",
    "THR015680": "The quote used the default USD rate table. I switched it to the EUR rate locked in the contract.",
    "THR016073": "15% is above the regional limit, so it routes to the deal desk. I submitted it there with the margin note.",
    "THR016600": "Send the renewal with the 30-day extension form; I prepared it from the template and linked it to the opportunity.",
}
P2_OUTCOMES = ("the quote went out", "the customer has the corrected quote", "the renewal is through", "the order went through")
P2_ACKS = ("ok, will try that.", "ok thanks, will try that.", "Noted, will try that.")
D2_REPLIES = ("I'm checking with the order-form owner and will come back to you.",
              "As a workaround, take the contact from the signed quote for now. I'm asking the order-form owner about a field.",
              "Let me check with the owner of the order form on this one.",
              "For now the billing contact on the account can stand in. I'll ask whether the form can carry it.",
              "Checking with the order-form owner; I'll update this thread.")
D2_STATUS = ("Orders in the latest batch still arrive without the activation contact.",
             "Latest batch: the activation contact is still missing on these orders.",
             "Same as before: the newest orders still come in without the activation contact.")


# ---- Helpers --------------------------------------------------------------------------------------------------------

def _sentences(value):
    return re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), value)


def _clean(value):
    found = text.scan(value)
    assert not found, f"verdict terms {found} in planted text {value!r}"
    assert "Rafay" not in value
    return value


def _say(rng, spec, avoid=()):
    """Plain text is scanned as is; a Tpl is rendered until it carries every needed fact and passes text.scan."""
    if isinstance(spec, str):
        return _clean(spec)
    for _ in range(2000):
        out = _sentences(text.render(spec.family, rng, **spec.slots).strip())
        if all(n in out for n in spec.need) and not any(a in out for a in avoid) and not text.scan(out):
            return _clean(out)
    raise RuntimeError(f"no {spec.family} template carries {spec.need}")


def _at(value):
    return datetime.fromisoformat(value)


def _stamp(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:00")


def _on(day, clock):
    return datetime.combine(date.fromisoformat(day), time.fromisoformat(clock))


def _anchors(row):
    refs = dict(part.split(":") for part in row["Anchors"].split(";") if part)
    return {ANCHOR_COLUMNS[kind]: ref for kind, ref in refs.items()}


def _blank_anchors(**filled):
    return {**{column: "" for column in ANCHOR_COLUMNS.values()}, **filled}


def _find(pattern, value, group=1):
    match = re.search(pattern, value)
    assert match, f"pattern {pattern!r} not in {value!r}"
    return match.group(group)


def _story_only(row):
    return (row["Row_ID"] not in ("", "NONE") and row["Table"] != "(background constraint)"
            and not row["Row_ID"].startswith(common.PINNED_PREFIXES))


def known_people(rows):
    """Every employee the rows file names, for Mentioned_Employee_IDs and name checks."""
    return sorted({eid for row in rows for eid in re.findall(r"E\d{4}", " ".join(row.values()))})


# ---- Planting -------------------------------------------------------------------------------------------------------

class _Planter:
    def __init__(self, ctx):
        self.ctx, self.people, self.columns = ctx, People(ctx), common.dictionary()
        self.rng, self.clock = common.rng("stories:text"), common.rng("stories:times")
        self.rows = common.story_rows()
        self.known = {eid: self.people.name[eid] for eid in known_people(self.rows)}
        self.planted = {}  # Row_ID -> table
        self.thread_texts = self._thread_texts()

    def add(self, table, row):
        assert set(row) == set(self.columns[table]), (table, sorted(set(row) ^ set(self.columns[table])))
        key = row[KEYS[table]]
        assert key not in self.planted, key
        self.planted[key] = table
        self.ctx.rows(table).append(row)

    def mentioned(self, body, author):
        return [eid for eid, name in self.known.items() if name in body and eid != author]

    def home(self, eid):
        return self.people.home[eid]

    def _thread_texts(self):
        """Texts for P2's and D2's threads, chosen per message role (request, reply, closing or status line)."""
        texts, by_thread = {}, {}
        for row in self.rows:
            if row["Case_ID"] in ("P2", "D2") and row["Table"] == "OP_collab_messages":
                by_thread.setdefault(_find(r"Thread (THR\d+)", row["Facts"]), []).append(row)
        topics = {row["Row_ID"]: _find(r"topic: (.*?)\. No work request", row["Facts"])
                  for row in self.rows if row["Case_ID"] in ("P2", "D2") and row["Table"] == "OP_collab_threads"}
        for thread_id, messages in by_thread.items():
            subject = messages[0]["Employee_ID"]
            helper, team = self.people.name[subject], self.people.team_name[messages[0]["Other_Party"].split()[0]]
            topic = topics[thread_id]
            for index, row in enumerate(messages):
                author = _find(r"author ([EM]\d+)", row["Facts"])
                if index == 0:
                    texts[row["Row_ID"]] = Tpl("message_request", (helper, topic), helper=helper, topic=topic,
                                               requester=self.people.name[author], beneficiary_team=team)
                elif author == subject:
                    texts[row["Row_ID"]] = P2_FIXES[thread_id] if row["Case_ID"] == "P2" else self.rng.choice(D2_REPLIES)
                elif row["Case_ID"] == "D2":
                    texts[row["Row_ID"]] = self.rng.choice(D2_STATUS)
                elif "Vague" in row["Text_Intent"]:
                    texts[row["Row_ID"]] = self.rng.choice(P2_ACKS)
                else:
                    texts[row["Row_ID"]] = _thanks(helper, team, topic, self.rng.choice(P2_OUTCOMES))
        return texts

    def text(self, row_id):
        return _say(self.rng, self.thread_texts.get(row_id) or TEXTS[row_id])

    def plant(self):
        story = [row for row in self.rows if _story_only(row) and row["Table"] != "HR_self_review_items"]
        seen = {}
        for row in story:
            if row["Row_ID"] in seen:  # a later event on a planted row (P1's July share): already in the first row's facts
                assert row["Table"] == seen[row["Row_ID"]] and "not a new row" in row["Facts"], row["Row_ID"]
                continue
            seen[row["Row_ID"]] = row["Table"]
        firsts = {}
        for row in story:
            firsts.setdefault(row["Row_ID"], row)
        order = ("OP_team_goals", "OP_goal_outcomes", "OP_collab_threads", "OP_collab_messages", "OP_dependency_blockers",
                 "OP_incident_handoffs", "OP_contributions", "OP_meeting_mentions", "HR_recognition_feedback",
                 "HR_recognition_events", "HR_one_on_ones")
        assert set(seen.values()) <= set(order), set(seen.values()) - set(order)
        messages = [row for row in firsts.values() if row["Table"] == "OP_collab_messages"]
        for table in order:
            for row in firsts.values():
                if row["Table"] == table:
                    getattr(self, table.lower())(row, messages)

    def op_team_goals(self, row, _):
        metric, unit, direction, target, goal_text = GOALS[row["Row_ID"]]
        owner = row["Other_Party"].split()[0]
        self.add("OP_team_goals", {
            "Team_Goal_ID": row["Row_ID"], "Owner_Team": self.people.team_name[owner], "Owner_Manager_ID": owner,
            "Quarter": _find(r"goal for (\d{4}-Q\d)", row["Facts"]), "Goal_Text": _clean(goal_text),
            "Metric_Name": metric, "Metric_Unit": unit, "Target_Direction": direction, "Baseline_Value": "",
            "Target_Value": target, "Set_Date": row["Date_Or_At"], "Due_Date": _find(r"by (\d{4}-\d\d-\d\d)", row["Facts"]),
            "Linked_Project_ID": "", "Data_Origin": ORIGIN})

    def op_goal_outcomes(self, row, _):
        value, numerator, denominator, note = OUTCOMES[row["Row_ID"]]
        self.add("OP_goal_outcomes", {
            "Goal_Outcome_ID": row["Row_ID"], "Team_Goal_ID": _find(r"goal (TGL\d+)", row["Facts"]),
            "Measured_At": iso(work_time(self.clock, date.fromisoformat(row["Date_Or_At"]), 0)), "Measured_Value": value,
            "Numerator": numerator, "Denominator": denominator, "Measurement_Note": _clean(note) if note else "",
            "Recorded_By_Manager_ID": row["Other_Party"].split()[0], "Data_Origin": ORIGIN})

    def op_collab_threads(self, row, messages):
        requesting = row["Other_Party"].split()[0]
        requester = _find(r"requester (E\d{4})", row["Other_Party"])
        last = max(_at(_find(r"sent (\S+?)\.", m["Facts"])) for m in messages
                   if _find(r"Thread (THR\d+)", m["Facts"]) == row["Row_ID"])
        closed = None if row["Case_ID"] == "D2" else last + timedelta(hours=1)  # D2's threads stay open
        self.add("OP_collab_threads", thread_row(
            row["Row_ID"], self.people, _at(row["Date_Or_At"]), requesting, self.home(row["Employee_ID"]), requester, None,
            _clean(_find(r"topic: (.*?)\. No work request", row["Facts"])), None, closed))

    def op_collab_messages(self, row, _):
        author = _find(r"author ([EM]\d+)", row["Facts"])
        sent = _find(r"sent (\S+?)\.", row["Facts"])
        assert sent == row["Date_Or_At"], row["Row_ID"]
        body = self.text(row["Row_ID"])
        self.add("OP_collab_messages", message_row(row["Row_ID"], self.people, _find(r"Thread (THR\d+)", row["Facts"]),
                                                   _at(sent), author, body, self.mentioned(body, author)))

    def op_dependency_blockers(self, row, _):
        blocking, raised_clock, resolved_clock, description, note = BLOCKERS[row["Row_ID"]]
        blocked = row["Other_Party"].split()[0]
        resolved = re.search(r"resolved by (E\d{4}) on (\d{4}-\d\d-\d\d)", row["Facts"])
        raised_at = _on(row["Date_Or_At"], raised_clock)
        resolved_at = _on(resolved.group(2), resolved_clock) if resolved else None
        if resolved:
            assert (resolved_at.date() - raised_at.date()).days == int(_find(r"(\d+) days blocked", row["Facts"]))
        self.add("OP_dependency_blockers", {
            "Blocker_ID": row["Row_ID"], "Raised_At": iso(raised_at), "Blocked_Team": self.people.team_name[blocked],
            "Blocked_Manager_ID": blocked, "Blocked_Team_Goal_ID": _find(r"blocked goal (TGL\d+)", row["Facts"]),
            "Blocking_Team": self.people.team_name[blocking], "Blocking_Manager_ID": blocking,
            "Blocker_Description": _clean(description), "Work_Request_ID": "",
            "Resolved_By_Employee_ID": resolved.group(1) if resolved else "",
            "Resolved_At": iso(resolved_at) if resolved else "",
            "Days_Blocked": (resolved_at.date() - raised_at.date()).days if resolved else "",
            "Resolution_Note": _clean(note) if resolved else "", "Data_Origin": ORIGIN})

    def op_incident_handoffs(self, row, _):
        assert row["Row_ID"] == INCIDENT["Incident_ID"] and row["Date_Or_At"] in INCIDENT["Started_At"]
        assert all(eid in row["Facts"] for eid in INCIDENT["Responder_Employee_IDs"].split(";"))
        self.add("OP_incident_handoffs", {**INCIDENT, "Owning_Team": self.people.team_name[INCIDENT["Owning_Manager_ID"]],
                                          "Incident_Notes": _clean(INCIDENT["Incident_Notes"]), "Data_Origin": ORIGIN})

    def op_contributions(self, row, _):
        project, topic, outcome = CONTRIBUTIONS[row["Row_ID"]]
        eid, day = row["Employee_ID"], row["Date_Or_At"]
        beneficiary = self.people.team_name[row["Other_Party"].split()[0]]
        goal = re.search(r"Team_Goal_ID (TGL\d+)", row["Facts"])
        effort = re.search(r"effort (\d+) hours", row["Facts"])
        name = self.people.name[eid]
        self.add("OP_contributions", {
            "Contribution_ID": row["Row_ID"], "Work_Request_ID": "",
            "Project_Name": f"{project} - {beneficiary} - {common.quarter_of(date.fromisoformat(day))}",
            "Employee_ID": eid, "Employee_Name": name, "Home_Team": self.people.team_name[self.home(eid)],
            "Beneficiary_Team": beneficiary, "Contribution_Date": day,
            "Contribution_Summary": _say(self.rng, Tpl("contribution_summary", (name, topic), employee=name,
                                                       beneficiary_team=beneficiary, topic=topic),
                                         avoid=CONTRIBUTION_VERBS_AVOIDED),
            "Business_Outcome": _clean(outcome),
            "Evidence_Description": _clean(f"Informal request from {beneficiary}; no work request; summary recorded on {day}."),
            "Data_Origin": ORIGIN, "Team_Goal_ID": goal.group(1) if goal else "",
            "Effort_Hours": effort.group(1) if effort else str(EFFORT_DEFAULT[row["Row_ID"]]), "Request_Channel": "informal"})

    def op_meeting_mentions(self, row, _):
        team = row["Other_Party"].split()[0]
        self.add("OP_meeting_mentions", {
            "Mention_ID": row["Row_ID"], "Meeting_Date": row["Date_Or_At"], "Meeting_Team": self.people.team_name[team],
            "Meeting_Manager_ID": team, "Mentioned_Employee_ID": row["Employee_ID"], "Note_Text": self.text(row["Row_ID"]),
            **_blank_anchors(**_anchors(row)), "Data_Origin": ORIGIN})

    def hr_recognition_feedback(self, row, _):
        facts, eid = row["Facts"], row["Employee_ID"]
        author = _find(r"author ([EM]\d+)", row["Other_Party"])
        partner_manager = author.startswith("M")
        team = author if partner_manager else self.home(author)
        assert team == row["Other_Party"].split()[0], row["Row_ID"]
        written = _on(row["Date_Or_At"], f"{self.clock.randint(9, 16):02d}:{self.clock.randrange(0, 60, 5):02d}")
        shared = re.search(r"(?:Shared_With_Home_Manager_At|shared) (\d{4}-\d\d-\d\d)", facts)
        recorded = re.search(r"(?:Share_Recorded_At|recorded) (\d{4}-\d\d-\d\d)", facts)
        assert bool(shared) == bool(recorded), row["Row_ID"]
        shared_at = recorded_at = None
        if shared:
            shared_at = _on(shared.group(1), f"{self.clock.randint(9, 15):02d}:{self.clock.randrange(0, 60, 5):02d}")
            recorded_at = max(_on(recorded.group(1), "00:00"), shared_at + timedelta(minutes=self.clock.randint(0, 20)))
        home = self.home(eid)
        self.add("HR_recognition_feedback", {
            "Interaction_ID": row["Row_ID"], "Interaction_Type": "Partner feedback",
            "Work_Request_ID": "", "Employee_ID": eid, "Employee_Name": self.people.name[eid],
            "Author_Manager_ID": author if partner_manager else "", "Author_Employee_ID": "" if partner_manager else author,
            "Author_Name": self.people.manager_name[author] if partner_manager else self.people.name[author],
            "Author_Team": self.people.team_name[team], "Recipient_Manager_ID": home,
            "Recipient_Manager_Name": self.people.manager_name[home], "Interaction_Date": row["Date_Or_At"],
            "Channel": "Quarterly partner review", "Message": self.text(row["Row_ID"]),
            "Shared_With_Home_Manager": "Yes" if shared else "No",
            "Record_Coverage": _find(r"Record_Coverage (complete|partial)", facts), "Data_Origin": ORIGIN,
            "Interaction_At": _stamp(written), "Author_Type": "partner_manager" if partner_manager else "partner_employee",
            **_blank_anchors(**_anchors(row)),
            "Shared_With_Home_Manager_At": _stamp(shared_at) if shared else "",
            "Share_Recorded_At": _stamp(recorded_at) if shared else ""})

    def hr_recognition_events(self, row, _):
        kind, clock, citation = RECOGNITION[row["Row_ID"]]
        anchors = _anchors(row)
        assert len(anchors) == 1 and "visibility team" in row["Facts"]
        self.add("HR_recognition_events", {
            "Recognition_ID": row["Row_ID"], "Employee_ID": row["Employee_ID"],
            "Given_By_Manager_ID": _find(r"given by (M\d+)", row["Other_Party"]), "Recognition_Type": kind,
            "Visibility": "team", "Recognized_At": _stamp(_on(row["Date_Or_At"], clock)),
            "Citation_Text": _say(self.rng, citation), **_blank_anchors(**anchors), "Data_Origin": ORIGIN})

    def hr_one_on_ones(self, row, _):
        self.add("HR_one_on_ones", {
            "One_On_One_ID": row["Row_ID"], "Manager_ID": _find(r"manager (M\d+)", row["Other_Party"]),
            "Employee_ID": row["Employee_ID"], "Meeting_Date": row["Date_Or_At"],
            "Topic_Code": _find(r"Topic_Code (\w+)", row["Facts"]), "Notes": self.text(row["Row_ID"]), "Data_Origin": ORIGIN})


def _enforce_background_constraints(ctx, people):
    """D7/D8 background-constraint rows: no blocker resolved for another team in the analysis window.

    ops (T1.2) does not know these two people, so a few ordinary background resolutions land on them. The
    resolver is cleared ("nobody recorded" is allowed by the dictionary) and the note is re-rendered without
    a name; no other person gains a signal. Returns the changed Blocker_IDs.
    """
    rng, changed = common.rng("stories:constraints"), []
    for row in ctx.rows("OP_dependency_blockers"):
        eid = row["Resolved_By_Employee_ID"]
        if (eid in ("E2198", "E0776") and row["Blocked_Manager_ID"] != people.home[eid]
                and WINDOW[0] <= row["Resolved_At"] <= WINDOW[1]):
            row["Resolved_By_Employee_ID"] = ""
            row["Resolution_Note"] = _say(rng, Tpl("blocker_resolution", (), helper="@@", days=row["Days_Blocked"], goal="@@"),
                                          avoid=("@@",))
            changed.append(row["Blocker_ID"])
    return changed


def apply(ctx):
    planter = _Planter(ctx)
    planter.plant()
    ctx.story_constraint_changes = _enforce_background_constraints(ctx, planter.people)  # QA only; never written
    for table in set(planter.planted.values()):
        ctx.rows(table).sort(key=lambda row: row[KEYS[table]])
    worksheet = common.read_csv(common.PRIVATE / "QA_discovery_v1_story_worksheet.csv")
    header = list(worksheet[0])[:15]
    with (common.PRIVATE / "QA_discovery_v1_answer_key.csv").open(encoding="utf-8-sig", newline="") as stream:
        assert next(csv.reader(stream)) == header, "worksheet columns differ from the answer key header"
    ctx.answer_key.extend({column: row[column] for column in header} for row in worksheet)
    ctx.story_planted = planter.planted  # QA only
    check(ctx, planter.planted)


# ---- Checks ---------------------------------------------------------------------------------------------------------

def _active(employee, day):
    return employee["Hire_Date"] <= day and (not employee["Termination_Date"] or employee["Termination_Date"] >= day)


def lowest_satisfaction(ctx, manager, n=10):
    """Plan §3.3: latest pulse at the as-of date, ties by change from the previous quarter, then ID."""
    as_of = common.AS_OF.isoformat()
    team = {row["Employee_ID"] for row in ctx.team(manager) if _active(row, as_of)}
    history = {}
    for row in ctx.rows("HR_employee_performance"):
        if row["Employee_ID"] in team and row["Recorded_At"] <= WINDOW[1]:
            history.setdefault(row["Employee_ID"], []).append((row["Quarter"], int(row["Pulse_Score"])))
    ranked = []
    for eid, scores in history.items():
        scores.sort()
        change = scores[-1][1] - scores[-2][1] if len(scores) > 1 else 0
        ranked.append((scores[-1][1], change, eid))
    return [eid for _, _, eid in sorted(ranked)[:n]]


def _work_refs(row):
    return {(kind, row[column]) for kind, column in ANCHOR_COLUMNS.items() if row.get(column)}


def check(ctx, planted):
    """Required absences, background constraints, coverage, share dates and satisfaction alignment (asserts)."""
    rows, t = common.story_rows(), ctx.tables
    employees = {row["Employee_ID"]: row for row in ctx.employees}
    home = {eid: row["Pilot_Manager_ID"] for eid, row in employees.items()}
    by_id = {table: {row[KEYS[table]]: row for row in t[table]} for table in KEYS if table in t}

    # Every story-only row exists exactly once in its table; copied P5 items are hr's unchanged rows.
    counts = {table: Counter(r[KEYS[table]] for r in t[table]) for table in {row["Table"] for row in rows if _story_only(row)}}
    for row in rows:
        if _story_only(row):
            assert counts[row["Table"]][row["Row_ID"]] == 1, (row["Row_ID"], counts[row["Table"]][row["Row_ID"]])
    source = {r["Item_ID"]: r for r in common.read_csv(common.EXTENSIONS / "HR_self_review_items.csv") if r["Item_ID"] in P5_SELF_REVIEWS}
    for item in P5_SELF_REVIEWS:
        assert by_id["HR_self_review_items"][item] == source[item] and not source[item]["Claimed_Goal_ID"], item

    # Share-date rules (dictionary) on every feedback row; planted rows also follow their facts.
    for r in t["HR_recognition_feedback"]:
        shared, recorded = r["Shared_With_Home_Manager_At"], r["Share_Recorded_At"]
        assert bool(shared) == bool(recorded) and r["Shared_With_Home_Manager"] == ("Yes" if shared else "No"), r["Interaction_ID"]
        assert not shared or r["Interaction_At"] <= shared <= recorded, r["Interaction_ID"]
    fb = by_id["HR_recognition_feedback"]

    def shared_by(row_id, moment):
        r = fb[row_id]
        return bool(r["Share_Recorded_At"]) and r["Shared_With_Home_Manager_At"] <= moment and r["Share_Recorded_At"] <= moment

    for row_id in ("INT042680", "INT042693", "INT042713"):
        assert not shared_by(row_id, WINDOW[1]), row_id
    assert fb["INT042713"]["Shared_With_Home_Manager_At"][:10] == fb["INT042713"]["Share_Recorded_At"][:10] == "2026-07-08"
    assert not fb["INT042680"]["Share_Recorded_At"] and not fb["INT042693"]["Share_Recorded_At"]
    for row_id in ("INT042602", "INT042665", "INT042667", "INT042682", "INT042697", "INT042712", "INT042683", "INT042706"):
        assert not shared_by(row_id, FOLLOW_END), row_id
    for row_id in ("INT042647", "INT042669", "INT042652", "INT042660", "INT042670"):
        assert shared_by(row_id, WINDOW[1]), row_id

    # Coverage: cited P1-P6 feedback complete, D5's two partial; OP_source_coverage as hr wrote it.
    cited = {row["Row_ID"] for row in rows if row["Table"] == "HR_recognition_feedback" and row["Row_ID"] != "NONE"}
    for row_id in cited:
        expected = "partial" if row_id in ("INT042683", "INT042706") else "complete"
        assert fb[row_id]["Record_Coverage"] == expected, row_id
    partial = [(r["Source_Table"], r["Home_Manager_ID"], r["Quarter"]) for r in t["OP_source_coverage"] if r["Coverage_Status"] != "complete"]
    assert partial == [("HR_recognition_feedback", "M41", "2026-Q3")], partial

    # FKs and anchors of planted rows.
    threads, goals = by_id["OP_collab_threads"], by_id["OP_team_goals"]
    anchor_tables = {"Contribution_ID": by_id["OP_contributions"], "Thread_ID": threads,
                     "Blocker_ID": by_id["OP_dependency_blockers"], "Incident_ID": by_id["OP_incident_handoffs"]}
    for row_id, table in planted.items():
        r = by_id[table][row_id]
        for column in ("Employee_ID", "Author_Employee_ID", "Requester_Employee_ID", "Resolved_By_Employee_ID", "Mentioned_Employee_ID"):
            assert not r.get(column) or r[column] in employees, (row_id, column)
        for eid in filter(None, (r.get("Mentioned_Employee_IDs", "") + ";" + r.get("Responder_Employee_IDs", "")).split(";")):
            assert eid in employees and employees[eid]["Employee_Name"] in (r.get("Message_Text") or r.get("Incident_Notes")), (row_id, eid)
        for column in ("Team_Goal_ID", "Blocked_Team_Goal_ID"):
            assert not r.get(column) or r[column] in goals, (row_id, column)
        filled = [column for column in anchor_tables if r.get(column)]
        for column in filled:
            assert r[column] in anchor_tables[column], (row_id, column)
        if table == "HR_recognition_feedback":
            assert filled, row_id
        if table == "HR_recognition_events":
            assert len(filled) == 1, row_id
        if table == "OP_meeting_mentions":
            assert len(filled) <= 1, row_id
        if table == "OP_collab_messages":
            thread = threads[r["Thread_ID"]]
            assert thread["Opened_At"] <= r["Sent_At"] and (not thread["Closed_At"] or r["Sent_At"] <= thread["Closed_At"]), row_id
        for column in TEXT_COLUMNS.get(table, ()):
            assert not text.scan(str(r[column])) and "Rafay" not in str(r[column]), (row_id, column)
        if row_id in ("MSG039594", "MSG039922", "MSG044743", "MSG046858", "INT042647", "INT042669", "CON077433", "THR008251"):
            assert "duplicate" not in " ".join(str(r[c]) for c in TEXT_COLUMNS[table]).lower(), row_id

    # Partner texts name the M32 subject by full name at least once.
    for case, eid in (("P1", "E0010"), ("P2", "E2156"), ("P3", "E0728"), ("P4", "E1401"), ("P4", "E1586"),
                      ("P4", "E0561"), ("P6", "E0970"), ("D1", "E1748"), ("D2", "E1333"), ("D5", "E1383"), ("D8", "E0776")):
        name = employees[eid]["Employee_Name"]
        texts = [str(by_id[table][rid][c]) for rid, table in planted.items() for c in TEXT_COLUMNS[table]
                 if next(r for r in rows if r["Row_ID"] == rid)["Case_ID"] == case]
        assert any(name in body for body in texts), (case, eid)

    # Generic exclusion: rows anchored to story work are only the planted ones.
    story_refs = {tuple(part.split(":")) for row in rows for part in row["Anchors"].split(";") if part}
    for table in ("HR_recognition_events", "HR_recognition_feedback", "HR_review_notes", "OP_meeting_mentions"):
        key = common.dictionary()[table][0]
        for r in t[table]:
            assert not (_work_refs(r) & story_refs) or r[key] in planted, (table, r)

    def none(case, table, window):
        return next(r for r in rows if r["Case_ID"] == case and r["Table"] == table and r["Row_ID"] == "NONE"
                    and r["Window"] == window)

    handled = set()

    def absence(case, table, window, ok):
        assert ok, f"{case} {table} {window}: {none(case, table, window)['Facts']}"
        handled.add((case, table, window))

    events = t["HR_recognition_events"]
    absence("P1", "HR_recognition_events", "analysis", not any(
        r["Employee_ID"] == "E0010" and r["Recognized_At"] <= WINDOW[1] and _work_refs(r) & {("blocker", "BLK003068"), ("thread", "THR012784")}
        for r in events))
    p2_threads = {("thread", ref.split(":")[1]) for ref in none("P2", "HR_recognition_events", "analysis")["Anchors"].split(";")}
    absence("P2", "HR_recognition_events", "analysis", not any(
        r["Employee_ID"] == "E2156" and _work_refs(r) & p2_threads for r in events + t["HR_recognition_feedback"]))
    absence("P2", "HR_one_on_ones", "analysis", not any(
        r["Employee_ID"] == "E2156" and r["Manager_ID"] == "M32" and r["Topic_Code"] == "workload"
        and "2025-10-01" <= r["Meeting_Date"] <= "2026-09-30" for r in t["HR_one_on_ones"]))

    def m03_about_e0728(r, start, end):
        team = r["Author_Manager_ID"] or home.get(r["Author_Employee_ID"])
        return team == "M03" and start <= r["Interaction_Date"] <= end and (
            r["Employee_ID"] == "E0728" or r["Incident_ID"] == "INC001840")

    absence("P3", "HR_recognition_feedback", "analysis",
            not any(m03_about_e0728(r, "2025-10-01", "2026-09-30") for r in t["HR_recognition_feedback"]))
    absence("P3", "HR_recognition_feedback", "follow-up",
            not any(m03_about_e0728(r, "2026-07-01", "2026-09-30") for r in t["HR_recognition_feedback"]))
    absence("P3", "HR_recognition_events", "analysis", not any(
        r["Employee_ID"] == "E0728" and r["Incident_ID"] == "INC001840" for r in events))
    p4_refs = {tuple(p.split(":")) for p in none("P4", "HR_recognition_events", "analysis")["Anchors"].split(";")}
    absence("P4", "HR_recognition_events", "analysis", not any(
        r["Employee_ID"] in ("E1401", "E1586", "E0561") and _work_refs(r) & p4_refs and r["Recognized_At"] <= WINDOW[1] for r in events))
    absence("P4", "OP_team_plans", "follow-up", not any(
        r["Planning_Manager_ID"] == "M32" and r["Plan_Date"] >= "2026-07-01"
        and (r["Partner_Manager_ID"] == "M16" or "Infrastructure" in r["Item_Text"]) for r in t["OP_team_plans"]))
    p5_people = ("E0001", "E0046", "E0051", "E0066", "E0074", "E0085")
    p5_refs = {("thread", "THR008711"), ("thread", "THR012388")}
    absence("P5", "HR_recognition_events", "analysis", not any(
        r["Employee_ID"] in p5_people and _work_refs(r) & p5_refs for r in events + t["HR_recognition_feedback"])
        and not any(re.search(r"risk list|at-risk|early.warning|renewal-risk", r["Goal_Text"], re.I) for r in t["HR_goals"])
        and not any(re.search(r"renew|risk", r["Goal_Text"], re.I) for r in t["HR_goals"] if r["Employee_ID"] == "E0001"))
    p6_refs = {("contribution", "CON077433"), ("thread", "THR008251")}
    absence("P6", "HR_recognition_events", "analysis", not any(
        r["Employee_ID"] in ("E0970", "E0107") and _work_refs(r) & p6_refs for r in events)
        and not any(r["Author_Employee_ID"] == "E0970" and r["Thread_ID"] == "THR008251" for r in t["OP_collab_messages"])
        and not any(r["Author_Employee_ID"] == "E0970" and _work_refs(r) & p6_refs for r in t["HR_recognition_feedback"]))
    absence("P6", "HR_recognition_events", "follow-up", not any(
        r["Employee_ID"] == "E0970" and _work_refs(r) & p6_refs for r in events))
    absence("D5", "HR_recognition_events", "analysis", not any(
        r["Employee_ID"] == "E1383" and r["Contribution_ID"] == "CON077466" for r in events))
    for case, eid, allowed_mention in (("D7", "E2198", None), ("D8", "E0776", "MTM008816")):
        problems = _constraint_problems(ctx, eid, allowed_mention)
        absence(case, "(background constraint)", "analysis", not problems or print(case, problems))
    expected = {(r["Case_ID"], r["Table"], r["Window"]) for r in rows if r["Row_ID"] == "NONE"}
    assert handled == expected, expected ^ handled

    # Satisfaction alignment (plan §3.3, STORIES_README).
    low = lowest_satisfaction(ctx, "M32")
    assert set(low) == {"E0010", "E2156", "E0728", "E1401", "E1586", "E1748", "E1333", "E2233", "E1383", "E2198"}, low
    assert "E0001" not in lowest_satisfaction(ctx, "M14")
    assert len(ctx.answer_key) == 14 and {r["Origin"] for r in ctx.answer_key} == {"hand_built"}


def _constraint_problems(ctx, eid, allowed_mention):
    """D7/D8 background-constraint rows, evaluated in the analysis window at the as-of date."""
    t, team = ctx.tables, ctx.employee(eid)["Pilot_Manager_ID"]
    threads = {r["Thread_ID"]: r for r in t["OP_collab_threads"]}
    problems = []
    problems += [r["Message_ID"] for r in t["OP_collab_messages"] if r["Author_Employee_ID"] == eid
                 and WINDOW[0] <= r["Sent_At"] <= WINDOW[1] and not threads[r["Thread_ID"]]["Work_Request_ID"]
                 and threads[r["Thread_ID"]]["Requesting_Manager_ID"] != team]
    problems += [r["Interaction_ID"] for r in t["HR_recognition_feedback"] if r["Employee_ID"] == eid
                 and r["Author_Type"] != "home_manager" and WINDOW[0] <= r["Interaction_At"] <= WINDOW[1]
                 and not (r["Share_Recorded_At"] and r["Share_Recorded_At"] <= WINDOW[1])]
    problems += [r["Mention_ID"] for r in t["OP_meeting_mentions"] if r["Mentioned_Employee_ID"] == eid
                 and r["Meeting_Manager_ID"] != team and WINDOW[0] <= r["Meeting_Date"] <= WINDOW[1] and r["Mention_ID"] != allowed_mention]
    problems += [r["Incident_ID"] for r in t["OP_incident_handoffs"] if eid in r["Responder_Employee_IDs"].split(";")
                 and WINDOW[0] <= r["Started_At"] <= WINDOW[1] and (eid == "E2198" or r["Owning_Manager_ID"] != team)]
    problems += [r["Blocker_ID"] for r in t["OP_dependency_blockers"] if r["Resolved_By_Employee_ID"] == eid
                 and WINDOW[0] <= r["Resolved_At"] <= WINDOW[1]]
    weeks = [r for r in t["OP_activity_weekly"] if r["Employee_ID"] == eid and WINDOW[0] <= r["Week_Start"] <= WINDOW[1]]
    problems += [r["Activity_Week_ID"] for r in weeks if int(r["After_Hours_Minutes"]) > 200 or float(r["Cross_Team_Hours"]) > 5]
    return problems


# ---- Self-check -----------------------------------------------------------------------------------------------------

def _signal_proxy(ctx, manager="M32"):
    """A simple stand-in for strongest_signals (plan §3.3): independent signal types per person from the planted and
    background rows at the as-of date, among active people outside the 10 lowest. Not the T2 tool."""
    t, as_of = ctx.tables, common.AS_OF.isoformat()
    team_name = ctx.manager(manager)["Primary_Team"]
    low = set(lowest_satisfaction(ctx, manager))
    members = {r["Employee_ID"]: r["Employee_Name"] for r in ctx.team(manager) if _active(r, as_of)}
    inside = lambda moment: WINDOW[0] <= moment <= WINDOW[1]
    types = {eid: set() for eid in members}
    tables = {eid: set() for eid in members}
    hidden = {eid: [] for eid in members}  # (date, work ref or None)
    recognized = {(r["Employee_ID"], ref) for r in t["HR_recognition_events"] if r["Recognized_At"] <= WINDOW[1] for ref in _work_refs(r)}

    def hit(eid, kind, table, day, ref=None, is_hidden=True):
        types[eid].add(kind)
        if is_hidden:
            types[eid].add("help_other_team")
            tables[eid].add(table)
            hidden[eid].append((day, ref))

    for r in t["OP_contributions"]:
        eid = r["Employee_ID"]
        if eid in members and inside(r["Contribution_Date"]) and r["Beneficiary_Team"] != r["Home_Team"]:
            if r["Request_Channel"] == "informal":
                hit(eid, "visibility_gap", "OP_contributions", r["Contribution_Date"], ("contribution", r["Contribution_ID"]))
                if r["Team_Goal_ID"]:
                    types[eid].add("importance")
    threads = {r["Thread_ID"]: r for r in t["OP_collab_threads"]}
    authors = {}
    for r in t["OP_collab_messages"]:
        authors.setdefault(r["Thread_ID"], set()).add(r["Author_Employee_ID"])
    for r in t["OP_collab_messages"]:
        th = threads[r["Thread_ID"]]
        if not inside(r["Sent_At"]) or th["Requesting_Manager_ID"] == manager or th["Responding_Manager_ID"] != manager or th["Work_Request_ID"]:
            continue
        if r["Author_Employee_ID"] in members:
            hit(r["Author_Employee_ID"], "visibility_gap", "OP_collab_messages", r["Sent_At"][:10], ("thread", th["Thread_ID"]))
        for eid in filter(None, r["Mentioned_Employee_IDs"].split(";")):
            if eid in members and eid != r["Author_Employee_ID"]:
                hit(eid, "visibility_gap", "OP_collab_messages", r["Sent_At"][:10], ("thread", th["Thread_ID"]))
                if eid not in authors[th["Thread_ID"]]:
                    types[eid].add("name_in_others_text")
    for r in t["OP_dependency_blockers"]:
        eid = r["Resolved_By_Employee_ID"]
        if eid in members and r["Blocked_Manager_ID"] != manager and inside(r["Resolved_At"]):
            if not r["Work_Request_ID"]:
                hit(eid, "visibility_gap", "OP_dependency_blockers", r["Resolved_At"][:10], ("blocker", r["Blocker_ID"]))
            if r["Blocked_Team_Goal_ID"]:
                types[eid].add("importance")
    for r in t["OP_incident_handoffs"]:
        if r["Owning_Manager_ID"] != manager and inside(r["Started_At"]):
            for eid in r["Responder_Employee_IDs"].split(";"):
                if eid in members:
                    hit(eid, "visibility_gap", "OP_incident_handoffs", r["Started_At"][:10], ("incident", r["Incident_ID"]))
    for r in t["OP_meeting_mentions"]:
        eid = r["Mentioned_Employee_ID"]
        if eid in members and r["Meeting_Manager_ID"] != manager and inside(r["Meeting_Date"]):
            refs = sorted(_work_refs(r))
            hit(eid, "visibility_gap", "OP_meeting_mentions", r["Meeting_Date"], refs[0] if refs else None)
            types[eid].add("name_in_others_text")
    for r in t["HR_recognition_feedback"]:
        if not inside(r["Interaction_At"]) or r["Author_Type"] == "home_manager":
            continue
        eid = r["Employee_ID"]
        if eid in members and not (r["Share_Recorded_At"] and r["Share_Recorded_At"] <= WINDOW[1]):
            refs = sorted(_work_refs(r))
            hit(eid, "visibility_gap", "HR_recognition_feedback", r["Interaction_Date"], refs[0] if refs else None)
        for other, name in members.items():
            if other != eid and name in r["Message"]:
                hit(other, "name_in_others_text", "HR_recognition_feedback", r["Interaction_Date"])
    recorded_help = {(r["Employee_ID"], r["Beneficiary_Team"]) for r in t["OP_contributions"] if r["Employee_ID"] in members}
    for r in t["HR_self_review_items"]:  # help to another team that matches no goal and no recorded contribution
        if (r["Employee_ID"] in members and r["Team_Helped"] != team_name and not r["Claimed_Goal_ID"]
                and (r["Employee_ID"], r["Team_Helped"]) not in recorded_help):
            types[r["Employee_ID"]].add("self_review")
            tables[r["Employee_ID"]].add("HR_self_review_items")
    weeks = [r for r in t["OP_activity_weekly"] if r["Employee_ID"] in members and inside(r["Week_Start"])]
    for column in ("After_Hours_Minutes", "Cross_Team_Hours"):
        values = sorted(float(r[column]) for r in weeks)
        mean = sum(values) / len(values)
        spread = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        median = values[len(values) // 2]
        for r in weeks:
            if float(r[column]) > median + 3 * spread:
                types[r["Employee_ID"]].add("workload")
                tables[r["Employee_ID"]].add("OP_activity_weekly")
    for eid, items in hidden.items():
        if any(ref is None or (eid, ref) not in recognized for _, ref in items):
            types[eid].add("recognition_gap")
        if len({common.quarter_of(date.fromisoformat(day)) for day, _ in items}) >= 2:
            types[eid].add("repetition")
    ranked = sorted((eid for eid in members if eid not in low and len(types[eid]) >= 2),
                    key=lambda eid: (-len(types[eid]), -len(tables[eid]), -len(hidden[eid]),
                                     -int(max((d for d, _ in hidden[eid]), default="0000-00-00").replace("-", ""))))
    return ranked, types, tables, hidden


def _self_check():
    import time as clock
    from . import hr, ops
    began = clock.perf_counter()
    ctx = common.load_context()
    ops.generate(ctx)
    hr.generate(ctx)
    background_done = clock.perf_counter()
    apply(ctx)
    elapsed = clock.perf_counter() - background_done
    columns = common.dictionary()
    for table in set(ctx.story_planted.values()):
        assert all(set(r) == set(columns[table]) for r in ctx.tables[table]), table
        ids = [r[KEYS[table]] for r in ctx.tables[table]]
        assert len(ids) == len(set(ids)), table
    print("planted per table:", dict(sorted(Counter(ctx.story_planted.values()).items())))
    print("D7/D8 background blockers with the resolver cleared:", ctx.story_constraint_changes)
    print("answer key rows:", len(ctx.answer_key))
    print("M32 10 lowest:", lowest_satisfaction(ctx, "M32"))
    print("M14 10 lowest:", lowest_satisfaction(ctx, "M14"))
    ranked, types, tables, hidden = _signal_proxy(ctx)
    rank = {eid: index + 1 for index, eid in enumerate(ranked)}
    print(f"signal proxy, M32 outside the 10 lowest ({len(ranked)} people with 2+ types):")
    for eid in ranked[:8]:
        print(f"  {rank[eid]}. {eid} types={len(types[eid])} {sorted(types[eid])} tables={len(tables[eid])} items={len(hidden[eid])}")
    for eid, role in (("E0970", "P6"), ("E0107", "D3"), ("E0561", "P4"), ("E0815", "D6"), ("E0776", "D8")):
        print(f"  {role} {eid}: rank {rank.get(eid, '-')}, types {sorted(types[eid])}, tables {sorted(tables[eid])}")
    print(f"runtime: stories {elapsed:.2f}s; ops+hr+stories {clock.perf_counter() - began:.1f}s")
    print("stories self-check: OK")


if __name__ == "__main__":
    _self_check()
