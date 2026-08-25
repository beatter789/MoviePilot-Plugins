# 115上传增强VUE 工作记录

## 当前状态

- 插件名称：115上传增强VUE
- 插件 ID：P115UploadEnhancerVUE
- 目录：`plugins.v2/p115uploadenhancervue`
- 当前版本：1.0.0
- 前端目录：`frontend/p115uploadenhancervue`
- 来源：从 `P115UploadEnhancer` 的 Vue 1.0.8 实现独立复制

## 已知问题（本轮不处理）

Vue 插件当前已知错误：

```text
组件加载错误，无法加载组件，请稍后再试
```

该问题记录在本文档中，作为新插件的待处理问题。本轮只完成插件拆分、目录隔离和版本初始化，不排查宿主 Vue 组件加载协议、联邦入口或资源加载问题。

## 版本规则

每次修复、功能增加或版本升级，必须同步更新 `package.v2.json`：

1. `plugin_version`、`package.v2.json` 的 `version` 和 `history` 最新键必须一致；
2. 版本号每次递增 `0.0.1`；
3. `history` 必须新增当前版本对应的记录；
4. 不记录 Cookie、Token 或其他敏感信息。
