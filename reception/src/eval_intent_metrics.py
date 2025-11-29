import json
from format import classify_intent
from sklearn.metrics import (
    accuracy_score, f1_score, precision_recall_fscore_support,
    confusion_matrix, cohen_kappa_score, matthews_corrcoef
)
import seaborn as sns
import matplotlib.pyplot as plt

# ----------------------------------------------------
# 1. Expanded Test Dataset
# ----------------------------------------------------
TEST_DATA = [
    # greeting
    ("hello", "greeting"),
    ("hi nao", "greeting"),
    ("hey there", "greeting"),

    # directory
    ("where is robotics lab", "directory"),
    ("locate room C-214", "directory"),
    ("find the innovation lab", "directory"),

    # hours
    ("when does the lab open", "hours"),
    ("what are the opening hours", "hours"),
    ("when do you close", "hours"),

    # contact
    ("who is professor sharma", "contact"),
    ("give me email of prof sharma", "contact"),
    ("faculty contact for Dr. Verma", "contact"),

    # close
    ("thank you, bye", "close"),
    ("thanks, that is all", "close"),

    # out-of-scope
    ("what is the population of delhi", "out_of_scope"),
    ("tell me a joke about robots", "out_of_scope"),
]

LABELS = ["greeting", "directory", "hours", "contact", "close", "out_of_scope"]

# ----------------------------------------------------
# 2. Run evaluation
# ----------------------------------------------------
gold_labels = []
pred_labels = []

print("==== Intent classification evaluation ====\n")

for text, gold in TEST_DATA:
    pred = classify_intent(text)
    gold_labels.append(gold)
    pred_labels.append(pred)

    print(f"Q: '{text:<40}' gold={gold:<12} pred={pred}")

# ----------------------------------------------------
# 3. Core Metrics
# ----------------------------------------------------
accuracy = accuracy_score(gold_labels, pred_labels)
macro_f1 = f1_score(gold_labels, pred_labels, average="macro")
weighted_f1 = f1_score(gold_labels, pred_labels, average="weighted")
kappa = cohen_kappa_score(gold_labels, pred_labels)
mcc = matthews_corrcoef(gold_labels, pred_labels)

print("\nOverall Metrics:")
print(f"  Accuracy     : {accuracy:.3f}")
print(f"  Macro-F1     : {macro_f1:.3f}")
print(f"  Weighted-F1  : {weighted_f1:.3f}")
print(f"  Cohen Kappa  : {kappa:.3f}")
print(f"  MCC          : {mcc:.3f}")

# ----------------------------------------------------
# 4. Per-class metrics
# ----------------------------------------------------
prec, rec, f1, _ = precision_recall_fscore_support(
    gold_labels, pred_labels, labels=LABELS, zero_division=0
)

print("\nPer-label metrics:")
for i, label in enumerate(LABELS):
    print(f"  {label:<12} P={prec[i]:.3f}  R={rec[i]:.3f}  F1={f1[i]:.3f}")

# ----------------------------------------------------
# 5. Confusion Matrix Plot
# ----------------------------------------------------
cm = confusion_matrix(gold_labels, pred_labels, labels=LABELS)

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=LABELS, yticklabels=LABELS)
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Intent Classification Confusion Matrix")
plt.tight_layout()
plt.show()
