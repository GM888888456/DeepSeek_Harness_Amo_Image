# -*- coding: utf-8 -*-
"""我想永远陪着你-关系（Relationship）插件。"""

try:
    from .main import AmoRelationshipPlugin, PLUGIN_NAME, PLUGIN_VERSION
except Exception:
    from main import AmoRelationshipPlugin, PLUGIN_NAME, PLUGIN_VERSION

# 旧模块名兼容一个升级周期；新 metadata 只加载 AmoRelationshipPlugin。
AmoImagePlugin = AmoRelationshipPlugin

__all__ = ["AmoRelationshipPlugin", "AmoImagePlugin", "PLUGIN_NAME", "PLUGIN_VERSION"]
