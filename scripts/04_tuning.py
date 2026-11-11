#!/usr/bin/env python3
"""
Week 4 — Tune XGBoost, inspect feature importance, and plot a confusion matrix.

Note on tuning method: the reference GitHub project used a full GridSearchCV
(100 combinations x 5-fold CV = 500 fits) on 169K rows. Our dataset is ~3.5x
larger (599K rows), so a full grid search would take too long on a laptop.
We use RandomizedSearchCV instead — it samples a limited number of random
combinations from the same parameter space, which is the standard, faster
alternative for larger datasets and still a legitimate tuning method.
"""
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay,
)
from xgboost import XGBClassifier

RSEED = 42

print("Loading cleaned data...")
df = pd.read_csv("data/Kickstarter_clean.csv")

# ---------------------------------------------------------------
# Same feature prep as 03_modeling.py
# ---------------------------------------------------------------
VAGUE_PITCH_WORDS = ["want", "create", "creating", "people", "make", "like", "business", "online", "life"]
kw_cols = [f"kw_{w}" for w in VAGUE_PITCH_WORDS]

y = df["target"]
X = df.drop(columns=["target", "backers_count", "usd_pledged", "location_state"])
cat_cols = ["category", "subcategory", "country", "location_type"]

# Columns the app shows as sliders — sentiment/kw_* are NOT here, they're
# computed live from the blurb text box instead (see app.py)
num_cols = ["goal", "staff_pick", "blurb_length", "name_length",
            "duration_days", "year", "month", "prep_days", "sentiment"] + kw_cols
slider_cols = ["goal", "duration_days", "blurb_length", "name_length", "prep_days"]

# Keep raw category options + numeric ranges for the app's input form,
# captured before one-hot encoding turns them into 0/1 columns
cat_options = {c: sorted(df[c].dropna().unique().tolist()) for c in cat_cols}
num_ranges = {c: (float(df[c].min()), float(df[c].median()), float(df[c].max()))
              for c in slider_cols}

X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=RSEED
)
print(f"Train size: {X_train.shape[0]} | Test size: {X_test.shape[0]}")

# ---------------------------------------------------------------
# 1. Hyperparameter tuning with RandomizedSearchCV
# ---------------------------------------------------------------
param_grid = {
    "max_depth": [4, 5, 6, 7, 8],
    "n_estimators": [50, 100, 150, 200, 250],
    "learning_rate": [0.05, 0.1, 0.2, 0.3, 0.4],
}

print("\nTuning XGBoost (RandomizedSearchCV, 15 combinations, 3-fold CV)...")
search = RandomizedSearchCV(
    estimator=XGBClassifier(random_state=RSEED, eval_metric="logloss"),
    param_distributions=param_grid,
    n_iter=15,
    cv=3,
    scoring="accuracy",
    random_state=RSEED,
    n_jobs=-1,
    verbose=1,
)
search.fit(X_train, y_train)

best_model = search.best_estimator_
print(f"\nBest params: {search.best_params_}")

y_pred = best_model.predict(X_test)
y_proba = best_model.predict_proba(X_test)[:, 1]

print(f"\nTuned XGBoost test accuracy: {accuracy_score(y_test, y_pred):.3f}")
print(f"Tuned XGBoost test precision: {precision_score(y_test, y_pred):.3f}")
print("\nFull classification report:")
print(classification_report(y_test, y_pred, target_names=["Failed", "Successful"]))

# ---------------------------------------------------------------
# 2. Confusion matrix
# ---------------------------------------------------------------
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(6, 5))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Failed", "Successful"])
disp.plot(ax=ax, cmap="Blues", values_format=",d")
ax.set_title("XGBoost (tuned) — Confusion Matrix")
plt.tight_layout()
plt.savefig("data/confusion_matrix.png", dpi=150)
print("\nSaved confusion matrix to data/confusion_matrix.png")

# ---------------------------------------------------------------
# 3. Feature importance (top 15)
# ---------------------------------------------------------------
importances = pd.Series(best_model.feature_importances_, index=X.columns)
top15 = importances.sort_values(ascending=False).head(15)

print("\nTop 15 most important features:")
print(top15)

fig, ax = plt.subplots(figsize=(8, 6))
top15.sort_values().plot(kind="barh", ax=ax, color="#C81E2C")
ax.set_title("Top 15 Feature Importance — XGBoost")
ax.set_xlabel("Importance")
plt.tight_layout()
plt.savefig("data/feature_importance.png", dpi=150)
print("Saved feature importance chart to data/feature_importance.png")

# ---------------------------------------------------------------
# 4. Save the tuned model + everything the app needs to rebuild a
#    matching input row at prediction time (same one-hot columns,
#    dropdown options, and realistic numeric ranges)
# ---------------------------------------------------------------
joblib.dump({
    "model": best_model,
    "feature_columns": list(X.columns),
    "cat_cols": cat_cols,
    "cat_options": cat_options,
    "num_cols": num_cols,
    "num_ranges": num_ranges,
    "vague_pitch_words": VAGUE_PITCH_WORDS,
    "test_accuracy": accuracy_score(y_test, y_pred),
}, "data/model.pkl")
print("Saved trained model + metadata to data/model.pkl")
