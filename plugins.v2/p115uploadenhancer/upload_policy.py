import re
from typing import Optional, Union


_SIZE_PATTERN = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([KMGT]?)B?\s*$", re.IGNORECASE)
_SIZE_MULTIPLIERS = {
    "": 1,
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
    "T": 1024**4,
}


def parse_size(value: Optional[Union[str, int, float]]) -> int:
    """
    将带单位的文件大小转换为字节

    支持纯数字字节值以及 K、M、G、T 单位，单位按 1024 进制换算

    :param value (str): 文件大小配置值

    :return int: 文件大小字节数，无值或格式无效时返回 0
    """
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return max(int(value), 0)
    match = _SIZE_PATTERN.fullmatch(str(value))
    if not match:
        return 0
    number = float(match.group(1))
    unit = match.group(2).upper()
    return max(int(number * _SIZE_MULTIPLIERS[unit]), 0)


def should_wait_for_reuse(
    enabled: bool,
    file_size: int,
    skip_wait_size: int,
    wait_time: int,
    wait_timeout: int,
) -> bool:
    """
    判断文件秒传失败后是否进入等待重试

    :param enabled (bool): 上传增强是否启用
    :param file_size (int): 文件大小
    :param skip_wait_size (int): 跳过等待阈值
    :param wait_time (int): 重试间隔秒数
    :param wait_timeout (int): 最长等待秒数

    :return bool: 是否进入等待重试
    """
    return (
        enabled
        and wait_time > 0
        and wait_timeout > 0
        and file_size > skip_wait_size
    )


def should_skip_real_upload(
    enabled: bool,
    file_size: int,
    threshold: int,
) -> bool:
    """
    判断秒传失败后是否跳过真实上传

    :param enabled (bool): 跳过真实上传是否启用
    :param file_size (int): 文件大小
    :param threshold (int): 生效阈值，0 表示全部文件

    :return bool: 是否跳过真实上传
    """
    return enabled and (threshold <= 0 or file_size >= threshold)
