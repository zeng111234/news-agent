"""规则管理模块 - 支持自然语言指令动态调整抓取源与筛选规则"""
import re
from typing import Tuple, Optional
from src.config import config


class RuleManager:
    """规则管理器 - 解析自然语言指令并执行"""

    def __init__(self):
        self.commands = {
            "add_source": self._cmd_add_source,
            "remove_source": self._cmd_remove_source,
            "list_sources": self._cmd_list_sources,
            "add_exclude": self._cmd_add_exclude,
            "add_include": self._cmd_add_include,
            "remove_keyword": self._cmd_remove_keyword,
            "list_rules": self._cmd_list_rules,
            "help": self._cmd_help,
        }

    def parse_and_execute(self, user_input: str) -> str:
        """解析自然语言指令并执行"""
        if not user_input or not user_input.strip():
            return "请输入指令，输入 '帮助' 查看可用命令"

        text = user_input.strip()

        # 尝试匹配各个命令
        result = self._try_parse_add_source(text)
        if result: return result

        result = self._try_parse_remove_source(text)
        if result: return result

        result = self._try_parse_add_keyword(text)
        if result: return result

        result = self._try_parse_remove_keyword(text)
        if result: return result

        result = self._try_parse_list(text)
        if result: return result

        # 精确命令匹配
        if text in ["帮助", "help", "?","h"]:
            return self._cmd_help()
        if text in ["源列表", "sources", "查看源", "列出源"]:
            return self._cmd_list_sources()
        if text in ["规则列表", "rules", "查看规则", "列出规则"]:
            return self._cmd_list_rules()

        return f"? 无法识别的指令: '{text}'\n{self._cmd_help()}"

    def _try_parse_add_source(self, text: str) -> Optional[str]:
        """尝试解析添加抓取源指令"""
        patterns = [
            r"添加[抓取源新闻源来源].*?[:：]?\s*([\w\u4e00-\u9fff]+).*?[:：]?\s*(https?://\S+)",
            r"加入[:：]?\s*([\w\u4e00-\u9fff]+).*?[:：]?\s*(https?://\S+)",
            r"新增[:：]?\s*([\w\u4e00-\u9fff]+).*?[:：]?\s*(https?://\S+)",
            r"add\s+source\s+([\w\u4e00-\u9fff]+)\s+(https?://\S+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()
                return self._cmd_add_source(name, url)
        return None

    def _try_parse_remove_source(self, text: str) -> Optional[str]:
        """尝试解析删除抓取源指令"""
        patterns = [
            r"(?:删除|移除|去掉|删除源|移除源)\s*[:：]?\s*([\w\u4e00-\u9fff]+)",
            r"delete\s+source\s+([\w\u4e00-\u9fff]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                return self._cmd_remove_source(name)
        return None

    def _try_parse_add_keyword(self, text: str) -> Optional[str]:
        """尝试解析添加关键词指令"""
        # 过滤...关键词 / 排除...关键词
        patterns = [
            (r"(?:过滤掉|排除|屏蔽|过滤|不要).*?[:：]?\s*([\w\u4e00-\u9fff]+)", "exclude"),
            (r"(?:保留|包含|重点|关注|包括).*?[:：]?\s*([\w\u4e00-\u9fff]+)", "include"),
        ]
        for pattern, category in patterns:
            match = re.search(pattern, text)
            if match:
                keyword = match.group(1).strip()
                return self._cmd_add_keyword(keyword, category)

        # 关键词+屏蔽/排除等
        match = re.search(r"([\w\u4e00-\u9fff]+)\s*(?:关键词|keyword).*?(?:屏蔽|排除|过滤|不要)", text)
        if not match:
            match = re.search(r"屏蔽|排除|过滤掉\s*[:：]?\s*([\w\u4e00-\u9fff]+)", text)
        if match:
            return self._cmd_add_keyword(match.group(1).strip(), "exclude")
        return None

    def _try_parse_remove_keyword(self, text: str) -> Optional[str]:
        """尝试解析删除关键词指令"""
        patterns = [
            r"(?:去掉|移除|删除|取消).*?过滤\s*[:：]?\s*([\w\u4e00-\u9fff]+)",
            r"取消\s*[:：]?\s*屏蔽\s*[:：]?\s*([\w\u4e00-\u9fff]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._cmd_remove_keyword(match.group(1).strip())
        return None

    def _try_parse_list(self, text: str) -> Optional[str]:
        """尝试解析列表指令"""
        match = re.search(r"(?:查看|列出|显示|list).*?(?:源|source|抓取源)", text)
        if match:
            return self._cmd_list_sources()
        match = re.search(r"(?:查看|列出|显示|list).*?(?:规则|规则|keyword)", text)
        if match:
            return self._cmd_list_rules()
        return None

    def _cmd_add_source(self, name: str, url: str) -> str:
        """添加抓取源"""
        source_type = "general"
        if "cctv" in url or "央视" in name:
            source_type = "cctv"
        success = config.add_source(name, url, source_type)
        if success:
            return f"? 已添加抓取源「{name}」\n   URL: {url}"
        return f"?? 抓取源「{name}」已存在"

    def _cmd_remove_source(self, name: str) -> str:
        """移除抓取源"""
        success = config.remove_source(name)
        if success:
            return f"? 已移除抓取源「{name}」"
        return f"?? 抓取源「{name}」不存在"

    def _cmd_list_sources(self) -> str:
        """列出所有抓取源"""
        sources = config.get_enabled_sources()
        if not sources:
            # 也显示禁用的
            from src.config import load_yaml, SOURCES_FILE
            all_cfg = load_yaml(SOURCES_FILE)
            all_sources = all_cfg.get("sources", {})
            if not all_sources:
                return "? 尚未配置任何抓取源"
            lines = ["? 抓取源列表:"]
            for name, info in all_sources.items():
                status = "? 启用" if info.get("enabled", True) else "? 禁用"
                lines.append(f"  {status} {name}")
                lines.append(f"     URL: {info['url']}")
            return "\n".join(lines)
        lines = ["? 已启用的抓取源:"]
        for name, info in sources.items():
            lines.append(f"  ? {name}")
            lines.append(f"     URL: {info['url']}")
        return "\n".join(lines)

    def _cmd_add_keyword(self, keyword: str, category: str) -> str:
        """添加关键词"""
        if category == "exclude":
            success = config.add_exclude_keyword(keyword)
            if success:
                return f"? 已添加排除关键词「{keyword}」"
            return f"?? 排除关键词「{keyword}」已存在"
        else:
            success = config.add_include_keyword(keyword)
            if success:
                return f"? 已添加包含关键词「{keyword}」"
            return f"?? 包含关键词「{keyword}」已存在"

    def _cmd_add_exclude(self, keyword: str) -> str:
        """添加排除关键词"""
        return self._cmd_add_keyword(keyword, "exclude")

    def _cmd_add_include(self, keyword: str) -> str:
        """添加包含关键词"""
        return self._cmd_add_keyword(keyword, "include")

    def _cmd_remove_keyword(self, keyword: str) -> str:
        """移除关键词"""
        success = config.remove_keyword(keyword, "exclude")
        if not success:
            success = config.remove_keyword(keyword, "include")
        if success:
            return f"? 已移除关键词「{keyword}」"
        return f"?? 关键词「{keyword}」不存在"

    def _cmd_list_rules(self) -> str:
        """列出所有筛选规则"""
        exclude = config.get_exclude_keywords()
        include = config.get_include_keywords()
        priority = config.get_priority_keywords()
        lines = ["? 当前筛选规则:"]
        if exclude:
            lines.append(f"  ? 排除关键词: {', '.join(exclude)}")
        if include:
            lines.append(f"  ? 包含关键词: {', '.join(include)}")
        if priority:
            lines.append(f"  ? 优先关键词: {', '.join(priority)}")
        lines.append(f"\n  简报设置:")
        lines.append(f"  最大文章数: {config.max_articles}")
        return "\n".join(lines)

    def _cmd_help(self) -> str:
        """帮助信息"""
        return """? 可用指令示例:

? **管理抓取源:**
  "添加源 央视新闻 https://news.cctv.com/china"
  "删除源 央视新闻"
  "列出源" / "sources"

? **管理筛选规则:**
  "过滤掉 广告"
  "屏蔽 推广"
  "取消屏蔽 广告"
  "列出规则" / "rules"

? 支持自然语言方式输入，系统会自动解析意图
"""