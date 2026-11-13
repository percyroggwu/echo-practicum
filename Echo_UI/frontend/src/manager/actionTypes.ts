export type ActionStatus =
  | "Draft"
  | "Planned"
  | "Confirmed in prototype"
  | "Cancelled"
  | "Completed";
export type ActionOrigin = {
  kind: "existing-evidence" | "synthetic-scenario" | "manager-created";
  label: string;
  insightId?: string;
};

export type Participant = {
  id: string;
  name: string;
  role: string;
  team: string;
  initials: string;
};

export type TimeSlot = { date: string; start: string; end: string };
export type BusyInterval = TimeSlot & {
  participantId?: string;
  roomId?: string;
  label: string;
};

export type MeetingRoom = {
  id: string;
  name: string;
  floor: string;
  capacity: number;
  amenities: string[];
  type: "Focus" | "Collaboration" | "Conference" | "Training";
  x: number;
  y: number;
  width: number;
  height: number;
};

export type MeetingPurpose =
  | "Recognition discussion"
  | "Workload check-in"
  | "Cross-team coordination"
  | "Team engagement"
  | "General team meeting";

export type MeetingRecord = {
  id: string;
  kind: "meeting";
  managerId: string;
  title: string;
  purpose: MeetingPurpose;
  description: string;
  participantIds: string[];
  slot: TimeSlot;
  duration: number;
  location: {
    type: "room" | "virtual" | "none";
    roomId?: string;
    label: string;
  };
  agenda: string;
  status: ActionStatus;
  origin: ActionOrigin;
  createdAt: string;
};

/** A real restaurant. Only facts from the cited source; Echo never books or contacts it. */
export type Venue = {
  id: string;
  name: string;
  address: string;
  cuisine: string;
  /** Only where a source said so. */
  meals?: ("Lunch" | "Dinner")[];
  note?: string;
  website: string;
  source: { label: string; url: string };
  /** Rough walking minutes from the office. */
  walk: number;
  lat: number;
  lon: number;
};

export type TeamEventRecord = {
  id: string;
  kind: "event";
  managerId: string;
  eventType: "Lunch" | "Dinner";
  title: string;
  teamSize: number;
  participantIds: string[];
  slot: TimeSlot;
  budgetPerPerson: number;
  area: string;
  requirements: string;
  venueId: string;
  estimatedTotal: number;
  invitation: string;
  status: ActionStatus;
  origin: ActionOrigin;
  createdAt: string;
};

export type EchoAction = MeetingRecord | TeamEventRecord;

export type SchedulerPrefill = Partial<
  Pick<
    MeetingRecord,
    "title" | "purpose" | "description" | "participantIds" | "origin"
  >
>;
