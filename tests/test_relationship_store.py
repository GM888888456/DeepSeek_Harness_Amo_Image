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

    def test_snapshot_counts(self):
        self.store.upsert_person("甲", person_id="A")
        self.assertEqual(self.store.snapshot()["counts"]["people"], 1)


if __name__ == "__main__":
    unittest.main()
