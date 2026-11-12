import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prompts import PLATFORMS, build_prompt  # noqa: E402
from repurpose import extract_title, main, mock_output, parse_platforms  # noqa: E402

ARTICLE = """# 测试标题

第一段：这里是一个结论。

第二段：这里是支撑结论的细节。

第三段：这里是行动建议。
"""


class BuildPromptTests(unittest.TestCase):
    def test_prompt_contains_platform_rules(self):
        prompt = build_prompt("xiaohongshu", ARTICLE, "真诚", "")
        for rule in PLATFORMS["xiaohongshu"]["rules"]:
            self.assertIn(rule, prompt)

    def test_prompt_defaults_and_brand(self):
        without_brand = build_prompt("weibo", ARTICLE, "克制")
        self.assertNotIn("账号人设", without_brand)

        with_brand = build_prompt("weibo", ARTICLE, "克制", "科技博主")
        self.assertIn("账号人设 / 语气要求：科技博主", with_brand)

    def test_prompt_carries_article_and_constraints(self):
        prompt = build_prompt("wechat", ARTICLE, "克制")
        self.assertIn("第一段：这里是一个结论。", prompt)
        self.assertIn("不要虚构经历、数据或引用", prompt)


class MockOutputTests(unittest.TestCase):
    def test_every_platform_returns_labeled_content(self):
        for platform, spec in PLATFORMS.items():
            with self.subTest(platform=platform):
                text = mock_output(platform, ARTICLE, "真诚")
                self.assertIn("离线示例输出", text)
                self.assertIn(spec["label"], text)
                self.assertGreater(len(text), 40)

    def test_titled_platforms_keep_original_title(self):
        for platform in ("xiaohongshu", "wechat"):
            with self.subTest(platform=platform):
                self.assertIn("测试标题", mock_output(platform, ARTICLE, "真诚"))

    def test_script_output_is_storyboard(self):
        text = mock_output("script", ARTICLE, "真诚")
        self.assertIn("镜号 1", text)
        self.assertIn("口播：", text)


class HelperTests(unittest.TestCase):
    def test_extract_title_prefers_heading(self):
        self.assertEqual(extract_title(ARTICLE), "测试标题")

    def test_extract_title_falls_back_to_first_line(self):
        self.assertEqual(extract_title("没有标题的正文"), "没有标题的正文")

    def test_parse_platforms_rejects_unknown(self):
        with self.assertRaises(SystemExit):
            parse_platforms("xiaohongshu,instagram")

    def test_parse_platforms_is_case_insensitive(self):
        self.assertEqual(parse_platforms("Xiaohongshu, weibo"), ["xiaohongshu", "weibo"])


class CliTests(unittest.TestCase):
    def test_mock_run_writes_each_platform_and_combined_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            article = Path(tmp) / "article.md"
            article.write_text(ARTICLE, encoding="utf-8")
            out_dir = Path(tmp) / "out"

            exit_code = main(
                ["-i", str(article), "-p", "xiaohongshu,weibo", "-o", str(out_dir), "--mock"]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue((out_dir / "xiaohongshu.md").exists())
            self.assertTrue((out_dir / "weibo.md").exists())
            combined = (out_dir / "all.md").read_text(encoding="utf-8")
            self.assertIn("# 小红书", combined)
            self.assertIn("# 微博", combined)


if __name__ == "__main__":
    unittest.main()
