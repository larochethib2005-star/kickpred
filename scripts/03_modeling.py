#!/usr/bin/env python3
"""
Week 3 — Train and compare 5 models on our own, cleaned Kickstarter dataset
(598,740 campaigns). Mirrors the reference GitHub project's approach, but
on our own, larger and more recent data.
"""
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix,
)

RSEED = 42

print("Loading cleaned data...")
df = pd.read_csv("data/Kickstarter_clean.csv")
print(f"Shape: {df.shape}")

# ---------------------------------------------------------------
# 1. Define target and features
#    backers_count / usd_pledged are excluded: data leakage
#    (only known AFTER a campaign launches, see slide 7)
# ---------------------------------------------------------------
y = df["target"]
X = df.drop(columns=["target", "backers_count", "usd_pledged"])

# location_state has 1,611 unique values -> one-hot encoding it would
# create 1,611 noisy columns, hurting more than helping a first model.
# We keep location_type (10 values) as a lighter geographic signal instead.
X = X.drop(columns=["location_state"])

print(f"\nFeatures used ({X.shape[1]}): {list(X.columns)}")

# ---------------------------------------------------------------
# 2. One-hot encode categorical columns
# ---------------------------------------------------------------
cat_cols = ["category", "subcategory", "country", "location_type"]
X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
print(f"After one-hot encoding: {X.shape[1]} columns")

# ---------------------------------------------------------------
# 3. Train / test split (70/30, stratified so both sets keep the
#    same success/failure ratio)
# ---------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=RSEED
)
print(f"\nTrain size: {X_train.shape[0]} | Test size: {X_test.shape[0]}")

VAGUE_PITCH_WORDS = ["want", "create", "creating", "people", "make", "like", "business", "online", "life"]
kw_cols = [f"kw_{w}" for w in VAGUE_PITCH_WORDS]

# Logistic Regression needs scaled numeric features; tree models don't
num_cols = ["goal", "staff_pick", "blurb_length", "name_length",
            "duration_days", "year", "month", "prep_days", "sentiment"] + kw_cols
scaler = StandardScaler()
X_train_scaled = X_train.copy()
X_test_scaled = X_test.copy()
X_train_scaled[num_cols] = scaler.fit_transform(X_train[num_cols])
X_test_scaled[num_cols] = scaler.transform(X_test[num_cols])

# ---------------------------------------------------------------
# 3b. Naive baseline: always predict the majority class
#     Gives a floor to compare every real model against — a model
#     that can't beat this isn't learning anything useful.
# ---------------------------------------------------------------
majority_class = y_train.mode()[0]
naive_accuracy = (y_test == majority_class).mean()
print(f"\nNaive baseline (always predict '{majority_class}'): "
      f"{naive_accuracy:.3f} accuracy")

# ---------------------------------------------------------------
# 4. Evaluation helper — computes all the metrics the professor
#    asked for, not just accuracy
# ---------------------------------------------------------------
results = []

def evaluate(name, model, X_tr, X_te):
    model.fit(X_tr, y_train)
    y_pred = model.predict(X_te)
    y_proba = model.predict_proba(X_te)[:, 1]

    row = {
        "model": name,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba),
    }
    results.append(row)

    train_acc = accuracy_score(y_train, model.predict(X_tr))
    print(f"\n{name}")
    print(f"  Train accuracy: {train_acc:.3f} | Test accuracy: {row['accuracy']:.3f}")
    print(f"  Precision: {row['precision']:.3f} | Recall: {row['recall']:.3f} | "
          f"F1: {row['f1']:.3f} | ROC-AUC: {row['roc_auc']:.3f}")
    if train_acc - row["accuracy"] > 0.15:
        print("  WARNING: large train/test gap -> overfitting")
    return model

# ---------------------------------------------------------------
# 5. Train and compare all 5 models
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("TRAINING MODELS")
print("=" * 60)

evaluate("Logistic Regression", LogisticRegression(max_iter=1000, random_state=RSEED),
          X_train_scaled, X_test_scaled)

evaluate("Decision Tree", DecisionTreeClassifier(random_state=RSEED),
          X_train, X_test)

evaluate("Random Forest", RandomForestClassifier(n_estimators=100, random_state=RSEED, n_jobs=-1),
          X_train, X_test)

evaluate("AdaBoost", AdaBoostClassifier(random_state=RSEED),
          X_train, X_test)

best_xgb = evaluate("XGBoost", XGBClassifier(random_state=RSEED, eval_metric="logloss"),
                      X_train, X_test)

# ---------------------------------------------------------------
# 6. Final comparison table
# ---------------------------------------------------------------
results_df = pd.DataFrame(results).set_index("model").round(3)
print("\n" + "=" * 60)
print("FINAL COMPARISON")
print("=" * 60)
print(results_df)

best_model_name = results_df["accuracy"].idxmax()
print(f"\nBest model by accuracy: {best_model_name}")

results_df.to_csv("data/model_comparison.csv")
print("Saved comparison table to data/model_comparison.csv")

# ---------------------------------------------------------------
# 7. Comparison chart — accuracy, F1, ROC-AUC side by side per model
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5.5))
results_df[["accuracy", "f1", "roc_auc"]].plot(
    kind="bar", ax=ax, color=["#C81E2C", "#7A0C14", "#1F1F1F"]
)
ax.set_title("Model Comparison — Accuracy, F1, ROC-AUC")
ax.set_ylabel("Score")
ax.set_xlabel("")
ax.set_ylim(0, 1)
ax.axhline(naive_accuracy, color="gray", linestyle="--", linewidth=1,
           label=f"Naive baseline ({naive_accuracy:.2f})")
ax.legend(loc="lower right")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig("data/model_comparison.png", dpi=150)
print("Saved comparison chart to data/model_comparison.png")
