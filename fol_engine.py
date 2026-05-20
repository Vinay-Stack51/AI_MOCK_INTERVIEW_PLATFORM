import re

class FOLEngine:
    def __init__(self):
        self.connectives = ["AND", "OR"]
        self.connectors = ['is', 'means', 'refers to', 'defined as', 'because', 'allows', 'explains']

    def Contains(self, answer: str, term: str) -> float:
        answer_lower = str(answer).lower()
        term_lower = str(term).lower()
        if term_lower in answer_lower:
            return 1.0
        if len(term_lower) > 4 and term_lower[:4] in answer_lower:
            return 0.5
        return 0.0

    def Explains(self, answer: str, concept: str) -> float:
        answer_lower = str(answer).lower()
        concept_lower = str(concept).lower()
        
        idx = answer_lower.find(concept_lower)
        if idx == -1: return 0.0
        
        start = max(0, idx - 40)
        end = min(len(answer_lower), idx + len(concept_lower) + 40)
        window = answer_lower[start:end]
        
        if any(conn in window for conn in self.connectors):
            return 1.0
        return 0.6

    def ExemplifiesCode(self, answer: str) -> float:
        ans_str = str(answer)
        patterns = [
            r'def\s+\w+\s*\(', r'class\s+\w+', r'\s+if\s+.*:', 
            r'\s+for\s+.*\sin\s+', r'return\s+.*', r'\w+\s*=\s*\[.*\]',
            r'\w+\s*\([\w\s,]*\)'
        ]
        score = 0.0
        for p in patterns:
            if re.search(p, ans_str):
                score += 0.4
        
        if "```" in ans_str or "    " in ans_str:
            score += 0.3
            
        return min(1.0, float(score))

    def IsDetailed(self, answer: str, min_words: int = 30) -> float:
        words = str(answer).split()
        if not words: return 0.0
        return min(1.0, len(words) / float(min_words))

    def Defines(self, answer: str, term: str) -> float:
        answer_lower = str(answer).lower()
        term_lower = str(term).lower()
        patterns = [
            f"{term_lower}\\s+is", f"{term_lower}\\s+refers\\s+to", 
            f"{term_lower}\\s+means", f"{term_lower}\\s+defined\\s+as"
        ]
        for p in patterns:
            if re.search(p, answer_lower):
                return 1.0
        return 0.0

    def evaluate_rule(self, rule: dict, answer: str) -> dict:
        if not rule: return {"satisfied": False, "score": 0.0, "trace": []}
        results = []
        trace = []
        
        for pred in rule.get("predicates", []):
            name = pred["fn"]
            args = pred.get("args", [])
            method = getattr(self, name, None)
            if method:
                score = float(method(answer, *args))
                results.append(score)
                satisfied_text = "TRUE" if score == 1.0 else "PARTIAL" if score > 0 else "FALSE"
                trace.append(f"{name}(answer, {', '.join(map(str, args))}) → {satisfied_text} ({score:.1f})")
            else:
                trace.append(f"{name} NOT FOUND!")
        
        connective = rule.get("connective", "AND")
        if not results:
            final_score = 0.0
        elif connective == "AND":
            final_score = sum(results) / len(results)
        else: # OR
            final_score = max(results)
            
        return {
            "satisfied": final_score >= 0.7,
            "score": float(final_score),
            "trace": trace
        }