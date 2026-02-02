import arxiv
import google.generativeai as genai
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# ================= 配置部分 =================
# 1. API Key 配置
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Error: GOOGLE_API_KEY not found.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 邮箱配置 (从环境变量获取)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com") # 默认使用 Gmail，可修改
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") # 注意：Gmail 需要使用“应用专用密码”
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# ================= 核心逻辑 =================

def get_latest_papers(topic="Relay Protection", max_results=3):
    """
    获取继电保护 (Relay Protection) 相关的最新论文
    """
    print(f"--- 正在检索关于 {topic} 的最新论文 ---")
    # 构建查询：继电保护 OR 电力系统保护
    search_query = f'{topic} OR "Power System Protection"'
    
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    papers_data = []
    for result in search.results():
        papers_data.append({
            "title": result.title,
            "abstract": result.summary,
            "url": result.entry_id,
            "first_author": result.authors[0].name if result.authors else "Unknown",
            "published": result.published.strftime("%Y-%m-%d")
        })
    return papers_data

def generate_summary(paper):
    """
    使用“继电保护专家” Prompt 生成解读
    """
    print(f"正在研读论文：{paper['title']} ...")

    prompt = f"""
# Role Assignment
你是一位拥有 20 年经验的资深**电力系统继电保护（Relay Protection）**领域专家，擅长快速阅读 IEEE Transactions 等英文顶级电气学术文献，并将其核心价值转化为逻辑严密、通俗易懂的中文技术简报。你对**故障分析、自适应保护、广域测量系统（WAMS）、行波保护、IEC 61850 标准以及含高比例新能源接入的电网保护控制**等前沿技术有深刻的理解。

# Task Description
请阅读我提供的学术论文内容（或摘要），输出一份结构化的中文研报。你的目标是帮助读者在 1 分钟内准确判断该论文在继电保护领域的学术价值或工程应用前景，并掌握其核心创新点。

# Constraints
1. 必须使用中文进行输出，但保留必要的英文专业术语（如 Differential Protection, PMU, GOOSE, Traveling Wave 等）。
2. 严禁直接翻译原文摘要，必须基于对电力系统原理的理解进行重述和概括。
3. 语气保持客观、专业，避免使用营销式夸张词汇。
4. "创新点"部分必须具体，指出该论文解决了传统保护方案中的什么具体痛点（如高阻接地检测难、CT 饱和影响、逆变器电源特性干扰等），而不仅是罗列公式。

# Output Format
请严格按照以下 Markdown 格式输出：

## 📄 论文标题：[论文的中文翻译标题]
**原标题**：{paper['title']}
**第一作者**：{paper['first_author']}
### 🎯 核心摘要
[在此处撰写 150-200 字的中文摘要。主要描述论文针对的电网场景、面临的保护难题、提出的保护新原理或改进算法，以及验证效果。]
### 💡 核心创新点与贡献
* **[创新点 1 名称]**：详细解释该创新的技术原理，以及它相对于现有传统工频量保护的优势。
* **[创新点 2 名称]**：描述该方法在模型构建或数据处理上的独特之处。
* **[创新点 3 名称]**：总结该论文在实验结果上的突破（需包含具体的提升数据）。
### 🧐 简评与启示
[用一句话总结该论文对当前新型电力系统保护研究的潜在影响，或在实际工程中的应用价值。]

---
# Input Data
Title: {paper['title']}
Abstract: {paper['abstract']}
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"解读失败，错误信息：{e}"

def send_email(subject, content):
    """
    发送邮件函数
    """
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        print("⚠️ 缺少邮箱配置，跳过发送邮件步骤，仅打印结果。")
        return

    print(f"正在发送邮件至 {RECEIVER_EMAIL} ...")
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = Header(subject, 'utf-8')

    # 将 Markdown 内容作为纯文本发送 (大部分邮件客户端能正常显示文本)
    # 如果需要富文本，可以使用 markdown2 库转 html，但这里保持简单
    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    try:
        # 使用 SSL 连接 (通常端口 465)
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def main():
    # 1. 获取论文 (修改 topic 为 Relay Protection 相关的关键词)
    # 你可以修改这里，比如 "Power System Protection" 或 "Microgrid Protection"
    papers = get_latest_papers(topic="Relay Protection", max_results=3)
    
    if not papers:
        print("未找到相关论文。")
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    report_header = f"⚡ 继电保护前沿论文日报 ({today_str})"
    
    full_report = f"# {report_header}\n\n"

    # 2. 生成解读
    for paper in papers:
        summary = generate_summary(paper)
        full_report += f"{summary}\n"
        full_report += f"🔗 **原文链接**: {paper['url']}\n"
        full_report += "---\n\n"

    # 3. 打印结果 (保留日志)
    print(full_report)

    # 4. 发送邮件
    send_email(subject=report_header, content=full_report)

if __name__ == "__main__":
    main()
