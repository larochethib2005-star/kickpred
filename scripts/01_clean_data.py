#!/usr/bin/env python3
"""
Week 1 — Data cleaning for the Kickstarter crowdfunding success prediction project.

Logic mirrors the reference GitHub project
(rishabhRsinghvi/CrowdFunding-Campaign-Success-Prediction, Introduction_and_Data_Cleaning.ipynb),
applied to our own, larger and more recent dataset
("Kickstarter Full Campaigns_694062_25_April_2026.csv").
"""
import re
import pandas as pd
import numpy as np
from nltk.sentiment import SentimentIntensityAnalyzer

RAW_PATH = "data/raw/kickstarter_full_campaigns.csv"
OUT_PATH = "data/Kickstarter_clean.csv"

# Words found (via word-frequency analysis of blurbs) to be more common in
# FAILED campaigns — generic, vague pitch language ("I want to create
# something for people") rather than a concrete product description.
# Words tied to specific product types (e.g. "tabletop", "album") were
# excluded: they just re-encode `category`, which the model already has.
VAGUE_PITCH_WORDS = ["want", "create", "creating", "people", "make", "like", "business", "online", "life"]

print("Loading raw data...")
df = pd.read_csv(RAW_PATH, low_memory=False)
print(f"Raw shape: {df.shape}")

# ---------------------------------------------------------------
# 1. Select columns of interest (same intent as the reference repo)
# ---------------------------------------------------------------
col_names = [
    "id", "backers_count", "blurb", "category_name", "category_parent_name",
    "country", "created_at", "deadline", "goal", "launched_at", "location_state",
    "location_type", "name", "staff_pick", "state", "static_usd_rate", "usd_pledged",
]
df = df[col_names]

# ---------------------------------------------------------------
# 2. Keep only finished campaigns: successful or failed
# ---------------------------------------------------------------
print("\nState counts (before filtering):")
print(df["state"].value_counts())

df = df.query("state in ['successful', 'failed']").copy()
df["target"] = (df["state"] == "successful").astype(int)
df.drop(columns=["state"], inplace=True)
print(f"\nAfter keeping only successful/failed: {df.shape}")

# ---------------------------------------------------------------
# 3. Remove duplicate campaigns (same id)
# ---------------------------------------------------------------
n_dupes = df.duplicated("id").sum()
print(f"Duplicate ids found: {n_dupes}")
df = df.drop_duplicates("id", keep="first").reset_index(drop=True)
df.drop(columns=["id"], inplace=True)
print(f"After removing duplicates: {df.shape}")

# ---------------------------------------------------------------
# 4. Blurb & name length (text proxy features, as in the reference repo)
# ---------------------------------------------------------------
df["blurb_length"] = df["blurb"].str.split().str.len()
df["blurb_length"] = df["blurb_length"].fillna(0).astype(int)
df["name_length"] = df["name"].str.split().str.len()
df["name_length"] = df["name_length"].fillna(0).astype(int)

# ---------------------------------------------------------------
# 4b. NLP features from the blurb text: sentiment score (VADER) +
#     presence of "vague pitch" keywords (see list above)
# ---------------------------------------------------------------
print("\nComputing sentiment scores (this takes a minute)...")
sia = SentimentIntensityAnalyzer()
blurb_filled = df["blurb"].fillna("")
df["sentiment"] = blurb_filled.apply(lambda t: sia.polarity_scores(t)["compound"])

blurb_lower = blurb_filled.str.lower()
for word in VAGUE_PITCH_WORDS:
    df[f"kw_{word}"] = blurb_lower.str.contains(rf"\b{word}\b", regex=True).astype(int)

df.drop(columns=["blurb", "name"], inplace=True)

# ---------------------------------------------------------------
# 5. Category / subcategory
#    (our dataset already has clean category_name / category_parent_name
#     columns, unlike the repo's which needed JSON parsing)
# ---------------------------------------------------------------
df.rename(columns={
    "category_parent_name": "category",
    "category_name": "subcategory",
}, inplace=True)
df["category"] = df["category"].fillna(df["subcategory"])
# When subcategory itself is missing, fall back to the main category
# (118,321 rows) instead of dropping ~20% of the dataset
df["subcategory"] = df["subcategory"].fillna(df["category"])
df["category"] = df["category"].str.strip().str.title()
df["subcategory"] = df["subcategory"].str.strip().str.title()

