// reference-sync — keep data/quick-reference.json (the Cheatsheet/Reference tab's see→answer map)
// in sync with what the bank actually tests. For each section (= a task statement "<d>.<n>"), it looks at
// every questions.json question carrying that `task` and proposes, in the EXACT quick-reference row schema:
//   (a) `q_ids` to attach to EXISTING rows the question already reflects, and
//   (b) NEW `see → answer` rows for nuances no current row covers.
//
// This is the generator half of the reference/bank link: `maintenance/reference-coverage.py` finds the gaps
// (deterministic set arithmetic); this workflow drafts the curated rows that close them. Answer prose is
// model-authored + human-reviewed on purpose — a stem cannot be turned into a good see→answer line
// deterministically, and `q_ids` are per-row judgement, never a keyword grep (see the questions.json schema
// note in CLAUDE.md). So this workflow EDITS NOTHING: it returns a reviewable patch; a maintainer applies it,
// then runs `python3 data/validate.py` + `python3 maintenance/reference-coverage.py`.
//
// GOLDEN SAMPLE: section 2.6 in quick-reference.json is hand-authored to the target shape (rows for
// ENABLE_TOOL_SEARCH=false / =auto threshold / MCP protocol order / the tool·resource·prompt triad, plus
// q_ids on the pre-existing rows). Calibrate the draft prompt against it: `args.sections=["2.6"]` should
// reproduce that section's rows and q_ids. Only widen scope once 2.6 round-trips cleanly.
//
// SCOPE (args): `sections` (array of "<d>.<n>", most specific) OR `domain` (int 1-5) OR neither (ALL 32).
// A full 32-section run is 64 agents — over the default 15-agent guideline; scope by domain for real runs.
export const meta = {
  name: 'ccaf-reference-sync',
  description: 'Sync quick-reference.json see→answer rows with the bank: propose q_ids for existing rows + new rows for uncovered nuances (proposal only, no edits)',
  phases: [
    { title: 'Scan', detail: 'enumerate in-scope sections + their bank questions by task' },
    { title: 'Draft', detail: 'per section: propose q_id attachments + new rows in the row schema' },
    { title: 'Verify', detail: 'per section: adversarially check each proposed row against the questions' },
  ],
}

const ROOT = args.root
const SCOPE = {
  sections: Array.isArray(args && args.sections) ? args.sections : null,
  domain: args && args.domain ? Number(args.domain) : null,
}

const SCAN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['sections'],
  properties: {
    sections: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['task', 'title', 'domain', 'bank_q_ids', 'current_row_count'],
        properties: {
          task: { type: 'string', description: 'e.g. "2.6"' },
          title: { type: 'string', description: 'the section title verbatim, e.g. "2.6 MCP tool search & protocol"' },
          domain: { type: 'integer' },
          bank_q_ids: { type: 'array', items: { type: 'integer' }, description: 'every questions.json id whose task == this section' },
          current_row_count: { type: 'integer' },
        },
      },
    },
  },
}

// One draft/verify proposal for a single section. Both stages share this shape.
const PROPOSAL_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['task', 'existing_updates', 'new_rows', 'uncovered_q_ids', 'summary'],
  properties: {
    task: { type: 'string' },
    existing_updates: {
      type: 'array',
      description: 'q_ids to attach to rows that ALREADY exist in this section',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['see', 'add_q_ids'],
        properties: {
          see: { type: 'string', description: 'the existing row\'s `see` text, verbatim, to locate it' },
          add_q_ids: { type: 'array', items: { type: 'integer' } },
        },
      },
    },
    new_rows: {
      type: 'array',
      description: 'brand-new rows in the exact quick-reference row schema, for nuances no current row covers',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['see', 'answer', 'q_ids'],
        properties: {
          see: { type: 'string', description: 'a real trigger/signal from the stem; plain text (rich() renders `code`/**bold**), no markdown headings' },
          answer: { type: 'string', description: 'short mechanism + the trap it beats; same voice as sibling rows' },
          q_ids: { type: 'array', items: { type: 'integer' }, description: 'the bank ids this row reflects — hand-picked, never every-question-on-the-task' },
        },
      },
    },
    uncovered_q_ids: { type: 'array', items: { type: 'integer' }, description: 'bank ids for this task still reflected by NO row after this proposal (deliberately, e.g. pure duplicates)' },
    summary: { type: 'string', description: 'one line: what was added and why' },
  },
}

phase('Scan')
const scopeText = SCOPE.sections
  ? `ONLY these sections (by task number): ${SCOPE.sections.join(', ')}.`
  : SCOPE.domain
    ? `ONLY sections in domain ${SCOPE.domain} (task numbers "${SCOPE.domain}.x").`
    : `EVERY section across all five domains.`

