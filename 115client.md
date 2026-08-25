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

### 本轮完成

- 已完成目标仓库同步到 `F:\工作区\v1\_remote-check`
- 已通过 Python 编译和 JSON 校验
- 已通过插件 ID、目录、主类、版本和作者静态检查
- 已通过 Git 暂存区 `diff --check`
- 已创建提交：`a199586 feat(p115uploadenhancer): add standalone 115 plus upload enhancement`
- Git 提交包含 AI 协作者信息
- Harness 使用 `127.0.0.1:7890` 代理推送失败，提示代理无法连接；本地提交仍已完成
- 需要用户在自己运行代理的 PowerShell 中推送

### 本轮上传准备

- 已确认目标仓库工作树为 `F:\工作区\v1\_remote-check`
- 将把目标仓库同步为当前 `MoviePilot-Plugins-main` 的插件代码和清单
- 本轮不上传 `CloudDrive2` 代码
- 上传前会再次执行 Python 编译、JSON 校验、目录/类名/版本检查
- 推送若受 GitHub 网络或凭据影响，将提供用户 PowerShell 推送命令

### 2026-06-09：配置语义复核

- `upload_module_skip_upload_wait_size` 单位为字节；文件大小小于等于该值时不等待秒传，直接进入真实上传
- `upload_module_force_upload_wait_size` 单位为字节；当前独立实现配置非零后，仅文件大小大于等于该值时进入等待
- `upload_module_skip_slow_upload_size` 单位为字节；“秒传失败跳过上传”开启后，阈值为 0 时所有秒传失败文件均返回失败，阈值非零时仅大于等于阈值的文件返回失败
- 当前配置页尚未展示 `upload_module_skip_slow_upload_size` 输入框
- 复核发现 `upload_module_enhancement` 总开关当前尚未接入上传方法判断，上传等待规则仍会运行；这是发布前需要修复的问题
- 当前强制等待条件与原 P115StrmHelper 的动态等待语义并不完全一致，需要在下一版本修正后再建议正式使用

### 2026-06-09：v1.0.1 配置与等待逻辑修复

#### 已修复

- `upload_module_enhancement` 总开关已真正接入上传逻辑
- 删除首次秒传失败后提前退出等待循环的问题
- 等待循环会按照配置间隔持续重试，直到秒传成功、用户取消或达到最长等待时间
- 最长等待结束且未启用“秒传失败跳过上传”时进入正常 OSS 分片上传
- 文件大小输入支持纯字节以及 `K`、`M`、`G`、`T` 单位，大小写不敏感，按 1024 进制换算
- 配置页新增“秒传失败跳过上传大小”输入框
- 删除未实现的通知配置项，避免界面给出无效开关
- 删除 `package.v2.json` 的 `release: true`，避免没有 GitHub Release 时出现 404
- 版本升级为 `1.0.1`

#### 配置示例语义

```text
等待间隔：300
最长等待：7200
跳过等待大小：800M
强制等待大小：0
秒传失败跳过上传：关闭
```

- 800MB 及以下首次秒传失败后直接真实上传
- 大于 800MB 的文件每 5 分钟重试秒传
- 任何一次 `reuse=True` 即秒传成功并结束
- 最长等待 2 小时后仍不能秒传则正常分片上传
- “强制等待大小”设置为 0 时关闭强制标记，不影响上述普通等待

#### 验证

- 所有插件 Python 文件编译通过
- `package.v2.json` 解析通过
- 插件 ID、目录、主类、作者和 `1.0.1` 版本一致性通过
- 确认清单不再包含 `release` 字段
- `test_upload_policy.py` 共 3 项测试通过：大小解析、等待阈值、秒传失败跳过真实上传

### 2026-06-09：强制等待阈值语义说明

当前 `1.0.1` 实现中：

- “跳过等待大小”决定是否进入等待：文件大小小于等于该值时直接真实上传，大于该值时进入等待
- “强制等待大小”目前只判断并记录 `强制等待=是/否` 日志，不会改变等待时长、重试次数或超时后的上传结果
- 配置 `跳过等待大小=800M`、`强制等待大小=5G` 时：
  - 小于等于 800MB：首次秒传失败后直接真实上传
  - 大于 800MB 且小于 5GB：进入普通等待
  - 大于等于 5GB：进入相同等待流程，但日志标记为强制等待
- 由于独立插件未移植原 P115StrmHelper 的中心测速决策，当前普通等待和强制等待没有实质行为差异
- 若要让“强制等待”具有真实作用，需要下一版明确普通等待的提前退出条件，再让达到强制阈值的文件忽略提前退出并等待到总超时

