export const meta = {
  name: 'ccaf-bank-coverage-audit',
  description: 'Audit the CCAF question bank coverage against the official Exam Guide v1.0 task statements + sample questions (report-only, no edits)',
  phases: [
    { title: 'Coverage', detail: 'one agent per domain maps bank questions to official task statements' },
    { title: 'Samples', detail: 'check whether the guide sample questions are represented in the bank' },
  ],
}

const ROOT = args.root
const GUIDE = args.guide

const COVERAGE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['domain', 'task_statements', 'orphan_q_ids', 'summary'],
  properties: {
    domain: { type: 'integer' },
    task_statements: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['id', 'title', 'covered_q_ids', 'count', 'verdict'],
        properties: {
          id: { type: 'string', description: 'e.g. "4.3"' },
          title: { type: 'string' },
          covered_q_ids: { type: 'array', items: { type: 'integer' } },
          count: { type: 'integer' },
          verdict: { type: 'string', enum: ['good', 'thin', 'none'] },
        },
      },
    },
    orphan_q_ids: { type: 'array', items: { type: 'integer' }, description: 'bank questions in this domain that map to no official task statement' },
    summary: { type: 'string', description: 'one-paragraph verdict: which task statements are under-covered and any orphans' },
  },
}

const SAMPLES_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['samples', 'missing_count', 'summary'],
  properties: {
    samples: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['guide_q', 'domain', 'in_bank', 'match_q_id', 'note'],
        properties: {
          guide_q: { type: 'string', description: 'e.g. "Q1" + short gist' },
          domain: { type: 'integer' },
          in_bank: { type: 'boolean' },
          match_q_id: { type: ['integer', 'null'] },
          note: { type: 'string' },
        },
      },
    },
    missing_count: { type: 'integer' },
    summary: { type: 'string' },
  },
}

phase('Coverage')
const domainTitles = {
  1: 'Agentic Architecture & Orchestration',
  2: 'Tool Design & MCP Integration',
  3: 'Claude Code Configuration & Workflows',
  4: 'Prompt Engineering & Structured Output',
  5: 'Context Management & Reliability',
}

const coverage = await parallel([1, 2, 3, 4, 5].map(d => () =>
  agent(
    `You are auditing CCAF question-bank coverage for **Domain ${d} — ${domainTitles[d]}** against the official Exam Guide v1.0.

Authoritative task-statement list: read \`${ROOT}/maintenance/sources.md\` — the "Official exam facts" block lists every domain's task statements (for D${d}, use exactly those, e.g. ${d}.1, ${d}.2, …). For fuller "Knowledge/Skills" detail per statement you MAY consult the guide PDF at \`${GUIDE}\` (it is 39 pages — if you read it, use the Read \`pages\` param on the Section 6 range, don't read the whole file), but the sources.md list is authoritative for WHICH statements exist.

Then read the bank \`${ROOT}/data/questions.json\` and consider ONLY questions where \`domain == ${d}\`.

For EACH official task statement ${d}.x:
- list the bank question \`id\`s that substantively test that statement's concept (a question can map to one statement; pick the best-fit statement),
- count them,
- verdict: "good" (>=3 questions), "thin" (1-2), "none" (0).
Also list \`orphan_q_ids\`: any domain-${d} bank question that maps to NONE of the official statements (genuinely off-blueprint), if any.

Be accurate, not generous — only count a question if it really tests that statement. Return the structured object. This is an audit; do not edit any file.`,
    { label: `coverage:D${d}`, phase: 'Coverage', schema: COVERAGE_SCHEMA }
  )
))

phase('Samples')
const samples = await agent(
  `You are checking whether the **Sample Questions** in the official CCAF Exam Guide are already represented in the plugin's question bank.

1. Read the guide's "Section 9: Sample Questions" from the PDF \`${GUIDE}\` — use the Read \`pages\` param on pages 30-39 (that's where the sample questions live; Q1 onward). Extract each sample question: its number, scenario, and a short gist of the stem + correct answer.
2. Read the bank \`${ROOT}/data/questions.json\`.
3. For each guide sample question, decide if the bank already contains a substantively equivalent question (same scenario + same underlying concept/correct principle — wording may differ). If yes, give the matching bank \`id\`; if no, mark \`in_bank: false\` with a short note on what's missing.

Return the structured object with a \`missing_count\` (how many sample questions are NOT represented) and a one-paragraph summary. Audit only — edit nothing.`,
  { label: 'samples-check', phase: 'Samples', schema: SAMPLES_SCHEMA }
)

return { coverage: coverage.filter(Boolean), samples }
