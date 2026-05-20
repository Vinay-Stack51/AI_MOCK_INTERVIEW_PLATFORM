"""
Unit III: Informed Search — A* Algorithm

Finds the minimum-time learning path to bring all topic scores to mastery (8.0).
Demonstrates State Space formulation, Path Cost g(n), and Admissible Heuristic h(n)
using a priority queue (heapq) to achieve A* optimality.
"""

import heapq
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set

@dataclass(frozen=True)
class LearningModule:
    name: str
    topic: str
    difficulty: str
    hours_cost: float
    score_improvement: float
    
    def __lt__(self, other):
        # Fallback comparison for heapq if 'f' values are tied
        return self.hours_cost < other.hours_cost

class AStarLearningPath:
    def __init__(self, topic_scores: Dict[str, float], mastery_threshold: float = 8.0):
        # Starting state (e.g., {"python": 4, "sql": 6, "dsa": 3})
        # Normalize keys and ensure we only track topics that actually exist in the db
        self.start_state = {k.lower(): v for k, v in topic_scores.items()}
        self.mastery_threshold = mastery_threshold
        
        # Available transitions (edges in the graph)
        # In a real app, these would come from a database. 
        self.available_modules = [
            # Python
            LearningModule("Python Basics & Variables", "python", "beginner", 1.0, 2.0),
            LearningModule("Python Data Structures", "python", "beginner", 1.5, 2.5),
            LearningModule("Python Functions & OOP", "python", "intermediate", 2.0, 2.0),
            LearningModule("Python Decorators & Generators", "python", "advanced", 3.0, 1.5),
            LearningModule("Python Metaclasses", "python", "advanced", 4.0, 2.0),
            
            # SQL
            LearningModule("SQL Select & Filtering", "sql", "beginner", 1.0, 2.0),
            LearningModule("SQL Joins & Subqueries", "sql", "intermediate", 2.0, 3.0),
            LearningModule("SQL Window Functions", "sql", "advanced", 3.0, 2.0),
            LearningModule("Database Optimization", "sql", "advanced", 4.0, 2.5),
            
            # DSA
            LearningModule("Arrays & Strings", "dsa", "beginner", 1.5, 2.0),
            LearningModule("Binary Search & Sorting", "dsa", "intermediate", 2.5, 2.5),
            LearningModule("Trees & Graphs", "dsa", "intermediate", 3.0, 2.0),
            LearningModule("Dynamic Programming", "dsa", "advanced", 4.0, 3.0),
            
            # JavaScript (fallback if user is tested on it)
            LearningModule("JS Fundamentals", "javascript", "beginner", 1.0, 2.0),
            LearningModule("JS Async & Promises", "javascript", "intermediate", 2.0, 2.5),
            LearningModule("JS Prototype Chain", "javascript", "advanced", 3.0, 2.0),

            # Java
            LearningModule("Java Foundations & JVM", "java", "beginner", 1.5, 2.0),
            LearningModule("Java Collections & OOP Design", "java", "intermediate", 2.5, 2.5),
            LearningModule("Java Concurrency & Performance", "java", "advanced", 3.5, 2.0),

            # OOP
            LearningModule("OOP Principles & Encapsulation", "oop", "beginner", 1.0, 2.0),
            LearningModule("Composition & SOLID Design", "oop", "intermediate", 2.0, 2.5),
            LearningModule("Architectural Abstractions", "oop", "advanced", 3.0, 2.0),

            # DBMS
            LearningModule("Relational Modeling Basics", "dbms", "beginner", 1.5, 2.0),
            LearningModule("Transactions & Schema Tradeoffs", "dbms", "intermediate", 2.5, 2.5),
            LearningModule("Distributed Data Systems", "dbms", "advanced", 3.5, 2.0),

            # Operating Systems
            LearningModule("Processes, Threads & Memory", "operating systems", "beginner", 1.5, 2.0),
            LearningModule("Scheduling, Deadlocks & Limits", "operating systems", "intermediate", 2.0, 2.5),
            LearningModule("Systems Performance Tuning", "operating systems", "advanced", 3.0, 2.0),

            # Computer Networks
            LearningModule("Networking Foundations", "computer networks", "beginner", 1.5, 2.0),
            LearningModule("HTTP, TLS & Troubleshooting", "computer networks", "intermediate", 2.5, 2.5),
            LearningModule("Distributed Traffic Engineering", "computer networks", "advanced", 3.5, 2.0),

            # React
            LearningModule("React Components & State", "react", "beginner", 1.5, 2.0),
            LearningModule("React Hooks & Performance", "react", "intermediate", 2.0, 2.5),
            LearningModule("Frontend Architecture Patterns", "react", "advanced", 3.0, 2.0),

            # Backend
            LearningModule("Backend Service Basics", "backend", "beginner", 1.5, 2.0),
            LearningModule("Reliability & Async Workflows", "backend", "intermediate", 2.5, 2.5),
            LearningModule("Distributed Backend Tradeoffs", "backend", "advanced", 3.5, 2.0),

            # API Design
            LearningModule("HTTP API Essentials", "api design", "beginner", 1.0, 2.0),
            LearningModule("Versioning, Errors & Rate Limits", "api design", "intermediate", 2.0, 2.5),
            LearningModule("Advanced Interface Strategy", "api design", "advanced", 3.0, 2.0),

            # Behavioral
            LearningModule("Structured Communication Practice", "behavioral", "beginner", 1.0, 2.0),
            LearningModule("Stakeholder & Team Communication", "behavioral", "intermediate", 1.5, 2.5),
            LearningModule("Leadership Through Influence", "behavioral", "advanced", 2.0, 2.0),
        ]

    def _state_to_tuple(self, state: Dict[str, float]) -> Tuple:
        """Convert state dictionary to hashable tuple for set membership checks"""
        return tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k, v in state.items()))

    def heuristic(self, state: Dict[str, float]) -> float:
        """
        h(n): Estimated cost (hours) to reach goal.
        Admissible heuristic: Sum of deficit points relative to mastery threshold,
        under-estimating the cost by assuming a very generous improvement-to-hour ratio.
        (Max observed ratio is 2.5 pts / 1.5 hr = 1.66 pts/hr. We use 2.0 to be strictly admissible -> h(n) = deficit / 2)
        """
        h_score = 0.0
        for topic, score in state.items():
            if score < self.mastery_threshold:
                deficit = self.mastery_threshold - score
                # Assume best case scenario: 2 score points improved per 1 hour spent
                h_score += (deficit / 2.0)
        return h_score

    def is_goal(self, state: Dict[str, float]) -> bool:
        """Check if all tracked topics have reached mastery"""
        for score in state.values():
            if score < self.mastery_threshold:
                return False
        return True

    def find_path(self) -> Tuple[List[LearningModule], float]:
        """
        Runs A* Search algorithm.
        Returns: (List of learning modules representing the optimal path, total hours cost)
        """
        # Edge case: If start state is empty or already at goal
        if not self.start_state or self.is_goal(self.start_state):
            return [], 0.0

        # Open list is a min-heap storing tuples:
        # (f_score, g_score, state_dict, path_of_modules)
        counter = 0 # Tie-breaker for identical f/g scores preventing dict comparison dicts
        
        g_start = 0.0
        h_start = self.heuristic(self.start_state)
        f_start = g_start + h_start
        
        open_list = [(f_start, counter, g_start, self.start_state, [])]
        
        # Closed list (visited states) mapped to their best known g-score to avoid worse redundant paths
        closed_list = {} 
        
        while open_list:
            # 1. Pop Best Node
            current_f, _, current_g, current_state, current_path = heapq.heappop(open_list)
            
            state_key = self._state_to_tuple(current_state)
            
            # If we've seen this state via a cheaper path, skip
            if state_key in closed_list and closed_list[state_key] <= current_g:
                continue
            
            closed_list[state_key] = current_g
            
            # 2. Goal Test
            if self.is_goal(current_state):
                return current_path, current_g
                
            # 3. Expand Neighbors (Apply Actions)
            for module in self.available_modules:
                # Only apply module if its topic is relevant and not already mastered in current state
                topic = module.topic.lower()
                if topic in current_state and current_state[topic] < self.mastery_threshold:
                    
                    # Prevent repeatedly taking the exact same module 
                    if module in current_path:
                        continue
                        
                    # Calculate new state
                    new_state = current_state.copy()
                    new_state[topic] = min(10.0, current_state[topic] + module.score_improvement)
                    
                    # Calculate g(n) and h(n)
                    new_g = current_g + module.hours_cost
                    new_h = self.heuristic(new_state)
                    new_f = new_g + new_h
                    
                    new_path = list(current_path)
                    new_path.append(module)
                    
                    counter += 1
                    heapq.heappush(open_list, (new_f, counter, new_g, new_state, new_path))
                    
        # Return empty list if no path finds goal (e.g. not enough modules available)
        return [], 0.0
