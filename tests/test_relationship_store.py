import os
import tempfile
import unittest

from relationship_store import RelationshipStore


class RelationshipStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = RelationshipStore(self.tmp.name)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_people_and_relationship_roundtrip(self):
        a = self.store.upsert_person("阿墨", person_id="P-amo")
        b = self.store.upsert_person("张经理", person_id="P-manager", entity_type="person")
        self.assertEqual(a["display_name"], "阿墨")
        self.store.set_relationship("P-amo", "P-manager", "bank_manager",
                                    familiarity=65, trust=80, source="manual")
        rows = self.store.list_relationships("P-amo")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["relation_type"], "bank_manager")
        self.assertEqual(rows[0]["trust"], 80)

    def test_interaction_idempotency(self):
        self.store.upsert_person("张经理", person_id="P-manager")
        one = self.store.record_interaction("P-manager", "谈授信", source_event_id="evt-1")
        two = self.store.record_interaction("P-manager", "重复事件", source_event_id="evt-1")
        self.assertEqual(one["interaction_id"], two["interaction_id"])
        self.assertEqual(len(self.store.list_interactions("P-manager")), 1)

    def test_unknown_person_rejected(self):
        with self.assertRaises(ValueError):
            self.store.record_interaction("missing", "不应写入")

    def test_relationship_requires_both_people(self):
        self.store.upsert_person("甲", person_id="A")
        with self.assertRaises(ValueError):
            self.store.set_relationship("A", "B", "friend")

    def test_legacy_import_keeps_uid_identity(self):
        result = self.store.import_legacy(
            [{"uid": "1001", "name": "张三", "alias": "老张"}],
            [{"a_uid": "1001", "b_uid": "1002", "relation": "同事", "note": "旧关系"}],
        )
        self.assertEqual(result["people_imported"], 1)
        self.assertEqual(result["relationships_imported"], 1)
        self.assertIsNotNone(self.store.get_person("1001"))
        self.assertIsNotNone(self.store.get_person("1002"))
        self.assertEqual(self.store.list_relationships("1001")[0]["relation_type"], "同事")

    def test_social_event_requires_known_participants(self):
        with self.assertRaises(ValueError):
            self.store.record_social_event("聚餐", participant_ids=["missing"])

    def test_snapshot_counts(self):
        self.store.upsert_person("甲", person_id="A")
        self.assertEqual(self.store.snapshot()["counts"]["people"], 1)


if __name__ == "__main__":
    unittest.main()
