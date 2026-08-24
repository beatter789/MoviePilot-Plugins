# 115上传增强

独立提供 `115网盘Plus` 存储模块，并增强上传过程中的 SHA1 秒传等待、等待超时和秒传失败处理

## 使用限制

- 本插件只支持 `115网盘Plus`
- 不支持 CloudDrive2
- 不接管 MoviePilot 原生 `u115`
- 不能和原 `P115Disk` 同时启用
- 使用本插件时，请关闭 `P115StrmHelper` 的“上传模块增强”，避免两个插件同时修改上传逻辑

## 迁移步骤

1. 记录原 `P115Disk` 的 Cookie 和超时配置
2. 停用原 `P115Disk`
3. 关闭 `P115StrmHelper` 的“上传模块增强”
4. 安装并启用本插件
5. 填写 Cookie
6. 确认 MoviePilot 的存储模块使用 `115网盘Plus`

## 秒传判断

插件使用 `p115client.upload_file_init` 初始化上传，并提交：

- 文件大小
- 文件完整 SHA1
- 大文件所需的范围 SHA1

当返回 `reuse` 时，表示 115网盘Plus 已完成秒传复用，插件不会继续上传文件

## CloudDrive2

CloudDrive2 Remote Upload 支持 MD5、SHA1 和 PikPakSha1 哈希协商，但没有独立的 SHA1 秒传查询 RPC。本插件不接管 CloudDrive2
