import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import ts from "typescript";

// Use the project's compiler so the suite also works on Node versions without native TS support.
const source = await readFile(
  new URL("../lib/chat-sessions.ts", import.meta.url),
  "utf8",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2020,
  },
});
const {
  conversationHref,
  loadSavedSessions,
  mergeSavedSessions,
  saveSessions,
} = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);
const message = (content, extra = {}) => ({
  id: "message",
  role: "assistant",
  content,
  ...extra,
});
const local = (id, messages = [], extra = {}) => ({
  id,
  title: `Local ${id}`,
  messages,
  createdAt: 1,
  ...extra,
});
const remote = (id, messages = []) => ({
  id,
  title: `Remote ${id}`,
  created_at: "2026-01-01T00:00:00Z",
  messages,
});

function storage(value) {
  let raw = value;
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: () => raw,
      setItem: (_key, value) => {
        raw = value;
      },
    },
  });
}

test("conversation URLs distinguish chats and encode IDs as a single route segment", () => {
  assert.equal(conversationHref("first"), "/c/first");
  assert.equal(conversationHref("second"), "/c/second");
  assert.equal(conversationHref("chat/with ?#"), "/c/chat%2Fwith%20%3F%23");
});

test("saved conversations retain their IDs and answers after a refresh", () => {
  storage(null);
  const sessions = [
    local("first", [message("First answer")]),
    local("second", [message("Second answer")]),
  ];
  saveSessions(sessions);
  assert.deepEqual(loadSavedSessions(), sessions);
});

test("corrupt storage and legacy demo records do not break opening a conversation", () => {
  storage("not JSON");
  assert.deepEqual(loadSavedSessions(), []);
  storage(
    JSON.stringify([
      null,
      { id: "broken" },
      local("demo-rag-1"),
      local("real", [null, message("Valid")]),
    ]),
  );
  assert.deepEqual(loadSavedSessions(), [local("real", [message("Valid")])]);
});

test("restoring an interrupted conversation removes stale loading spinners", () => {
  storage(JSON.stringify([local("first", [message("", { isLoading: true })])]));
  assert.equal(loadSavedSessions()[0].messages[0].isLoading, false);
});

test("direct links can resolve conversations fetched from saved backend history", () => {
  const merged = mergeSavedSessions(
    [],
    [
      remote("first", [message("First answer")]),
      remote("second", [message("Second answer")]),
    ],
  );
  assert.equal(
    merged.find((chat) => chat.id === "second").messages[0].content,
    "Second answer",
  );
  assert.equal(
    merged.find((chat) => chat.id === "missing"),
    undefined,
  );
});

test("late history sync preserves locally saved answers, source details and renames", () => {
  const current = local(
    "first",
    [message("New answer", { citations: ["research.pdf"] })],
    { title: "Renamed" },
  );
  assert.deepEqual(
    mergeSavedSessions([current], [remote("first", [message("Old answer")])]),
    [current],
  );
});

test("late history sync cannot overwrite a response generating in another route", () => {
  const generating = local("first", [message("", { isLoading: true })]);
  assert.deepEqual(
    mergeSavedSessions(
      [generating],
      [remote("first", [message("Older answer")])],
    ),
    [generating],
  );
});

test("a server-completed answer can recover an interrupted response after refresh", () => {
  const merged = mergeSavedSessions(
    [local("first", [message("")])],
    [remote("first", [message("Completed answer")])],
  );
  assert.equal(merged[0].messages[0].content, "Completed answer");
});

test("history sync cannot resurrect a conversation deleted while the request was pending", () => {
  assert.deepEqual(
    mergeSavedSessions([], [remote("deleted")], new Set(["deleted"])),
    [],
  );
});

test("disabled browser storage falls back without crashing the workspace", () => {
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    get() {
      throw new Error("Storage disabled");
    },
  });
  assert.deepEqual(loadSavedSessions(), []);
  assert.doesNotThrow(() => saveSessions([local("first")]));
  delete globalThis.localStorage;
});
