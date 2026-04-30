import streamlit as st
import numpy as np
import plotly.graph_objects as go
import copy

from simulator.models import Platform, Campaign
from simulator.defaults import get_default_platforms, DEFAULT_OVERLAP, PLATFORM_NAMES
from simulator.engine import run_simulation, run_euid_simulation, analyse

st.set_page_config(page_title="CTV Frequency Simulator", layout="wide")

st.title("CTV Cross-Platform Frequency Simulator")
st.caption(
    "Model household ad frequency exposure across CTV platforms. "
    "Cross-platform frequency remains largely uncontrollable at the planning stage — "
    "solutions like data clean rooms and EUID exist, but require enterprise infrastructure "
    "and platform buy-in that most planning teams don't have access to. "
    "This tool makes the problem visible before you spend."
)

# ── Section 1: Platform Inputs ────────────────────────────────────────────────

st.header("1. Platform Setup")
st.caption(
    "Configure each platform's audience size, budget, CPM, per-platform frequency cap, "
    "and estimated EUID adoption rate. "
    "Netflix is pre-set to 0% EUID — it operates a proprietary ad stack with no participation "
    "in open identity frameworks."
)

defaults = get_default_platforms()
platform_inputs = []

header_cols = st.columns([2, 2, 2, 2, 2, 2])
for col, h in zip(header_cols, ["Platform", "Universe (HHs)", "Budget (£)", "CPM (£)", "Freq Cap", "EUID %"]):
    col.markdown(f"**{h}**")

for p in defaults:
    cols = st.columns([2, 2, 2, 2, 2, 2])
    name      = cols[0].text_input("", value=p.name, key=f"name_{p.name}", label_visibility="collapsed")
    universe  = cols[1].number_input("", value=p.universe_size, step=500_000, key=f"univ_{p.name}", label_visibility="collapsed")
    budget    = cols[2].number_input("", value=float(p.budget), step=1_000.0, key=f"budget_{p.name}", label_visibility="collapsed")
    cpm       = cols[3].number_input("", value=float(p.cpm), step=0.5, key=f"cpm_{p.name}", label_visibility="collapsed")
    freq_cap  = cols[4].number_input("", value=p.frequency_cap, min_value=1, max_value=20, step=1, key=f"cap_{p.name}", label_visibility="collapsed")

    # Netflix EUID locked to 0
    if p.name == "Netflix":
        cols[5].markdown("🔒 0%")
        euid = 0.0
    else:
        euid = cols[5].number_input(
            "", value=float(round(p.euid_adoption_rate * 100)),
            min_value=0.0, max_value=100.0, step=5.0,
            key=f"euid_{p.name}", label_visibility="collapsed"
        ) / 100.0

    platform_inputs.append(Platform(
        name=name,
        universe_size=int(universe),
        budget=float(budget),
        cpm=float(cpm),
        frequency_cap=int(freq_cap),
        euid_adoption_rate=float(euid),
    ))

# ── Section 2: Overlap Matrix ─────────────────────────────────────────────────

