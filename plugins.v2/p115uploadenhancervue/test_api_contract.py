import ast
import unittest
from pathlib import Path


class QRCodeApiContractTest(unittest.TestCase):
    """二维码 API 必须暴露明确的查询参数，避免 FastAPI 返回 422。"""

    @classmethod
    def setUpClass(cls) -> None:
        source = Path(__file__).with_name("__init__.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        plugin_class = next(
            node
            for node in module.body
            if isinstance(node, ast.ClassDef) and node.name == "P115UploadEnhancerVUE"
        )
        cls.methods = {
            node.name: node
            for node in plugin_class.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def test_get_qrcode_query_parameters(self) -> None:
        method = self.methods["get_qrcode"]
        self.assertIsNone(method.args.kwarg)
        self.assertEqual(
            [argument.arg for argument in method.args.args],
            ["self", "client_type"],
        )

    def test_check_qrcode_query_parameters(self) -> None:
        method = self.methods["check_qrcode"]
        self.assertIsNone(method.args.kwarg)
        self.assertEqual(
            [argument.arg for argument in method.args.args],
            ["self", "uid", "time", "sign", "client_type"],
        )


if __name__ == "__main__":
    unittest.main()
