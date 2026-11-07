// can_administer: may a dose of this medication be given at `now`?
// The rules are in docs/spec/02-domain-model.md §2.8 and docs/spec/07-portable-core.md §7.7.
//
// - Limits come from the order revision in force: a minimum interval between doses and a maximum
//   number of doses in a rolling window. A one-off `not_before` lockout and the order's dates apply too.
// - Doses entered in error don't count. Refused, skipped and not-needed doses don't count; spat-out and
//   vomited doses count unless the order says otherwise.
// - A dose recorded on another device counts as up to `clock_skew_margin_ms` later than its recorded time.
// - On a device, the answer is `unverified` when the dose history is older than the freshness bound or
//   the clock looks wrong. If the clock looks right and the records already rule the dose out, the answer
//   is `denied`, however old the history.
// - `next_allowed_at` walks the dated revisions, so a revision taking effect before the next allowed time
//   applies its own limits.

import { kernelError } from '../errors';
import { add, sub } from '../ints';
import {
  at,
  expectArray,
  expectBoolean,
  expectEnum,
  expectId,
  expectInteger,
  expectNullableId,
  expectNullableInteger,
  expectObject,
  join,
  type Obj,
} from '../validate';

const INSTANT_MAX = 4102444800000; // 2100-01-01T00:00:00Z
const DURATION_MAX = 31622400000; // 366 days
const FRESHNESS_MAX = 2592000000; // 30 days
const MARGIN_MAX = 86400000; // 1 day
const COUNT_MAX = 1000;
const MAX_REVISIONS = 64;
const MAX_ADMINISTRATIONS = 5000;

const ORDER_STATUSES: readonly string[] = ['active', 'paused', 'completed', 'discontinued'];
const DOSE_STATUSES: readonly string[] = ['given', 'partial', 'refused', 'spat_out', 'vomited_after', 'skipped', 'not_needed'];
const COMPUTED_ON: readonly string[] = ['server', 'device'];

interface Context {
  readonly isDevice: boolean;
  readonly deviceId: string | null;
  readonly lastServerTimeSeen: number | null;
  readonly historyConfirmedAt: number | null;
  readonly freshnessBoundMs: number;
  readonly clockSkewMarginMs: number;
}

interface Revision {
  readonly id: string;
  readonly effectiveFrom: number;
  readonly minIntervalMs: number | null;
  readonly maxCount: number | null;
  readonly windowMs: number | null;
}

interface Order {
  readonly status: string;
  readonly startsAt: number;
  readonly endsAt: number | null;
  readonly notBeforeAt: number | null;
  readonly countsSpatOutAndVomited: boolean;
  readonly revisions: readonly Revision[]; // sorted by effectiveFrom
}

interface Dose {
  readonly id: string;
  readonly administeredAt: number;
  readonly status: string;
  readonly enteredInError: boolean;
  readonly deviceId: string | null;
}

interface Counted {
  readonly id: string;
  readonly t: number; // when it may have happened, at the latest (recorded time plus any skew margin)
  readonly raw: number; // the recorded time
}

interface Reason {
  readonly code: string;
  readonly until: number | null;
}

function itemAt<T>(list: readonly T[], index: number): T {
  const value = list[index];
  if (value === undefined) {
    throw kernelError('INTERNAL', null);
  }
  return value;
}

