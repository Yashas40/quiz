/**
 * Client-side Sandbox payload validator (Node/Browser)
 * validateSandboxPayload(payload) -> { ok: boolean, error: string | null }
 *
 * Mirrors server-side validation rules in utils/sandbox_validator.py
 */

const ALLOWED_TOPICS = new Set(["ada", "python", "web_development"]);
const ALLOWED_MODES = new Set(["single", "multiplayer"]);
const ALLOWED_FORMATS = new Set(["mcq", "coding", "mixed"]);
const ALLOWED_DIFFICULTIES = new Set(["easy", "medium", "hard", "mixed"]);
const ALLOWED_EDIT_ACTIONS = new Set([
  "add", "remove", "replace", "modify", "shuffle",
  "adjust_scoring", "adjust_difficulty", "adjust_topic",
  "regenerate_tests", "rewrite_explanations", "sanitize"
]);

function isNonEmptyString(x) {
  return typeof x === 'string' && x.trim().length > 0;
}

function validateGenerate(payload) {
  const required = ["mode", "session_id", "num_questions"];
  for (const k of required) {
    if (!(k in payload)) return { ok: false, error: `GENERATE MODE ERROR: Missing required field '${k}'.` };
  }
  if (!ALLOWED_MODES.has(payload.mode)) return { ok: false, error: "Field 'mode' must be 'single' or 'multiplayer'." };
  if (!isNonEmptyString(payload.session_id)) return { ok: false, error: "'session_id' must be a non-empty string." };
  if (!Number.isInteger(payload.num_questions) || payload.num_questions < 1) return { ok: false, error: "'num_questions' must be an integer >=1." };

  const topics = payload.topics || [];
  if (!Array.isArray(topics)) return { ok: false, error: "'topics' must be an array." };
  for (const t of topics) {
    if (typeof t !== 'string') return { ok: false, error: "Each topic must be a string." };
    if (t && !ALLOWED_TOPICS.has(t.toLowerCase())) return { ok: false, error: `Invalid topic: ${t}.` };
  }

  const difficulty = payload.difficulty || 'mixed';
  if (!ALLOWED_DIFFICULTIES.has(difficulty)) return { ok: false, error: "Invalid difficulty." };

  const fmt = payload.format || 'mcq';
  if (!ALLOWED_FORMATS.has(fmt)) return { ok: false, error: "Invalid format." };

  const mix = payload.mix || { mcq_percent: 80, coding_percent: 20 };
  if (typeof mix !== 'object') return { ok: false, error: "'mix' must be an object." };
  const mcq_p = mix.mcq_percent; const coding_p = mix.coding_percent;
  if (typeof mcq_p !== 'number' || typeof coding_p !== 'number') return { ok: false, error: "Mix percentages must be numeric." };
  if (Math.round(mcq_p + coding_p) !== 100) return { ok: false, error: "Mix percentages must add up to 100." };

  if ('time_per_question_seconds' in payload) {
    if (!Number.isInteger(payload.time_per_question_seconds) || payload.time_per_question_seconds <= 0) return { ok: false, error: "'time_per_question_seconds' must be a positive integer." };
  }

  if (payload.mode === 'multiplayer') {
    if (!Array.isArray(payload.players) || payload.players.length < 2) return { ok: false, error: "Multiplayer requires at least two players." };
  }

  return { ok: true, error: null };
}

function validateEdit(payload) {
  if (!('source_package' in payload) || !('edit_request' in payload)) return { ok: false, error: "EDIT MODE ERROR: Both 'source_package' and 'edit_request' must be provided." };
  if (typeof payload.source_package !== 'object' || payload.source_package === null) return { ok: false, error: "'source_package' must be an object." };
  if (typeof payload.edit_request !== 'object' || payload.edit_request === null) return { ok: false, error: "'edit_request' must be an object." };

  const action = payload.edit_request.action;
  if (!isNonEmptyString(action) || !ALLOWED_EDIT_ACTIONS.has(action)) return { ok: false, error: `Invalid edit action: ${action}.` };

  const targets = payload.edit_request.targets;
  if (targets !== undefined && !(targets === 'all' || Array.isArray(targets))) return { ok: false, error: "'targets' must be a list or 'all'." };

  // Shallow validation of source_package.questions if present (structure only)
  if (Array.isArray(payload.source_package.questions)) {
    for (const q of payload.source_package.questions) {
      if (!q || typeof q !== 'object') return { ok: false, error: 'Each question must be an object.' };
      if (!isNonEmptyString(q.q_id)) return { ok: false, error: 'Each question must have a non-empty q_id.' };
      if (!['mcq','coding'].includes(q.type)) return { ok: false, error: 'Question type must be mcq or coding.' };
      if (!isNonEmptyString(q.topic) || !ALLOWED_TOPICS.has(q.topic.toLowerCase())) return { ok: false, error: `Invalid question topic: ${q.topic}.` };
      if (!Number.isInteger(q.time_limit_seconds) || q.time_limit_seconds <= 0) return { ok: false, error: 'time_limit_seconds must be positive integer.' };
    }
  }

  return { ok: true, error: null };
}

export function validateSandboxPayload(payload) {
  if (typeof payload !== 'object' || payload === null) return { ok: false, error: 'Payload must be an object.' };
  if ('source_package' in payload || 'edit_request' in payload) return validateEdit(payload);
  if ('mode' in payload || 'session_id' in payload || 'num_questions' in payload) return validateGenerate(payload);
  return { ok: false, error: 'Missing payload: provide GENERATE or EDIT fields.' };
}

// CommonJS support
if (typeof module !== 'undefined') module.exports = { validateSandboxPayload };
