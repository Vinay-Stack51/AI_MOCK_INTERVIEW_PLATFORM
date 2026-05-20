from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
import html as _html

@dataclass
class STRIPSAction:
    name: str
    preconditions: Set[str]   # facts that must be TRUE
    add_effects: Set[str]     # facts added after action
    del_effects: Set[str]     # facts removed after action
    cost: float = 1.0

class GoalStackPlanner:
    def __init__(self, initial_state: Set[str], goal_state: Set[str], actions: List[STRIPSAction]):
        self.state = initial_state.copy()
        self.goal_state = goal_state
        self.actions = actions
        self.plan = []
        self.execution_log = []
        self._full_plan_names = []

    def plan_interview(self) -> List[str]:
        """
        Goal Stack Planning algorithm (Simplified)
        Determines a sequence of actions to reach the goal state.
        """
        # In a real Goal Stack Planner, we use a stack to decompose goals.
        # Here we simulate the sequence based on the standard flow for the UI.
        stack = list(self.goal_state)
        planned_actions = []
        current_temp_state = self.state.copy()
        
        # Simple linear solver for these specific interview actions
        max_iters = 20
        while not self.goal_state.issubset(current_temp_state) and max_iters > 0:
            max_iters -= 1
            for action in self.actions:
                if action.name in planned_actions: continue
                if action.preconditions.issubset(current_temp_state):
                    planned_actions.append(action.name)
                    current_temp_state.update(action.add_effects)
                    current_temp_state.difference_update(action.del_effects)
                    break
        
        self._full_plan_names = planned_actions
        return planned_actions

    def get_current_action(self, answer_history: List[Dict]) -> str:
        """
        Determine which STRIPS action is currently pending.
        """
        for action_name in self._full_plan_names:
            action = next((a for a in self.actions if a.name == action_name), None)
            if action and not action.add_effects.issubset(self.state):
                return action_name
        return "session_complete"

    def execute_step(self, action_name: str) -> Dict:
        """
        Apply effects of an action to the state.
        """
        action = next((a for a in self.actions if a.name == action_name), None)
        if not action:
            return {"success": False, "log": f"Action {action_name} not found"}
        
        if action.preconditions.issubset(self.state):
            self.state.update(action.add_effects)
            self.state.difference_update(action.del_effects)
            entry = f"Executed: {action_name}. State added: {action.add_effects}"
            self.execution_log.append(entry)
            return {"success": True, "new_state": self.state, "log_entry": entry}
        
        return {"success": False, "log": f"Preconditions not met for {action_name}"}

    def get_plan_html(self) -> str:
        """
        Returns an HTML string showing the plan as a vertical timeline.
        """
        def _esc(value) -> str:
            return _html.escape(str(value), quote=True)

        html = '<div style="font-family:sans-serif;padding:10px;">'
        current_action = self.get_current_action([]) # Placeholder for determining current
        
        found_current = False
        for name in self._full_plan_names:
            action_obj = next((a for a in self.actions if a.name == name), None)
            is_completed = action_obj.add_effects.issubset(self.state) if action_obj else False
            
            icon = "✅" if is_completed else "▶️" if not found_current else "⏳"
            color = "#10b981" if is_completed else "#3b82f6" if not found_current else "#94a3b8"
            pulse_class = "pulsing" if not is_completed and not found_current else ""
            
            if not is_completed and not found_current:
                found_current = True
            
            safe_label = _esc(str(name).replace('_', ' ').title())
            # Avoid leading whitespace so Streamlit's markdown parser
            # consistently treats this as an HTML block.
            html += (
                f'<div style="display:flex;align-items:center;margin-bottom:8px;color:{color};">'
                f'<span style="margin-right:10px;">{icon}</span>'
                f'<span style="font-weight:500;">{safe_label}</span>'
                f'</div>'
            )
        html += "</div>"
        return html

def get_strips_actions():
    return [
        STRIPSAction(
            name="greet_candidate",
            preconditions={"session_started"},
            add_effects={"candidate_greeted"},
            del_effects=set()
        ),
        STRIPSAction(
            name="ask_beginner_question",
            preconditions={"candidate_greeted"},
            add_effects={"basics_assessed"},
            del_effects=set()
        ),
        STRIPSAction(
            name="ask_intermediate_question",
            preconditions={"basics_assessed"},
            add_effects={"intermediate_assessed"},
            del_effects=set()
        ),
        STRIPSAction(
            name="ask_advanced_question",
            preconditions={"intermediate_assessed"},
            add_effects={"advanced_assessed"},
            del_effects=set()
        ),
        STRIPSAction(
            name="remediate_weak_topic",
            preconditions={"weak_topic_identified"},
            add_effects={"remediation_done"},
            del_effects={"weak_topic_identified"}
        ),
        STRIPSAction(
            name="generate_report",
            preconditions={"basics_assessed", "intermediate_assessed"},
            add_effects={"report_generated"},
            del_effects=set()
        ),
        STRIPSAction(
            name="close_session",
            preconditions={"report_generated"},
            add_effects={"session_closed"},
            del_effects=set()
        )
    ]

def update_state_from_answers(planner, answer_history):
    """
    Derive STRIPS facts from actual interview progress.
    """
    if not answer_history:
        return
    
    for ans in answer_history:
        diff = str(ans.get("difficulty", "")).lower()
        if "beginner" in diff:
            planner.state.add("basics_assessed")
        elif "intermediate" in diff:
            planner.state.add("intermediate_assessed")
        elif "advanced" in diff:
            planner.state.add("advanced_assessed")
        
        if ans.get("score", 10) < 5:
            planner.state.add("weak_topic_identified")
        
        topic = str(ans.get("topic", "")).lower()
        planner.state.add(f"{topic}_assessed")
