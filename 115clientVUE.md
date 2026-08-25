# 115上传增强VUE 工作记录

## 当前状态

- 插件：`P115UploadEnhancerVUE`
- 目录：`plugins.v2/p115uploadenhancervue`
- 当前代码版本：`1.1.0`
- 前端目录：`frontend/p115uploadenhancervue`
- 接口前缀：`plugin/P115UploadEnhancerVUE/...`
- 本插件与传统 `P115UploadEnhancer` 独立部署；传统版记录见 `115client.md`。

## 拆分与实现历史

- `v1.0.0`：从传统插件 Vue 1.0.8 实现独立拆分，隔离目录、配置前缀和接口路径。
- `v1.1.0`：与传统版统一版本基线；Vue 代码和构建产物保持独立。
- Vue 页面包含账户信息、配置页面、二维码弹窗、扫码状态轮询、Cookie 保存和账户状态刷新。
- 构建产物位于插件目录的 `dist/assets`；源码位于 `frontend/p115uploadenhancervue`。

## 已知问题与范围

- 曾记录宿主报错“组件加载错误，无法加载组件，请稍后再试”；问题涉及 MoviePilot 的 Vue 组件协议、联邦入口或资源加载，需在 Vue 专项任务中处理。
- 本项目只处理传统插件，不在此文档中修改或验证 Vue 实现。

## Vue 版本规则

每次 Vue 插件修复、功能增加或版本升级，都必须同步更新 `package.v2.json`：

1. 版本号递增 `0.0.1`；
2. `plugin_version`、`package.v2.json` 的 `version` 和 `history` 最新键必须完全一致；
3. `history` 必须新增当前版本记录；
4. 提交前必须执行版本字段与 `history` 最新键一致性检查；
5. 不记录 Cookie、Token、密码、Machine ID 或其他账号秘密。
