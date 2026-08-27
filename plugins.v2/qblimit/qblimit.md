## 当前范围

- 插件：`QbLimit`
- 目录：`plugins.v2\qblimit`
- 当前版本：`1.0.3`
- 作者：beatter789（<https://github.com/beatter789>）

## qBittorrent 排除标签

- 配置项：`qBittorrent 排除标签`，每行填写一个完整标签名称。
- 命中任意排除标签的 qBittorrent 种子，不会执行本插件的种子级标签限速；该规则优先级最高。
- 排除仅跳过本插件的种子级操作，不会清除或修改种子已有的上传限速。
- 下载器级全局限速仍会对全部种子生效；Transmission 不使用此配置。

## API 与测试

- 提交前必须执行 Python 编译、JSON 解析、传统插件测试、`git diff --check` 和版本一致性检查。

## 版本与提交强制约定

- 每次修复、功能增加或版本升级，都必须同步更新 `package.v2.json`。
- 每次变更版本号递增 `0.0.1`。
- 每次变更必须在 `history` 中新增与当前版本号完全一致的记录。
- `package.v2.json` 的 `version`、插件代码 `plugin_version` 和 `history` 最新键必须三者一致。
- 后续提交前必须执行版本字段和 `history` 最新键一致性检查，确认代码版本、package version、history 最新键完全一致后才允许提交或推送。
