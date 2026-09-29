"""
Skill test bank + scoring.

Each test has MCQ and code-output ("what does this print?") questions.
Score = correct / total * 100, returned with per-question feedback, a band
label, and targeted advice.
"""

# Each question: {q, options:[...], answer: index, kind: 'mcq'|'code', explain}
TESTS = {
    "Python": [
        {"q": "What is the output?", "kind": "code", "code": "print(2 ** 3 ** 2)", "options": ["64", "512", "72", "TypeError"], "answer": 1, "explain": "** is right-associative: 3**2=9, then 2**9=512."},
        {"q": "Which of these is NOT a built-in data type in Python?", "kind": "mcq", "options": ["list", "dict", "array", "tuple"], "answer": 2, "explain": "array lives in the `array` module; the built-in sequence is `list`."},
        {"q": "What is the output?", "kind": "code", "code": "x = [1, 2, 3]\nprint(x[1:])", "options": ["[1, 2]", "[2, 3]", "[1, 2, 3]", "[2]"], "answer": 1, "explain": "Slicing from index 1 to the end gives [2, 3]."},
        {"q": "What does len({'a':1,'b':2}) return?", "kind": "mcq", "options": ["2", "4", "1", "Error"], "answer": 0, "explain": "len of a dict = number of keys."},
        {"q": "What is the output?", "kind": "code", "code": "def f(a, b=[]):\n    b.append(a)\n    return b\nprint(f(1), f(2))", "options": ["[1] [2]", "[1] [1, 2]", "[1, 2] [1, 2]", "Error"], "answer": 1, "explain": "Default mutable args are evaluated once and shared across calls."},
        {"q": "Which keyword creates an anonymous function?", "kind": "mcq", "options": ["def", "lambda", "func", "anon"], "answer": 1, "explain": "lambda x: x*2 defines an inline function."},
        {"q": "What is the output?", "kind": "code", "code": "print('abc'[::-1])", "options": ["abc", "cba", "c", "Error"], "answer": 1, "explain": "[::-1] reverses a string via slicing."},
        {"q": "What is the type of 5 / 2 in Python 3?", "kind": "mcq", "options": ["int", "float", "Decimal", "Depends on division setting"], "answer": 1, "explain": "/ always returns a float (2.5); // returns an int."},
    ],
    "JavaScript": [
        {"q": "What is the output?", "kind": "code", "code": "console.log(typeof null)", "options": ["'null'", "'object'", "'undefined'", "'boolean'"], "answer": 1, "explain": "Historic quirk: typeof null === 'object'."},
        {"q": "What is the output?", "kind": "code", "code": "console.log(0.1 + 0.2 === 0.3)", "options": ["true", "false", "Error", "undefined"], "answer": 1, "explain": "Floating-point: 0.1+0.2 = 0.30000000000000004."},
        {"q": "What does [1,2,3].map(x => x * 2) return?", "kind": "mcq", "options": ["[1, 2, 3]", "[2, 4, 6]", "6", "undefined"], "answer": 1, "explain": "map transforms each element."},
        {"q": "What is the output?", "kind": "code", "code": "console.log('5' + 3, '5' - 3)", "options": ["53 2", "8 2", "53 53", "Error"], "answer": 0, "explain": "+ concatenates strings; - coerces to numbers."},
        {"q": "Which declares a block-scoped variable that cannot be reassigned?", "kind": "mcq", "options": ["var", "let", "const", "static"], "answer": 2, "explain": "const = block-scoped + no rebinding."},
        {"q": "What is the output?", "kind": "code", "code": "setTimeout(() => console.log('A'), 0)\nconsole.log('B')", "options": ["A then B", "B then A", "A only", "B only"], "answer": 1, "explain": "setTimeout callback runs after the current synchronous code."},
        {"q": "What is the output?", "kind": "code", "code": "console.log([10, 1, 2].sort())", "options": ["[1, 2, 10]", "[10, 1, 2]", "[1, 10, 2]", "[2, 1, 10]"], "answer": 1, "explain": "Default sort is lexicographic ('10' < '2')."},
        {"q": "What does Object.keys({a:1, b:2}) return?", "kind": "mcq", "options": ["[1, 2]", "['a', 'b']", "['a1', 'b2']", "undefined"], "answer": 1, "explain": "Object.keys returns the key names."},
    ],
    "SQL": [
        {"q": "Which clause filters rows BEFORE grouping?", "kind": "mcq", "options": ["HAVING", "WHERE", "GROUP BY", "ORDER BY"], "answer": 1, "explain": "WHERE filters rows; HAVING filters groups."},
        {"q": "What does COUNT(*) vs COUNT(col) differ on?", "kind": "mcq", "options": ["No difference", "COUNT(col) skips NULLs", "COUNT(*) skips NULLs", "COUNT(col) is faster"], "answer": 1, "explain": "COUNT(col) counts non-NULL values only."},
        {"q": "What is the result?", "kind": "code", "code": "SELECT 10 / 3;", "options": ["3.33", "3", "3.3333", "Error — depends on the DB"], "answer": 3, "explain": "Integer division rules differ by database."},
        {"q": "Which JOIN returns all rows from the LEFT table plus matches from the right?", "kind": "mcq", "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"], "answer": 1, "explain": "LEFT JOIN keeps every left row, NULL-filling when unmatched."},
        {"q": "What does GROUP BY do?", "kind": "mcq", "options": ["Sorts rows", "Groups rows sharing column values so aggregates can run per group", "Removes duplicates", "Indexes the table"], "answer": 1, "explain": "It collapses rows per distinct key for aggregation."},
        {"q": "What is the output?", "kind": "code", "code": "SELECT NULL = NULL;", "options": ["true", "false", "NULL", "Error"], "answer": 2, "explain": "Comparisons with NULL yield NULL — use IS NULL."},
        {"q": "Which is faster for exact lookup on an indexed column?", "kind": "mcq", "options": ["LIKE '%x%'", "LIKE 'x%'", "=", "REGEXP"], "answer": 2, "explain": "Equality on an indexed column can use the index; leading-wildcard LIKE cannot."},
        {"q": "What does this return?", "kind": "code", "code": "SELECT MAX(salary) FROM emp\nWHERE salary < (SELECT MAX(salary) FROM emp);", "options": ["Highest salary", "Second-highest salary", "Lowest salary", "NULL always"], "answer": 1, "explain": "Classic second-highest-salary query."},
    ],
    "React": [
        {"q": "What must a React component name start with?", "kind": "mcq", "options": ["lowercase letter", "uppercase letter", "$", "any character"], "answer": 1, "explain": "Capitalised names distinguish components from DOM tags."},
        {"q": "Which hook adds local state?", "kind": "mcq", "options": ["useEffect", "useState", "useMemo", "useRef"], "answer": 1, "explain": "useState returns [value, setter]."},
        {"q": "What is the output in the console?", "kind": "code", "code": "useEffect(() => {\n  console.log('run');\n}, [])", "options": ["Runs on every render", "Runs once after mount", "Runs never", "Runs before mount"], "answer": 1, "explain": "Empty dependency array = run once after first render."},
        {"q": "Why do lists need the `key` prop?", "kind": "mcq", "options": ["For styling", "To help React identify items across re-renders", "It's optional decoration", "For accessibility"], "answer": 1, "explain": "Keys let React match old/new items efficiently."},
        {"q": "What does state updates do in React?", "kind": "mcq", "options": ["Mutate the DOM directly", "Trigger a re-render", "Reload the page", "Nothing in function components"], "answer": 1, "explain": "Setting state schedules a re-render."},
        {"q": "What is the output?", "kind": "code", "code": "const [n, setN] = useState(0);\nsetN(n + 1); setN(n + 1);\n// what is n after this batch?", "options": ["2", "1", "0", "Error"], "answer": 1, "explain": "Both calls read the same stale n — use setN(prev => prev + 1)."},
        {"q": "Which renders JSX?", "kind": "mcq", "options": ["ReactDOM.render (legacy) / createRoot in React 18", "React.print", "React.draw", "JSX auto-renders"], "answer": 0, "explain": "React 18 uses createRoot(rootEl).render(<App/>)."},
        {"q": "What does props stand for / contain?", "kind": "mcq", "options": ["Internal state", "Read-only inputs passed from parent to child", "CSS classes", "Event handlers only"], "answer": 1, "explain": "Props flow one way: parent -> child."},
    ],
    "Java": [
        {"q": "Which is NOT a Java primitive type?", "kind": "mcq", "options": ["int", "String", "boolean", "double"], "answer": 1, "explain": "String is a class, not a primitive."},
        {"q": "What is the default value of an int field in a class?", "kind": "mcq", "options": ["null", "0", "garbage", "compiler error"], "answer": 1, "explain": "Fields get zero-defaults; local variables must be initialised."},
        {"q": "What is the output?", "kind": "code", "code": "System.out.println(10 / 3);", "options": ["3.33", "3", "3.3333", "Error"], "answer": 1, "explain": "Integer division truncates."},
        {"q": "Which collection guarantees no duplicates?", "kind": "mcq", "options": ["ArrayList", "HashSet", "LinkedList", "Vector"], "answer": 1, "explain": "Set semantics = uniqueness."},
        {"q": "What keyword prevents a class from being subclassed?", "kind": "mcq", "options": ["static", "final", "sealed (Java 17) — also valid", "private"], "answer": 1, "explain": "final classes (e.g. String) cannot be extended."},
        {"q": "What is the output?", "kind": "code", "code": "String a = \"hi\";\nString b = new String(\"hi\");\nSystem.out.println(a == b);", "options": ["true", "false", "Error", "null"], "answer": 1, "explain": "== compares references; use .equals() for content."},
        {"q": "Which loop always runs at least once?", "kind": "mcq", "options": ["for", "while", "do-while", "for-each"], "answer": 2, "explain": "do-while tests the condition after the body."},
        {"q": "What does JVM stand for / do?", "kind": "mcq", "options": ["Compiles to machine code upfront", "Runs Java bytecode on any platform", "Manages version control", "Packages jars"], "answer": 1, "explain": "Write once, run anywhere — the JVM executes .class bytecode."},
    ],
    "Data Structures": [
        {"q": "What is the average time complexity of a hashmap lookup?", "kind": "mcq", "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "answer": 0, "explain": "Hashing gives O(1) average lookups."},
        {"q": "Which traversal visits the root first?", "kind": "mcq", "options": ["In-order", "Pre-order", "Post-order", "Level-order"], "answer": 1, "explain": "Pre-order = root, left, right."},
        {"q": "Which data structure is used for BFS?", "kind": "mcq", "options": ["Stack", "Queue", "Heap", "Trie"], "answer": 1, "explain": "BFS explores level by level using a FIFO queue."},
        {"q": "What is the output of pop() on a stack pushed 1, 2, 3?", "kind": "mcq", "options": ["1", "2", "3", "Error"], "answer": 2, "explain": "Stacks are LIFO."},
        {"q": "Time complexity of binary search on a sorted array of n elements?", "kind": "mcq", "options": ["O(n)", "O(log n)", "O(1)", "O(n log n)"], "answer": 1, "explain": "Each step halves the search space."},
        {"q": "Which sort has the best worst-case complexity?", "kind": "mcq", "options": ["Quick sort", "Merge sort", "Bubble sort", "Insertion sort"], "answer": 1, "explain": "Merge sort guarantees O(n log n); quick sort degrades to O(n²)."},
        {"q": "A min-heap's root contains what?", "kind": "mcq", "options": ["Maximum element", "Minimum element", "Median", "Random element"], "answer": 1, "explain": "Min-heap keeps the smallest at the root."},
        {"q": "Detecting a cycle in a linked list is best done with…", "kind": "mcq", "options": ["Merge sort", "Floyd's tortoise & hare", "Binary search", "Hashing the values"], "answer": 1, "explain": "Two pointers at different speeds meet iff a cycle exists."},
    ],
    "Machine Learning": [
        {"q": "Which is a supervised learning task?", "kind": "mcq", "options": ["Clustering", "Spam classification", "Dimensionality reduction", "Anomaly detection (unsupervised)"], "answer": 1, "explain": "Labels (spam/not-spam) make it supervised."},
        {"q": "High training accuracy, low test accuracy indicates…", "kind": "mcq", "options": ["Underfitting", "Overfitting", "Good fit", "Data leakage always"], "answer": 1, "explain": "Memorising the training set = overfitting."},
        {"q": "Which metric for an imbalanced binary classification?", "kind": "mcq", "options": ["Accuracy", "F1-score", "MSE", "R²"], "answer": 1, "explain": "F1 balances precision and recall when classes are skewed."},
        {"q": "What does gradient descent minimise?", "kind": "mcq", "options": ["The learning rate", "The loss/cost function", "The number of features", "The bias only"], "answer": 1, "explain": "It steps against the loss gradient."},
        {"q": "L2 regularisation (Ridge) does what?", "kind": "mcq", "options": ["Removes features", "Shrinks weights to reduce overfitting", "Increases variance", "Normalises labels"], "answer": 1, "explain": "Penalises large weights; L1 (Lasso) also sparsifies."},
        {"q": "What is the train/validation/test split for?", "kind": "mcq", "options": ["Faster training", "Unbiased estimate of generalisation", "Visualisation", "Feature engineering"], "answer": 1, "explain": "Test set simulates unseen data."},
        {"q": "Which algorithm is NOT a classifier?", "kind": "mcq", "options": ["Logistic regression", "Random forest", "k-NN", "k-Means"], "answer": 3, "explain": "k-Means is unsupervised clustering."},
        {"q": "Bias-variance tradeoff: simpler models tend to have…", "kind": "mcq", "options": ["High variance", "High bias", "Both high", "Neither"], "answer": 1, "explain": "Simple models underfit (bias); complex ones overfit (variance)."},
    ],
    "Node.js": [
        {"q": "What is Node.js built on?", "kind": "mcq", "options": ["JVM", "V8 JavaScript engine", "CLR", "CPython"], "answer": 1, "explain": "Chrome's V8 engine + libuv event loop."},
        {"q": "How does Node handle concurrent I/O?", "kind": "mcq", "options": ["One thread per request", "Non-blocking event loop", "Process per request", "It blocks per request"], "answer": 1, "explain": "Single-threaded event loop + async I/O."},
        {"q": "What does module.exports do?", "kind": "mcq", "options": ["Imports a module", "Defines what require() returns from a file", "Starts the server", "Freezes an object"], "answer": 1, "explain": "It is the object require() hands back."},
        {"q": "What is the output?", "kind": "code", "code": "const fs = require('fs');\nconst data = fs.readFileSync('x.txt');", "options": ["Runs asynchronously", "Blocks the event loop until read completes", "Throws always", "Returns a Promise"], "answer": 1, "explain": "readFileSync blocks; prefer fs.promises."},
        {"q": "What does npm init do?", "kind": "mcq", "options": ["Installs dependencies", "Creates package.json", "Starts the app", "Publishes the package"], "answer": 1, "explain": "Scaffolds the project manifest."},
        {"q": "Which returns a Promise?", "kind": "mcq", "options": ["http.createServer", "fetch", "fs.mkdirSync", "process.exit"], "answer": 1, "explain": "fetch is Promise-based."},
        {"q": "Express is primarily a…", "kind": "mcq", "options": ["Database", "Web application framework", "Testing library", "Bundler"], "answer": 1, "explain": "Express provides routing + middleware over http."},
        {"q": "What is middleware in Express?", "kind": "mcq", "options": ["Hardware layer", "Functions that run between request and response", "Template engine", "Cluster manager"], "answer": 1, "explain": "app.use(fn) chains request-processing functions."},
    ],
}


