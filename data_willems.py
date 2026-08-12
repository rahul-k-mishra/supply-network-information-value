"""Loader for the Willems (2008) MSOM real-world multi-echelon dataset.

The dataset (38 supply chains implemented in practice, up to ~2,025 stages) is
publicly available from the MSOM e-companion / the author's site as an Excel
workbook. Download it once and pass --willems-file.

Design = REAL TOPOLOGY + DOCUMENTED SIMULATED OVERLAY:
  * Nodes, edges, costs, classifications: taken from the data (real).
  * Conjunctive structure: assembly BOMs -- inputs of DIFFERENT classifications
    are distinct required categories; same-classification parallel suppliers of
    a node are treated as substitutable within one category (tunable via
    strict_conjunctive=True, which makes every input its own category).
  * Regions: not present in the data; assigned by seeded community detection
    (or by classification with overlay="classification"). Multiple overlay
    seeds per chain = replication units. This must be stated in the paper as a
    modelling overlay, never as an observed property.

Robust parsing: sheets and columns are auto-detected. If detection fails, run
  python run_experiment.py --dataset willems --willems-file FILE --inspect
to print sheet names/headers, then supply a mapping JSON via --willems-map.
"""
import json
import re
import numpy as np
import networkx as nx
from simcore import Network
from netgen import assign_latent_rates

_STAGE_NAME = {"stagename", "stage_name", "name", "stage"}
_SRC = {"sourcestage", "source", "from", "fromstage"}
_DST = {"destinationstage", "destination", "target", "to", "tostage", "targetstage"}
_COST = {"stagecost", "cost", "stage_cost"}
_CLS = {"stageclassification", "classification", "class", "stagetype", "type"}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def inspect_workbook(path, mapping=None):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    mapping = json.load(open(mapping)) if isinstance(mapping, str) else (mapping or {})
    for ws in wb.worksheets:
        rows = [[c.value for c in r] for r in ws.iter_rows(min_row=1, max_row=12)]
        hit = _find_header_row(rows, mapping)
        if hit is None:
            print(f"sheet={ws.title!r:28s} -> no stage/link table detected "
                  f"(first cells: {[r[0] for r in rows[:3] if r]})")
        else:
            ri, cols, name_c, src_c, dst_c = hit
            got = []
            if name_c is not None: got.append(f"stage-name@col{name_c}")
            if src_c is not None and dst_c is not None:
                got.append(f"links@cols{src_c},{dst_c}")
            print(f"sheet={ws.title!r:28s} -> header row {ri+1}: {', '.join(got)}"
                  f" | headers={[h for h in rows[ri] if h is not None][:8]}")


def _find_header_row(rows, mapping, max_scan=12):
    """Scan the first rows for the one that carries recognizable headers
    (workbooks often put titles/blank rows above the table)."""
    best = None
    best_score = 0
    for ri in range(min(max_scan, len(rows))):
        cols = {i: _norm(h) for i, h in enumerate(rows[ri]) if h is not None}
        if not cols:
            continue
        name_c = _find(cols, mapping.get("stage_name"), _STAGE_NAME)
        src_c = _find(cols, mapping.get("source"), _SRC)
        dst_c = _find(cols, mapping.get("destination"), _DST)
        score = (2 if name_c is not None else 0) + (3 if (src_c is not None and dst_c is not None) else 0)
        if score > best_score:
            best, best_score = (ri, cols, name_c, src_c, dst_c), score
    return best


