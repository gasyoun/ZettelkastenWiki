"""Data-driven quiz engine.

One renderer + a declarative spec replaces the twelve hand-copied
``_render_*_quiz`` templates the ORS-FAQ generator carried (~1,400 lines of
near-identical JS). Two modes cover both ORS patterns:

- ``router``: each answer accumulates; a terminal option (or the last
  question) maps to a result via ``result`` keys on options. Multi-question
  logic beyond simple key concatenation can use ``decide_js`` — a JS function
  body receiving ``answers`` (dict of question key → option value) and
  returning a result key.
- ``scored``: options carry ``correct`` + ``explain``; the score maps to a
  result through ``score_results`` thresholds.

All state and the restart handler live on ``window`` (namespaced per quiz id)
— the ORS restart-bug lesson: an inline ``onclick`` can only see globals, so
IIFE-local handlers silently no-op.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass, field

from .catalog import escape_attr
from .config import SiteConfig


@dataclass(frozen=True)
class QuizOption:
    label: str
    value: str = ""
    #: router mode: jump straight to this result key (terminal option).
    result: str = ""
    #: scored mode: whether this option is the correct answer.
    correct: bool = False
    #: scored mode: shown after answering.
    explain: str = ""


@dataclass(frozen=True)
class QuizQuestion:
    key: str
    prompt: str
    options: tuple


@dataclass(frozen=True)
class QuizCTA:
    label: str
    url: str
    secondary: bool = False


@dataclass(frozen=True)
class QuizResult:
    title: str
    why: str = ""
    extra_html: str = ""
    ctas: tuple = ()


@dataclass(frozen=True)
class QuizSpec:
    quiz_id: str
    heading: str
    lead: str
    questions: tuple
    results: dict
    mode: str = "router"  # "router" | "scored"
    #: router mode fallback: answers joined "key=value" → result key; when no
    #: option carries a terminal ``result``, the LAST answered option's value
    #: is the result key.
    decide_js: str = ""
    #: scored mode: [(min_score, result_key), …] highest threshold first.
    score_results: tuple = ()
    #: scored mode: "You scored {score} of {total}" template ({score}/{total}).
    score_template: str = "Score: {score} / {total}"


def _spec_payload(spec: QuizSpec) -> dict:
    return {
        "mode": spec.mode,
        "questions": [
            {
                "key": q.key,
                "prompt": q.prompt,
                "options": [
                    {
                        "label": o.label,
                        "value": o.value or o.label,
                        "result": o.result,
                        "correct": o.correct,
                        "explain": o.explain,
                    }
                    for o in q.options
                ],
            }
            for q in spec.questions
        ],
        "results": {
            key: {
                "title": r.title,
                "why": r.why,
                "extra": r.extra_html,
                "ctas": [
                    {"label": c.label, "url": c.url, "secondary": c.secondary} for c in r.ctas
                ],
            }
            for key, r in spec.results.items()
        },
        "scoreResults": [list(pair) for pair in spec.score_results],
        "scoreTemplate": spec.score_template,
    }


def render_quiz(spec: QuizSpec, config: SiteConfig) -> str:
    """Render one quiz section (markup + engine JS) from its spec."""
    strings = config.strings
    qid = spec.quiz_id
    payload = json.dumps(_spec_payload(spec), ensure_ascii=False).replace("<", "\\u003c").replace(
        ">", "\\u003e"
    )
    progress_tpl = strings.quiz_progress.replace("{n}", "__N__").replace("{total}", "__T__")
    return f"""
<section class="quiz-section" id="quiz-{escape_attr(qid)}">
<h2>{html.escape(spec.heading)}</h2>
<p class="quiz-lead">{html.escape(spec.lead)}</p>
<div id="zkq-{escape_attr(qid)}">
  <div class="zkq-progress" id="zkq-{escape_attr(qid)}-progress"></div>
  <h3 class="zkq-question" id="zkq-{escape_attr(qid)}-q"></h3>
  <div class="zkq-options" id="zkq-{escape_attr(qid)}-options"></div>
  <div id="zkq-{escape_attr(qid)}-result"></div>
  <p><a href="#" id="zkq-{escape_attr(qid)}-restart" style="display:none;" onclick="return window.zkqRestart_{qid}(event)">{html.escape(strings.quiz_restart)}</a></p>
