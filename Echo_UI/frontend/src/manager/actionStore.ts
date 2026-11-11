import type { EchoAction } from "./actionTypes";

const key = (managerId: string) =>
  `echo-action-center-v1-${managerId.toUpperCase()}`;

function isAction(value: unknown): value is EchoAction {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  const slot = item.slot as Record<string, unknown> | undefined;
  const statuses = [
    "Draft",
    "Planned",
    "Confirmed in prototype",
    "Cancelled",
    "Completed",
  ];
  return (
    (item.kind === "meeting" || item.kind === "event") &&
    typeof item.id === "string" &&
    typeof item.title === "string" &&
    statuses.includes(String(item.status)) &&
    Array.isArray(item.participantIds) &&
    item.participantIds.every((id) => typeof id === "string") &&
    !!slot &&
    typeof slot.date === "string" &&
    typeof slot.start === "string" &&
    typeof slot.end === "string"
  );
}

export function loadActions(managerId: string): EchoAction[] {
  try {
    const parsed: unknown = JSON.parse(
      localStorage.getItem(key(managerId)) ?? "[]",
    );
    return Array.isArray(parsed) ? parsed.filter(isAction) : [];
  } catch {
    return [];
  }
}

export function saveActions(managerId: string, actions: EchoAction[]) {
  try {
    localStorage.setItem(key(managerId), JSON.stringify(actions.slice(0, 100)));
  } catch {
    /* Browser storage can be unavailable; current-session state still works. */
  }
}

export function nextActionId(
  managerId: string,
  kind: "meeting" | "event",
  actions: EchoAction[],
) {
  let index = actions.length + 1;
  let candidate = `${managerId.toLowerCase()}-${kind}-${index}`;
  while (actions.some((action) => action.id === candidate))
    candidate = `${managerId.toLowerCase()}-${kind}-${++index}`;
  return candidate;
}
