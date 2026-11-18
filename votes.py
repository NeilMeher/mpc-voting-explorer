"""Source-linked MPC voting timeline and post-meeting text experiment."""
import collections
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUT = "2025-04-01"
FORBIDDEN = {"vote", "voted", "dissent", "dissented", "agree", "yes", "no", "bps"}


def load():
    return json.loads((ROOT / "votes.json").read_text(encoding="utf-8"))


def words(text):
    return re.findall("[a-z]+", text.lower())


def assert_clean(rows):
    for row in rows:
        tokens = set(words(row["reason"]))
        if tokens.intersection(FORBIDDEN) or re.search(r"\d", row["reason"]):
            raise ValueError(f'Explicit vote text in {row["meeting"]}, {row["member"]}')


class Bayes:
    def __init__(self, rows):
        self.n = collections.Counter(row["dissent"] for row in rows)
        self.counts = [collections.Counter(), collections.Counter()]
        for row in rows:
            self.counts[row["dissent"]].update(words(row["reason"]))
        self.vocab = set().union(*self.counts)
        self.totals = [sum(c.values()) + len(self.vocab) for c in self.counts]

    def predict(self, text, balance):
        matched = [word for word in words(text) if word in self.vocab]
        scores = [sum(math.log((self.counts[cls][word]+1)/self.totals[cls]) for word in matched)
                  + (0 if balance else math.log(self.n[bool(cls)]))
                  for cls in (0,1)]
        return scores[1] > scores[0]


def metrics(gold, predictions):
    pairs = list(zip(gold, predictions, strict=True))
    tp = sum(g and p for g,p in pairs)
    tn = sum(not g and not p for g,p in pairs)
    fp = sum(not g and p for g,p in pairs)
    positives = sum(gold)
    recall = tp / positives
    specificity = tn / (len(pairs) - positives)
    return dict(accuracy=(tp+tn)/len(pairs), precision=tp/(tp+fp) if tp+fp else None,
                recall=recall, balanced_accuracy=(recall+specificity)/2,
                true_positive=tp, false_positive=fp, true_negative=tn)


def evaluate(rows):
    assert_clean(rows)
    training = [row for row in rows if row["meeting"] < CUT]
    held_out = [row for row in rows if row["meeting"] >= CUT]
    model = Bayes(training)
    gold = [row["dissent"] for row in held_out]
    # This deliberately leaks the answer from the voting table to contrast with reason-only inputs.
    from_vote_field = ["dissent" if row["dissent"] else "agree" for row in held_out]
    predictors = dict(majority=[False]*len(gold),
                      empirical=[model.predict(row["reason"], False) for row in held_out],
                      balanced=[model.predict(row["reason"], True) for row in held_out],
                      leaked=[label=="dissent" for label in from_vote_field])
    return dict(training=len(training), testing=len(gold), dissent=sum(gold),
                metrics={name:metrics(gold, pred) for name,pred in predictors.items()},
                predictions=[dict(meeting=row["meeting"], member=row["member"], dissent=row["dissent"],
                                  **{name:pred[i] for name,pred in predictors.items()})
                             for i,row in enumerate(held_out)])


def draw(rows):
    table = []
    for r in rows:
        table.append(f'<tr><td>{r["meeting"]}</td><td>{html.escape(r["member"])}</td>'
                     f'<td>{r["preferred_bps"]/100:.2f}%</td><td>{"Dissent" if r["dissent"] else "Agreed"}</td>'
                     f'<td>{html.escape(r["reason"])}</td><td><a href="{html.escape(r["source"])}" '
                     f'title="{html.escape(r["locator"])}">Minutes · {r["published"]}</a></td></tr>')
    top = """<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>MPC voting timeline</title><style>body{font:1rem/1.6 system-ui;color:#163447;max-width:70rem;margin:4rem auto;padding:0 1rem;background:#f4f7fa}
table{border-collapse:collapse;width:100%;background:white}td,th{border-bottom:1px solid #cfdbe1;padding:.65rem;text-align:left}
input{font:inherit;margin:.75rem;padding:.35rem}.scroll{overflow-x:auto}a{color:#0b6070}</style>
<h1>MPC voting timeline</h1><p>Explore preferred policy repo rates and the reasons in the published minutes.</p>
<label>Search by member, date, vote or reason <input type=search></label><div class=scroll>
<table><thead><tr><th>Meeting</th><th>Member</th><th>Preferred rate</th><th>Vote</th><th>Reason summary</th><th>Source</th></tr></thead><tbody>"""
    end = """</tbody></table></div><script>document.querySelector("input").addEventListener("input",event=>{
for(const row of document.querySelectorAll("tbody tr"))row.hidden=!row.textContent.toLowerCase().includes(event.target.value.trim().toLowerCase());
});</script></html>"""
    (ROOT / "index.html").write_text(top + "\n".join(table) + end, encoding="utf-8")


if __name__ == "__main__":
    rows = load()
    report = evaluate(rows)
    (ROOT / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    draw(rows)
    print(json.dumps(report["metrics"], indent=2))
