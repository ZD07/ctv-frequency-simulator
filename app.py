import streamlit as st
import numpy as np
import plotly.graph_objects as go
import copy

from simulator.models import Platform, Campaign
from simulator.defaults import get_default_platforms, DEFAULT_OVERLAP
from simulator.engine import run_simulation, analyse

st.set_page_config(page_title="CTV Frequency Simulator", layout="wide")

st.title("CTV Cross-Platform Frequency Simulator")
st.caption(
    "Model household ad frequency exposure across CTV platforms. "
    "Cross-platform frequency remains largely uncontrollable at the planning stage — "
    "solutions like data clean rooms exist but require enterprise infrastructure and "
    "platform buy-in that most planning teams don't have access to. "
    "This tool makes the problem visible before you spend."
)

# ── Section 1: Platform Inputs ────────────────────────────────────────────────

st.header("1. Platform Setup")
st.caption("Configure each platform's audience size, budget, CPM, and per-platform frequency cap.")

defaults = get_default_platforms()
platform_inputs = []

header_cols = st.columns([2, 2, 2, 2, 2])
for col, h in zip(header_cols, ["Platform", "Universe (HHs)", "Budget (£)", "CPM (£)", "Freq Cap"]):
    col.markdown(f"**{h}**")

for p in defaults:
    cols = st.columns([2, 2, 2, 2, 2])
    name     = cols[0].text_input("Platform name", value=p.name, key=f"name_{p.name}", label_visibility="collapsed")
    universe = cols[1].number_input("Universe", value=p.universe_size, step=500_000, key=f"univ_{p.name}", label_visibility="collapsed")
    budget   = cols[2].number_input("Budget", value=float(p.budget), step=1_000.0, key=f"budget_{p.name}", label_visibility="collapsed")
    cpm      = cols[3].number_input("CPM", value=float(p.cpm), step=0.5, key=f"cpm_{p.name}", label_visibility="collapsed")
    freq_cap = cols[4].number_input("Freq cap", value=p.frequency_cap, min_value=1, max_value=20, step=1, key=f"cap_{p.name}", label_visibility="collapsed")

    platform_inputs.append(Platform(
        name=name,
        universe_size=int(universe),
        budget=float(budget),
        cpm=float(cpm),
        frequency_cap=int(freq_cap),
    ))

# ── Section 2: Overlap Matrix ─────────────────────────────────────────────────

st.header("2. Platform Overlap Assumptions")
st.caption(
    "Estimated % of households on platform A who are also on platform B. "
    "Pre-populated with UK estimates derived from BARB and Ofcom data (2024/25). "
    "Treat as modelled assumptions — platforms do not publish overlap data publicly."
)

n = len(platform_inputs)
overlap = copy.deepcopy(DEFAULT_OVERLAP[:n, :n])

for i in range(n):
    cols = st.columns(n + 1)
    cols[0].markdown(f"**{platform_inputs[i].name}**")
    for j in range(n):
        if i == j:
            cols[j + 1].markdown("—")
        elif j > i:
            val = cols[j + 1].number_input(
                f"{platform_inputs[i].name}/{platform_inputs[j].name}",
                min_value=0.0, max_value=1.0,
                value=float(DEFAULT_OVERLAP[i][j]),
                step=0.01,
                key=f"overlap_{i}_{j}",
                label_visibility="collapsed"
            )
            overlap[i][j] = val
            overlap[j][i] = val
        else:
            cols[j + 1].markdown(f"`{overlap[i][j]:.2f}`")

# ── Section 3: Campaign Settings ─────────────────────────────────────────────

st.header("3. Campaign Settings")
col1, col2 = st.columns(2)
target_cap = col1.number_input(
    "Target cross-platform frequency cap (max impressions per household)",
    min_value=1, max_value=30, value=5, step=1
)
n_sims = col2.selectbox(
    "Simulation precision",
    options=[50_000, 100_000, 200_000],
    index=1,
    format_func=lambda x: f"{x:,} households"
)

# ── Run ───────────────────────────────────────────────────────────────────────

run = st.button("Run Simulation", type="primary", use_container_width=True)

if run:
    campaign = Campaign(
        platforms=platform_inputs,
        overlap_matrix=overlap,
        target_frequency_cap=int(target_cap),
        n_simulations=int(n_sims)
    )

    with st.spinner("Simulating household exposures..."):
        frequencies = run_simulation(campaign)
        results = analyse(frequencies, campaign)

    if not results:
        st.error("Simulation returned no results. Check your inputs.")
    else:
        st.header("4. Results")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Unique Reach", f"{results['reach_pct']:.1f}%",
                  help="% of total simulated households reached at least once")
        m2.metric("Avg Cross-Platform Frequency", f"{results['avg_frequency']:.1f}x",
                  help="Average number of times a reached household saw an ad")
        m3.metric("Over-Exposed Households", f"{results['over_exposure_pct']:.1f}%",
                  help=f"% of reached households who exceeded your {target_cap}x frequency cap")
        m4.metric("Estimated Wasted Spend", f"£{results['wasted_spend']:,.0f}",
                  help=f"Budget spent on impressions beyond the {target_cap}x cap ({results['waste_pct_of_budget']:.1f}% of total)")

        st.subheader("Frequency Distribution")
        freq_dist = results["frequency_distribution"]
        x = list(range(len(freq_dist)))
        y = freq_dist

        colours = ["#ef4444" if xi > target_cap else "#3b82f6" for xi in x]

        fig = go.Figure(go.Bar(
            x=x, y=y,
            marker_color=colours,
            hovertemplate="Frequency: %{x}<br>Households: %{y:,}<extra></extra>"
        ))
        fig.add_vline(
            x=target_cap + 0.5,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Cap: {target_cap}x",
            annotation_position="top right"
        )
        fig.update_layout(
            xaxis_title="Total impressions per household",
            yaxis_title="Simulated households",
            showlegend=False,
            plot_bgcolor="white",
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔵 Within cap  🔴 Over-exposed")

        st.subheader("Per-Platform Breakdown")
        pcols = st.columns(len(platform_inputs))
        for col, p in zip(pcols, platform_inputs):
            col.metric(p.name, f"£{p.budget:,.0f}")
            col.caption(
                f"~{p.capped_reach / 1_000_000:.1f}M HHs reached\n"
                f"Avg freq: {p.avg_frequency:.1f}x\n"
                f"CPM: £{p.cpm}"
            )
