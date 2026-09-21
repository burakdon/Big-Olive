"""Sankey diagram: olive oil flowing into Italy (by source) and out of Italy
(by destination). This is the direct-evidence complement to the
credit-gap charts -- instead of inferring re-export from aggregate
mismatches, this shows the actual bilateral flows.

Reads data/raw/comtrade_olive_oil_flows.csv, produced by
src/data_collection/fetch_comtrade_flows.py (must be run locally first --
see that script's docstring for setup).

Produces outputs/figures/combined/italy_flow_sankey.html (interactive)
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def find_project_root():
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "README.md").exists() and (parent / "data").exists():
            return parent
    raise FileNotFoundError("Project root could not be found.")


def build(latest_year: int | None = None, top_n_partners: int = 8):
    root = find_project_root()
    raw_path = root / "data" / "raw" / "comtrade_olive_oil_flows.csv"

    if not raw_path.exists():
        raise SystemExit(
            f"{raw_path} not found.\n"
            "Run src/data_collection/fetch_comtrade_flows.py locally first "
            "(needs a Comtrade API key and real internet access -- see its docstring)."
        )

    df = pd.read_csv(raw_path)

    if latest_year is None:
        latest_year = int(df["refYear"].max())
    df = df[df["refYear"] == latest_year]

    imports = df[df["flow_label"] == "import"].copy()
    exports = df[df["flow_label"] == "export"].copy()

    # Aggregate by partner in case of multiple HS subcodes
    imports = imports.groupby("partnerDesc", as_index=False)["netWgt"].sum()
    exports = exports.groupby("partnerDesc", as_index=False)["netWgt"].sum()

    imports = imports[imports.partnerDesc != "World"].sort_values("netWgt", ascending=False).head(top_n_partners)
    exports = exports[exports.partnerDesc != "World"].sort_values("netWgt", ascending=False).head(top_n_partners)

    # Build node list: sources -> Italy -> destinations.
    # A country can appear on both sides (e.g. Spain is both a top import
    # source and a top export destination for Italy). Don't use a single
    # {name: index} dict for lookups -- if the same name appears in both
    # `sources` and `destinations`, a shared dict silently overwrites the
    # first index with the second. Use positional indices tied to each
    # list's own row order instead.
    sources = imports.partnerDesc.tolist()
    destinations = exports.partnerDesc.tolist()
    nodes = sources + ["Italy"] + destinations

    n_sources = len(sources)
    italy_idx = n_sources
    dest_offset = n_sources + 1

    link_source, link_target, link_value = [], [], []
    for i, (_, row) in enumerate(imports.iterrows()):
        link_source.append(i)
        link_target.append(italy_idx)
        link_value.append(row.netWgt)
    for j, (_, row) in enumerate(exports.iterrows()):
        link_source.append(italy_idx)
        link_target.append(dest_offset + j)
        link_value.append(row.netWgt)

    node_colors = (
        ["#c0392b"] * len(sources) +
        ["#2d6a4f"] +
        ["#3d5a80"] * len(destinations)
    )

    # Pin explicit x/y positions so Plotly's auto-arrangement can't fold a
    # same-named node (e.g. Spain on both sides) into a loop.
    # Evenly spaced centers were wrong: node height is proportional to
    # flow, so Spain's bar covered the smaller partners. Stack by value
    # with a gap so the ribbons actually separate.
    def stacked_centers(weights, edge=0.03, gap=0.055):
        weights = [float(w) for w in weights]
        n = len(weights)
        if n == 0:
            return []
        if n == 1:
            return [0.5]
        total = sum(weights) or 1.0
        available = max(1.0 - 2 * edge - gap * (n - 1), 0.2)
        heights = [available * (w / total) for w in weights]
        centers = []
        cursor = edge
        for height in heights:
            centers.append(cursor + height / 2.0)
            cursor += height + gap
        return centers

    src_y = stacked_centers(imports["netWgt"].tolist())
    dst_y = stacked_centers(exports["netWgt"].tolist())
    node_x = [0.02] * len(sources) + [0.5] + [0.98] * len(destinations)
    node_y = src_y + [0.5] + dst_y

    # Keep a gap on both sides of the Sankey so labels sit in the margin,
    # not on top of the flow bands. Plotly always draws node labels toward
    # the links, which is what caused the overlap.
    domain_x = [0.18, 0.78]
    domain_y = [0.04, 0.86]

    fig = go.Figure(data=[go.Sankey(
        arrangement="fixed",
        domain=dict(x=domain_x, y=domain_y),
        textfont=dict(size=1, color="rgba(0,0,0,0)"),
        node=dict(
            pad=28, thickness=16,
            line=dict(color="black", width=0.5),
            label=[""] * len(nodes),
            customdata=nodes,
            color=node_colors,
            x=node_x, y=node_y,
            hovertemplate="%{customdata}<extra></extra>",
        ),
        link=dict(source=link_source, target=link_target, value=link_value,
                  color="rgba(160,160,160,0.35)"),
    )])

    # Empirically, smaller node y renders closer to the top of this chart.
    def paper_y(node_y_value):
        return domain_y[1] - node_y_value * (domain_y[1] - domain_y[0])

    display_names = {
        "Other Asia, nes": "Other Asia",
        "United Kingdom": "UK",
    }
    label_font = dict(family="Georgia, serif", size=13, color="#1a1a1a")
    annotations = []
    for name, y in zip(sources, src_y):
        annotations.append(dict(
            x=domain_x[0] - 0.012,
            y=paper_y(y),
            xref="paper",
            yref="paper",
            text=display_names.get(name, name),
            showarrow=False,
            xanchor="right",
            yanchor="middle",
            font=label_font,
        ))
    for name, y in zip(destinations, dst_y):
        annotations.append(dict(
            x=domain_x[1] + 0.012,
            y=paper_y(y),
            xref="paper",
            yref="paper",
            text=display_names.get(name, name),
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=label_font,
        ))
    annotations.append(dict(
        x=0.5,
        y=paper_y(0.5),
        xref="paper",
        yref="paper",
        text="Italy",
        showarrow=False,
        xanchor="center",
        yanchor="middle",
        font=dict(family="Georgia, serif", size=14, color="#1a1a1a"),
        bgcolor="rgba(255,255,255,0.9)",
        borderpad=4,
    ))

    fig.update_layout(
        title_text=f"Olive Oil In, Olive Oil Out: Italy's Trade Flows, {latest_year}<br>"
                    f"<sup>Left = where Italy's imported oil comes from. Right = where Italy's exports go.</sup>",
        font=dict(family="Georgia, serif", size=13),
        height=820,
        width=1100,
        margin=dict(l=30, r=30, t=90, b=30),
        annotations=annotations,
    )

    out_dir = root / "outputs" / "figures" / "combined"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "italy_flow_sankey.html"
    fig.write_html(out_path, include_plotlyjs="cdn")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    build()
