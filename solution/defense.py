"""Online pipeline checks using only the published context and metered API.

One tool call per event; no file access, event tables or phase-specific logic.
"""
from api import Verdict


def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)


def check_data_batch(payload, ctx):
    profile = _query(ctx, "batch_profile", (payload["batch_id"],))
    if "error" in profile:
        return _unavailable("checks", profile)
    b = ctx.baseline
    reasons = []
    for name, lower, upper in (
        ("row_count", "row_count_min", "row_count_max"),
        ("mean_amount", "mean_amount_min", "mean_amount_max"),
    ):
        if not b[lower] <= profile[name] <= b[upper]:
            reasons.append(name + " outside calibrated range")
    if profile["null_rate"]["customer_id"] > b["null_rate_max"]:
        reasons.append("customer_id null rate")
    if profile["staleness_min"] > b["staleness_min_max"]:
        reasons.append("stale batch")
    return _verdict("checks", reasons)


def check_contract_checkpoint(payload, ctx):
    diff = _query(ctx, "contract_diff", (payload["contract_id"], payload["checkpoint_batch_id"]))
    if "error" in diff:
        return _unavailable("contracts", diff)
    reasons = list(diff["violations"])
    if diff["freshness_delay_min"] > ctx.baseline["freshness_delay_max_min"]:
        reasons.append("freshness SLA exceeded")
    return _verdict("contracts", reasons)


def check_lineage_run(payload, ctx):
    graph = _query(ctx, "lineage_graph_slice", (payload["run_id"],))
    if "error" in graph:
        return _unavailable("lineage", graph)
    reasons = []
    if graph["duration_ms"] > ctx.baseline["lineage_duration_ms_max"]:
        reasons.append("anomalous runtime")
    # Producers may name the declaration expected_upstream or declared_upstream.
    # Read the declaration carried by the event, never a fixed topology.
    expected = payload.get("expected_upstream", payload.get("declared_upstream"))
    if expected is None and "inputs" in payload:
        expected = [dataset["name"] for dataset in payload["inputs"]]
    # Some producers declare only part of their real lineage in inputs. Learn
    # the stable topology of each job from earlier valid events in THIS run.
    # Versioned jobs get separate baselines; a new job cannot inherit another's.
    job = payload.get("job")
    topology_key = (job, payload.get("schema_version"), payload.get("contract_version"))
    topology = ctx.state.setdefault("lineage_topology", {})
    observed = set(graph["actual_upstream"])
    if job is not None and topology_key in topology:
        expected = set(expected or ()) | topology[topology_key]
    if expected is not None:
        if set(expected) - set(graph["actual_upstream"]):
            reasons.append("missing expected upstream edge")
    elif not graph["actual_upstream"]:
        reasons.append("no upstream lineage")
    expected_downstream = payload.get("expected_downstream_count")
    if expected_downstream is None and "outputs" in payload:
        expected_downstream = len(payload["outputs"])
    if expected_downstream is not None:
        if graph["actual_downstream_count"] < expected_downstream:
            reasons.append("missing expected downstream output")
    elif graph["actual_downstream_count"] == 0:
        reasons.append("orphaned output")
    if job is not None and not reasons:
        topology.setdefault(topology_key, set()).update(observed)
    return _verdict("lineage", reasons)


def check_feature_materialization(payload, ctx):
    drift = _query(ctx, "feature_drift", (payload["feature_view"], payload["batch_id"]))
    if "error" in drift:
        return _unavailable("ai_infra", drift)
    reasons = []
    if drift["mean_shift_sigma"] > ctx.baseline["feature_mean_shift_sigma_max"]:
        reasons.append("training-serving feature skew")
    return _verdict("ai_infra", reasons)


def check_embedding_batch(payload, ctx):
    drift = _query(ctx, "embedding_drift", (payload["corpus"], payload["chunk_batch_id"]))
    if "error" in drift:
        return _unavailable("ai_infra", drift)
    reasons = []
    if drift["centroid_shift"] > ctx.baseline["embedding_centroid_shift_max"]:
        reasons.append("embedding centroid drift")
    if drift["avg_doc_age_days"] > ctx.baseline["corpus_avg_doc_age_days_max"]:
        reasons.append("stale RAG corpus")
    return _verdict("ai_infra", reasons)


def _query(ctx, method, args):
    # Cache is per run and keyed by the documented tool arguments, not answers.
    cache = ctx.state.setdefault("tool_cache", {})
    key = (method, args)
    if key not in cache:
        result = getattr(ctx.tools, method)(*args)
        if "error" not in result:
            cache[key] = result
        return result
    return cache[key]


def _verdict(pillar, reasons):
    return Verdict(alert=bool(reasons), pillar=pillar,
                   reason="; ".join(reasons) if reasons else "within published limits")


def _unavailable(pillar, result):
    # A tool failure is not evidence that this event is a real data fault.
    return Verdict(alert=False, pillar=pillar, confidence=0.0,
                   reason="tool unavailable: " + str(result["error"]))
