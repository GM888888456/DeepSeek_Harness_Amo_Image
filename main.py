# -*- coding: utf-8 -*-
"""Amo Relationship：只负责人物身份、社会关系、互动历史与社会事件。"""
from __future__ import annotations

import json
import os

from astrbot.api import logger
from astrbot.api.star import Context, Star

try:
    from astrbot.api.web import request as web_request
except Exception:  # pragma: no cover
    web_request = None

try:
    from .relationship_store import RelationshipStore
except Exception:  # pragma: no cover
    from relationship_store import RelationshipStore  # type: ignore

PLUGIN_NAME = "DeepSeek_Harness_Amo_Relationship"
PLUGIN_VERSION = "1.2.1"
try:
    import yaml
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "metadata.yaml"),
              encoding="utf-8") as fh:
        PLUGIN_VERSION = str((yaml.safe_load(fh) or {}).get("version") or PLUGIN_VERSION)
except Exception:
    pass


class AmoRelationshipPlugin(Star):
    """社会关系域插件；不再承载图片生成、自拍档案或语音运行时。"""

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            from .config_guard import heal as cfg_heal, fallback_data_dir
        except Exception:
            try:
                from config_guard import heal as cfg_heal, fallback_data_dir  # type: ignore
            except Exception:
                cfg_heal = fallback_data_dir = None

        if cfg_heal is not None:
            try:
                result = cfg_heal(
                    self.config,
                    plugin_name=PLUGIN_NAME,
                    plugin_dir=self.plugin_dir,
                    data_dir=fallback_data_dir(self.plugin_dir, PLUGIN_NAME),
                    logger=logger,
                )
                if result.get("restored"):
                    logger.info("[relationship] 已恢复配置项：%s", ", ".join(result["restored"]))
            except Exception as exc:
                logger.debug("[relationship] 配置自愈失败：%s", exc)

        try:
            from astrbot.core.utils.astrbot_path import get_astrbot_data_path
            data_dir = os.path.join(
                str(get_astrbot_data_path()), "plugin_data", PLUGIN_NAME
            )
        except Exception:
            data_dir = fallback_data_dir(self.plugin_dir, PLUGIN_NAME) if fallback_data_dir else os.path.join(
                self.plugin_dir, "data"
            )
        self.relationship_store = RelationshipStore(data_dir)
        self._register_web_apis()

    async def _read_body(self) -> dict:
        if web_request is None:
            return {}
        try:
            payload = await web_request.json(default={}) or {}
        except Exception:
            payload = {}
        return payload if isinstance(payload, dict) else {}

    async def api_relationship_snapshot(self):
        store = self.relationship_store
        return {"code": 0, "data": store.snapshot()}

    async def api_relationship_people(self):
        query = str((await self._read_body()).get("q") or "")
        return {"code": 0, "data": {"items": self.relationship_store.find_people(query, 100)}}

    async def api_relationship_person_save(self):
        body = await self._read_body()
        try:
            item = self.relationship_store.upsert_person(
                body.get("display_name") or body.get("name"),
                person_id=body.get("person_id") or None,
                aliases=body.get("aliases") or [],
                entity_type=body.get("entity_type") or "person",
                attributes=body.get("attributes") or {},
            )
            return {"code": 0, "data": item}
        except Exception as exc:
            return {"code": 1, "msg": str(exc)}

    async def api_relationship_edges(self):
        body = await self._read_body()
        return {"code": 0, "data": {"items": self.relationship_store.list_relationships(
            body.get("person_id") or None,
            include_inactive=bool(body.get("include_inactive")),
        )}}

    async def api_relationship_edge_save(self):
        body = await self._read_body()
        try:
            rows = self.relationship_store.set_relationship(
                body.get("subject_id"), body.get("object_id"), body.get("relation_type"),
                familiarity=body.get("familiarity"), trust=body.get("trust"),
                confidence=body.get("confidence", 1.0), source=body.get("source", "manual"),
                note=body.get("note", ""), status=body.get("status", "active"),
            )
            return {"code": 0, "data": {"items": rows}}
        except Exception as exc:
            return {"code": 1, "msg": str(exc)}

    async def api_relationship_interactions(self):
        body = await self._read_body()
        person_id = str(body.get("person_id") or "")
        if not person_id:
            return {"code": 1, "msg": "缺少 person_id"}
        return {"code": 0, "data": {"items": self.relationship_store.list_interactions(
            person_id, body.get("limit", 50)
        )}}

    async def api_relationship_interaction_record(self):
        body = await self._read_body()
        try:
            item = self.relationship_store.record_interaction(
                body.get("person_id"), body.get("summary", ""),
                channel=body.get("channel", ""), kind=body.get("kind", "conversation"),
                occurred_at=body.get("occurred_at"), sentiment=body.get("sentiment"),
                source_event_id=body.get("source_event_id"),
                metadata=body.get("metadata") or {},
            )
            return {"code": 0, "data": item}
        except Exception as exc:
            return {"code": 1, "msg": str(exc)}

    async def api_relationship_events(self):
        return {"code": 0, "data": {"items": self.relationship_store.list_social_events(200)}}

    async def api_relationship_event_save(self):
        body = await self._read_body()
        try:
            item = self.relationship_store.record_social_event(
                body.get("title"), event_type=body.get("event_type", "social"),
                starts_at=body.get("starts_at"), ends_at=body.get("ends_at"),
                location=body.get("location", ""),
                participant_ids=body.get("participant_ids") or [],
                status=body.get("status", "planned"),
                metadata=body.get("metadata") or {},
                event_id=body.get("event_id") or None,
            )
            return {"code": 0, "data": item}
        except Exception as exc:
            return {"code": 1, "msg": str(exc)}

    async def api_relationship_import_legacy(self):
        body = await self._read_body()
        try:
            result = self.relationship_store.import_legacy(
                body.get("profiles"), body.get("relations")
            )
            return {"code": 0, "data": result}
        except Exception as exc:
            return {"code": 1, "msg": str(exc)}

    def _register_web_apis(self):
        routes = [
            ("/relationship/snapshot", self.api_relationship_snapshot, ["GET"]),
            ("/relationship/people", self.api_relationship_people, ["GET", "POST"]),
            ("/relationship/person/save", self.api_relationship_person_save, ["POST"]),
            ("/relationship/edges", self.api_relationship_edges, ["GET", "POST"]),
            ("/relationship/edge/save", self.api_relationship_edge_save, ["POST"]),
            ("/relationship/interactions", self.api_relationship_interactions, ["GET", "POST"]),
            ("/relationship/interaction/record", self.api_relationship_interaction_record, ["POST"]),
            ("/relationship/events", self.api_relationship_events, ["GET"]),
            ("/relationship/event/save", self.api_relationship_event_save, ["POST"]),
            ("/relationship/import-legacy", self.api_relationship_import_legacy, ["POST"]),
        ]
        for path, handler, methods in routes:
            try:
                self.context.register_web_api("/" + PLUGIN_NAME + path, handler, methods, path)
            except TypeError:
                try:
                    self.context.register_web_api("/" + PLUGIN_NAME + path, methods, path, handler)
                except Exception as exc:
                    logger.warning("[relationship] API %s 注册失败：%s", path, exc)
            except Exception as exc:
                logger.warning("[relationship] API %s 注册失败：%s", path, exc)
