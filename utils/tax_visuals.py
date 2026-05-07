import matplotlib.pyplot as plt


def plot_tax_comparison(old_tax, new_tax):
    labels = ["Old Regime", "New Regime"]
    values = [old_tax, new_tax]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values)

    ax.set_ylabel("Tax (₹)")
    ax.set_title("Tax Comparison")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"₹{height:,.0f}",
            ha="center",
            va="bottom"
        )

    return fig


def plot_scenario_comparison(scenarios):
    labels = [s["scenario"] for s in scenarios]
    old_values = [s["old_tax"] for s in scenarios]
    new_values = [s["new_tax"] for s in scenarios]

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    old_bars = ax.bar([i - width/2 for i in x], old_values, width, label="Old Regime")
    new_bars = ax.bar([i + width/2 for i in x], new_values, width, label="New Regime")

    ax.set_ylabel("Tax (₹)")
    ax.set_title("Tax Simulation Scenarios")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bars in [old_bars, new_bars]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"₹{height:,.0f}",
                ha="center",
                va="bottom",
                fontsize=9
            )

    plt.tight_layout()
    return fig