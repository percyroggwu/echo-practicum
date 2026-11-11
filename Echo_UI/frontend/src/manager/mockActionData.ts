import type {
  BusyInterval,
  MeetingRoom,
  Participant,
} from "./actionTypes";

export const ACTION_TIME_ZONE = "America/New_York";

export function participantsFor(
  managerId: string,
  team: string,
): Participant[] {
  const names = [
    ["Jordan Lee", "Senior Analyst"],
    ["Maya Patel", "Program Manager"],
    ["Theo Brooks", "Operations Partner"],
    ["Sofia Chen", "People Analyst"],
    ["Amara Okafor", "Project Lead"],
    ["Eli Romero", "Data Specialist"],
    ["Nina Foster", "Coordinator"],
    ["Marcus Bell", "Business Partner"],
    ["Priya Shah", "Product Analyst"],
    ["Owen Reed", "Team Lead"],
    ["Leila Hassan", "Research Associate"],
    ["Caleb Wright", "Operations Analyst"],
  ];
  return names.map(([name, role], index) => ({
    id: `${managerId.toLowerCase()}-p${index + 1}`,
    name,
    role,
    team,
    initials: name
      .split(" ")
      .map((part) => part[0])
      .join(""),
  }));
}

export const ROOMS: MeetingRoom[] = [
  {
    id: "room-a",
    name: "Collaboration Room A",
    floor: "North · Floor 2",
    capacity: 4,
    amenities: ["Display", "Whiteboard"],
    type: "Collaboration",
    x: 7,
    y: 12,
    width: 25,
    height: 26,
  },
  {
    id: "room-b",
    name: "Conference Room B",
    floor: "North · Floor 2",
    capacity: 8,
    amenities: ["Video", "Display", "Whiteboard"],
    type: "Conference",
    x: 37,
    y: 12,
    width: 27,
    height: 26,
  },
  {
    id: "room-c",
    name: "Strategy Room C",
    floor: "North · Floor 2",
    capacity: 12,
    amenities: ["Video", "Display", "Accessible"],
    type: "Conference",
    x: 69,
    y: 12,
    width: 24,
    height: 39,
  },
  {
    id: "room-d",
    name: "Training Room D",
    floor: "South · Floor 3",
    capacity: 20,
    amenities: ["Video", "Projector", "Accessible"],
    type: "Training",
    x: 7,
    y: 58,
    width: 38,
    height: 28,
  },
  {
    id: "room-e",
    name: "Focus Room E",
    floor: "South · Floor 3",
    capacity: 2,
    amenities: ["Display"],
    type: "Focus",
    x: 51,
    y: 58,
    width: 18,
    height: 28,
  },
  {
    id: "room-f",
    name: "Workshop Room F",
    floor: "South · Floor 3",
    capacity: 10,
    amenities: ["Whiteboard", "Projector", "Accessible"],
    type: "Collaboration",
    x: 74,
    y: 58,
    width: 19,
    height: 28,
  },
];

export const BASE_BUSY: BusyInterval[] = [
  {
    date: "2026-11-16",
    start: "09:00",
    end: "10:00",
    participantId: "p1",
    label: "Project review",
  },
  {
    date: "2026-11-16",
    start: "11:00",
    end: "12:00",
    participantId: "p2",
    label: "Team sync",
  },
  {
    date: "2026-11-16",
    start: "14:00",
    end: "15:30",
    participantId: "p3",
    label: "Focus time",
  },
  {
    date: "2026-11-17",
    start: "09:30",
    end: "10:30",
    participantId: "p1",
    label: "Partner call",
  },
  {
    date: "2026-11-17",
    start: "13:00",
    end: "14:00",
    participantId: "p2",
    label: "Planning",
  },
  {
    date: "2026-11-17",
    start: "14:00",
    end: "15:00",
    participantId: "p4",
    label: "Review",
  },
  {
    date: "2026-11-18",
    start: "10:00",
    end: "11:30",
    participantId: "p3",
    label: "Workshop",
  },
  {
    date: "2026-11-18",
    start: "13:30",
    end: "14:30",
    participantId: "p1",
    label: "One-to-one",
  },
  {
    date: "2026-11-19",
    start: "09:00",
    end: "10:30",
    participantId: "p2",
    label: "Department meeting",
  },
  {
    date: "2026-11-19",
    start: "15:00",
    end: "16:30",
    participantId: "p4",
    label: "Training",
  },
  {
    date: "2026-11-20",
    start: "11:00",
    end: "12:00",
    participantId: "p1",
    label: "Weekly close",
  },
  {
    date: "2026-11-20",
    start: "13:00",
    end: "14:00",
    participantId: "p3",
    label: "Planning",
  },
];

export const BASE_ROOM_BUSY: BusyInterval[] = [
  {
    date: "2026-11-16",
    start: "09:00",
    end: "10:30",
    roomId: "room-a",
    label: "Reserved",
  },
  {
    date: "2026-11-16",
    start: "13:00",
    end: "14:30",
    roomId: "room-b",
    label: "Reserved",
  },
  {
    date: "2026-11-17",
    start: "10:00",
    end: "12:00",
    roomId: "room-c",
    label: "Reserved",
  },
  {
    date: "2026-11-18",
    start: "13:00",
    end: "16:00",
    roomId: "room-d",
    label: "Training",
  },
  {
    date: "2026-11-19",
    start: "09:00",
    end: "11:00",
    roomId: "room-f",
    label: "Workshop",
  },
  {
    date: "2026-11-20",
    start: "14:00",
    end: "15:30",
    roomId: "room-b",
    label: "Reserved",
  },
];

// Restaurants are real places now, with sources: see venues.ts.
export { VENUES } from "./venues";

export const RECOMMENDATIONS = [
  {
    id: "recognition-gap",
    category: "Existing Echo evidence",
    title: "Recognition follow-up",
    context:
      "Documented cross-team work received positive feedback, but no contribution-specific recognition record is linked.",
    limitation:
      "A missing linked record does not prove recognition was absent.",
    action:
      "Schedule a discussion to review the contribution and confirm whether recognition already occurred.",
    tool: "scheduler" as const,
  },
  {
    id: "workload-check",
    category: "Existing Echo evidence",
    title: "Workload coordination",
    context:
      "A team member has supported another department repeatedly in the synthetic contribution history.",
    limitation:
      "Contribution hours alone do not show that the employee is overloaded.",
    action:
      "Hold a workload check-in and coordinate priorities with the partner-team manager if appropriate.",
    tool: "scheduler" as const,
  },
  {
    id: "team-connection",
    category: "Synthetic scenario",
    title: "Team connection",
    context:
      "For demonstration only: team members expressed interest in more optional opportunities to connect.",
    limitation:
      "A social event is an optional intervention, not a proven remedy for morale.",
    action:
      "Consider a voluntary lunch or dinner after reviewing budget and schedule constraints.",
    tool: "event" as const,
  },
];
