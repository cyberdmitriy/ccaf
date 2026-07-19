export const meta = {
  name: 'ccaf-fact-currency-audit',
  description: 'Cross-check falsifiable technical claims in the CCAF bank + lessons against current official docs and Exam Guide v1.0 (report-only, flag stale details)',
  phases: [
    { title: 'Fact-check', detail: 'one agent per domain: extract concrete technical claims, verify each against official docs' },
  ],
}

const ROOT = args.root
const GUIDE = args.guide

const FACT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['domain', 'claims', 'stale_count', 'unverifiable_count', 'summary'],
  properties: {
    domain: { type: 'integer' },
    claims: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['claim', 'where', 'category', 'verdict', 'evidence'],
        properties: {
          claim: { type: 'string', description: 'the specific falsifiable fact as stated in the content' },
          where: { type: 'string', description: 'bank question id(s) or lesson/trap file + section' },
          category: { type: 'string', enum: ['flag', 'path', 'number', 'api', 'name', 'other'] },
          verdict: { type: 'string', enum: ['current', 'stale', 'unverifiable'] },
          evidence: { type: 'string', description: 'official doc URL + what it says (or why unverifiable)' },
          fix_hint: { type: 'string', description: 'if stale: the correct current value; else ""' },
        },
      },
    },
    stale_count: { type: 'integer' },
    unverifiable_count: { type: 'integer' },
    summary: { type: 'string' },
  },
}

const domainTitles = {
  1: 'Agentic Architecture & Orchestration',
  2: 'Tool Design & MCP Integration',
  3: 'Claude Code Configuration & Workflows',
  4: 'Prompt Engineering & Structured Output',
  5: 'Context Management & Reliability',
}
// per-domain the doc areas most worth checking (concrete, drift-prone specifics)
const domainDocHints = {
  1: 'Agent SDK / Claude Code: hook names (PreToolUse/PostToolUse), the Task tool + allowedTools, subagent/AgentDefinition config, session flags (--resume, fork_session), stop_reason values (tool_use/end_turn).',
  2: 'MCP + tools: config file paths & scoping (.mcp.json project vs ~/.claude.json user — CHECK these paths are still current, Claude Code has reorganized settings), tool_choice values (auto/any/{type:tool,name}), MCP resources vs tools, built-in tool names (Read/Write/Edit/Bash/Grep/Glob), structured-error fields (errorCategory/isRetryable).',
  3: 'Claude Code CLI & config: flag names (-p/--print, --output-format json, --json-schema, --system-prompt, --bare, --strict-mcp-config), CLAUDE.md hierarchy paths (~/.claude/CLAUDE.md, .claude/CLAUDE.md), .claude/rules glob frontmatter, .claude/commands vs .claude/skills, SKILL.md frontmatter keys (context:fork, allowed-tools, argument-hint), @import, plan mode.',
  4: 'API: Message Batches API specifics (50% cost, 24h window, no latency SLA, custom_id, no multi-turn tool calling) — VERIFY the numbers, tool_use JSON schema + tool_choice, enum/nullable field patterns.',
  5: 'Mostly conceptual (summarization, escalation, provenance, sampling) — few falsifiable specifics; check any concrete API/flag/field names (e.g. /compact, scratchpad/state-manifest terminology) but expect little drift.',
}

phase('Fact-check')
const results = await parallel([1, 2, 3, 4, 5].map(d => () =>
  agent(
    `You are a **fact-currency auditor** for the CCAF study plugin, **Domain ${d} — ${domainTitles[d]}**. Your job: find any place the bundled content states a **falsifiable technical detail** that is now **stale/wrong** vs current official Anthropic docs. Report-only — edit nothing.

## What to read (this repo: ${ROOT})
- Bank: \`${ROOT}/data/questions.json\`, questions where \`domain == ${d}\`.
- Lessons/traps: \`${ROOT}/data/tutor-prompts.md\` and \`${ROOT}/data/exam-traps.md\` — the \`## Domain ${d}\` section of each.
- Authoritative exam terminology (a POINT-IN-TIME snapshot the exam tests against): \`${ROOT}/maintenance/sources.md\` ("Official exam facts"), and if useful the Exam Guide PDF \`${GUIDE}\` (39pp; use Read \`pages\` on the Section 6 range for D${d}, don't read it all).

## What to extract & verify
Pull only **falsifiable specifics** — flag names, CLI options, config-file paths, numeric limits, API parameters, field names, enum values. IGNORE pure concepts/pedagogy (those don't drift). For D${d}, pay special attention to: ${domainDocHints[d]}

For each specific claim, verify it against **current official docs** using WebFetch / WebSearch:
- Claude Code docs: https://code.claude.com/docs/en/ (cli reference, hooks, slash-commands, skills, settings, mcp, plan mode) + changelog https://code.claude.com/docs/en/changelog
- Platform/API docs: https://platform.claude.com/docs/en/ (tool use, message batches)
Use WebSearch for a specific fact if you can't find the right page. If WebFetch/WebSearch is unavailable in your environment, mark claims \`unverifiable\` with evidence "no web access" rather than guessing.

## Judgement
- **current** — official docs confirm the detail as stated.
- **stale** — docs contradict it (renamed flag, changed number, moved path, removed feature). Put the correct current value in \`fix_hint\`. THESE ARE THE VALUABLE FINDS.
- **unverifiable** — you could not confirm from official docs.
Crucial nuance: the exam is closed-book and tests against **Exam Guide v1.0 (Effective July 2026)**. A detail that MATCHES the Guide but was later changed in a newer Claude Code build is **NOT** a problem for the exam — note it, but mark it \`current\` (with a note) unless it also contradicts the Guide. Only mark \`stale\` when the content contradicts BOTH current docs AND is not what the Guide says, i.e. a genuine error in our content.

Be selective — report the specifics that matter, not every word. Return the structured object with accurate stale_count / unverifiable_count.`,
    { label: `factcheck:D${d}`, phase: 'Fact-check', schema: FACT_SCHEMA }
  )
))

return { results: results.filter(Boolean) }