### 2026-08-24：用户反馈 405/401 上传后查询异常

#### 日志结论

- `HTTP Error 405: Method Not Allowed` 出现在独立插件 `P115Api._query_item()` 的 `get_id_to_path()` / `get_attr()` 查询链，不是上传等待逻辑本身
- Plus 查询失败后，`get_item()` 会回退到 MoviePilot 原生 `u115` 存储
- 原生 `u115` 返回 `HTTP 401 Unauthorized`，随后抛出“请先扫码登录”，说明 u115 存储没有有效登录状态或没有配置扫码登录
- 405 本身不等于“频繁拉取导致风控”，当前代码已有 `get_item`、list、路径查询限流和缓存；日志不足以单独证明频率触发风控

#### 可能原因排序

1. 115 Web API 对当前请求方法/接口组合返回 405
2. p115client、P115Disk 来源代码和当前 115 服务端接口不匹配
3. 115 会话、设备签名或稳定点缓存失效，导致接口异常
4. 短时间内反复 list/query 触发风控，可能性存在但尚未证实
5. u115 降级链未登录，导致 405 后又出现 401

#### 当前建议

- 先不要反复刷新目录或重复重试，避免放大请求量
- 确认新的 `115上传增强` 使用有效 Cookie
- 如果 MoviePilot 同时启用了原生 u115 存储，完成扫码登录或暂时避免触发该降级链
- 保留首次 405 前后的完整日志，用于区分接口不匹配和风控
- 后续应增加 405 冷却熔断，避免 Web API 失败后连续调用 u115 降级；同时需要确认 p115client 版本和 P115Disk 版本是否匹配

本轮未修改代码，仅完成日志分析和工作记录更新。

### 2026-08-24：与原始 P115Disk 逐文件对比

#### 对比结果

- `p115_client.py`、`tools.py`、`requirements.txt` 与原始 Plus 插件一致
- `cache.py` 仅将缓存命名空间从 `p115disk_` 改为 `p115uploadenhancer_`，属于必要隔离
- `__init__.py` 主要差异为类名、插件元数据、配置前缀、上传配置注入和新增上传配置页面
- `p115_api.py` 的公共 API 方法结构与原始文件一致，差异主要为上传策略和日志名称

#### 发现并修复

- 原始复制代码在 Plus 查询异常后会降级调用原生 `u115`
- 该降级会导致 Plus 405 后继续触发原生 u115 401“请先扫码登录”，形成用户日志中的 405 + 401 混合错误
- 独立插件已移除 `_get_u115_item()` 降级调用，Plus 查询失败现在直接抛出明确的 `Plus 查询文件信息失败`
- 这样符合本插件只支持 `115网盘Plus` 的要求，也不会再把原生 u115 的登录状态混入 Plus 插件
- 删除 `StorageChain` 导入后重新编译通过

#### 尚未发现的结构性问题

- 未发现独立插件缺少原始 P115Api 公共方法
- 未发现 `p115_client.py`、依赖或 UA 工具被错误改写
- 本轮只修改目标独立插件，没有修改原始 `MoviePilot-Plugins-main-v2`

### 2026-08-24：检查 P115StrmHelper 速率限制

- `utils/limiter.py` 提供 `RateLimiter(qps)` 和 `ApiEndpointCooldown(cooldown)`
- `core/p115.py` 的分享接口按速度档位使用 0.25/0.5/1/1.5 秒冷却，注释明确 `pro.api.115.com` 风控严重
- `api.py` 的 `browse_dir_api` 对网盘目录接口设置至少 2 秒间隔，并缓存目录结果
- `api.py` 的 `fs_files_iter` 设置 `cooldown=2`，即分页目录请求之间至少间隔 2 秒
- `core/p115.py` 的通用分页迭代器支持 cooldown，且会在每次接口调用前等待到达最小间隔
- `core/u115_open.py` 的下载链接接口使用 `RateLimiter(qps=1.0)`，并处理 429/Retry-After
- `core/p115disk.py` 上传初始化失败使用 3 次重试和 2、4 秒退避；秒传等待间隔由配置控制
- P115StrmHelper 没有发现一个覆盖所有 115 接口的统一“每秒 2 次”全局限流器；它是按接口/操作分别限流、冷却和缓存
- 独立 P115UploadEnhancer 当前 `p115_api.py` 的 `fs_files_iter` 仍使用 `cooldown=1.5`，比 P115StrmHelper 的目录分页 2 秒更激进
- 独立插件当前 RateLimiter 也是按操作分别计数，`storage_usage`、`list`、`get_item` 等不会共享全局额度；这可能允许并发请求叠加
- 后续应至少将目录分页 cooldown 提高到 2 秒，并为 115 API 增加跨操作全局请求锁/节流，以及 405 冷却熔断

