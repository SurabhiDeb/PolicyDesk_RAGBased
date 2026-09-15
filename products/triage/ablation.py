import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from classify import classify

HINDI = "Namaste, mera card kaam nahi kar raha hai UK ke bahar. Please help."
ENGLISH = "Hello, my card is not working outside the UK. Please help."

for label, text in (("hindi  ", HINDI), ("english", ENGLISH)):
    got = classify(text)
    print(f"{label}  team={got['team']:12} urgency={got['urgency']}  escalate={got['escalate']}")