import { BASE_BUSY, BASE_ROOM_BUSY } from "./mockActionData";
import type { EchoAction, MeetingRecord, TimeSlot } from "./actionTypes";

export const WORK_START = 9 * 60;
export const WORK_END = 17 * 60;

export function toMinutes(value: string) {
  const [hours, minutes] = value.split(":").map(Number);
  return hours * 60 + minutes;
}

export function fromMinutes(value: number) {
  return `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
}

export function overlaps(a: TimeSlot, b: TimeSlot) {
  return (
    a.date === b.date &&
    toMinutes(a.start) < toMinutes(b.end) &&
    toMinutes(b.start) < toMinutes(a.end)
  );
}

function participantBaseId(participantId: string) {
  return participantId.replace(/^.*-p/, "p");
}

export function participantBusy(participantId: string, actions: EchoAction[]) {
  const baseId = participantBaseId(participantId);
  const fixed = BASE_BUSY.filter((item) => item.participantId === baseId);
  const saved = actions
    .filter(
      (action) =>
        action.status !== "Cancelled" &&
        action.participantIds.includes(participantId),
    )
    .map((action) => ({ ...action.slot, participantId, label: action.title }));
  return [...fixed, ...saved];
}

export function isParticipantSlotFree(
  participantIds: string[],
  slot: TimeSlot,
  actions: EchoAction[],
  ignoreId?: string,
) {
  return participantIds.every((id) =>
    participantBusy(
      id,
      actions.filter((a) => a.id !== ignoreId),
    ).every((busy) => !overlaps(slot, busy)),
  );
}

export function roomBusy(roomId: string, actions: EchoAction[]) {
  const fixed = BASE_ROOM_BUSY.filter((item) => item.roomId === roomId);
  const saved = actions
    .filter(
      (action): action is MeetingRecord =>
        action.kind === "meeting" &&
        action.status !== "Cancelled" &&
        action.location.type === "room" &&
        action.location.roomId === roomId,
    )
    .map((action) => ({ ...action.slot, roomId, label: action.title }));
  return [...fixed, ...saved];
}

export function isRoomFree(
  roomId: string,
  slot: TimeSlot,
  actions: EchoAction[],
  ignoreId?: string,
) {
  return roomBusy(
    roomId,
    actions.filter((a) => a.id !== ignoreId),
  ).every((busy) => !overlaps(slot, busy));
}

export function suggestedSlots(
  participantIds: string[],
  weekDates: string[],
  duration: number,
  actions: EchoAction[],
  limit = 6,
) {
  const result: TimeSlot[] = [];
  for (const date of weekDates) {
    for (let start = WORK_START; start + duration <= WORK_END; start += 30) {
      const slot = {
        date,
        start: fromMinutes(start),
        end: fromMinutes(start + duration),
      };
      if (isParticipantSlotFree(participantIds, slot, actions))
        result.push(slot);
      if (result.length === limit) return result;
    }
  }
  return result;
}

export function addDays(date: string, amount: number) {
  const next = new Date(`${date}T12:00:00`);
  next.setDate(next.getDate() + amount);
  return next.toISOString().slice(0, 10);
}

export function weekDates(monday: string) {
  return Array.from({ length: 5 }, (_, index) => addDays(monday, index));
}

export function formatTime(time: string) {
  const [hour, minute] = time.split(":").map(Number);
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(2026, 0, 1, hour, minute));
}

export function formatDate(
  date: string,
  options: Intl.DateTimeFormatOptions = {
    weekday: "short",
    month: "short",
    day: "numeric",
  },
) {
  return new Intl.DateTimeFormat(undefined, options).format(
    new Date(`${date}T12:00:00`),
  );
}
