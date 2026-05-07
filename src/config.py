"""配置管理模块 - 加载环境变量和配置文件"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent

# 配置文件路径
CONFIG_DIR = ROOT_DIR / "config"
SOURCES_FILE = CONFIG_DIR / "sources.yaml"
RULES_FILE = CONFIG_DIR / "rules.yaml"
ENV_FILE = ROOT_DIR / ".env"


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_env() -> Dict[str, str]:
    """加载环境变量配置
    
    优先级：系统环境变量 > .env 文件
    兼容 GitHub Actions Secrets 注入机制（无 .env 文件时也能正常工作）。
    """
    env_vars = {}
    env_file = ENV_FILE

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value

    # 预期读取的环境变量键名列表
    expected_keys = [
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_API_BASE",
        "DEEPSEEK_MODEL",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "MAIL_TO",
        "BRIEFING_TIME",
        "BRIEFING_TIMEZONE",
    ]

    # 系统环境变量优先（覆盖 .env 中的值）
    for key in expected_keys:
        env_value = os.environ.get(key)
        if env_value is not None:
            env_vars[key] = env_value

    return env_vars


class Config:
    """全局配置类"""

    def __init__(self):
        self._env = load_env()
        self._sources = load_yaml(SOURCES_FILE)
        self._rules = load_yaml(RULES_FILE)

    # ---- DeepSeek API 配置 ----
    @property
    def deepseek_api_key(self) -> Optional[str]:
        return self._env.get("DEEPSEEK_API_KEY")

    @property
    def deepseek_api_base(self) -> str:
        return self._env.get("DEEPSEEK_API_BASE", "https://api.deepseek.com")

    @property
    def deepseek_model(self) -> str:
        return self._env.get("DEEPSEEK_MODEL", "deepseek-chat")

    @property
    def has_deepseek_config(self) -> bool:
        return bool(self.deepseek_api_key) and self.deepseek_api_key != "your_deepseek_api_key_here"

    # ---- 邮件配置 ----
    @property
    def smtp_host(self) -> str:
        return self._env.get("SMTP_HOST", "smtp.qq.com")

    @property
    def smtp_port(self) -> int:
        return int(self._env.get("SMTP_PORT", 465))

    @property
    def smtp_user(self) -> Optional[str]:
        return self._env.get("SMTP_USER")

    @property
    def smtp_password(self) -> Optional[str]:
        return self._env.get("SMTP_PASSWORD")

    @property
    def mail_to(self) -> Optional[str]:
        return self._env.get("MAIL_TO")

    @property
    def has_email_config(self) -> bool:
        return all([
            self.smtp_user and self.smtp_user != "your_qq_email@qq.com",
            self.smtp_password and self.smtp_password != "your_smtp_authorization_code_here",
            self.mail_to and self.mail_to != "recipient_email@example.com",
        ])

    # ---- 简报配置 ----
    @property
    def briefing_time(self) -> str:
        return self._env.get("BRIEFING_TIME", "08:00")

    @property
    def briefing_timezone(self) -> str:
        return self._env.get("BRIEFING_TIMEZONE", "Asia/Shanghai")

    @property
    def max_articles(self) -> int:
        rules = self._rules.get("briefing", {})
        return rules.get("max_articles", 10)

    @property
    def include_source_link(self) -> bool:
        rules = self._rules.get("briefing", {})
        return rules.get("include_source_link", True)

    # ---- 抓取源配置 ----
    def get_enabled_sources(self) -> Dict[str, Dict[str, Any]]:
        """获取所有启用的抓取源"""
        sources = self._sources.get("sources", {})
        return {name: src for name, src in sources.items() if src.get("enabled", True)}

    def add_source(self, name: str, url: str, source_type: str = "general") -> bool:
        """添加新抓取源"""
        sources = self._sources.setdefault("sources", {})
        if name in sources:
            return False
        sources[name] = {"url": url, "type": source_type, "enabled": True}
        self._save_sources()
        return True

    def remove_source(self, name: str) -> bool:
        """移除抓取源"""
        sources = self._sources.get("sources", {})
        if name not in sources:
            return False
        del sources[name]
        self._save_sources()
        return True

    def toggle_source(self, name: str) -> bool:
        """启用/禁用抓取源"""
        sources = self._sources.get("sources", {})
        if name not in sources:
            return False
        sources[name]["enabled"] = not sources[name].get("enabled", True)
        self._save_sources()
        return True

    def _save_sources(self):
        """保存抓取源配置到文件"""
        with open(SOURCES_FILE, "w", encoding="utf-8") as f:
            yaml.dump(self._sources, f, allow_unicode=True, default_flow_style=False)

    # ---- 筛选规则配置 ----
    def get_exclude_keywords(self) -> list:
        return self._rules.get("filter_rules", {}).get("exclude_keywords", [])

    def get_include_keywords(self) -> list:
        return self._rules.get("filter_rules", {}).get("include_keywords", [])

    def get_priority_keywords(self) -> list:
        return self._rules.get("priority_keywords", [])

    def add_exclude_keyword(self, keyword: str) -> bool:
        """添加排除关键词"""
        keywords = self._rules.setdefault("filter_rules", {}).setdefault("exclude_keywords", [])
        if keyword in keywords:
            return False
        keywords.append(keyword)
        self._save_rules()
        return True

    def add_include_keyword(self, keyword: str) -> bool:
        """添加包含关键词"""
        keywords = self._rules.setdefault("filter_rules", {}).setdefault("include_keywords", [])
        if keyword in keywords:
            return False
        keywords.append(keyword)
        self._save_rules()
        return True

    def remove_keyword(self, keyword: str, category: str = "exclude") -> bool:
        """移除关键词"""
        key = f"{category}_keywords"
        keywords = self._rules.get("filter_rules", {}).get(key, [])
        if keyword not in keywords:
            return False
        keywords.remove(keyword)
        self._save_rules()
        return True

    def _save_rules(self):
        """保存规则配置到文件"""
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            yaml.dump(self._rules, f, allow_unicode=True, default_flow_style=False)


# 全局单例
config = Config()