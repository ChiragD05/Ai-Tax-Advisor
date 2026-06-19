import plotly.graph_objects as go


def plot_tax_comparison(old_tax, new_tax):
    labels = ["Old Regime", "New Regime"]
    values = [old_tax, new_tax]

    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker_color=["#4F46E5", "#10B981"],  # Indigo & Emerald Green
            text=[f"₹{old_tax:,.2f}", f"₹{new_tax:,.2f}"],
            textposition='auto',
            hoverinfo='y',
        )
    ])

    fig.update_layout(
        title={
            'text': "Tax Regime Comparison",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        yaxis_title="Tax Liability (₹)",
        template="plotly_white",
        height=320,
        margin=dict(l=40, r=40, t=50, b=20),
        yaxis=dict(tickformat=",.0f")
    )

    return fig


def plot_scenario_comparison(scenarios):
    labels = [s["scenario"] for s in scenarios]
    old_values = [s["old_tax"] for s in scenarios]
    new_values = [s["new_tax"] for s in scenarios]

    fig = go.Figure(data=[
        go.Bar(name='Old Regime', x=labels, y=old_values, marker_color='#4F46E5'),
        go.Bar(name='New Regime', x=labels, y=new_values, marker_color='#10B981')
    ])

    fig.update_layout(
        barmode='group',
        title={
            'text': "Tax Simulation Scenarios",
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        yaxis_title="Tax Liability (₹)",
        template="plotly_white",
        height=400,
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(tickformat=",.0f")
    )

    return fig