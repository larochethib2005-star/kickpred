#!/usr/bin/env python3
"""
Week 2 — Exploratory Data Analysis for the Kickstarter crowdfunding
success prediction project.

For each candidate feature (category, goal, duration, staff_pick), we
check whether it actually relates to campaign success, and save a bar
chart so the relationship is visible, not just printed as numbers.
"""
import pandas as pd
import matplotlib.pyplot as plt

RED = "#C81E2C"

df = pd.read_csv("data/Kickstarter_clean.csv")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())


def plot_success_rate(series, title, filename, xlabel=""):
    """Bar chart of success rate (%) per group, saved as a PNG."""
    fig, ax = plt.subplots(figsize=(8, 5))
    (series * 100).plot(kind="bar", ax=ax, color=RED)
    ax.set_title(title)
    ax.set_ylabel("Success rate (%)")
    ax.set_xlabel(xlabel)
    ax.set_ylim(0, 100)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(f"data/{filename}", dpi=150)
    plt.close(fig)
    print(f"Saved data/{filename}")


# ---------------------------------------------------------------
# 1. Success rate by category
# ---------------------------------------------------------------
success_by_category = df.groupby("category")["target"].mean().sort_values(ascending=False)
print("\n--- Success rate by category ---")
print(success_by_category)
plot_success_rate(success_by_category, "Success Rate by Category",
                    "eda_category.png")

# ---------------------------------------------------------------
# 2. Success rate by funding goal bucket
# ---------------------------------------------------------------
df["goal_bucket"] = pd.cut(
    df["goal"], bins=[0, 1000, 5000, 10000, 50000, 100000, float("inf")],
    labels=["<1k", "1k-5k", "5k-10k", "10k-50k", "50k-100k", ">100k"],
)
success_by_goal = df.groupby("goal_bucket", observed=True)["target"].mean()
print("\n--- Success rate by goal bucket ---")
print(success_by_goal)
plot_success_rate(success_by_goal, "Success Rate by Funding Goal",
                    "eda_goal.png", xlabel="Funding goal (USD)")

# ---------------------------------------------------------------
# 3. Success rate by campaign duration bucket
#    (counts printed alongside: a group's rate is only meaningful
#    if there are enough campaigns behind it)
# ---------------------------------------------------------------
df["duration_bucket"] = pd.cut(
    df["duration_days"], bins=[0, 15, 30, 45, 60, float("inf")],
    labels=["<15d", "15-30d", "30-45d", "45-60d", ">60d"],
)
print("\n--- Campaign count by duration bucket (sanity check) ---")
print(df["duration_bucket"].value_counts())
success_by_duration = df.groupby("duration_bucket", observed=True)["target"].mean()
print("\n--- Success rate by duration bucket ---")
print(success_by_duration)
plot_success_rate(success_by_duration, "Success Rate by Campaign Duration",
                    "eda_duration.png", xlabel="Campaign duration")

# ---------------------------------------------------------------
# 4. Success rate by staff pick
# ---------------------------------------------------------------
print("\n--- Campaign count by staff_pick (sanity check) ---")
print(df["staff_pick"].value_counts())
success_by_staffpick = df.groupby("staff_pick")["target"].mean()
success_by_staffpick.index = ["Not picked", "Staff Pick"]
print("\n--- Success rate by staff pick ---")
print(success_by_staffpick)
plot_success_rate(success_by_staffpick, "Success Rate by Staff Pick",
                    "eda_staff_pick.png")

# ---------------------------------------------------------------
# 5. Success rate by year — does the platform behave differently
#    over time? (2009 and 2026 are partial years, kept but note
#    their low counts when reading the chart)
# ---------------------------------------------------------------
print("\n--- Campaign count by year (sanity check) ---")
print(df["year"].value_counts().sort_index())
success_by_year = df.groupby("year")["target"].mean()
print("\n--- Success rate by year ---")
print(success_by_year)
plot_success_rate(success_by_year, "Success Rate by Year (2009-2026)",
                    "eda_year.png", xlabel="Year")

print("\nDone. 5 charts saved in data/.")
