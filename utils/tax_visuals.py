import matplotlib.pyplot as plt


def plot_tax_comparison(old_tax, new_tax):

    labels = ["Old Regime", "New Regime"]
    values = [old_tax, new_tax]

    fig, ax = plt.subplots(figsize=(6, 4))

    bars = ax.bar(labels, values)

    ax.set_ylabel("Tax (₹)")
    ax.set_title("Tax Comparison")

    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.3
    )

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