# ---------------------------------------------------------------
# 5a. Group rare subcategories into "Other"
#     161 subcategories exist; 35 of them have under 500 campaigns
#     (only 1.7% of rows). One-hot encoding all 161 creates mostly
#     empty, noisy columns that likely worsen overfitting on tree
#     models (Decision Tree / Random Forest) without adding real
#     signal. Grouping the rare ones keeps 126 meaningful categories.
# ---------------------------------------------------------------
MIN_SUBCATEGORY_COUNT = 500
subcat_counts = df["subcategory"].value_counts()
rare_subcats = subcat_counts[subcat_counts < MIN_SUBCATEGORY_COUNT].index
n_grouped = df["subcategory"].isin(rare_subcats).sum()
df["subcategory"] = df["subcategory"].where(~df["subcategory"].isin(rare_subcats), "Other")
print(f"\nGrouped {len(rare_subcats)} rare subcategories "
      f"({n_grouped} rows, {n_grouped/len(df)*100:.1f}%) into 'Other'")
print(f"Subcategories remaining: {df['subcategory'].nunique()}")

# ---------------------------------------------------------------
# 5b. Location state / type (verified: ~99.7% filled across ALL
#     countries, not just the US, e.g. GB -> England/Scotland/Wales,
#     CA -> provinces, DE -> Lander, FR -> regions)
# ---------------------------------------------------------------
df["location_state"] = df["location_state"].fillna("Unknown")
df["location_type"] = df["location_type"].fillna("Unknown")

# ---------------------------------------------------------------
# 6. Dates -> duration, year, month, creation-to-launch gap
#    (timestamps are Unix seconds stored as numbers; casting to numeric
#     first avoids pandas misreading them as date strings)
# ---------------------------------------------------------------
launched_raw = pd.to_numeric(df["launched_at"], errors="coerce")
deadline_raw = pd.to_numeric(df["deadline"], errors="coerce")
created_raw = pd.to_numeric(df["created_at"], errors="coerce")
df["launched_at"] = pd.to_datetime(launched_raw, unit="s", errors="coerce")
df["deadline"] = pd.to_datetime(deadline_raw, unit="s", errors="coerce")
df["created_at"] = pd.to_datetime(created_raw, unit="s", errors="coerce")

n_before = len(df)
df = df.dropna(subset=["launched_at", "deadline"])
print(f"Rows dropped for invalid dates: {n_before - len(df)}")

df["duration_days"] = (df["deadline"] - df["launched_at"]).dt.days
df["year"] = df["launched_at"].dt.year
df["month"] = df["launched_at"].dt.month
# New feature: how long the creator prepared before launching
df["prep_days"] = (df["launched_at"] - df["created_at"]).dt.days
df["prep_days"] = df["prep_days"].clip(lower=0)  # guard against bad timestamps
df.drop(columns=["launched_at", "deadline", "created_at"], inplace=True)

# ---------------------------------------------------------------
# 7. Convert goal to USD (same logic as the reference repo)
# ---------------------------------------------------------------
df["goal"] = (df["goal"] * df["static_usd_rate"]).round(2)
df.drop(columns=["static_usd_rate"], inplace=True)

# ---------------------------------------------------------------
# 7b. Drop rows with missing goal (<1% of rows) — goal is our most
#     important feature, so we don't want to guess/impute it.
#     Note: the gap comes from missing static_usd_rate (exchange rate),
#     which only shows up once goal is converted to USD.
# ---------------------------------------------------------------
n_before = len(df)
df = df.dropna(subset=["goal"])
print(f"Rows dropped for missing goal: {n_before - len(df)}")

# ---------------------------------------------------------------
# 8. staff_pick -> 0/1
# ---------------------------------------------------------------
df["staff_pick"] = df["staff_pick"].astype(bool).astype(int)

# ---------------------------------------------------------------
# 9. Final sanity checks
# ---------------------------------------------------------------
print("\nFinal columns:", list(df.columns))
print("Final shape:", df.shape)
print("\nTarget balance:")
print(df["target"].value_counts(normalize=True).round(4) * 100)
print("\nMissing values per column:")
print(df.isna().sum()[df.isna().sum() > 0])

df.to_csv(OUT_PATH, index=False)
print(f"\nSaved cleaned dataset to: {OUT_PATH}")
