from typing import List, Dict
import random


class ConstraintSatisfactionPlanner:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base

    def generate_interview_plan(self) -> List[Dict]:
        """
        Generates a 10-question interview plan using CSP + Backtracking.
        Constraints:
        - 4 Beginner
        - 4 Intermediate
        - 2 Advanced
        - At least 3 topics
        - No duplicate questions
        """

        domain = []

        for topic, diff_dict in self.kb.questions.items():
            for diff, questions in diff_dict.items():
                for q in questions:
                    q_copy = dict(q)
                    q_copy["topic"] = topic
                    q_copy["difficulty_level"] = diff
                    domain.append(q_copy)

        random.shuffle(domain)

        constraints = {
            "beginner_target": 4,
            "intermediate_target": 4,
            "advanced_target": 2,
            "min_topics": 3,
            "total_questions": 10,
        }

        if not self._is_feasible(domain, constraints):
            return []

        assignment = []

        if self._backtrack(assignment, domain, constraints):
            return assignment

        return []

    def _is_feasible(self, domain: List[Dict], constraints: Dict) -> bool:
        counts = {"beginner": 0, "intermediate": 0, "advanced": 0}

        for q in domain:
            counts[q.get("difficulty_level", "beginner")] += 1

        return (
            counts["beginner"] >= constraints["beginner_target"]
            and counts["intermediate"] >= constraints["intermediate_target"]
            and counts["advanced"] >= constraints["advanced_target"]
        )

    def _backtrack(
        self,
        assignment: List[Dict],
        domain: List[Dict],
        constraints: Dict,
    ) -> bool:

        if len(assignment) == constraints["total_questions"]:
            topics = set(q.get("topic") for q in assignment)
            return len(topics) >= constraints["min_topics"]

        counts = {"beginner": 0, "intermediate": 0, "advanced": 0}
        used_ids = set(q["id"] for q in assignment)

        for q in assignment:
            counts[q["difficulty_level"]] += 1

        for q in domain:

            if q["id"] in used_ids:
                continue

            diff = q["difficulty_level"]

            if diff == "beginner" and counts["beginner"] >= constraints["beginner_target"]:
                continue
            if diff == "intermediate" and counts["intermediate"] >= constraints["intermediate_target"]:
                continue
            if diff == "advanced" and counts["advanced"] >= constraints["advanced_target"]:
                continue

            assignment.append(q)

            if self._backtrack(assignment, domain, constraints):
                return True

            assignment.pop()

        return False