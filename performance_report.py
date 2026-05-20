"""
Performance Report Generation (Unit VI - Planning)
Generates comprehensive feedback and learning path
"""

from typing import List, Dict, Any
from datetime import datetime
from learning_path_astar import AStarLearningPath


class PerformanceReport:
    def __init__(self):
        self.report_templates = {
            "strength": [
                "Strong understanding of {topic}",
                "Good grasp on {concept} concepts",
                "Excellent problem-solving approach in {area}"
            ],
            "weakness": [
                "Need improvement in {topic}",
                "Focus more on {concept}",
                "Practice more {area}-related questions"
            ],
            "improvement": [
                "Review {topic} fundamentals",
                "Study {concept} with practical examples",
                "Work on {area} problem-solving"
            ]
        }

    # ================= MAIN REPORT =================
    def generate_report(self, user_profile: Dict, answers: List[Dict]) -> Dict:
        """
        Generate comprehensive performance report
        """

        if not answers:
            return self._generate_empty_report(user_profile)

        overall_score = self._calculate_overall_score(answers)
        topic_performance = self._analyze_topic_performance(answers)
        strengths = self._identify_strengths(topic_performance)
        weaknesses = self._identify_weaknesses(topic_performance)
        progress = self._calculate_progress(answers)

        learning_path = self._generate_learning_path(weaknesses, user_profile)

        report = {
            "report_id": f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_profile": user_profile,
            "summary": {
                "total_questions": len(answers),
                "overall_score": overall_score,
                "performance_level": self._get_performance_level(overall_score),
                "completion_rate": self._calculate_completion_rate(answers)
            },
            "detailed_analysis": {
                "by_topic": topic_performance,
                "by_difficulty": self._analyze_difficulty_performance(answers),
                "progress_over_time": progress,
                "strongest_topics": strengths[:3],
                "weakest_topics": weaknesses[:3]
            },
            "learning_path": learning_path,
            "recommendations": self._generate_recommendations(weaknesses, strengths),
            "next_steps": self._generate_next_steps(weaknesses, user_profile),
            "resources": self._suggest_resources(weaknesses)
        }

        return report

    # ================= EMPTY REPORT =================
    def _generate_empty_report(self, user_profile: Dict) -> Dict:
        return {
            "report_id": f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_profile": user_profile,
            "summary": {
                "total_questions": 0,
                "overall_score": 0.0,
                "performance_level": "not_started",
                "completion_rate": 0.0
            },
            "detailed_analysis": {
                "by_topic": {},
                "by_difficulty": {
                    "beginner": {"average_score": 0, "questions_attempted": 0},
                    "intermediate": {"average_score": 0, "questions_attempted": 0},
                    "advanced": {"average_score": 0, "questions_attempted": 0}
                },
                "progress_over_time": [],
                "strongest_topics": [],
                "weakest_topics": []
            },
            "learning_path": [
                {
                    "phase": "foundation",
                    "focus": "getting_started",
                    "goal": "Complete your first interview session",
                    "estimated_time": "10 minutes",
                    "priority": "high"
                }
            ],
            "recommendations": [
                "Start your first interview practice session",
                "Complete your profile with target role",
                "Practice regularly"
            ],
            "next_steps": [
                "Start mock interview",
                "Answer questions",
                "Review feedback"
            ],
            "resources": []
        }

    # ================= SCORING =================
    def _calculate_overall_score(self, answers: List[Dict]) -> float:
        scores = [a.get("score", 0) for a in answers]
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    def _calculate_completion_rate(self, answers: List[Dict]) -> float:
        target = 10
        return round(min(len(answers) / target, 1.0) * 100, 1)

    def _get_performance_level(self, score: float) -> str:
        if score >= 8.5:
            return "expert"
        elif score >= 7:
            return "advanced"
        elif score >= 5:
            return "intermediate"
        elif score >= 3:
            return "beginner"
        return "needs_practice"

    # ================= TOPIC ANALYSIS =================
    def _analyze_topic_performance(self, answers: List[Dict]) -> Dict:
        topic_scores = {}
        topic_counts = {}

        for a in answers:
            topic = a.get("topic", "general")
            score = a.get("score", 0)

            topic_scores[topic] = topic_scores.get(topic, 0) + score
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        result = {}
        for t in topic_scores:
            avg = topic_scores[t] / topic_counts[t]
            result[t] = {
                "average_score": round(avg, 1),
                "questions_attempted": topic_counts[t],
                "level": self._get_performance_level(avg)
            }

        return result

    def _analyze_difficulty_performance(self, answers: List[Dict]) -> Dict:
        levels = {"beginner": [], "intermediate": [], "advanced": []}

        for a in answers:
            diff = a.get("difficulty", "beginner")
            if diff in levels:
                levels[diff].append(a.get("score", 0))

        result = {}
        for k, v in levels.items():
            if v:
                avg = sum(v) / len(v)
                result[k] = {
                    "average_score": round(avg, 1),
                    "questions_attempted": len(v)
                }
            else:
                result[k] = {
                    "average_score": 0,
                    "questions_attempted": 0
                }

        return result

    # ================= STRENGTHS / WEAKNESSES =================
    def _identify_strengths(self, topic_perf: Dict) -> List[Dict]:
        data = [
            {"topic": t, "score": v["average_score"]}
            for t, v in topic_perf.items()
        ]
        return sorted(data, key=lambda x: x["score"], reverse=True)

    def _identify_weaknesses(self, topic_perf: Dict) -> List[Dict]:
        data = [
            {"topic": t, "score": v["average_score"]}
            for t, v in topic_perf.items()
        ]
        return sorted(data, key=lambda x: x["score"])

    # ================= PROGRESS =================
    def _calculate_progress(self, answers: List[Dict]) -> List[Dict]:
        return [
            {
                "question_number": i + 1,
                "score": a.get("score", 0),
                "topic": a.get("topic", "general")
            }
            for i, a in enumerate(answers)
        ]

    # ================= LEARNING PATH =================
    def _generate_learning_path(self, weaknesses: List[Dict], profile: Dict) -> List[Dict]:
        topic_scores = {}

        for w in weaknesses:
            topic_scores[w["topic"].lower()] = w["score"]

        if not topic_scores:
            role = profile.get("target_role", "").lower()
            topic_scores = {"python": 0, "dsa": 0} if "data" not in role else {"python": 0, "sql": 0}

        astar = AStarLearningPath(topic_scores)
        modules, total = astar.find_path()

        path = []

        for m in modules:
            path.append({
                "phase": m.difficulty,
                "focus": m.topic,
                "goal": m.name,
                "estimated_time": f"{m.hours_cost} hours",
                "priority": "high"
            })

        if path:
            path.insert(0, {
                "phase": "optimal_plan",
                "focus": "A* Optimized Path",
                "goal": "Reach mastery efficiently",
                "estimated_time": f"Total: {total} hours",
                "priority": "critical"
            })

        return path

    # ================= RECOMMENDATIONS =================
    def _generate_recommendations(self, weaknesses, strengths):
        recs = []

        if weaknesses:
            recs.append(f"Focus on {weaknesses[0]['topic']}")

        if strengths:
            recs.append(f"Leverage strength in {strengths[0]['topic']}")

        recs.append("Practice daily mock interviews")
        recs.append("Revise weak concepts regularly")

        return recs

    def _generate_next_steps(self, weaknesses, profile):
        steps = []

        if weaknesses:
            steps.append(f"Start with {weaknesses[0]['topic']} basics")

        steps.append("Take mock interview in 2 days")
        steps.append("Track progress daily")

        return steps

    def _suggest_resources(self, weaknesses):
        return []