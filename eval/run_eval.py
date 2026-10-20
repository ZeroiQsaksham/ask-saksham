"""Evaluate the agent.

Retrieval only (no API key needed):
    python -m eval.run_eval                 # about-me mode: right file in top-k?
    python -m eval.run_eval --mode astro    # astrologer mode: right chapter in top-k?

Full answers too (needs GROQ_API_KEY): also checks expected keywords in the answer.
    python -m eval.run_eval --answers
    python -m eval.run_eval --mode astro --answers --sleep 20   # pause between questions (Groq free tier)
"""
import argparse
import asyncio
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).parent


def normalise(text: str) -> str:
    # LLMs often use non-breaking hyphens/spaces and curly quotes; normalise before matching.
    text = re.sub(r"[‐-―−]", "-", text).replace(" ", " ")
    return text.replace("’", "'").replace("′", "'").lower()


async def collect(stream) -> str:
    return "".join([t async for t in stream])


def run(mode: str, check_answers: bool, pause: float) -> None:
    if mode == "astro":
        from app.astro import stream_astro_answer as answer_fn
        from app.retriever import search_book

        questions = json.loads((HERE / "astro_questions.json").read_text(encoding="utf-8"))
    else:
        from app.agent import stream_answer as answer_fn
        from app.retriever import search

        questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))

    hits = graded = answer_passes = answer_total = 0
    for item in questions:
        q = item["question"]
        if mode == "astro":
            found = [p["chapter"] for p in search_book(q)]
            nums = {int(re.search(r"Chapter (\d+)", c).group(1)) for c in found if c.startswith("Chapter")}
            expected = set(item["expected_chapters"])
            hit = bool(nums & expected) if expected else None
            shown = sorted(nums)
        else:
            found = [r["source"] for r in search(q)]
            hit = item["expected_source"] in found
            shown = found
        if hit is not None:
            graded += 1
            hits += hit
        line = f"[{'HIT ' if hit else ('n/a ' if hit is None else 'MISS')}] {q}  ->  {shown}"

        keywords = item.get("expected_keywords") or []
        if check_answers and keywords:
            answer = normalise(asyncio.run(collect(answer_fn(q, []))))
            ok = all(k.lower() in answer for k in keywords)
            answer_passes += ok
            answer_total += 1
            line += f"  | answer {'PASS' if ok else 'FAIL'}"
            time.sleep(pause)
        print(line, flush=True)

    print(f"\nRetrieval hit rate @k: {hits}/{graded} = {hits / max(graded, 1):.0%}")
    if answer_total:
        print(f"Answer keyword accuracy: {answer_passes}/{answer_total} = {answer_passes / answer_total:.0%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["about", "astro"], default="about")
    parser.add_argument("--answers", action="store_true", help="also call the LLM and check answers")
    parser.add_argument("--sleep", type=float, default=0, help="seconds to wait between LLM calls")
    args = parser.parse_args()
    run(args.mode, args.answers, args.sleep)