const scan = await agent(
  `Enumerate the CCAF reference sections in scope so they can be synced against the bank.

Read \`${ROOT}/data/quick-reference.json\` (the see→answer map; each section title starts with a task number "<d>.<n>") and \`${ROOT}/data/questions.json\` (each question carries a \`task\` "<d>.<n>").

Scope: ${scopeText}

For each in-scope section return: its \`task\` number, its \`title\` verbatim, its \`domain\`, the list of every questions.json \`id\` whose \`task\` equals that section's number (\`bank_q_ids\`), and how many rows the section currently has. Return the structured object. Read only — edit nothing.`,
  { label: 'scan', phase: 'Scan', schema: SCAN_SCHEMA }
)

let sections = (scan && scan.sections) || []
if (SCOPE.sections) sections = sections.filter(s => SCOPE.sections.includes(s.task))
else if (SCOPE.domain) sections = sections.filter(s => s.domain === SCOPE.domain)
log(`reference-sync: ${sections.length} section(s) in scope, ${sections.reduce((n, s) => n + s.bank_q_ids.length, 0)} bank questions to reconcile`)

const proposals = await pipeline(
  sections,
  // DRAFT — propose q_id attachments + new rows for one section.
  (sec) => agent(
    `You are syncing ONE section of the CCAF Cheatsheet (\`${ROOT}/data/quick-reference.json\`) with the question bank, so the see→answer map reflects every nuance the bank actually tests for this task statement.

Section: **${sec.title}** (task ${sec.task}, domain ${sec.domain}).
Bank questions for this task: ids ${JSON.stringify(sec.bank_q_ids)}.

Steps:
1. Read this section's current rows in \`${ROOT}/data/quick-reference.json\` (find the section whose title is "${sec.title}").
2. Read each bank question ${JSON.stringify(sec.bank_q_ids)} in \`${ROOT}/data/questions.json\` — its \`stem\`, \`options\`, \`correct\`, and \`explanation\`.
3. Study the GOLDEN reference section 2.6 ("2.6 MCP tool search & protocol") in the same file — it is the hand-authored target shape (curated rows + q_ids on pre-existing rows). Match its voice and density.
4. For EACH bank question decide:
   - if an EXISTING row already states the nuance it tests → add its id to that row via \`existing_updates\` (locate the row by its \`see\` text, verbatim).
   - else → author a NEW row in \`new_rows\`: \`see\` = the real trigger/signal a learner would scan for (plain text; you may use \`code\`/**bold** which the app renders; NO markdown headings), \`answer\` = the short correct mechanism AND the near-miss it beats, in the same terse voice as the sibling rows, \`q_ids\` = the id(s) this row reflects.
   - a question that is a pure duplicate of another already covered → list its id in \`uncovered_q_ids\` (deliberately unreferenced), don't invent a redundant row.

Rules: keep exam wording and API tokens (\`stop_reason\`, \`tool_choice\`, \`ENABLE_TOOL_SEARCH\`, …) in English exactly. \`q_ids\` are per-row judgement — attach an id only to the row that genuinely states what that question tests, never every question on the task to every row. Do NOT edit any file — return the structured proposal only.`,
    { label: `draft:${sec.task}`, phase: 'Draft', schema: PROPOSAL_SCHEMA }
  ),
  // VERIFY — adversarially check the draft against the actual questions.
  (draft, sec) => draft && agent(
    `Adversarially verify a proposed sync of CCAF Cheatsheet section **${sec.title}** (task ${sec.task}) against the bank. Default to CUTTING anything not clearly correct.

The draft proposal:
${JSON.stringify(draft, null, 2)}

Check against \`${ROOT}/data/questions.json\` (ids ${JSON.stringify(sec.bank_q_ids)}) and the current section in \`${ROOT}/data/quick-reference.json\`:
- Is every \`answer\` factually correct per the question's \`correct\` option and \`explanation\`? Cut or fix any that misstate the mechanism.
- Is each \`see\` a real signal a learner scans for (not a paraphrase of the answer, not a markdown heading)?
- Does any \`new_row\` duplicate an existing row or another new row? Fold duplicates into \`existing_updates\`/\`uncovered_q_ids\`.
- Is every \`q_id\` attached ONLY to the row that genuinely reflects that question? Remove over-broad attachments.
- Format: plain \`see\`, terse curated \`answer\` matching sibling voice, English exam terms/API tokens intact.

Return the SAME PROPOSAL_SCHEMA shape as the corrected, ready-to-apply proposal (keep only what survives; put the rationale for any cut in \`summary\`).`,
    { label: `verify:${sec.task}`, phase: 'Verify', schema: PROPOSAL_SCHEMA }
  )
)

const patch = proposals.filter(Boolean)
const totals = patch.reduce((a, p) => ({
  new_rows: a.new_rows + p.new_rows.length,
  updates: a.updates + p.existing_updates.length,
}), { new_rows: 0, updates: 0 })
log(`reference-sync proposal: ${totals.new_rows} new row(s), ${totals.updates} existing-row q_id update(s) across ${patch.length} section(s) — REVIEW then apply by hand, then run validate.py + reference-coverage.py`)

return { patch, scope: SCOPE }
