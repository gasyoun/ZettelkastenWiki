"""The data-driven quiz engine."""

import json
import re

from example_site import CONFIG, DEMO_QUIZ

from zettelkastenwiki import QuizOption, QuizQuestion, QuizResult, QuizSpec, render_quiz

_PAYLOAD_RE = re.compile(r"var SPEC = (\{.*?\});\n", re.DOTALL)


def test_router_quiz_renders_spec_as_json():
    html_text = render_quiz(DEMO_QUIZ, CONFIG)
    match = _PAYLOAD_RE.search(html_text)
    assert match, "embedded spec payload missing"
    payload = json.loads(match.group(1).replace("\\u003c", "<").replace("\\u003e", ">"))
    assert payload["mode"] == "router"
    assert len(payload["questions"]) == 2
    assert set(payload["results"]) == {"garden", "faq", "docs"}


def test_restart_handler_is_window_global():
    """Inline onclick handlers only see globals — the ORS restart-bug guard."""
    html_text = render_quiz(DEMO_QUIZ, CONFIG)
    assert 'onclick="return window.zkqRestart_setup(event)"' in html_text
    assert "window.zkqRestart_setup = function" in html_text


def test_scored_quiz_payload():
    spec = QuizSpec(
        quiz_id="facts",
        heading="True or false?",
        lead="Two statements.",
        mode="scored",
        questions=(
            QuizQuestion(
                key="q1",
                prompt="The sky is blue.",
                options=(
                    QuizOption(label="True", correct=True, explain="It is."),
                    QuizOption(label="False"),
                ),
            ),
        ),
        results={
            "high": QuizResult(title="Well done"),
            "low": QuizResult(title="Try again"),
        },
        score_results=((1, "high"), (0, "low")),
        score_template="You scored {score} of {total}",
    )
    html_text = render_quiz(spec, CONFIG)
    payload = json.loads(_PAYLOAD_RE.search(html_text).group(1))
    assert payload["mode"] == "scored"
    assert payload["scoreResults"] == [[1, "high"], [0, "low"]]
    assert payload["questions"][0]["options"][0]["correct"] is True


def test_quiz_content_is_escaped():
    spec = QuizSpec(
        quiz_id="esc",
        heading="<script>alert(1)</script>",
        lead="safe & sound",
        questions=(
            QuizQuestion(key="q", prompt="?", options=(QuizOption(label="a", result="r"),)),
        ),
        results={"r": QuizResult(title="</script><b>x</b>")},
    )
    html_text = render_quiz(spec, CONFIG)
    assert "<script>alert(1)</script>" not in html_text
    assert "&lt;script&gt;" in html_text
    # The embedded JSON escapes angle brackets so it can't break out of <script>.
    assert "\\u003c/script\\u003e" in html_text
