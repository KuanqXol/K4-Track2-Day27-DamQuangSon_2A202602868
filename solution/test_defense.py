"""Synthetic regression tests; no phase keys, encrypted schedules or labels.

Run from the repository root: python -B -m unittest discover -s solution -v
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness" / "child_env"))
from api import SiegeContext, Verdict

spec = importlib.util.spec_from_file_location("defense", ROOT / "solution" / "defense.py")
defense = importlib.util.module_from_spec(spec)
spec.loader.exec_module(defense)


class Tools:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def __getattr__(self, method):
        def call(*args):
            self.calls.append((method, args))
            return self.results[method]
        return call


class DefenseTests(unittest.TestCase):
    def setUp(self):
        self.baseline = json.loads((ROOT / "data" / "baselines.json").read_text())

    def context(self, **results):
        return SimpleNamespace(tools=Tools(results), baseline=self.baseline, state={})

    def clean_batch(self):
        b = self.baseline
        return dict(row_count=(b["row_count_min"] + b["row_count_max"]) / 2,
                    mean_amount=(b["mean_amount_min"] + b["mean_amount_max"]) / 2,
                    null_rate={"customer_id": b["null_rate_max"] / 2},
                    std_amount=10, staleness_min=b["staleness_min_max"] / 2)

    def test_registration_and_dispatch(self):
        ctx = SiegeContext(Tools({"batch_profile": self.clean_batch()}), self.baseline)
        defense.register(ctx)
        self.assertEqual(set(ctx._handlers), {"data_batch", "contract_checkpoint", "lineage_run",
                                             "feature_materialization", "embedding_batch"})
        v = ctx.dispatch({"type": "data_batch", "payload": {"batch_id": "new-batch"}})
        self.assertIsInstance(v, Verdict)
        self.assertFalse(v.alert)

    def test_clean_batch_and_exact_calibrated_boundaries(self):
        b = self.baseline
        for row in (b["row_count_min"], b["row_count_max"]):
            for mean in (b["mean_amount_min"], b["mean_amount_max"]):
                p = self.clean_batch()
                p.update(row_count=row, mean_amount=mean, staleness_min=b["staleness_min_max"],
                         null_rate={"customer_id": b["null_rate_max"]})
                ctx = self.context(batch_profile=p)
                self.assertFalse(defense.check_data_batch({"batch_id": "boundary"}, ctx).alert)

    def test_each_batch_fault_independently(self):
        b = self.baseline
        changes = [dict(row_count=b["row_count_min"] - 1),
                   dict(row_count=b["row_count_max"] + 1),
                   dict(mean_amount=b["mean_amount_min"] - 1),
                   dict(mean_amount=b["mean_amount_max"] + 1),
                   dict(null_rate={"customer_id": b["null_rate_max"] + .001}),
                   dict(staleness_min=b["staleness_min_max"] + 1)]
        for change in changes:
            with self.subTest(change=change):
                p = self.clean_batch()
                p.update(change)
                self.assertTrue(defense.check_data_batch({"batch_id": "unseen"},
                                                        self.context(batch_profile=p)).alert)

    def test_contract_schema_type_and_sla(self):
        limit = self.baseline["freshness_delay_max_min"]
        payload = {"contract_id": "orders", "checkpoint_batch_id": "checkpoint"}
        for violations, delay, alert in [([], limit, False), (["schema_hash_mismatch"], 0, True),
                                          (["type_violation"], 0, True), ([], limit + 1, True)]:
            ctx = self.context(contract_diff={"violations": violations, "freshness_delay_min": delay})
            self.assertEqual(defense.check_contract_checkpoint(payload, ctx).alert, alert)
            self.assertEqual(ctx.tools.calls, [("contract_diff", ("orders", "checkpoint"))])

    def test_lineage_missing_declared_input_with_other_upstream_present(self):
        ctx = self.context(lineage_graph_slice={"duration_ms": 1, "actual_upstream": ["raw.customers"],
                                              "actual_downstream_count": 1})
        payload = {"run_id": "run", "inputs": [{"name": "raw.orders"}], "outputs": [{"name": "stg.orders"}]}
        self.assertTrue(defense.check_lineage_run(payload, ctx).alert)

    def test_lineage_all_declared_inputs_and_extra_edge(self):
        ctx = self.context(lineage_graph_slice={"duration_ms": 1,
                                              "actual_upstream": ["raw.orders", "raw.customers"],
                                              "actual_downstream_count": 1})
        payload = {"run_id": "run", "inputs": [{"name": "raw.orders"}], "outputs": [{"name": "stg.orders"}]}
        self.assertFalse(defense.check_lineage_run(payload, ctx).alert)

    def test_lineage_runtime_and_orphan_output(self):
        for duration, count in [(self.baseline["lineage_duration_ms_max"] + 1, 1), (1, 0)]:
            ctx = self.context(lineage_graph_slice={"duration_ms": duration, "actual_upstream": ["a"],
                                                  "actual_downstream_count": count})
            self.assertTrue(defense.check_lineage_run({"run_id": "run"}, ctx).alert)

    def test_lineage_learns_partial_declaration_without_cross_job_leak(self):
        ctx = self.context(lineage_graph_slice={"duration_ms": 1,
                                              "actual_upstream": ["orders", "customers"],
                                              "actual_downstream_count": 1})
        payload = {"run_id": "first", "job": "transform", "inputs": [{"name": "orders"}]}
        self.assertFalse(defense.check_lineage_run(payload, ctx).alert)
        ctx.tools.results["lineage_graph_slice"] = {"duration_ms": 1, "actual_upstream": ["orders"],
                                                   "actual_downstream_count": 1}
        payload["run_id"] = "second"
        self.assertTrue(defense.check_lineage_run(payload, ctx).alert)
        payload.update(run_id="other-job", job="different")
        self.assertFalse(defense.check_lineage_run(payload, ctx).alert)
        payload.update(run_id="versioned", job="transform", schema_version="v2")
        self.assertFalse(defense.check_lineage_run(payload, ctx).alert)

    def test_declared_source_and_sink_can_be_clean(self):
        ctx = self.context(lineage_graph_slice={"duration_ms": 1, "actual_upstream": [],
                                              "actual_downstream_count": 0})
        self.assertFalse(defense.check_lineage_run({"run_id": "run", "inputs": [], "outputs": []}, ctx).alert)

    def test_feature_skew_boundary(self):
        limit = self.baseline["feature_mean_shift_sigma_max"]
        for shift, alert in [(0, False), (limit, False), (limit + .1, True)]:
            ctx = self.context(feature_drift={"mean_shift_sigma": shift})
            self.assertEqual(defense.check_feature_materialization(
                {"feature_view": "view", "batch_id": "new"}, ctx).alert, alert)
            self.assertEqual(ctx.tools.calls, [("feature_drift", ("view", "new"))])

    def test_embedding_shift_and_age_independently(self):
        shift = self.baseline["embedding_centroid_shift_max"]
        age = self.baseline["corpus_avg_doc_age_days_max"]
        for s, a, alert in [(shift, age, False), (shift + .01, 0, True), (0, age + 1, True)]:
            ctx = self.context(embedding_drift={"centroid_shift": s, "avg_doc_age_days": a})
            self.assertEqual(defense.check_embedding_batch({"corpus": "docs", "chunk_batch_id": "new"}, ctx).alert, alert)

    def test_tool_errors_across_all_handlers(self):
        cases = [(defense.check_data_batch, "batch_profile", {"batch_id": "bad"}),
                 (defense.check_contract_checkpoint, "contract_diff", {"contract_id": "x", "checkpoint_batch_id": "bad"}),
                 (defense.check_lineage_run, "lineage_graph_slice", {"run_id": "bad"}),
                 (defense.check_feature_materialization, "feature_drift", {"feature_view": "x", "batch_id": "bad"}),
                 (defense.check_embedding_batch, "embedding_drift", {"corpus": "x", "chunk_batch_id": "bad"})]
        for handler, method, payload in cases:
            with self.subTest(method=method):
                ctx = self.context(**{method: {"error": "not yet available"}})
                verdict = handler(payload, ctx)
                self.assertFalse(verdict.alert)
                self.assertEqual(verdict.confidence, 0)
                self.assertIn("tool unavailable", verdict.reason)
                self.assertFalse(ctx.state["tool_cache"])

    def test_cache_reuses_same_ref_but_not_other_event_or_run(self):
        ctx = self.context(batch_profile=self.clean_batch())
        for ref in ["first", "first", "second"]:
            defense.check_data_batch({"batch_id": ref}, ctx)
        self.assertEqual(len(ctx.tools.calls), 2)
        other = self.context(batch_profile=self.clean_batch())
        defense.check_data_batch({"batch_id": "first"}, other)
        self.assertEqual(len(other.tools.calls), 1)

    def test_failed_rpc_can_retry_without_poisoned_cache(self):
        ctx = self.context(batch_profile={"error": "temporary"})
        defense.check_data_batch({"batch_id": "same"}, ctx)
        ctx.tools.results["batch_profile"] = self.clean_batch()
        self.assertFalse(defense.check_data_batch({"batch_id": "same"}, ctx).alert)
        self.assertEqual(len(ctx.tools.calls), 2)


if __name__ == "__main__":
    unittest.main()
