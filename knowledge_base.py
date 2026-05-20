from __future__ import annotations

from typing import Any, Dict, List, Optional

from question_bank_data import QUESTION_BLUEPRINT, SKILL_ALIASES, TOPIC_METADATA


class KnowledgeBase:
    def __init__(self):
        self.skill_aliases = {
            self._normalize(k): v for k, v in SKILL_ALIASES.items()
        }
        self.skill_topics = self._initialize_topics()
        self.questions = self._initialize_questions()
        self.ideal_answers = self._initialize_ideal_answers()

    # ---------------- QUESTIONS ---------------- #

    def _initialize_questions(self):
        question_id = 1
        built = {}

        for topic, difficulty_map in QUESTION_BLUEPRINT.items():
            built[topic] = {}

            for difficulty, entries in difficulty_map.items():
                built[topic][difficulty] = []

                for raw in entries:
                    q = dict(raw)

                    q.update({
                        "id": question_id,
                        "topic": topic,
                        "difficulty": difficulty,
                        "difficulty_level": difficulty,
                        "keywords": [k.lower() for k in q.get("keywords", [])],
                        "concepts": [c.lower() for c in q.get("concepts", [])],
                        "role_tags": q.get("role_tags", []),
                        "skill_tags": q.get("skill_tags", []),
                    })

                    q["fol_rules"] = self._build_fol_rules(q)

                    built[topic][difficulty].append(q)
                    question_id += 1

        return built

    # ---------------- FOL RULE GENERATION ---------------- #

    def _build_fol_rules(self, question: Dict[str, Any]) -> List[Dict[str, Any]]:
        keywords = question.get("keywords", [])
        concepts = question.get("concepts", [])
        example = (question.get("ideal_answer") or {}).get("example", "")
        difficulty = question.get("difficulty", "beginner")

        min_words = {
            "beginner": 18,
            "intermediate": 28,
            "advanced": 40,
        }.get(difficulty, 20)

        partial_words = max(10, min_words // 2)

        good_predicates = []

        # Strong signals
        for k in keywords[:2]:
            good_predicates.append({"fn": "Contains", "args": [k]})

        if concepts:
            good_predicates.append({"fn": "Explains", "args": [concepts[0]]})

        if example:
            good_predicates.append({"fn": "ExemplifiesCode", "args": []})

        good_predicates.append({"fn": "IsDetailed", "args": [min_words]})

        partial_focus = concepts[0] if concepts else (keywords[0] if keywords else question["topic"])

        partial_predicates = [
            {"fn": "Contains", "args": [partial_focus]},
            {"fn": "IsDetailed", "args": [partial_words]},
        ]

        return [
            {
                "type": "GoodAnswer",
                "predicates": good_predicates,
                "connective": "AND",
                "weight": 1.0,
            },
            {
                "type": "PartialAnswer",
                "predicates": partial_predicates,
                "connective": "AND",
                "weight": 0.5,
            },
        ]

    # ---------------- TOPIC RESOLUTION ---------------- #

    def _initialize_topics(self):
        return {
            self._normalize(t): data
            for t, data in TOPIC_METADATA.items()
        }

    def _initialize_ideal_answers(self):
        return {
            q["id"]: q.get("ideal_answer", {"key_points": [], "example": ""})
            for q in self.get_all_questions()
        }

    def _normalize(self, token: Any) -> str:
        return str(token or "").strip().lower()

    # ---------------- SKILL MAPPING ---------------- #

    def expand_skill_to_topics(self, token: Any) -> List[str]:
        token = self._normalize(token)

        if not token:
            return []

        if token in self.questions:
            return [token]

        return [
            t for t in self.skill_aliases.get(token, [])
            if t in self.questions
        ]

    def resolve_topics_from_profile(self, profile: Dict[str, Any]) -> List[str]:
        ordered = []
        seen = set()

        def add(items):
            for item in items:
                t = self._normalize(item)
                if t in self.questions and t not in seen:
                    seen.add(t)
                    ordered.append(t)

        skills = [self._normalize(s) for s in profile.get("skills", [])]
        role = self._normalize(profile.get("target_role", ""))

        for s in skills:
            add(self.expand_skill_to_topics(s))

        add(self.expand_skill_to_topics(role))

        if not ordered:
            add(self.expand_skill_to_topics("software engineer"))

        if "behavioral" not in seen:
            ordered.append("behavioral")

        return ordered

    def get_topic_weight_map(self, profile: Dict[str, Any]) -> Dict[str, float]:
        topics = self.resolve_topics_from_profile(profile)
        total = max(len(topics), 1)

        return {
            t: max(0.2, round(1.0 - (i * (0.7 / total)), 3))
            for i, t in enumerate(topics)
        }

    # ---------------- QUESTION ACCESS ---------------- #

    def get_all_questions(self):
        return [
            q
            for topic in self.questions.values()
            for diff in topic.values()
            for q in diff
        ]

    def get_questions_by_topic(self, topic: str, level: Optional[str] = None):
        t = self._normalize(topic)

        if t not in self.questions:
            return []

        if level is None:
            return [
                q
                for diff in self.questions[t].values()
                for q in diff
            ]

        return self.questions[t].get(self._normalize(level), [])

    def get_question_by_id(self, q_id: int) -> Optional[Dict[str, Any]]:
        q_id = str(q_id)

        for q in self.get_all_questions():
            if str(q["id"]) == q_id:
                return q

        return None

    # ---------------- BFS ---------------- #

    def explore_topics_bfs(self):
        nodes = []

        for topic, diff_map in self.questions.items():
            nodes.append({"name": topic.title(), "level": "topic"})

            for diff, questions in diff_map.items():
                nodes.append({"name": diff.capitalize(), "level": "difficulty"})

                for q in questions:
                    nodes.append({
                        "name": q["question"],
                        "id": q["id"],
                        "level": "question",
                    })

        return nodes