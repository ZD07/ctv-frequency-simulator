# CTV Cross-Platform Frequency Simulator

A tool for modelling household ad frequency exposure across CTV streaming platforms.

## The Problem

Frequency capping in CTV is broken. There's no shared identity layer across streaming platforms — a household can see the same ad twelve times across YouTube, Netflix, Amazon, and Disney+ in a single weekend, and the advertiser has no visibility into it. Walled gardens don't share exposure data. Frequency caps set inside each DSP are per-platform only.

This tool makes that problem visible and quantifiable.

## What It Does

Given a set of CTV platforms, budget allocations, CPMs, and household overlap assumptions, the simulator models the likely cross-platform frequency distribution across a synthetic population of households. It surfaces:

- Estimated unique reach across all platforms combined
- Average cross-platform frequency per reached household
- The proportion of households likely to be over-exposed beyond a defined cap
- Estimated wasted spend from excess frequency

## How It Works

The simulation uses a **Gaussian copula** to model correlated household subscription probabilities across platforms. This approach allows overlap between platform audiences to be captured without requiring actual identity-level data — which mirrors the real-world constraint the industry faces.

For each simulated household, the model determines which platforms they're reachable on (using correlated probabilities derived from the overlap matrix), then samples a per-platform impression frequency using a Poisson distribution capped at the platform's frequency limit. The total cross-platform frequency is the sum across all platforms.

Overlap estimates are pre-populated with UK figures derived from BARB and Ofcom data (2024) and can be adjusted.

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Deploy for free on [Streamlit Community Cloud](https://streamlit.io/cloud) by connecting your GitHub repo.

## Limitations & Caveats

- This is a **simulation**, not a measurement tool. It models what is likely, not what is happening.
- Overlap estimates are approximations based on panel data. Actual overlaps vary by campaign targeting, daypart, and content genre.
- The tool does not account for household composition (multiple viewers per device) or cross-device exposure.
- It does not model frequency recency — five exposures in one day and five over a month are treated the same.

These are the same limitations faced by every planning tool in the market right now. The difference is this makes them explicit.

## Built By

Zia Din — [linkedin.com/in/zia-din](https://linkedin.com/in/zia-din) | [github.com/ZD07](https://github.com/ZD07)
