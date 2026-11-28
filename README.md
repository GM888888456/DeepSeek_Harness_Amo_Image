# Amo Relationship（关系模块）

> 当前开发分支：`amo-refactor-20261128`

Relationship 是 Amo 的社会关系数据域。它不承担聊天、人格、日程、图片生成或语音合成；这些运行时能力由 Terminal 统一协调和持有。

## 职责边界

- **Relationship**：人物/组织身份、别名、社会关系边、熟悉度、信任度、互动历史、社会事件。
- **Terminal**：聊天主链、人格、日程、心流、情绪与私人亲密状态；同时持有图片生成、图片理解、自拍档案和语音运行时。
- **业务插件**（Finance、Medical、Market 等）：保存各自领域的数据，通过稳定的 person_id / organization_id 关联主体，不自行维护第二套社会关系图谱。

Relationship 不反向调用 Terminal，不接管日程或聊天主链。Terminal 可以读取/写入 Relationship 的社会关系数据。

## 数据

关系数据存于独立目录：

`plugin_data/DeepSeek_Harness_Amo_Relationship/`

由 `relationship_store.py` 管理。人物、关系边、互动和社会事件在同一关系数据域内维护。Terminal 的日程、人格、心流和 Amo 对用户的私人亲密状态不迁入此库。

## Web API

所有接口均以 `/DeepSeek_Harness_Amo_Relationship` 为前缀：

| 路径 | 方法 | 用途 |
|---|---|---|
| `/relationship/snapshot` | GET | 关系数据概览 |
| `/relationship/people` | GET / POST | 查询人物 |
| `/relationship/person/save` | POST | 保存人物 |
| `/relationship/edges` | GET / POST | 查询关系边 |
| `/relationship/edge/save` | POST | 保存关系边 |
| `/relationship/interactions` | GET / POST | 查询互动历史 |
| `/relationship/interaction/record` | POST | 记录互动 |
| `/relationship/events` | GET | 查询社会事件 |
| `/relationship/event/save` | POST | 保存社会事件 |
| `/relationship/import-legacy` | POST | 幂等导入旧关系数据 |

## WebUI

`views/dashboard/` 使用 Terminal 的基础视觉规范，提供人物、关系、互动与社会事件管理。

## 媒体迁移

图片生成、provider、提示词一致性、参考图、自拍档案与语音运行时已经迁入 Terminal 的 `amo_core/media_image/` 和 `amo_core/media_voice/`。Relationship 不再注册媒体 API、不再加载语音实例，也不再提供媒体配置项。

Terminal 首次加载媒体引擎时，会把旧 Relationship 数据目录中的媒体资产（参考图、场景状态、脸部锁定和自拍缓存）复制到 Terminal 的媒体目录；迁移不会移动或删除 Relationship 的 SQLite 数据。旧文件已从本仓库工作分支清理，Git 历史仍可用于回滚。

## 开发约定

- 关系主库唯一：Relationship。
- 私人亲密状态唯一：Terminal。
- 互动写入应提供稳定的 `source_event_id`，以支持幂等去重。
- 不要在 Relationship 中重新引入图片、语音、日程或聊天主链逻辑。
