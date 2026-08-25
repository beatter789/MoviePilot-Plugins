import unittest

from upload_policy import parse_size, should_skip_real_upload, should_wait_for_reuse


class UploadPolicyTest(unittest.TestCase):
    """
    上传增强策略测试
    """

    def test_parse_size_units(self) -> None:
        """
        测试 K、M、G 和纯字节输入
        """
        self.assertEqual(parse_size("1024K"), 1024 * 1024)
        self.assertEqual(parse_size("800M"), 800 * 1024**2)
        self.assertEqual(parse_size("1G"), 1024**3)
        self.assertEqual(parse_size(1024), 1024)
        self.assertEqual(parse_size("bad"), 0)

    def test_wait_threshold(self) -> None:
        """
        测试跳过等待阈值和总开关
        """
        threshold = parse_size("800M")
        self.assertFalse(
            should_wait_for_reuse(True, threshold, threshold, 300, 7200)
        )
        self.assertTrue(
            should_wait_for_reuse(True, threshold + 1, threshold, 300, 7200)
        )
        self.assertFalse(
            should_wait_for_reuse(False, threshold + 1, threshold, 300, 7200)
        )

    def test_skip_real_upload(self) -> None:
        """
        测试秒传失败后跳过真实上传策略
        """
        self.assertFalse(should_skip_real_upload(False, 1024, 0))
        self.assertTrue(should_skip_real_upload(True, 1024, 0))
        self.assertFalse(should_skip_real_upload(True, 1024, 2048))
        self.assertTrue(should_skip_real_upload(True, 2048, 2048))


if __name__ == "__main__":
    unittest.main()