</div>
<script>
(function () {{
  var SPEC = {payload};
  var ID = "zkq-{qid}";
  var elQ = document.getElementById(ID + "-q");
  var elOpts = document.getElementById(ID + "-options");
  var elRes = document.getElementById(ID + "-result");
  var elProg = document.getElementById(ID + "-progress");
  var elRestart = document.getElementById(ID + "-restart");
  var state = {{ answers: {{}}, step: 0, score: 0 }};
  function progressText(n, total) {{
    return "{progress_tpl}".replace("__N__", n).replace("__T__", total);
  }}
  function decide(answers) {{
    {spec.decide_js or "return null;"}
  }}
  function pickResult() {{
    if (SPEC.mode === "scored") {{
      var pairs = SPEC.scoreResults.slice().sort(function (a, b) {{ return b[0] - a[0]; }});
      for (var i = 0; i < pairs.length; i++) {{
        if (state.score >= pairs[i][0]) return SPEC.results[pairs[i][1]];
      }}
      return null;
    }}
    var custom = decide(state.answers);
    if (custom && SPEC.results[custom]) return SPEC.results[custom];
    if (state.terminal && SPEC.results[state.terminal]) return SPEC.results[state.terminal];
    var last = state.lastValue;
    return SPEC.results[last] || null;
  }}
  function esc(s) {{
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }}
  function showResult() {{
    var r = pickResult();
    elProg.textContent = "";
    elQ.textContent = "{escape_attr(strings.quiz_result_intro)}";
    elOpts.style.display = "none";
    var htmlParts = [];
    if (SPEC.mode === "scored") {{
      htmlParts.push("<p class='zkq-score'>" + esc(SPEC.scoreTemplate
        .replace("{{score}}", state.score).replace("{{total}}", SPEC.questions.length)) + "</p>");
    }}
    if (r) {{
      htmlParts.push("<p class='quiz-result-title'>" + esc(r.title) + "</p>");
      if (r.why) htmlParts.push("<p class='quiz-result-why'>" + esc(r.why) + "</p>");
      if (r.extra) htmlParts.push(r.extra);
      if (r.ctas && r.ctas.length) {{
        var ctas = r.ctas.map(function (c) {{
          var cls = c.secondary ? "btn-secondary" : "btn-primary";
          return "<a class='" + cls + "' href='" + esc(c.url) + "'>" + esc(c.label) + "</a>";
        }});
        htmlParts.push("<p class='quiz-result-ctas'>" + ctas.join(" ") + "</p>");
      }}
    }}
    elRes.style.display = "";
    elRes.innerHTML = htmlParts.join("");
    elRestart.style.display = "inline";
  }}
  function advance() {{
    state.step++;
    if (state.terminal || state.step >= SPEC.questions.length) showResult();
    else render();
  }}
  function render() {{
    elRes.style.display = "none";
    elRes.innerHTML = "";
    elOpts.style.display = "";
    elProg.textContent = progressText(state.step + 1, SPEC.questions.length);
    var cur = SPEC.questions[state.step];
    elQ.textContent = cur.prompt;
    elOpts.innerHTML = "";
    cur.options.forEach(function (o) {{
      var b = document.createElement("button");
      b.className = "quiz-opt";
      b.textContent = o.label;
      b.onclick = function () {{
        state.answers[cur.key] = o.value;
        state.lastValue = o.value;
        if (o.result) state.terminal = o.result;
        if (SPEC.mode === "scored") {{
          var buttons = elOpts.querySelectorAll("button");
          buttons.forEach(function (btn) {{ btn.disabled = true; }});
          b.className = "quiz-opt " + (o.correct ? "correct" : "wrong");
          if (!o.correct) {{
            cur.options.forEach(function (other, i) {{
              if (other.correct) buttons[i].className = "quiz-opt correct";
            }});
          }}
          if (o.correct) state.score++;
          if (o.explain) {{
            var p = document.createElement("p");
            p.className = "zkq-explain";
            p.textContent = o.explain;
            elOpts.appendChild(p);
          }}
          var next = document.createElement("button");
          next.className = "quiz-opt";
          next.textContent = "→";
          next.onclick = advance;
          elOpts.appendChild(next);
        }} else {{
          advance();
        }}
      }};
      elOpts.appendChild(b);
    }});
  }}
  window.zkqRestart_{qid} = function (e) {{
    if (e) e.preventDefault();
    state = {{ answers: {{}}, step: 0, score: 0 }};
    elRestart.style.display = "none";
    render();
    return false;
  }};
  render();
}})();
</script>
</section>
"""
