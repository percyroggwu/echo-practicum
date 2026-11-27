import clsx from "clsx";
import { ArrowLeft, CheckCircle2, Gift, PenLine } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { Button, Card } from "../components/ui";
import type { Participant } from "./actionTypes";
import { BookingSteps, demoRef, useBookingSequence } from "./booking";
import { OWN_WORDS_MIN, OwnWords, withOwnWords } from "./Brief";

/** What the manager can send. Everything is a demo: no card is bought and nothing is sent. */
const GIFTS = [
  { id: "note", label: "Note only", amount: 0 },
  { id: "25", label: "$25 gift card", amount: 25 },
  { id: "50", label: "$50 gift card", amount: 50 },
  { id: "100", label: "$100 gift card", amount: 100 },
] as const;
const KINDS = ["Digital gift card (any store)", "Coffee card", "Meal voucher"] as const;

const STEPS = [
  "Checking the recognition budget",
  "Creating the gift card",
  "Adding your note",
  "Scheduling delivery",
];

function draft(name: string, giftLabel: string | null) {
  const first = name.trim().split(/\s+/)[0] || "there";
  return `Hi ${first},\n\nI wanted to say thank you for the work you did for another team this quarter. It made a real difference, and I want to make sure it is seen.${giftLabel ? ` A small ${giftLabel.toLowerCase()} is on its way as a thank-you.` : ""}\n\nThank you.`;
}

/** Recognize someone: a note, optionally with a gift card. A demo booking: nothing is bought or sent. */
export default function RecognizeTool({
  managerId,
  participants,
  onBack,
  onDone,
}: {
  managerId: string;
  participants: Participant[];
  onBack: () => void;
  onDone: (message: string) => void;
}) {
  // People Discovery found below the surface come first, so the person in the story is one click away.
  const [found, setFound] = useState<string[]>([]);
  const [name, setName] = useState("");
  useEffect(() => {
    let live = true;
    api
      .teamDiscovery(managerId)
      .then((r) => {
        if (!live) return;
        const names = [...new Set((r.discovery?.findings ?? []).flatMap((f) => f.employee_names))];
        setFound(names);
        setName((current) => current || names[0] || "");
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [managerId]);
  const suggestions = [...new Set([...found, ...participants.map((p) => p.name)])];
  const [giftId, setGiftId] = useState<(typeof GIFTS)[number]["id"]>("50");
  const [kind, setKind] = useState<(typeof KINDS)[number]>(KINDS[0]);
  const [own, setOwn] = useState("");
  const [ref, setRef] = useState<string | null>(null);
  const gift = GIFTS.find((g) => g.id === giftId)!;
  const giftLabel = gift.amount ? `$${gift.amount} ${kind.split(" (")[0].toLowerCase()}` : null;
  const text = useMemo(() => withOwnWords(draft(name, giftLabel), own), [name, giftLabel, own]);
  const ready = own.trim().length >= OWN_WORDS_MIN && name.trim().length > 1;
  const steps = gift.amount ? STEPS : ["Adding your note", "Scheduling delivery"];
  const sequence = useBookingSequence(steps);

  function send() {
    setRef(demoRef(gift.amount ? "GC" : "NT"));
    sequence.start();
  }

  return (
    <section className="space-y-5">
      <div>
        <button
          type="button"
          onClick={onBack}
          className="mb-2 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600"
        >
          <ArrowLeft className="size-4" /> Action Center
        </button>
        <h2 className="flex items-center gap-2 text-2xl font-semibold">
          <Gift className="size-6 text-rose-500" /> Recognize someone
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          A note in your words, with a gift card if you like. Demo only: no card is bought and nothing is sent.
        </p>
      </div>

      {ref ? (
        <Card className="p-5">
          <BookingSteps steps={steps} done={sequence.done} />
          {sequence.finished && (
            <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200" role="status">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="size-5" />
                {gift.amount ? `${giftLabel} for ${name}` : `Note for ${name}`}
              </div>
              <p className="mt-1">
                Reference <span className="font-mono">{ref}</span>. In a real company this would go through your
                recognition tool; here nothing was bought or sent.
              </p>
              <div className="mt-3 flex gap-2">
                <Button variant="primary" onClick={() => onDone(`Recognition for ${name} sent (demo). Reference ${ref}.`)}>
                  Done
                </Button>
                <Button variant="ghost" onClick={() => { setRef(null); setOwn(""); }}>
                  Recognize someone else
                </Button>
              </div>
            </div>
          )}
        </Card>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[1fr_1.2fr]">
          <Card className="space-y-4 p-5">
            <label className="block text-sm font-medium">
              Who
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                list="recognize-people"
                placeholder="Type or pick a name"
                className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
              />
              <datalist id="recognize-people">
                {suggestions.map((n) => (
                  <option key={n} value={n} />
                ))}
              </datalist>
              {found.length > 0 && (
                <span className="mt-1.5 flex flex-wrap gap-1.5">
                  {found.map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => setName(n)}
                      className={clsx(
                        "rounded-full px-2.5 py-0.5 text-xs font-medium ring-1",
                        n === name ? "bg-amber-100 text-amber-900 ring-amber-300 dark:bg-amber-500/15 dark:text-amber-100" : "text-slate-600 ring-slate-200 hover:bg-slate-50 dark:text-slate-300 dark:ring-slate-700",
                      )}
                    >
                      {n} · found by Discovery
                    </button>
                  ))}
                </span>
              )}
            </label>
            <div>
              <div className="text-sm font-medium">Add a gift</div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {GIFTS.map((g) => (
                  <button
                    key={g.id}
                    type="button"
                    onClick={() => setGiftId(g.id)}
                    className={clsx(
                      "rounded-xl border px-3 py-2 text-sm transition",
                      g.id === giftId
                        ? "border-rose-300 bg-rose-50 font-semibold text-rose-900 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100"
                        : "border-slate-200 hover:border-rose-200 dark:border-slate-700",
                    )}
                  >
                    {g.label}
                  </button>
                ))}
              </div>
            </div>
            {gift.amount > 0 && (
              <label className="block text-sm font-medium">
                Type
                <select
                  value={kind}
                  onChange={(e) => setKind(e.target.value as (typeof KINDS)[number])}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
                >
                  {KINDS.map((k) => (
                    <option key={k}>{k}</option>
                  ))}
                </select>
              </label>
            )}
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <PenLine className="size-4 text-indigo-500" /> The note
            </div>
            <pre className="mt-2 whitespace-pre-wrap rounded-xl bg-slate-50 p-3 font-sans text-sm leading-6 text-slate-700 dark:bg-slate-950 dark:text-slate-300">
              {text}
            </pre>
            <OwnWords id="recognize-own-words" value={own} onChange={setOwn} />
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Button variant="primary" icon={Gift} disabled={!ready} onClick={send}>
                {gift.amount ? `Send note and ${giftLabel}` : "Send note"}
              </Button>
              {!ready && <span className="text-xs text-slate-500">Add a line in your own words first.</span>}
            </div>
          </Card>
        </div>
      )}
    </section>
  );
}
