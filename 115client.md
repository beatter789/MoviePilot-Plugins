# 115上传增强工作记录

## 2026-06-09：需求确认与 API 审查

### 用户目标

- 在 `MoviePilot-Plugins-main` 新增独立插件
- 插件名称：115上传增强
- 只支持 115网盘Plus
- 原 `MoviePilot-Plugins-main-v2` 中的 `P115StrmHelper` 不做修改
- 作者：beatter789
- 作者主页：`https://github.com/beatter789`
- 后续每轮工作结束都更新本文件

### 已检查来源

- `MoviePilot-Plugins-main-v2/plugins.v2/p115disk/`
  - Plus 存储模块基础实现
  - `__init__.py`
  - `p115_api.py`
  - `p115_client.py`
  - `cache.py`
  - `tools.py`
  - `requirements.txt`
- `MoviePilot-Plugins-main-v2/plugins.v2/p115strmhelper/core/p115disk.py`
  - 原上传增强实现参考
- `MoviePilot-Plugins-main-v2/plugins.v2/p115strmhelper/patch/p115disk_upload.py`
  - 原 P115Disk 上传猴子补丁入口
- `p115client-main/p115client/tool/upload.py`
  - 115 秒传存在性判断和上传初始化实现
- `CloudDrive2_gRPC_API_Guide.md`
  - CloudDrive2 Remote Upload 哈希与状态协议

### API 结论

#### 115网盘Plus

`p115client` 支持：

- `upload_file_init`
- `upload_for_check_existence(sha1, size)`
- `reuse=True` 表示初始化上传阶段秒传成功
- 大于等于 1 MB 时支持范围 SHA1 二次校验

Plus 原始 `P115Api.upload` 已经计算完整 SHA1，并通过 `read_range_bytes_or_hash` 进行初始化上传和秒传判断。

#### CloudDrive2

CloudDrive2 Remote Upload 支持：

- MD5
- SHA1
- PikPakSha1
- `known_hashes`
- 服务端发送 `RemoteHashDataRequest`
- 客户端通过 `RemoteHashProgress` 回报哈希
- 最终状态可能为 `Finish`、`Skipped`、`Cancelled`、`Error` 等

但文档没有发现独立的“仅通过 SHA1 查询是否可秒传”RPC。Remote Upload 是上传协商流程，是否跳过真实传输由 CloudDrive2 服务端和目标云盘驱动决定。

CloudDrive2 Direct Write 模式不做预先 SHA1 秒传判断。

本次独立插件不包含 CloudDrive2 代码。

### 已完成

- 在目标仓库复制 `p115disk` 基础代码到：
  - `plugins.v2/p115uploadenhancer/`
- 新插件主类改为 `P115UploadEnhancer`
- 插件目录为 `p115uploadenhancer`
- 插件显示名改为 `115上传增强`
- 作者信息改为 `beatter789`
- 配置前缀改为 `p115uploadenhancer_`
- 版本设置为 `1.0.0`
- `package.v2.json` 已加入 `P115UploadEnhancer`
- Plus `P115Api` 已开始整合上传增强配置和等待逻辑

### 重要兼容约束

新插件会提供 `115网盘Plus` 存储模块，因此不能和原 `P115Disk` 同时启用。

使用新插件时需要：

1. 停用原 `P115Disk`
2. 关闭 `P115StrmHelper` 的“上传模块增强”
3. 启用 `P115UploadEnhancer`
4. 在新插件中配置 Cookie
5. 确认 MoviePilot 使用 `115网盘Plus`

原 `P115StrmHelper` 源码本轮没有修改。

### 本轮实际变更

- 新增 `plugins.v2/p115uploadenhancer/`，复制 Plus 存储基础代码
- 主类改为 `P115UploadEnhancer`
- `package.v2.json` 新增 `P115UploadEnhancer` 条目
- 将 Plus `P115Api.upload` 复制到独立插件并接入上传配置
- 增加基础等待、等待超时、阈值和秒传失败跳过逻辑
- 将复制代码中的缓存命名空间改为 `p115uploadenhancer_`
- 新增插件 README
- 确认原 `MoviePilot-Plugins-main-v2` 未修改

### 本轮验证

- 首次递归编译命令因 PowerShell 不展开通配符而失败，已改用逐文件路径编译
- JSON 结构校验通过
- 独立插件 Python 文件编译通过
- 目标目录不是 Git 工作树，无法在该目录直接执行 Git 状态检查
- 尚未完成运行时导入测试和版本门禁
- 当前代码仍需清理部分 `P115Disk` 日志/API 文本，并完成上传通知独立化

### 待完成

- 完善独立插件配置页面中的上传增强配置项展示（本轮已加入基础字段）
- 完成上传通知的独立实现
- 清理复制代码中与旧插件无关的引用和日志名（仍有部分待清理）
- 增加冲突检测，避免原 `P115Disk` 同时启用
- 添加 README
- 添加测试和静态校验
- 检查 Python 语法、JSON、版本门禁和目录规范
- 继续更新本文件

### 本轮测试评估

可以在当前环境完成：

- Python 语法编译
- JSON 解析
- AST/静态结构检查
- 目录名、主类名、清单键和版本一致性检查
- 使用 Mock 替身测试部分秒传/等待策略

当前环境不能完成：

- MoviePilot 宿主真实加载
- P115Disk/存储模块真实注册
- 使用真实 Cookie 访问 115
- 真实 SHA1 秒传判断
- 真实 OSS 分片上传、Token 刷新和取消流程

真实联调需要用户自己的 MoviePilot 环境和有效 115 Cookie。Cookie、Token、密码和 Machine ID 不要发送到聊天。

### 本轮上传准备

- 已确认目标仓库工作树为 `F:\工作区\v1\_remote-check`
- 将把目标仓库同步为当前 `MoviePilot-Plugins-main` 的插件代码和清单
- 本轮不上传 `CloudDrive2` 代码
- 上传前会再次执行 Python 编译、JSON 校验、目录/类名/版本检查
- 推送若受 GitHub 网络或凭据影响，将提供用户 PowerShell 推送命令

### 安全说明

本文件不得记录 Cookie、Token、密码、Machine ID 或其他账号秘密。