### 2026-08-24：v1.0.2 请求保护修复

#### 已完成

- 目录分页 `fs_files_iter` 的 cooldown 从 `1.5` 秒调整为 `2` 秒
- 新增 `request_guard.py`，对独立插件内的 P115Client 调用增加共享请求节流，默认两次请求至少间隔 `1` 秒
- 任一请求出现 HTTP 405 后开启 10 分钟熔断
- 熔断期间不再向 115 发起请求，直接返回冷却提示
- `list()` 增加实例级并发锁，避免同一插件实例同时扫描目录
- `usage()` 增加 60 秒缓存和并发锁，避免 MoviePilot 重复请求存储用量
- 移除 Plus 查询失败后调用原生 `u115` 的降级路径
- 版本升级为 `1.0.2`

#### 验证

- 独立插件全部 Python 文件编译通过
- JSON 解析和版本一致性通过
- 原有 3 项上传策略测试通过
- 新增 3 项请求防护测试通过：共享间隔、405 熔断、405 识别
- 未修改 `MoviePilot-Plugins-main-v2`

#### 注意

- 共享节流只覆盖本独立插件实例；如果原生 u115、P115Disk 或其他插件同时启用，它们各自的请求不会共享此限流器
- 405 熔断默认 600 秒（10 分钟），重启插件/容器后内存状态会清除
- 这次修复降低请求频率，但不能保证 115 服务端一定不再返回 405；仍需观察真实环境日志

### 2026-08-24：v1.0.3 扫码登录与账户状态

#### 已完成

- 新增 `account.py`，参考 P115StrmHelper 实现 115 二维码获取、扫码状态检查、登录结果 Cookie 解析、账户信息和空间信息查询
- 配置页新增获取二维码、检查 Cookie、清理缓存按钮
- 主页面显示 Cookie 状态、用户名、VIP 状态、VIP 到期时间、总空间、已用空间和剩余空间
- 主页面的清理缓存按钮已移除，清理缓存移动到配置页面
- 清理缓存只清理路径 ID 和文件详情本地缓存，不删除网盘文件、不清除 Cookie
- Cookie 缺失或无效时显示 `请在配置页面中设置有效的115网盘Cookie`
- 账户成功状态缓存 1 小时，失败状态缓存 5 分钟
- 账户状态使用并发锁，避免页面刷新产生重复的用户信息和空间请求
- 二维码状态由页面按约 2 秒轮询，登录成功后保存 Cookie 并重建客户端
- 二维码获取、状态检查和账户请求均接入共享节流与 405 熔断
- 新增 `qrcode` 依赖
- 版本升级为 `1.0.3`

#### 请求频率

- 账户成功检查：默认最多每小时真实请求一次；主页面重复加载使用缓存
- 账户检查失败：默认 5 分钟内使用失败缓存，不重复请求
- 手动“检查 Cookie/刷新账户信息”：强制清除缓存并请求一次，但仍受共享节流和 405 熔断保护
- 用户点击获取二维码：每次点击请求一次
- 二维码状态轮询：前端建议约 2 秒一次；服务端不创建后台轮询任务
- 二维码登录成功后立即停止前端轮询
- 405 后沿用 10 分钟熔断

#### 2026-08-24：页面反馈修复

- 扫码按钮无反馈：为二维码、Cookie检查、账户刷新接口增加明确的开始/成功/失败日志和统一 `code/msg` 返回字段
- Cookie 输入框上边框显示异常：VTextField 增加 `variant=outlined` 和 `density=comfortable`
- 刷新账户信息和检查 Cookie 无日志：新增用户操作日志、未配置 Cookie 日志和检查结果日志
- 主页面账户状态现在会直接调用账户状态接口，并显示 Cookie、用户名、VIP 和空间摘要
- 当前 VForm 按钮事件可以调用后端接口并返回结果；若宿主不支持返回值绑定，二维码图片仍不会自动显示，自动轮询也需要后续使用 Vue 数据页面实现

#### 测试

- 全部 Python 文件编译通过
- JSON 校验通过
- 上传策略、请求保护、账户状态和二维码状态共 9 项 Mock 测试通过
- 测试没有输出 Cookie 或完整登录响应

### 安全说明

本文件不得记录 Cookie、Token、密码、Machine ID 或其他账号秘密。