function compareIds(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

function compareRevisions(a: Revision, b: Revision): number {
  if (a.effectiveFrom !== b.effectiveFrom) {
    return a.effectiveFrom < b.effectiveFrom ? -1 : 1;
  }
  return compareIds(a.id, b.id);
}

function compareCounted(a: Counted, b: Counted): number {
  if (a.t !== b.t) {
    return a.t < b.t ? -1 : 1;
  }
  return compareIds(a.id, b.id);
}

// ---------------------------------------------------------------- validation

function readInstant(value: unknown, path: string): number {
  return expectInteger(value, path, 0, INSTANT_MAX);
}

function readNullableInstant(value: unknown, path: string): number | null {
  return expectNullableInteger(value, path, 0, INSTANT_MAX);
}

function readContext(value: unknown): Context {
  const path = 'context';
  const o = expectObject(value, path, [
    'computed_on',
    'device_id',
    'last_server_time_seen',
    'history_confirmed_at',
    'freshness_bound_ms',
    'clock_skew_margin_ms',
  ]);
  const isDevice = expectEnum(o['computed_on'], join(path, 'computed_on'), COMPUTED_ON) === 'device';
  const deviceId = expectNullableId(o['device_id'], join(path, 'device_id'));
  const lastServerTimeSeen = readNullableInstant(o['last_server_time_seen'], join(path, 'last_server_time_seen'));
  const historyConfirmedAt = readNullableInstant(o['history_confirmed_at'], join(path, 'history_confirmed_at'));
  const freshnessBoundMs = expectInteger(o['freshness_bound_ms'], join(path, 'freshness_bound_ms'), 0, FRESHNESS_MAX);
  const clockSkewMarginMs = expectInteger(o['clock_skew_margin_ms'], join(path, 'clock_skew_margin_ms'), 0, MARGIN_MAX);
  if (isDevice) {
    if (deviceId === null) {
      throw kernelError('INVALID_CONTEXT', join(path, 'device_id'));
    }
  } else {
    // The server is authoritative: it names no device and needs no freshness or clock checks.
    if (deviceId !== null) {
      throw kernelError('INVALID_CONTEXT', join(path, 'device_id'));
    }
    if (lastServerTimeSeen !== null) {
      throw kernelError('INVALID_CONTEXT', join(path, 'last_server_time_seen'));
    }
    if (historyConfirmedAt !== null) {
      throw kernelError('INVALID_CONTEXT', join(path, 'history_confirmed_at'));
    }
  }
  return {
    isDevice: isDevice,
    deviceId: deviceId,
    lastServerTimeSeen: lastServerTimeSeen,
    historyConfirmedAt: historyConfirmedAt,
    freshnessBoundMs: freshnessBoundMs,
    clockSkewMarginMs: clockSkewMarginMs,
  };
}

function readRevision(value: unknown, path: string): Revision {
  const o = expectObject(value, path, ['id', 'effective_from', 'min_interval_ms', 'max_doses']);
  const id = expectId(o['id'], join(path, 'id'));
  const effectiveFrom = readInstant(o['effective_from'], join(path, 'effective_from'));
  const minIntervalMs = expectNullableInteger(o['min_interval_ms'], join(path, 'min_interval_ms'), 1, DURATION_MAX);
  let maxCount: number | null = null;
  let windowMs: number | null = null;
  const maxDoses = o['max_doses'];
  if (maxDoses !== null) {
    const m = expectObject(maxDoses, join(path, 'max_doses'), ['count', 'window_ms']);
    maxCount = expectInteger(m['count'], join(join(path, 'max_doses'), 'count'), 1, COUNT_MAX);
    windowMs = expectInteger(m['window_ms'], join(join(path, 'max_doses'), 'window_ms'), 1, DURATION_MAX);
  }
  return { id: id, effectiveFrom: effectiveFrom, minIntervalMs: minIntervalMs, maxCount: maxCount, windowMs: windowMs };
}

function readOrder(value: unknown): Order {
  const path = 'order';
  const o = expectObject(value, path, [
    'id',
    'status',
    'starts_at',
    'ends_at',
    'not_before',
    'counts_spat_out_and_vomited',
    'revisions',
  ]);
  expectId(o['id'], join(path, 'id'));
  const status = expectEnum(o['status'], join(path, 'status'), ORDER_STATUSES);
  const startsAt = readInstant(o['starts_at'], join(path, 'starts_at'));
  const endsAt = readNullableInstant(o['ends_at'], join(path, 'ends_at'));
  let notBeforeAt: number | null = null;
  if (o['not_before'] !== null) {
    const nb = expectObject(o['not_before'], join(path, 'not_before'), ['at']);
    notBeforeAt = readInstant(nb['at'], join(join(path, 'not_before'), 'at'));
  }
  const countsSpatOutAndVomited = expectBoolean(o['counts_spat_out_and_vomited'], join(path, 'counts_spat_out_and_vomited'));
  const revisionsPath = join(path, 'revisions');
  const list = expectArray(o['revisions'], revisionsPath, MAX_REVISIONS);
  if (list.length === 0) {
    throw kernelError('TOO_FEW_ITEMS', revisionsPath);
  }
  const revisions: Revision[] = [];
  const ids = new Set<string>();
  const starts = new Set<number>();
  for (let i = 0; i < list.length; i++) {
    const revision = readRevision(list[i], at(revisionsPath, i));
    if (ids.has(revision.id)) {
      throw kernelError('DUPLICATE_ID', join(at(revisionsPath, i), 'id'));
    }
    if (starts.has(revision.effectiveFrom)) {
      throw kernelError('DUPLICATE_EFFECTIVE_FROM', join(at(revisionsPath, i), 'effective_from'));
    }
    ids.add(revision.id);
    starts.add(revision.effectiveFrom);
    revisions.push(revision);
  }
  revisions.sort(compareRevisions);
  return {
    status: status,
    startsAt: startsAt,
    endsAt: endsAt,
    notBeforeAt: notBeforeAt,
    countsSpatOutAndVomited: countsSpatOutAndVomited,
    revisions: revisions,
  };
}

function readDoses(value: unknown): Dose[] {
  const path = 'administrations';
  const list = expectArray(value, path, MAX_ADMINISTRATIONS);
  const doses: Dose[] = [];
  const ids = new Set<string>();
  for (let i = 0; i < list.length; i++) {
    const itemPath = at(path, i);
    const o = expectObject(list[i], itemPath, ['id', 'administered_at', 'status', 'entered_in_error', 'device_id']);
    const id = expectId(o['id'], join(itemPath, 'id'));
    if (ids.has(id)) {
      throw kernelError('DUPLICATE_ID', join(itemPath, 'id'));
    }
    ids.add(id);
    doses.push({
      id: id,
      administeredAt: readInstant(o['administered_at'], join(itemPath, 'administered_at')),
      status: expectEnum(o['status'], join(itemPath, 'status'), DOSE_STATUSES),
      enteredInError: expectBoolean(o['entered_in_error'], join(itemPath, 'entered_in_error')),
      deviceId: expectNullableId(o['device_id'], join(itemPath, 'device_id')),
    });
  }
  return doses;
}

// ---------------------------------------------------------------- rules

function countsAsGiven(status: string, countsSpatOutAndVomited: boolean): boolean {
  if (status === 'given' || status === 'partial') {
    return true;
  }
  if (status === 'spat_out' || status === 'vomited_after') {
    return countsSpatOutAndVomited;
  }
  return false;
}

function isOtherDevice(dose: Dose, context: Context): boolean {
  return dose.deviceId !== null && dose.deviceId !== context.deviceId;
}

function revisionAt(revisions: readonly Revision[], time: number): Revision | null {
  let found: Revision | null = null;
  for (let i = 0; i < revisions.length; i++) {
    const revision = itemAt(revisions, i);
    if (revision.effectiveFrom > time) {
      break;
    }
    found = revision;
  }
  return found;
}

function nextBoundaryAfter(revisions: readonly Revision[], time: number): number | null {
  for (let i = 0; i < revisions.length; i++) {
    const revision = itemAt(revisions, i);
    if (revision.effectiveFrom > time) {
      return revision.effectiveFrom;
    }
  }
  return null;
}

// Index of the first dose still inside the window ending at `time`. Doses are sorted by `t`.
function firstInWindow(counted: readonly Counted[], time: number, windowMs: number): number {
  let k = 0;
  while (k < counted.length && add(itemAt(counted, k).t, windowMs) <= time) {
    k++;
  }
  return k;
}

// The earliest time from `time` on when one more dose stays within the maximum.
function windowAllows(counted: readonly Counted[], time: number, maxCount: number, windowMs: number): number {
  const k = firstInWindow(counted, time, windowMs);
  const inWindow = counted.length - k;
  if (inWindow < maxCount) {
    return time;
  }
  return add(itemAt(counted, k + inWindow - maxCount).t, windowMs);
}

// The earliest time from `time` on that meets one revision's interval and window limits.
function revisionAllows(revision: Revision, time: number, counted: readonly Counted[], lastT: number | null): number {
  let candidate = time;
  if (revision.minIntervalMs !== null && lastT !== null) {
    const afterInterval = add(lastT, revision.minIntervalMs);
    if (afterInterval > candidate) {
      candidate = afterInterval;
    }
  }
  if (revision.maxCount !== null && revision.windowMs !== null) {
    const afterWindow = windowAllows(counted, time, revision.maxCount, revision.windowMs);
    if (afterWindow > candidate) {
      candidate = afterWindow;
    }
  }
  return candidate;
}

function nextAllowedAt(order: Order, counted: readonly Counted[], lastT: number | null, now: number): number | null {
  let time = now;
  if (order.startsAt > time) {
    time = order.startsAt;
  }
  if (order.notBeforeAt !== null && order.notBeforeAt > time) {
    time = order.notBeforeAt;
  }
  const firstEffective = itemAt(order.revisions, 0).effectiveFrom;
  if (firstEffective > time) {
    time = firstEffective;
  }
  for (let step = 0; step <= order.revisions.length; step++) {
    const revision = revisionAt(order.revisions, time);
    if (revision === null) {
      throw kernelError('INTERNAL', null);
    }
    const candidate = revisionAllows(revision, time, counted, lastT);
    const boundary = nextBoundaryAfter(order.revisions, time);
    if (boundary === null || candidate < boundary) {
      return order.endsAt !== null && candidate >= order.endsAt ? null : candidate;
    }
    time = boundary;
  }
  throw kernelError('INTERNAL', null);
}

function clockLooksWrong(context: Context, doses: readonly Dose[], now: number): boolean {
  if (context.lastServerTimeSeen !== null && now < context.lastServerTimeSeen) {
    return true;
  }
  if (context.historyConfirmedAt !== null && now < context.historyConfirmedAt) {
    return true;
  }
  for (let i = 0; i < doses.length; i++) {
    const dose = itemAt(doses, i);
    if (dose.enteredInError) {
      continue;
    }
    const earliest = isOtherDevice(dose, context) || dose.deviceId === null
      ? sub(dose.administeredAt, context.clockSkewMarginMs)
      : dose.administeredAt;
    if (earliest > now) {
      return true;
    }
  }
  return false;
}

function historyIsStale(context: Context, now: number): boolean {
  return context.historyConfirmedAt === null || sub(now, context.historyConfirmedAt) > context.freshnessBoundMs;
}

// ---------------------------------------------------------------- operation

export function canAdminister(request: Obj): unknown {
  const r = expectObject(request, '', ['schema_version', 'now', 'context', 'order', 'administrations']);
  expectInteger(r['schema_version'], 'schema_version', 1, 1);
  const now = readInstant(r['now'], 'now');
  const context = readContext(r['context']);
  const order = readOrder(r['order']);
  const doses = readDoses(r['administrations']);

  const counted: Counted[] = [];
  let lastGiven: number | null = null;
  for (let i = 0; i < doses.length; i++) {
    const dose = itemAt(doses, i);
    if (dose.enteredInError || !countsAsGiven(dose.status, order.countsSpatOutAndVomited)) {
      continue;
    }
    const t = isOtherDevice(dose, context) ? add(dose.administeredAt, context.clockSkewMarginMs) : dose.administeredAt;
    counted.push({ id: dose.id, t: t, raw: dose.administeredAt });
    if (lastGiven === null || dose.administeredAt > lastGiven) {
      lastGiven = dose.administeredAt;
    }
  }
  counted.sort(compareCounted);
  const lastT = counted.length > 0 ? itemAt(counted, counted.length - 1).t : null;

  const revision = revisionAt(order.revisions, now);
  const suspect = context.isDevice && clockLooksWrong(context, doses, now);
  const stale = context.isDevice && historyIsStale(context, now);

  const ruleReasons: Reason[] = [];
  let ended = false;
  if (order.status === 'active') {
    ended = order.endsAt !== null && now >= order.endsAt;
    if (now < order.startsAt) {
      ruleReasons.push({ code: 'ORDER_NOT_STARTED', until: order.startsAt });
    }
    if (ended) {
      ruleReasons.push({ code: 'ORDER_ENDED', until: null });
    } else {
      if (revision === null) {
        ruleReasons.push({ code: 'NO_REVISION_IN_FORCE', until: itemAt(order.revisions, 0).effectiveFrom });
      }
      if (order.notBeforeAt !== null && now < order.notBeforeAt) {
        ruleReasons.push({ code: 'NOT_BEFORE', until: order.notBeforeAt });
      }
      if (revision !== null) {
        if (revision.minIntervalMs !== null && lastT !== null) {
          const until = add(lastT, revision.minIntervalMs);
          if (until > now) {
            ruleReasons.push({ code: 'MIN_INTERVAL', until: until });
          }
        }
        if (revision.maxCount !== null && revision.windowMs !== null) {
          const until = windowAllows(counted, now, revision.maxCount, revision.windowMs);
          if (until > now) {
            ruleReasons.push({ code: 'MAX_PER_WINDOW', until: until });
          }
        }
      }
    }
  }

  const statusReasons: Reason[] = [];
  if (suspect) {
    statusReasons.push({ code: 'CLOCK_SUSPECT', until: null });
  }
  if (stale) {
    statusReasons.push({ code: 'HISTORY_STALE', until: null });
  }

  let decision = 'allowed';
  let reasons: Reason[] = [];
  let nextAllowed: number | null = null;
  if (order.status !== 'active') {
    decision = 'denied';
    reasons = [{ code: 'ORDER_INACTIVE', until: null }];
  } else if (ruleReasons.length > 0) {
    decision = suspect ? 'unverified' : 'denied';
    reasons = ruleReasons.concat(statusReasons);
    nextAllowed = ended ? null : nextAllowedAt(order, counted, lastT, now);
  } else if (statusReasons.length > 0) {
    decision = 'unverified';
    reasons = statusReasons;
  }

  let dosesInWindow: number | null = null;
  if (revision !== null && revision.maxCount !== null && revision.windowMs !== null) {
    dosesInWindow = counted.length - firstInWindow(counted, now, revision.windowMs);
  }

  const reasonsOut: { code: string; until: number | null }[] = [];
  for (let i = 0; i < reasons.length; i++) {
    const reason = itemAt(reasons, i);
    reasonsOut.push({ code: reason.code, until: reason.until });
  }

  return {
    decision: decision,
    reasons: reasonsOut,
    next_allowed_at: nextAllowed,
    last_given_at: lastGiven,
    doses_in_window: dosesInWindow,
    history_confirmed_at: context.isDevice ? context.historyConfirmedAt : now,
    revision_id: revision === null ? null : revision.id,
  };
}
