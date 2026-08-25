from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import ChainEventType
from app.helper.storage import StorageHelper
from app.schemas import StorageOperSelectionEventData, FileItem, StorageUsage

from .account import P115AccountService
from .p115_api import P115Api
from .request_guard import P115RequestGuard
from .p115_client import create_client, build_timeout_config


class P115UploadEnhancer(_PluginBase):
    """
    115 网盘储存插件：更快更强的 115 网盘存储模块，支持文件列表、上传下载、快照等功能
    """

    # 插件名称
    plugin_name = "115上传增强"
    # 插件描述
    plugin_desc = "提供115网盘Plus存储模块并增强上传、秒传等待和失败处理。"
    # 插件图标
    plugin_icon = (
        "https://raw.githubusercontent.com/jxxghp/MoviePilot-Frontend/"
        "refs/heads/v2/src/assets/images/misc/u115.png"
    )
    # 插件版本
    plugin_version = "1.1.1"
    # 插件作者
    plugin_author = "beatter789"
    # 作者主页
    author_url = "https://github.com/beatter789"
    # 插件配置项ID前缀
    plugin_config_prefix = "p115uploadenhancer_"
    # 加载顺序
    plugin_order = 99
    # 可使用的用户级别
    auth_level = 1

    # 是否启用
    _enabled = False
    _client = None
    _disk_name = None
    _p115_api = None
    _cookie = None
    _account_service = None
    _config = {}

    def __init__(self):
        """
        初始化
        """
        super().__init__()

        self._disk_name = "115网盘Plus"

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        if not config:
            return

        self._config = dict(config)
        _, form_defaults = self.get_form()
        merged = {**form_defaults, **config}
        if merged != config:
            self.update_config(merged)
        config = merged

        if config:
            storage_helper = StorageHelper()
            storages = storage_helper.get_storagies()
            if not any(
                s.type == self._disk_name and s.name == self._disk_name
                for s in storages
            ):
                storage_helper.add_storage(
                    storage=self._disk_name, name=self._disk_name, conf={}
                )

            self._enabled = config.get("enabled")
            self._cookie = config.get("cookie")

            if not self._cookie:
                self._account_service = P115AccountService(
                    client=None,
                    guard=P115RequestGuard(interval=1.0, circuit_seconds=600.0),
                )
                return

            try:
                timeout_kwargs = {}
                if config.get("timeout_enabled", True):
                    timeout_kwargs["default_timeout"] = build_timeout_config(
                        timeout_enabled=True,
                        connect=config.get("timeout_default_connect", 30),
                        pool=config.get("timeout_default_pool", 15),
                        read=config.get("timeout_default_read", 60),
                        write=config.get("timeout_default_write", 60),
                    )
                    timeout_kwargs["slow_timeout"] = build_timeout_config(
                        timeout_enabled=True,
                        connect=config.get("timeout_slow_connect", 30),
                        pool=config.get("timeout_slow_pool", 15),
                        read=config.get("timeout_slow_read", 300),
                        write=config.get("timeout_slow_write", 300),
                    )
                self._client = create_client(
                    self._cookie,
                    **timeout_kwargs,
                )
                self._p115_api = P115Api(
                    client=self._client,
                    disk_name=self._disk_name,
                    upload_config=config,
                )
                self._account_service = P115AccountService(
                    client=self._p115_api.client,
                    guard=self._p115_api._request_guard,
                )
            except Exception as e:
                logger.error(f"115 网盘客户端创建失败: {e}")

    def get_state(self) -> bool:
        """
        返回插件启用状态

        :return bool: True 表示插件已启用
        """
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        返回插件远程命令列表，本插件无远程命令

        :return List: 远程命令列表（本插件为空）
        """
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取插件 API 端点

        :return List: 插件 API 端点列表
        """
        return [
            {
                "path": "/clear_cache",
                "endpoint": self.clear_cache,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "清理缓存",
                "description": "清理115网盘文件路径ID缓存和文件详情ID缓存",
            },
            {
                "path": "/account_status",
                "endpoint": self.account_status,
                "auth": "bear",
                "methods": ["GET"],
                "summary": "获取115账户状态",
                "description": "检查Cookie并获取115账户和空间信息",
            },
            {
                "path": "/refresh_account_status",
                "endpoint": self.refresh_account_status,
                "auth": "bear",
                "methods": ["POST"],
                "summary": "刷新115账户状态",
                "description": "强制刷新115账户和空间信息",
            },
        ]

    def account_status(self) -> Dict[str, Any]:
        """
        获取 Cookie 有效性、115账户信息和空间信息

        :return Dict: 账户状态
        """
        logger.info("【115上传增强】开始检查115 Cookie和账户状态")
        if not self._account_service or not self._cookie:
            logger.warning("【115上传增强】未配置115 Cookie")
            return {
                "code": 1,
                "success": False,
                "cookie_valid": False,
                "error_message": "请在配置页面中设置有效的115网盘Cookie",
                "msg": "请在配置页面中设置有效的115网盘Cookie",
            }
        result = self._account_service.get_status()
        result["code"] = 0 if result.get("success") else 1
        result["msg"] = result.get("error_message") or "115账户信息获取成功"
        logger.info(
            "【115上传增强】115账户状态检查完成：%s",
            "有效" if result.get("success") else "无效",
        )
        return result

    def refresh_account_status(self) -> Dict[str, Any]:
        """
        强制刷新 Cookie、账户信息和空间信息

        :return Dict: 账户状态
        """
        logger.info("【115上传增强】用户请求刷新115账户信息")
        if not self._account_service or not self._cookie:
            return self.account_status()
        result = self._account_service.get_status(force=True)
        result["code"] = 0 if result.get("success") else 1
        result["msg"] = result.get("error_message") or "115账户信息刷新成功"
        logger.info(
            "【115上传增强】115账户信息刷新完成：%s",
            "成功" if result.get("success") else "失败",
        )
        return result

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """
        返回 Vue 配置页面的初始配置

        :return Tuple: Vue 页面不使用 VForm，返回空页面和默认配置
        """
        return self.get_legacy_form()

    def get_legacy_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """
        保留旧版 VForm 配置结构


        :return Tuple: 页面配置和数据结构的元组
        """
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 12},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "cookie",
                                            "label": "115 Cookie",
                                             "variant": "outlined",
                                             "density": "comfortable",
                                            "hint": "Cookie 可以复用 115 网盘 STRM 助手的配置",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 3},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "upload_module_enhancement",
                                            "label": "启用上传增强",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 3},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "upload_module_skip_slow_upload",
                                            "label": "秒传失败跳过上传",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "props": {"v-if": "upload_module_enhancement"},
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [{"component": "VTextField", "props": {"model": "upload_module_wait_time", "label": "等待间隔（秒）", "type": "number", "min": 0}}],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [{"component": "VTextField", "props": {"model": "upload_module_wait_timeout", "label": "最长等待（秒）", "type": "number", "min": 0}}],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [{"component": "VTextField", "props": {"model": "upload_module_skip_upload_wait_size", "label": "跳过等待大小", "placeholder": "例如 800M、1G、1024K", "hint": "文件大小小于等于此值时直接上传；支持 K/M/G/T，0 表示不跳过", "persistent-hint": True}}],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [{"component": "VTextField", "props": {"model": "upload_module_force_upload_wait_size", "label": "强制等待大小", "placeholder": "例如 5G、1024M", "hint": "用于标记大文件强制等待并写入日志；0 表示关闭，支持 K/M/G/T", "persistent-hint": True}}],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "props": {"v-if": "upload_module_enhancement && upload_module_skip_slow_upload"},
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [{"component": "VTextField", "props": {"model": "upload_module_skip_slow_upload_size", "label": "秒传失败跳过上传大小", "placeholder": "例如 5G；0 表示所有文件", "hint": "达到此大小后，等待结束仍不能秒传则返回失败，不进行真实上传", "persistent-hint": True}}],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 3},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "timeout_enabled",
                                            "label": "启用超时控制",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "props": {"v-if": "timeout_enabled"},
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_default_connect",
                                            "label": "普通-连接超时(秒)",
                                            "hint": "默认30",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_default_pool",
                                            "label": "普通-连接池超时(秒)",
                                            "hint": "默认15",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_default_read",
                                            "label": "普通-读取超时(秒)",
                                            "hint": "默认60",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_default_write",
                                            "label": "普通-写入超时(秒)",
                                            "hint": "默认60",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "props": {"v-if": "timeout_enabled"},
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_slow_connect",
                                            "label": "慢操作-连接超时(秒)",
                                            "hint": "默认30",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_slow_pool",
                                            "label": "慢操作-连接池超时(秒)",
                                            "hint": "默认15",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_slow_read",
                                            "label": "慢操作-读取超时(秒)",
                                            "hint": "默认300",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 6, "md": 3},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "timeout_slow_write",
                                            "label": "慢操作-写入超时(秒)",
                                            "hint": "默认300",
                                            "persistent-hint": True,
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [{"component": "VBtn", "props": {"color": "secondary", "variant": "outlined", "prepend-icon": "mdi-account-check", "block": True}, "text": "检查 Cookie", "events": {"click": {"api": "plugin/P115UploadEnhancer/refresh_account_status", "method": "post"}}}],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [{"component": "VBtn", "props": {"color": "warning", "variant": "outlined", "prepend-icon": "mdi-delete-sweep", "block": True}, "text": "清理缓存", "events": {"click": {"api": "plugin/P115UploadEnhancer/clear_cache", "method": "post"}}}],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [{"component": "VAlert", "props": {"type": "info", "variant": "tonal", "density": "compact"}, "text": "可在这里检查账户状态或清理本地路径缓存。清理缓存不会删除网盘文件，也不会清除 Cookie。"}],
                            },
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "cookie": "",
            "upload_module_enhancement": True,

            "upload_module_wait_time": 300,
            "upload_module_wait_timeout": 3600,
            "upload_module_skip_upload_wait_size": "0",
            "upload_module_force_upload_wait_size": "0",
            "upload_module_skip_slow_upload": False,
            "upload_module_skip_slow_upload_size": "0",
            "timeout_enabled": True,
            "timeout_default_connect": 30,
            "timeout_default_pool": 15,
            "timeout_default_read": 60,
            "timeout_default_write": 60,
            "timeout_slow_connect": 30,
            "timeout_slow_pool": 15,
            "timeout_slow_read": 300,
            "timeout_slow_write": 300,
        }

    def get_page(self) -> List[dict]:
        """
        获取插件主页面

        :return List: 插件数据页面配置列表
        """
        status = self.account_status()
        if status.get("success"):
            user_info = status.get("user_info") or {}
            storage_info = status.get("storage_info") or {}
            status_text = (
                f"Cookie：有效\n"
                f"用户名：{user_info.get('name') or '未知'}\n"
                f"VIP：{'永久' if user_info.get('is_forever_vip') else '是' if user_info.get('is_vip') else '否'}\n"
                f"VIP到期：{user_info.get('vip_expire_date') or '无'}\n"
                f"总空间：{storage_info.get('total') or '未知'}\n"
                f"已用空间：{storage_info.get('used') or '未知'}\n"
                f"剩余空间：{storage_info.get('remaining') or '未知'}"
            )
            alert_type = "success"
        else:
            status_text = status.get(
                "error_message", "请在配置页面中设置有效的115网盘Cookie"
            )
            alert_type = "warning"
        rows = []
        if status.get("success"):
            user_info = status.get("user_info") or {}
            storage_info = status.get("storage_info") or {}
            rows = [
                ("Cookie", "有效"),
                ("用户名", user_info.get("name") or "未知"),
                (
                    "VIP",
                    "永久" if user_info.get("is_forever_vip") else "是" if user_info.get("is_vip") else "否",
                ),
                ("VIP到期", user_info.get("vip_expire_date") or "无"),
                ("总空间", storage_info.get("total") or "未知"),
                ("已用空间", storage_info.get("used") or "未知"),
                ("剩余空间", storage_info.get("remaining") or "未知"),
            ]
        else:
            rows = [("Cookie", status_text)]
        row_content = []
        for label, value in rows:
            row_content.append(
                {
                    "component": "VRow",
                    "props": {"dense": True, "class": "py-1"},
                    "content": [
                        {
                            "component": "VCol",
                            "props": {"cols": 4, "sm": 3, "class": "text-medium-emphasis"},
                            "text": label,
                        },
                        {
                            "component": "VCol",
                            "props": {"cols": 8, "sm": 9},
                            "text": value,
                        },
                    ],
                }
            )
        row_content.append(
            {
                "component": "VBtn",
                "props": {"color": "primary", "prepend-icon": "mdi-account-check", "class": "mt-3"},
                "text": "刷新账户信息",
                "events": {"click": {"api": "plugin/P115UploadEnhancer/refresh_account_status", "method": "post"}},
            }
        )
        return [
            {
                "component": "VCard",
                "props": {"variant": "outlined"},
                "content": [
                    {"component": "VCardTitle", "text": "115账户信息"},
                    {
                        "component": "VCardText",
                        "content": [
                            {
                                "component": "VAlert",
                                "props": {"type": alert_type, "variant": "tonal"},
                                "text": status_text if not status.get("success") else "账户状态正常",
                            },
                            *row_content,
                        ],
                    },
                ],
            }
        ]

    def get_module(self) -> Dict[str, Any]:
        """
        获取插件模块声明，用于胁持系统模块实现

        :return Dict: 模块方法映射字典
        """
        return {
            "list_files": self.list_files,
            "any_files": self.any_files,
            "download_file": self.download_file,
            "upload_file": self.upload_file,
            "delete_file": self.delete_file,
            "rename_file": self.rename_file,
            "get_file_item": self.get_file_item,
            "get_parent_item": self.get_parent_item,
            "snapshot_storage": self.snapshot_storage,
            "storage_usage": self.storage_usage,
            "support_transtype": self.support_transtype,
            "create_folder": self.create_folder,
            "exists": self.exists,
            "get_item": self.get_item,
        }

    @eventmanager.register(ChainEventType.StorageOperSelection)
    def storage_oper_selection(self, event: Event):
        """
        监听存储选择事件，返回当前类为操作对象

        :param event (Event): 存储选择事件
        """
        if not self._enabled:
            return
        event_data: StorageOperSelectionEventData = event.event_data
        if event_data.storage == self._disk_name:
            event_data.storage_oper = self._p115_api  # noqa

    def list_files(
        self, fileitem: FileItem, recursion: bool = False
    ) -> Optional[List[FileItem]]:
        """
        查询当前目录下所有目录和文件

        :param fileitem (FileItem): 目录文件项
        :param recursion (bool): 是否递归查询

        :return List: 文件项列表，如果存储不匹配则返回 None
        """

        if fileitem.storage != self._disk_name:
            return None

        if recursion:
            result = self._p115_api.iter_files(fileitem)
            if result is not None:
                return result

        def __get_files(_item: FileItem, _r: Optional[bool] = False):
            """
            递归处理
            """
            _items = self._p115_api.list(_item)
            if _items:
                if _r:
                    for t in _items:
                        if t.type == "dir":
                            __get_files(t, _r)
                        else:
                            result.append(t)
                else:
                    result.extend(_items)

        result = []
        __get_files(fileitem, recursion)

        return result

    def any_files(self, fileitem: FileItem, extensions: list = None) -> Optional[bool]:
        """
        查询当前目录下是否存在指定扩展名任意文件

        :param fileitem (FileItem): 目录文件项
        :param extensions (List): 扩展名列表，如 [\".mkv\", \".mp4\"]，为 None 表示查询任意文件

        :return bool: 存在返回 True，不存在返回 False，存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        def __any_file(_item: FileItem):
            """
            递归处理
            """
            _items = self._p115_api.list(_item)
            if _items:
                if not extensions:
                    return True
                for t in _items:
                    if (
                        t.type == "file"
                        and t.extension
                        and f".{t.extension.lower()}" in extensions
                    ):
                        return True
                    elif t.type == "dir":
                        if __any_file(t):
                            return True
            return False

        return __any_file(fileitem)

    def create_folder(self, fileitem: FileItem, name: str) -> Optional[FileItem]:
        """
        创建目录

        :param fileitem (FileItem): 父目录文件项
        :param name (str): 要创建的目录名称

        :return FileItem: 创建成功返回目录文件项，失败或存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p115_api.create_folder(fileitem=fileitem, name=name)

    def download_file(self, fileitem: FileItem, path: Path = None) -> Optional[Path]:
        """
        下载文件

        :param fileitem (FileItem): 文件项
        :param path (Path): 本地保存路径

        :return Path: 下载成功返回本地文件路径，失败或存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p115_api.download(fileitem, path)

    def upload_file(
        self, fileitem: FileItem, path: Path, new_name: Optional[str] = None
    ) -> Optional[FileItem]:
        """
        上传文件

        :param fileitem (FileItem): 保存目录项
        :param path (Path): 本地文件路径
        :param new_name (str): 新文件名，为 None 则使用本地文件名

        :return FileItem: 上传成功返回文件项，失败或存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p115_api.upload(fileitem, path, new_name)

    def delete_file(self, fileitem: FileItem) -> Optional[bool]:
        """
        删除文件或目录

        :param fileitem (FileItem): 要删除的文件项

        :return bool: 删除成功返回 True，失败或存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p115_api.delete(fileitem)

    def rename_file(self, fileitem: FileItem, name: str) -> Optional[bool]:
        """
        重命名文件或目录

        :param fileitem (FileItem): 要重命名的文件项
        :param name (str): 新名称

        :return bool: 重命名成功返回 True，失败或存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p115_api.rename(fileitem, name)

    def exists(self, fileitem: FileItem) -> Optional[bool]:
        """
        判断文件或目录是否存在

        :param fileitem (FileItem): 文件项

        :return bool: 存在返回 True，不存在返回 False，存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return True if self.get_item(fileitem) else False

    def get_item(self, fileitem: FileItem) -> Optional[FileItem]:
        """
        查询目录或文件

        :param fileitem (FileItem): 文件项

        :return FileItem: 查询到的文件项，不存在或存储不匹配返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return self.get_file_item(storage=fileitem.storage, path=Path(fileitem.path))

    def get_file_item(self, storage: str, path: Path) -> Optional[FileItem]:
        """
        根据路径获取文件项

        :param storage (str): 存储类型
        :param path (Path): 文件路径

        :return FileItem: 文件项，存储不匹配或不存在返回 None
        """
        if storage != self._disk_name:
            return None

        return self._p115_api.get_item(path)

    def get_parent_item(self, fileitem: FileItem) -> Optional[FileItem]:
        """
        获取上级目录项

        :param fileitem (FileItem): 文件项

        :return FileItem: 上级目录文件项，存储不匹配或不存在返回 None
        """
        if fileitem.storage != self._disk_name:
            return None

        return self._p115_api.get_parent(fileitem)

    def snapshot_storage(
        self,
        storage: str,
        path: Path,
        last_snapshot_time: float = None,
        max_depth: int = 5,
    ) -> Optional[Dict[str, Dict]]:
        """
        快照存储

        :param storage (str): 存储类型
        :param path (Path): 路径
        :param last_snapshot_time (float): 上次快照时间，用于增量快照
        :param max_depth (int): 最大递归深度，避免过深遍历

        :return Dict: 文件信息字典，key 为文件路径，value 为文件信息
        """
        if storage != self._disk_name:
            return None

        files_info = {}

        def __snapshot_file(_fileitm: FileItem, current_depth: int = 0):
            """
            递归获取文件信息
            """
            try:
                if _fileitm.type == "dir":
                    if current_depth >= max_depth:
                        return

                    if (
                        self.snapshot_check_folder_modtime  # noqa
                        and last_snapshot_time
                        and _fileitm.modify_time
                        and _fileitm.modify_time <= last_snapshot_time
                    ):
                        return

                    sub_files = self._p115_api.list(_fileitm)
                    for sub_file in sub_files:
                        __snapshot_file(sub_file, current_depth + 1)
                else:
                    if getattr(_fileitm, "modify_time", 0) > last_snapshot_time:
                        files_info[_fileitm.path] = {
                            "size": _fileitm.size or 0,
                            "modify_time": getattr(_fileitm, "modify_time", 0),
                            "type": _fileitm.type,
                        }

            except Exception as e:
                logger.debug(f"Snapshot error for {_fileitm.path}: {e}")

        fileitem = self._p115_api.get_item(path)
        if not fileitem:
            return {}

        __snapshot_file(fileitem)

        return files_info

    def storage_usage(self, storage: str) -> Optional[StorageUsage]:
        """
        存储使用情况

        :param storage (str): 存储类型

        :return StorageUsage: 存储使用情况对象，存储不匹配返回 None
        """
        if storage != self._disk_name:
            return None

        return self._p115_api.usage()

    def support_transtype(self, storage: str) -> Optional[dict]:
        """
        获取支持的整理方式

        :param storage (str): 存储类型

        :return Dict: 支持的整理方式字典，存储不匹配返回 None
        """
        if storage != self._disk_name:
            return None

        return {"move": "移动", "copy": "复制"}

    def clear_cache(self) -> Dict[str, Any]:
        """
        清理缓存

        :return Dict: 清理结果，包含 code 和 msg
        """
        try:
            if not self._p115_api:
                return {
                    "code": 1,
                    "msg": "插件未启用或未初始化",
                }

            self._p115_api._id_cache.clear()
            self._p115_api._id_item_cache.clear()

            logger.info("【115上传增强】缓存清理成功")
            return {
                "code": 0,
                "msg": "缓存清理成功",
            }
        except Exception as e:
            logger.error(f"【115上传增强】缓存清理失败: {e}", exc_info=True)
            return {
                "code": 1,
                "msg": f"缓存清理失败: {str(e)}",
            }

    def stop_service(self):
        """
        退出插件
        """
        pass
