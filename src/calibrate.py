"""Compare LLM judge vs hand labels in eval/calibration_examples.json."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import eval_judge

def main():
    rows = [json.loads(l) for l in open("eval/calibration_examples.json") if l.strip() and l.strip().startswith('{"id"')]
    print(f"{len(rows)} calibration examples")
    agree = 0
    for r in rows:
        j = eval_judge.judge(r["question"], r["response"], r["retrieved"],
                             r["expected_source"], r["answerable"])
        h = r["human"]["pass"]
        match = (j["pass"] == h)
        agree += match
        print(f"{r['id']}: judge_pass={j['pass']} ({j['backend']}) human_pass={h} match={match}")
        print(f"  judge={j}")
        print(f"  human={r['human']}")
    print(f"agreement: {agree}/{len(rows)} = {agree/max(1,len(rows)):.2f}")
    print("To recalibrate: edit human labels in eval/calibration_examples.json, "
          "adjust rubric thresholds in src/eval_judge.py, rerun.")

if __name__ == "__main__":
    main()
