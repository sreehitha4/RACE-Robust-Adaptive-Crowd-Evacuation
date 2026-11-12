// Run with `npm test` (Node 22.18+ strips the types natively, no test framework needed).
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseMessage } from "../src/contract.ts";
import { LAYOUT, MockSim, isBlocked } from "../src/sources/mock.ts";
import { parseReplay } from "../src/sources/replay.ts";
import { RunStore } from "../src/store.ts";

test("contract accepts the mock layout and frames", () => {
  assert.equal(parseMessage(LAYOUT).type, "environment");
  assert.equal(parseMessage(new MockSim(20, 1).frame()).type, "frame");
});

test("contract errors name the offending field", () => {
  const frame = { type: "frame", simulation_time: 1, total_agents: 1, evacuated: 0, agents: [{ id: 1, x: 2, y: null, vx: 0, vy: 0, state: "walking" }] };
  assert.throws(() => parseMessage(frame), /message\.agents\[0\]\.y should be a finite number, got null/);
  assert.throws(() => parseMessage({ type: "tick" }), /message\.type should be "environment" or "frame"/);
  assert.throws(() => parseMessage({ ...LAYOUT, walls: [[[0, 0]]] }), /message\.walls\[0\] should be at least 2/);
});

test("mock sim evacuates everyone without crossing walls", () => {
  const sim = new MockSim(140, 42);
  assert.equal(sim.total, 140);
  while (!sim.done && sim.time < 300) {
    sim.step(0.05);
    for (const a of sim.agents) assert.ok(!isBlocked(a.x, a.y), `agent ${a.id} inside a wall at ${a.x},${a.y}`);
    assert.equal(sim.agents.length + sim.evacuated, sim.total);
  }
  assert.ok(sim.done, `${sim.agents.length} agents still inside after ${sim.time.toFixed(0)} s`);
});

test("replay files may omit the type fields", () => {
  const { type: _, ...environment } = LAYOUT;
  const { type: __, ...frame } = new MockSim(5, 3).frame();
  const run = parseReplay(JSON.stringify({ environment, frames: [frame] }));
  assert.equal(run.frames[0].type, "frame");
  assert.throws(() => parseReplay(JSON.stringify({ environment, frames: [{ ...frame, evacuated: "x" }] })), /frames\[0\]\.evacuated/);
});

test("store interpolates by id, keeps trails and computes T50", () => {
  const store = new RunStore();
  store.setEnvironment(LAYOUT);
  const frame = (t: number, x: number, evacuated: number) => ({
    type: "frame" as const, simulation_time: t, total_agents: 2, evacuated,
    agents: [{ id: 7, x, y: 1, vx: 1, vy: 0, state: "walking" }],
  });
  store.push(frame(0, 0, 0), 1000);
  store.push(frame(1, 1, 1), 1100);
  assert.equal(store.agentsAt(1150)[0].x, 0.5);
  assert.equal(store.agentsAt(5000)[0].x, 1);
  assert.equal(store.trails.get(7)!.length, 2);
  assert.equal(store.timeTo(0.5), 1);
  assert.equal(store.timeTo(0.9), undefined);
  store.push(frame(0, 3, 0), 1200); // time went backwards: a reset, so history is cleared
  assert.equal(store.trails.get(7)!.length, 1);
  assert.equal(store.agentsAt(1200)[0].x, 3);
});