def available_tests() -> list[dict]:
    return [
        {"skill": s, "questions": len(qs), "mcq": sum(1 for q in qs if q["kind"] == "mcq"),
         "code": sum(1 for q in qs if q["kind"] == "code")}
        for s, qs in TESTS.items()
    ]


def get_test(skill: str) -> dict:
    """Questions WITHOUT answers (so the client can't cheat)."""
    if skill not in TESTS:
        raise ValueError(f"no test available for '{skill}'")
    qs = []
    for i, q in enumerate(TESTS[skill]):
        qs.append({
            "index": i,
            "kind": q["kind"],
            "question": q["q"],
            "code": q.get("code"),
            "options": q["options"],
        })
    return {"skill": skill, "total": len(qs), "questions": qs}


def grade_test(skill: str, answers: list) -> dict:
    """answers: list of chosen option indexes (or null) in question order."""
    if skill not in TESTS:
        raise ValueError(f"no test available for '{skill}'")
    qs = TESTS[skill]
    if len(answers) != len(qs):
        raise ValueError(f"expected {len(qs)} answers, got {len(answers)}")

    correct = 0
    per_question = []
    for q, a in zip(qs, answers):
        is_right = (a == q["answer"])
        correct += is_right
        per_question.append({
            "question": q["q"],
            "your_answer": q["options"][a] if isinstance(a, int) and 0 <= a < len(q["options"]) else "(skipped)",
            "correct_answer": q["options"][q["answer"]],
            "correct": is_right,
            "explanation": q["explain"],
        })

    percent = round(100 * correct / len(qs), 1)
    band, advice = _band(percent)
    return {
        "skill": skill,
        "correct": correct,
        "total": len(qs),
        "percent": percent,
        "band": band,
        "advice": advice,
        "per_question": per_question,
    }


def _band(p: float) -> tuple[str, str]:
    if p >= 85:
        return "Expert", "Strong command. Add this skill prominently to your resume and mention it in interviews."
    if p >= 70:
        return "Proficient", "Good level. Review the questions you missed and you're interview-ready."
    if p >= 50:
        return "Learning", "Basics are there. Follow the resource link in your gap roadmap and retake in a week."
    return "Beginner", "Focus on fundamentals first — take the guided resource, practise, then retake the test."