st.header("2. Platform Overlap Assumptions")
st.caption(
    "Estimated % of households on platform A who are also on platform B. "
    "Pre-populated with UK estimates from BARB and Ofcom data (2024/25). "
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
        baseline_freq  = run_simulation(campaign)
        euid_freq      = run_euid_simulation(campaign)
        baseline       = analyse(baseline_freq, campaign)
        euid_results   = analyse(euid_freq, campaign)

    if not baseline:
        st.error("Simulation returned no results. Check your inputs.")
    else:
        st.header("4. Results")

        # ── Headline metrics ──────────────────────────────────────────────────
        tab1, tab2 = st.tabs(["Current State (No Coordination)", "EUID Scenario"])

        with tab1:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Unique Reach", f"{baseline['reach_pct']:.1f}%")
            m2.metric("Avg Cross-Platform Frequency", f"{baseline['avg_frequency']:.1f}x")
            m3.metric("Over-Exposed Households", f"{baseline['over_exposure_pct']:.1f}%")
            m4.metric("Estimated Wasted Spend", f"£{baseline['wasted_spend']:,.0f}",
                      help=f"{baseline['waste_pct_of_budget']:.1f}% of total budget")

        with tab2:
            waste_delta = euid_results['wasted_spend'] - baseline['wasted_spend']
            overexp_delta = euid_results['over_exposure_pct'] - baseline['over_exposure_pct']

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Unique Reach", f"{euid_results['reach_pct']:.1f}%")
            m2.metric("Avg Cross-Platform Frequency", f"{euid_results['avg_frequency']:.1f}x")
            m3.metric("Over-Exposed Households", f"{euid_results['over_exposure_pct']:.1f}%",
                      delta=f"{overexp_delta:+.1f}pp", delta_color="inverse")
            m4.metric("Estimated Wasted Spend", f"£{euid_results['wasted_spend']:,.0f}",
                      delta=f"£{waste_delta:+,.0f}", delta_color="inverse")

            avg_euid = np.mean([p.euid_adoption_rate for p in platform_inputs]) * 100
            st.caption(
                f"Average EUID adoption across this buy: **{avg_euid:.0f}%**. "
                "Netflix contributes 0% EUID coverage. "
                "Impressions from EUID-enabled inventory are coordinated under a shared cap; "
                "non-EUID impressions (including all Netflix inventory) accumulate independently."
            )

        # ── Frequency distribution chart ──────────────────────────────────────
        st.subheader("Frequency Distribution")

        baseline_dist = baseline["frequency_distribution"]
        euid_dist     = euid_results["frequency_distribution"]
        max_x = max(len(baseline_dist), len(euid_dist))
        x = list(range(max_x))

        baseline_y = baseline_dist + [0] * (max_x - len(baseline_dist))
        euid_y     = euid_dist     + [0] * (max_x - len(euid_dist))

        colours = ["#ef4444" if xi > target_cap else "#3b82f6" for xi in x]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x, y=baseline_y,
            name="Current state",
            marker_color=colours,
            opacity=0.85,
            hovertemplate="Frequency: %{x}<br>Households: %{y:,}<extra>Current</extra>"
        ))
        fig.add_trace(go.Bar(
            x=x, y=euid_y,
            name="EUID scenario",
            marker_color=["#f97316" if xi > target_cap else "#22c55e" for xi in x],
            opacity=0.60,
            hovertemplate="Frequency: %{x}<br>Households: %{y:,}<extra>EUID</extra>"
        ))
        fig.add_vline(
            x=target_cap + 0.5,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Cap: {target_cap}x",
            annotation_position="top right"
        )
        fig.update_layout(
            barmode="overlay",
            xaxis_title="Total impressions per household",
            yaxis_title="Simulated households",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="white",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🔵 Current: within cap   🔴 Current: over-exposed   🟢 EUID: within cap   🟠 EUID: over-exposed")

        # ── EUID coverage breakdown ───────────────────────────────────────────
        st.subheader("EUID Coverage by Platform")
        st.caption("How much of each platform's inventory is addressable via EUID in this scenario.")

        ecols = st.columns(len(platform_inputs))
        for col, p in zip(ecols, platform_inputs):
            pct = p.euid_adoption_rate * 100
            bar = "🟩" * int(pct // 20) + "⬜" * (5 - int(pct // 20))
            col.metric(p.name, f"{pct:.0f}%")
            col.caption(bar)

        # ── Per-platform breakdown ─────────────────────────────────────────────
        st.subheader("Per-Platform Budget Breakdown")
        pcols = st.columns(len(platform_inputs))
        for col, p in zip(pcols, platform_inputs):
            col.metric(p.name, f"£{p.budget:,.0f}")
            col.caption(
                f"~{p.capped_reach / 1_000_000:.1f}M HHs reached\n"
                f"Avg freq: {p.avg_frequency:.1f}x\n"
                f"CPM: £{p.cpm}"
            )