def load_all_chains(path, n_regions=6, overlay="community", overlay_seed=0,
                    strict_conjunctive=False, min_nodes=30, mapping=None,
                    chains=None, lam=0.0):
    """Returns list of Network objects, one per usable chain."""
    tables = _read_tables(path, mapping)
    nets, report = [], []
    for chain_id, (stages, edges) in sorted(tables.items()):
        if chains and chain_id not in chains:
            continue
        net, info = _build_network(chain_id, stages, edges, n_regions, overlay,
                                   overlay_seed, strict_conjunctive)
        if net is not None and lam > 0:
            net = assign_latent_rates(net, lam,
                                      np.random.default_rng(7 * 1009 * chain_id
                                                            + overlay_seed))
        if net is not None:
            info["cone"] = net.n
        if net is not None and net.n >= min_nodes:
            nets.append(net)
            info["status"] = "KEPT"
        elif net is not None:
            info["status"] = f"SKIPPED (cone {net.n} < min_nodes {min_nodes})"
        else:
            info["status"] = f"SKIPPED ({info.get('reason', 'unparseable')})"
        report.append(info)
    if overlay_seed == 0:
        for r in report:
            print(f"  chain {r['chain']:02d}: stages={r['stages']:4d} "
                  f"links={r['links']:4d} matched={r['matched']:4d} "
                  f"sinks={r['sinks']:2d} focal={r['focal']!s:20.20s} "
                  f"cls={r['focal_cls']!s:12.12s} cone={r['cone']:4d} "
                  f"-> {r['status']}", flush=True)
        part_focal = [r for r in report if r["status"] == "KEPT"
                      and any(k in _norm(r["focal_cls"]) for k in ("part", "manuf"))]
        if len(part_focal) > len([r for r in report if r["status"] == "KEPT"]) / 2:
            print("  WARNING: most focal stages classify as Part/Manuf -- link "
                  "direction may be inverted in this workbook; tell me.")
    if not nets:
        sizes = sorted((r["cone"] for r in report if r["cone"]), reverse=True)
        raise RuntimeError(
            "All selected chains were skipped (see per-chain report above). "
            f"Largest cone among them: {sizes[0] if sizes else 0} nodes. "
            "Most likely the chains you selected are below --min-nodes; "
            "lower it (e.g. --min-nodes 8) or pick larger chain ids.")
    return nets


