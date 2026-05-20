"""
Intelligent Question Selection using Informed Search (Unit III)
Implements a role-aware Best-First Search heuristic with graceful fallbacks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class QuestionSelector:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.question_history: List[int] = []
        self.performance_history: List[Dict[str, Any]] = []

    def select_next_question(self, user_profile: Dict, previous_answers: List[Dict]) -> Optional[Dict]:
        candidate_questions = self._get_candidate_questions(user_profile)
        available_questions = [q for q in candidate_questions if q.get("id") not in self.question_history]

        if not available_questions:
            available_questions = [
                q for q in self.kb.get_all_questions() if q.get("id") not in self.question_history
            ]
        if not available_questions:
            return None

        scored_questions = []
        for question in available_questions:
            score = self._calculate_heuristic(question, user_profile, previous_answers)
            scored_questions.append((score, question))

        scored_questions.sort(key=lambda item: item[0], reverse=True)
        selected = dict(scored_questions[0][1])

        try:
            import streamlit as st

            if st.session_state.get("ai_enhanced_mode", False):
                from utils import call_gemini

                topic = str(selected.get("topic", "general"))
                difficulty = str(selected.get("difficulty", "intermediate"))
                role = str(user_profile.get("target_role", "candidate"))
                concepts = selected.get("concepts", [])
                anchor = str(concepts[0]) if concepts else topic
                prompt = (
                    f"You are a technical interviewer. Generate exactly one interview question about "
                    f"{topic} at {difficulty} level for a {role} candidate. "
                    f"Anchor it around {anchor}. Return only the question text in under 28 words."
                )
                llm_question = call_gemini(prompt, feature_name="Feature 4: Dynamic Question")
                if llm_question:
                    selected["question"] = llm_question
        except Exception:
            pass

        if selected.get("id") is not None:
            self.question_history.append(selected["id"])
        return selected

    def _calculate_heuristic(self, question: Dict, profile: Dict, previous_answers: List[Dict]) -> float:
        relevance = self._calculate_relevance(question, profile)
        difficulty_match = self._calculate_difficulty_match(question, profile)
        novelty = self._calculate_novelty(question)
        weakness_focus = self._calculate_weakness_focus(question, previous_answers)
        topic_balance = self._calculate_topic_balance(question, previous_answers)
        return float(
            (0.34 * relevance)
            + (0.24 * difficulty_match)
            + (0.16 * novelty)
            + (0.18 * weakness_focus)
            + (0.08 * topic_balance)
        )

    def _calculate_relevance(self, question: Dict, profile: Dict) -> float:
        topic_weights = self.kb.get_topic_weight_map(profile)
        question_topic = str(question.get("topic", "")).lower()
        base = topic_weights.get(question_topic, 0.2)

        target_role = str(profile.get("target_role", "")).lower()
        role_tags = [str(tag).lower() for tag in question.get("role_tags", [])]
        if target_role and target_role in role_tags:
            base += 0.2

        selected_skills = {str(skill).lower() for skill in profile.get("skills", [])}
        skill_tags = {str(tag).lower() for tag in question.get("skill_tags", [])}
        overlap = selected_skills.intersection(skill_tags)
        if overlap:
            base += min(0.2, 0.07 * len(overlap))

        return float(min(1.0, base))

    def _calculate_difficulty_match(self, question: Dict, profile: Dict) -> float:
        user_level = str(profile.get("experience_level", "entry")).lower()
        if "entry" in user_level:
            expected = "beginner"
        elif "mid" in user_level:
            expected = "intermediate"
        else:
            expected = "advanced"

        diff_map = {"beginner": 1, "intermediate": 2, "advanced": 3}
        target_value = diff_map.get(expected, 1)
        question_value = diff_map.get(str(question.get("difficulty", "beginner")).lower(), 1)
        distance = abs(target_value - question_value)
        if distance == 0:
            return 1.0
        if distance == 1:
            return 0.72
        return 0.38

    def _calculate_novelty(self, question: Dict) -> float:
        question_id = question.get("id")
        if question_id in self.question_history:
            return 0.0

        history_length = len(self.question_history)
        recent_slice = self.question_history[max(0, history_length - 5) : history_length]
        if question_id in recent_slice:
            return 0.3
        return 1.0

    def _calculate_weakness_focus(self, question: Dict, previous_answers: List[Dict]) -> float:
        if not previous_answers:
            return 0.5

        question_topic = str(question.get("topic", "")).lower()
        for answer in reversed(previous_answers):
            if str(answer.get("topic", "")).lower() == question_topic:
                latest_score = float(answer.get("score", 5.0))
                return float(max(0.0, min(1.0, 1.0 - (latest_score / 10.0))))
        return 0.5

    def _calculate_topic_balance(self, question: Dict, previous_answers: List[Dict]) -> float:
        if len(previous_answers) < 2:
            return 0.8

        recent_topics = [str(answer.get("topic", "")).lower() for answer in previous_answers[-2:]]
        question_topic = str(question.get("topic", "")).lower()
        if recent_topics.count(question_topic) >= 2:
            return 0.2
        if recent_topics and recent_topics[-1] == question_topic:
            return 0.5
        return 1.0

    def get_predicted_questions(
        self, user_profile: Dict, previous_answers: List[Dict], n: int = 3
    ) -> List[Tuple[float, Dict]]:
        candidates = self._get_candidate_questions(user_profile)
        available = [q for q in candidates if q.get("id") not in self.question_history]
        if not available:
            available = [q for q in self.kb.get_all_questions() if q.get("id") not in self.question_history]
        if not available:
            return []

        scored = []
        for question in available:
            score = self._calculate_heuristic(question, user_profile, previous_answers)
            scored.append((score, question))

        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:n]

    def _get_candidate_questions(self, profile: Dict) -> List[Dict]:
        resolved_topics = self.kb.resolve_topics_from_profile(profile)
        candidates: List[Dict] = []

        for topic in resolved_topics:
            candidates.extend(self.kb.get_questions_by_topic(topic))

        if len(candidates) < 15:
            role = str(profile.get("target_role", "")).lower()
            for question in self.kb.get_all_questions():
                role_tags = [str(tag).lower() for tag in question.get("role_tags", [])]
                if role and role in role_tags:
                    candidates.append(question)

        if not candidates:
            candidates = self.kb.get_all_questions()

        deduped: List[Dict] = []
        seen_ids = set()
        for question in candidates:
            qid = question.get("id")
            if qid not in seen_ids:
                seen_ids.add(qid)
                deduped.append(question)
        return deduped

    def update_performance(self, question_id: int, score: float, topic: str):
        self.performance_history.append(
            {
                "q_id": question_id,
                "score": float(score),
                "topic": topic,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    def reset_history(self):
        self.question_history = []
        self.performance_history = []
