# Monetary Policy Voting Explorer

What reasons do MPC members give for preferring a different repo rate, and can simple text features distinguish dissent on new meetings? The timeline records 30 member votes from five RBI minutes, with concise rationale summaries and links to the minutes.

There was one rate dissent in the 12 held-out records. The majority baseline reached 91.7% accuracy with zero dissent recall. Unigram Naive Bayes with empirical priors missed the dissent and generated three false positives. Equal priors found the dissent and produced four false positives. The leaked label control scored 100% by construction. With one positive, this is weak evidence about out-of-sample detection.

Use Python 3.11 or later. Run `python -m unittest -v` and `python votes.py`, then open `index.html` and search “dissent”. Saugata Bhattacharya's June 2025 vote favored a 25-basis-point cut although the adopted cut was 50 basis points. No dependencies or keys are required.

The source register in `votes.json` stores the date of each meeting and release, the original RBI link, and a source locator. To recreate it, transcribe the vote and preferred amount from the voting table, then use the separate member statement for the reason. Member and meeting identifiers, literal vote words and rates are excluded from model input. The reason summaries were written after the votes and can still carry implicit signals. Explain why accuracy hides the rare class and why the split holds out whole meetings.

Neil Meher specified the project. Codex transcribed the votes, drafted rationale summaries and ran the experiment. Neil's independent review of summaries and labels is pending.