# ---------------------------------------------------------------------------
def _read_tables(path, mapping):
    """chain_id -> (stage rows, edge rows). Handles one workbook with per-chain
    sheets (stage + edge tables in the same or separate sheets)."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    mapping = json.load(open(mapping)) if isinstance(mapping, str) else (mapping or {})
    chains = {}
    for ws in wb.worksheets:
        m = re.search(r"(\d+)", ws.title)
        if not m:
            continue                    # Introduction / legend / overview sheets
        cid = int(m.group(1))
        rows = [[c.value for c in r] for r in ws.iter_rows()]
        if not rows:
            continue
        stage_rows, edge_rows = _split_tables(rows, mapping)
        st, ed = chains.setdefault(cid, ([], []))
        st.extend(stage_rows)
        ed.extend(edge_rows)
    return {cid: t for cid, t in chains.items() if t[0] and t[1]}


def _split_tables(rows, mapping):
    """Find the header row (titles/blank rows may precede it), then parse the
    stage and/or link table below it. Diagram-only sheets yield nothing."""
    hit = _find_header_row(rows, mapping)
    if hit is None:
        return [], []
    ri, cols, name_c, src_c, dst_c = hit
    cost_c = _find(cols, mapping.get("cost"), _COST)
    cls_c = _find(cols, mapping.get("classification"), _CLS)

    stage_rows, edge_rows = [], []
    for r in rows[ri + 1:]:
        if name_c is not None and name_c < len(r) and r[name_c] not in (None, ""):
            stage_rows.append({
                "name": str(r[name_c]).strip(),
                "cost": _num(r[cost_c]) if cost_c is not None and cost_c < len(r) else 1.0,
                "cls": str(r[cls_c]).strip() if cls_c is not None and cls_c < len(r) and r[cls_c] else "NA",
            })
        if (src_c is not None and dst_c is not None and src_c < len(r)
                and dst_c < len(r) and r[src_c] not in (None, "")
                and r[dst_c] not in (None, "")):
            edge_rows.append((str(r[src_c]).strip(), str(r[dst_c]).strip()))
    return stage_rows, edge_rows


def _find(cols, override, keys):
    if override:
        for i, c in cols.items():
            if c == _norm(override):
                return i
    for i, c in cols.items():
        if c in keys:
            return i
    return None


def _num(x):
    try:
        return max(0.01, float(x))
    except (TypeError, ValueError):
        return 1.0


# ---------------------------------------------------------------------------
def _build_network(chain_id, stages, edges, n_regions, overlay, overlay_seed,
                   strict_conjunctive):
    names = {s["name"] for s in stages}
    info = {"chain": chain_id, "stages": len(names), "links": len(edges),
            "matched": 0, "sinks": 0, "focal": "-", "focal_cls": "-", "cone": 0}
    G = nx.DiGraph()                             # edge u -> v : u supplies v
    for s in stages:
        G.add_node(s["name"], cost=s["cost"], cls=s["cls"])
    for u, v in edges:
        if u in names and v in names and u != v:
            G.add_edge(u, v)
    info["matched"] = G.number_of_edges()
    if G.number_of_edges() == 0:
        info["reason"] = "no links matched stage names"
        return None, info
    if not nx.is_directed_acyclic_graph(G):
        info["reason"] = "graph has cycles"
        return None, info

    # focal: single sink -> that sink; multiple sinks (distribution-style
    # chains serving many end products) -> a virtual MARKET node consuming
    # every sink as its own category, so loss = fraction of end products
    # starved and the WHOLE chain is used instead of one sink's shard.
    sinks = [v for v in G if G.out_degree(v) == 0]
    info["sinks"] = len(sinks)
    if not sinks:
        info["reason"] = "no sink stage"
        return None, info
    virtual = len(sinks) > 1
    if virtual:
        focal = "__market__"
        G.add_node(focal, cost=1.0, cls="Market")
        for s in sinks:
            G.add_edge(s, focal)
        info["focal"] = f"__market__({len(sinks)} sinks)"
        info["focal_cls"] = "Market"
    else:
        focal = sinks[0]
        info["focal"] = focal
        info["focal_cls"] = G.nodes[focal]["cls"]
    cone = nx.ancestors(G, focal) | {focal}
    info["cone"] = len(cone) - (1 if virtual else 0)   # report real stages
    H = G.subgraph(cone).copy()

    # tiers = longest path distance from focal (guarantees supplier tier >
    # consumer tier along every edge -> valid cascade order by -tier)
    tier = {focal: 0}
    for v in reversed(list(nx.topological_sort(H))):     # upstream last? ensure order
        pass
    for v in nx.topological_sort(H.reverse(copy=False)):  # focal first, upstream later
        for u in H.predecessors(v):                       # u supplies v
            tier[u] = max(tier.get(u, 0), tier[v] + 1)

    nodes = sorted(H.nodes, key=lambda v: tier[v])        # focal gets id 0
    idx = {v: i for i, v in enumerate(nodes)}
    n = len(nodes)

    rng = np.random.default_rng(1009 * chain_id + overlay_seed)
    if overlay == "classification":
        classes = sorted({H.nodes[v]["cls"] for v in nodes})
        cmap = {c: i % n_regions for i, c in enumerate(rng.permutation(classes))}
        region = np.array([cmap[H.nodes[v]["cls"]] for v in nodes])
    else:
        comms = list(nx.algorithms.community.greedy_modularity_communities(
            H.to_undirected()))
        order = rng.permutation(len(comms))
        region = np.zeros(n, dtype=int)
        for k, ci in enumerate(order):
            for v in comms[ci]:
                region[idx[v]] = k % n_regions

    suppliers = [dict() for _ in range(n)]
    for v in nodes:
        preds = list(H.predecessors(v))
        if not preds:
            continue
        if strict_conjunctive or (virtual and v == focal):
            # end products at the virtual focal are never substitutable
            groups = {i: [u] for i, u in enumerate(preds)}
        elif False:
            pass
        else:
            groups = {}
            for u in preds:                                # same class = substitutable
                groups.setdefault(H.nodes[u]["cls"], []).append(u)
            groups = {i: g for i, (_, g) in enumerate(sorted(groups.items()))}
        suppliers[idx[v]] = {c: tuple(idx[u] for u in g) for c, g in groups.items()}

    cost = np.array([H.nodes[v]["cost"] for v in nodes], dtype=float)
    deep = cost[np.array([tier[v] for v in nodes]) >= 2]
    cost = cost / (np.median(deep) if len(deep) and np.median(deep) > 0 else max(cost.max(), 1.0))
    cost = np.clip(cost, 0.05, None)
    region_p = np.full(n_regions, 0.015)
    frag = rng.choice(n_regions, size=max(1, n_regions // 3), replace=False)
    region_p[frag] = rng.uniform(0.08, 0.11, size=len(frag))
    return Network(n=n, suppliers=suppliers, region=region,
                   tier=np.array([tier[v] for v in nodes], dtype=int),
                   n_regions=n_regions, node_cost=cost, focal=0,
                   region_p=region_p,
                   name=f"willems_chain{chain_id:02d}_seed{overlay_seed}"), info
