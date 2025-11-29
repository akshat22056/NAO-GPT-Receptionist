# quick_latency_summary.py
import csv

LATENCY_CSV = "latency_log.csv"

def main():
    rows = []
    with open(LATENCY_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        print("No latency rows logged yet.")
        return

    def avg(col):
        vals = [float(r[col]) for r in rows]
        return sum(vals) / len(vals)

    print(f"Samples: {len(rows)}")
    for col in ["stt_ms", "plan_ms", "speak_ms", "total_ms"]:
        print(f"{col:10}: mean = {avg(col):.2f} ms")

if __name__ == "__main__":
    main()
