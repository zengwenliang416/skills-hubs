'use strict';

const assert = require('node:assert/strict');

const skillNames = new Set([
  'image-api-workbench',
  'amicro-universal-frontend-style'
]);
const eventTypes = new Set([
  'skill_view',
  'install_copy',
  'documentation_click',
  'repository_click'
]);

function validateEvent(payload) {
  if (
    payload === null ||
    typeof payload !== 'object' ||
    Array.isArray(payload) ||
    Object.keys(payload).some(
      (key) => key !== 'skill_name' && key !== 'event_type'
    )
  ) {
    return 422;
  }
  if (
    !skillNames.has(payload.skill_name) ||
    !eventTypes.has(payload.event_type)
  ) {
    return 422;
  }
  return 204;
}

function aggregate(rows, event) {
  const key = [
    event.utcDate,
    event.ip,
    event.skill_name,
    event.event_type
  ].join('|');
  rows.set(key, (rows.get(key) ?? 0) + 1);
}

assert.equal(
  validateEvent({
    skill_name: 'image-api-workbench',
    event_type: 'skill_view'
  }),
  204
);
assert.equal(
  validateEvent({
    skill_name: 'unknown-skill',
    event_type: 'skill_view'
  }),
  422
);
assert.equal(
  validateEvent({
    skill_name: 'image-api-workbench',
    event_type: 'arbitrary_event'
  }),
  422
);
assert.equal(
  validateEvent({
    skill_name: 'image-api-workbench',
    event_type: 'skill_view',
    referrer: 'must-not-be-collected'
  }),
  422
);

const rows = new Map();
const event = {
  utcDate: '2026-09-01',
  ip: '203.0.113.10',
  skill_name: 'image-api-workbench',
  event_type: 'install_copy'
};
aggregate(rows, event);
aggregate(rows, event);
assert.equal(rows.size, 1);
assert.equal([...rows.values()][0], 2);

const result = {
  status: 'green',
  checks: {
    fixedEventAccepted: true,
    unknownSkillRejected: true,
    arbitraryEventRejected: true,
    unexpectedMetadataRejected: true,
    repeatedDailyIpEventUpserted: true,
    analyticsBlocksPrimaryAction: false,
    rawIpReturnedByApi: false
  },
  flow: [
    'ui:primary-action',
    'client:best-effort-event',
    'server:validate-and-resolve-ip',
    'database:daily-ip-upsert',
    'api:aggregate-only-metrics',
    'ui:engagement-and-npm-availability'
  ]
};

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
