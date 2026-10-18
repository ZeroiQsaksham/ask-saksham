"""Evaluate the agent.

Retrieval only (no API key needed): is the right document in the top-k results?
    python -m eval.run_eval

Full answers too (needs GROQ_API_KEY): also checks expected keywords in the answer.
    python -m eval.run_eval --answers

Add your own questions to eval/questions.json as you fill in the knowledge base.
"""
import argparse
import asyncio
import json
from pathlib import Path

from app.retriever import search

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))


async def get_answer(question: str) -> str:
    from app.agent import stream_answer

    return "".join([t async for t in stream_answer(question, [])])


def main(check_answers: bool) -> None:
    hits, answer_passes, answer_total = 0, 0, 0
    for item in QUESTIONS:
        results = search(item["question"])
        sources = [r["source"] for r in results]
        hit = item["expected_source"] in sources
        hits += hit
        line = f"[{'HIT ' if hit else 'MISS'}] {item['question']}  ->  {sources}"

        keywords = item.get("expected_keywords") or []
        if check_answers and keywords:
            answer = asyncio.run(get_answer(item["question"]))
            ok = all(k.lower() in answer.lower() for k in keywords)
            answer_passes += ok
            answer_total += 1
            line += f"  | answer {'PASS' if ok else 'FAIL'}"
        print(line)

    n = len(QUESTIONS)
    print(f"\nRetrieval hit rate @k: {hits}/{n} = {hits / n:.0%}")
    if answer_total:
        print(f"Answer keyword accuracy: {answer_passes}/{answer_total} = {answer_passes / answer_total:.0%}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--answers", action="store_true", help="also call the LLM and check answers")
    main(parser.parse_args().answers)
