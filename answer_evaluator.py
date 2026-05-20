"""
Answer Evaluation System (Unit V)
Uses FOL traces plus richer metadata-based scoring for the expanded question bank.
Also integrates LLM-based coaching feedback when AI-enhanced mode is active.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fol_engine import FOLEngine


class AnswerEvaluator:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.fol = FOLEngine()

    def evaluate_answer(self, q_id: int, answer: str) -> Dict[str, Any]:
        question = self.kb.get_question_by_id(q_id)
        if not question:
            return {
                "score": 0.0,
                "strengths": [],
                "weaknesses": ["Question not found in the knowledge base."],
                "missing_concepts": [],
                "fol_trace": [],
                "suggestions": ["Please try another question."],
                "feedback": "Question not found",
                "ideal_answer": {"key_points": [], "example": ""},
            }

        answer_text = str(answer or "").strip()
        answer_lower = answer_text.lower()

        keywords = [str(keyword).lower() for keyword in question.get("keywords", [])]
        concepts = [str(concept).lower() for concept in question.get("concepts", [])]
        ideal_answer = question.get("ideal_answer", {"key_points": [], "example": ""})

        matched_keywords = [keyword for keyword in keywords if keyword in answer_lower]
        missing_keywords = [keyword for keyword in keywords if keyword not in answer_lower]

        explained_concepts: List[str] = []
        missing_concepts: List[str] = []
        concept_scores: List[float] = []
        for concept in concepts:
            score = self.fol.Explains(answer_text, concept)
            concept_scores.append(score)
            if score >= 0.6:
                explained_concepts.append(concept)
            else:
                missing_concepts.append(concept)

        keyword_score = len(matched_keywords) / max(len(keywords), 1)
        concept_score = sum(concept_scores) / max(len(concept_scores), 1) if concept_scores else 0.0
        detail_score = self.fol.IsDetailed(answer_text, self._min_words_for(question.get("difficulty", "beginner")))
        code_score = self.fol.ExemplifiesCode(answer_text) if ideal_answer.get("example") else min(1.0, 0.45 + (detail_score * 0.4))

        fol_rules = question.get("fol_rules", [])
        good_rule = next((rule for rule in fol_rules if rule["type"] == "GoodAnswer"), None)
        partial_rule = next((rule for rule in fol_rules if rule["type"] == "PartialAnswer"), None)

        good_res = self.fol.evaluate_rule(good_rule, answer_text) if good_rule else {"score": 0.0, "trace": []}
        part_res = self.fol.evaluate_rule(partial_rule, answer_text) if partial_rule else {"score": 0.0, "trace": []}
        fol_total = (good_res.get("score", 0.0) * 0.7) + (part_res.get("score", 0.0) * 0.3)

        total = (
            (0.28 * keyword_score)
            + (0.28 * concept_score)
            + (0.18 * detail_score)
            + (0.12 * code_score)
            + (0.14 * fol_total)
        )
        final_score = round(min(10.0, total * 10.0), 1)

        fol_trace: List[str] = []
        if good_rule:
            fol_trace.append("RULE: GoodAnswer Criteria")
            fol_trace.extend(good_res.get("trace", []))
        if partial_rule:
            fol_trace.append("RULE: PartialAnswer Criteria")
            fol_trace.extend(part_res.get("trace", []))

        strengths: List[str] = []
        weaknesses: List[str] = []
        suggestions: List[str] = []

        if matched_keywords:
            strengths.append(
                "You referenced important technical terms such as "
                + ", ".join(matched_keywords[:3])
                + "."
            )
        if explained_concepts:
            strengths.append(
                "You explained core concepts including "
                + ", ".join(explained_concepts[:2])
                + "."
            )
        if detail_score >= 0.8:
            strengths.append("Your answer had useful detail instead of a one-line definition.")
        if code_score >= 0.7 and ideal_answer.get("example"):
            strengths.append("You supported your explanation with an example or code-like reasoning.")

        if missing_keywords:
            weaknesses.append(
                "You missed some key technical language such as "
                + ", ".join(missing_keywords[:3])
                + "."
            )
        if missing_concepts:
            weaknesses.append(
                "The explanation did not fully cover concepts like "
                + ", ".join(missing_concepts[:2])
                + "."
            )
        if detail_score < 0.6:
            weaknesses.append("The answer needs more depth and structure to feel interview-ready.")
        if ideal_answer.get("example") and code_score < 0.5:
            weaknesses.append("A concrete example would make the answer much stronger.")

        if missing_concepts:
            suggestions.append(
                "Explicitly explain "
                + ", ".join(missing_concepts[:2])
                + " instead of only naming them."
            )
        if missing_keywords:
            suggestions.append(
                "Use precise interview language such as "
                + ", ".join(missing_keywords[:2])
                + " when relevant."
            )
        if detail_score < 0.6:
            suggestions.append("Structure the answer as definition, tradeoff, and example.")
        if ideal_answer.get("example") and code_score < 0.5:
            suggestions.append("Add one short real-world or code example to ground the explanation.")
        if not suggestions:
            suggestions.append("Push the answer one step further by adding a tradeoff or production example.")

        result = {
            "score": final_score,
            "strengths": strengths or ["You gave a reasonable starting answer."],
            "weaknesses": weaknesses,
            "missing_concepts": missing_concepts,
            "matched_keywords": matched_keywords,
            "fol_trace": fol_trace,
            "suggestions": suggestions,
            "feedback": f"Your answer scored {final_score}/10 based on concept coverage, clarity, and logic traces.",
            "ideal_answer": ideal_answer,
        }

        # LLM-based coaching feedback (from the SaaS UI branch)
        try:
            import streamlit as st
            if st.session_state.get('ai_enhanced_mode', False):
                from utils import call_gemini

                prompt = (
                    f"You are a technical interview coach. The candidate was asked: '{question.get('question', '')}'.\n"
                    f"They answered: '{answer_text}'.\n"
                    f"The evaluation system detected they scored {final_score}/10.\n"
                    f"They mentioned these correct keywords: {', '.join(matched_keywords) if matched_keywords else 'None'}.\n"
                    f"They missed these important concepts: {', '.join(missing_concepts) if missing_concepts else 'None'}.\n"
                    f"Write 2-3 sentences of constructive coaching feedback. Be specific, "
                    f"encouraging, and tell them exactly what to add next time. No bullet points."
                )

                llm_feedback = call_gemini(prompt, feature_name="Feature 2: Coach Feedback")
                if llm_feedback:
                    result["llm_feedback"] = llm_feedback
                else:
                    result["llm_feedback"] = " ".join(suggestions)
            else:
                result["llm_feedback"] = " ".join(suggestions)
        except Exception:
            result["llm_feedback"] = " ".join(suggestions)

        return result

    def _min_words_for(self, difficulty: str) -> int:
        return {"beginner": 18, "intermediate": 28, "advanced": 40}.get(str(difficulty).lower(), 20)