"""邮件推送服务 - 通过 QQ邮箱 SMTP 发送每日简报"""
import smtplib
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
from typing import Optional
from pathlib import Path
from src.config import config

# 模板目录
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def load_html_template() -> str:
    """加载 HTML 邮件模板"""
    template_path = TEMPLATE_DIR / "daily_briefing.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def markdown_to_html(markdown_text: str) -> str:
    """将 Markdown 转换为 HTML"""
    return markdown.markdown(markdown_text, extensions=["extra", "codehilite"])


def build_html_briefing(markdown_content: str) -> str:
    """构建 HTML 格式的简报"""
    template = load_html_template()
    content_html = markdown_to_html(markdown_content)

    if template:
        today = datetime.now().strftime("%Y年%m月%d日")
        html = template.replace("{{CONTENT}}", content_html)
        html = html.replace("{{DATE}}", today)
        return html
    else:
        # 无模板时使用简单 HTML
        today = datetime.now().strftime("%Y年%m月%d日")
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>每日国际新闻简报 - {today}</title></head>
<body style="font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
    <div style="background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        {content_html}
    </div>
    <div style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
        <p>本简报由 News Agent 自动生成 · {today}</p>
    </div>
</body>
</html>"""


class EmailSender:
    """邮件发送器"""

    def __init__(self):
        self.host = config.smtp_host
        self.port = config.smtp_port
        self.user = config.smtp_user
        self.password = config.smtp_password
        self.mail_to = config.mail_to

    def send_briefing(self, markdown_content: str) -> bool:
        """发送每日简报邮件"""
        if not all([self.user, self.password, self.mail_to]):
            print("  [错误] 邮件配置不完整，请检查 .env 文件")
            print(f"    SMTP_USER: {'已设置' if self.user else '未设置'}")
            print(f"    SMTP_PASSWORD: {'已设置' if self.password else '未设置'}")
            print(f"    MAIL_TO: {'已设置' if self.mail_to else '未设置'}")
            return False

        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"? 每日国际新闻简报 - {today}"

        try:
            # 构建邮件
            msg = MIMEMultipart("alternative")
            msg["From"] = f"News Agent <{self.user}>"
            msg["To"] = self.mail_to
            msg["Subject"] = Header(subject, "utf-8")

            # 纯文本版本（兼容）
            text_part = MIMEText(markdown_content, "plain", "utf-8")
            msg.attach(text_part)

            # HTML 版本
            html_content = build_html_briefing(markdown_content)
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # 发送
            print(f"  [邮件] 正在连接到 {self.host}:{self.port}...")
            if self.port == 465:
                # SSL 方式
                with smtplib.SMTP_SSL(self.host, self.port, timeout=30) as server:
                    server.login(self.user, self.password)
                    server.sendmail(self.user, self.mail_to, msg.as_string())
            else:
                # STARTTLS 方式
                with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                    server.starttls()
                    server.login(self.user, self.password)
                    server.sendmail(self.user, self.mail_to, msg.as_string())

            print(f"  [邮件] ? 简报已成功发送至 {self.mail_to}")
            return True

        except smtplib.SMTPAuthenticationError:
            print(f"  [错误] SMTP 认证失败，请检查邮箱地址和授权码")
            print(f"    ? 提示：QQ邮箱需要使用 授权码 而不是QQ密码")
            return False
        except smtplib.SMTPException as e:
            print(f"  [错误] SMTP 发送失败: {e}")
            return False
        except Exception as e:
            print(f"  [错误] 邮件发送异常: {e}")
            return False