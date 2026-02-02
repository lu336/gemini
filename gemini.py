import arxiv
import google.generativeai as genai
import datetime
import os

# 配置部分：请在此处填入你的 Google Gemini API Key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# 初始化 Gemini 模型，这里我们使用支持长文本的 flash 版本以平衡速度与成本
model = genai.GenerativeModel('gemini-3.0-pro')

def get_latest_papers(topic="Large Language Models", max_results=3):
    """
    从 ArXiv 获取指定主题的最新论文
    """
    print(f"正在检索关于 {topic} 的最新论文...")

    # 构建查询：按提交时间倒序排列
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    papers_data = []
    for result in search.results():
        papers_data.append({
            "title": result.title,
            "abstract": result.summary,
            "url": result.entry_id,
            "published": result.published
        })

    return papers_data

def generate_summary(paper):
    """
    调用 Gemini API 生成中文解读
    """
    print(f"正在研读论文：{paper['title']} ...")

    # 这里植入我们在上一步设计好的 Prompt
    prompt = f"""
    You are an expert academic researcher. Please analyze the following paper metadata.
    
    Input Data:
    Title: {paper['title']}
    Abstract: {paper['abstract']}

    Requirements:
    1. Translate title to Simplified Chinese.
    2. Summarize core content (100-150 words) in Chinese.
    3. List exactly 3 key innovation points.
    4. Provide 2-3 tags.
    5. Output strictly in Markdown format as defined previously.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"解读失败，错误信息：{e}"

def main():
    # 1. 获取论文
    # 你可以修改 topic 参数来关注不同的领域，例如 "Multimodal AI"
    papers = get_latest_papers(topic="LLM", max_results=2)

    daily_report = f"# 📅 AI 前沿论文日报 ({datetime.date.today()})\n\n"

    # 2. 逐篇处理
    for paper in papers:
        summary = generate_summary(paper)

        # 拼接内容
        daily_report += f"{summary}\n"
        daily_report += f"🔗 **原文链接**: {paper['url']}\n"
        daily_report += "---\n\n"

    # 3. 输出结果（实际部署时这里可以替换为发送邮件或推送到微信的代码）
    print("\n" + "="*20 + " 生成结果 " + "="*20 + "\n")
    print(daily_report)

if __name__ == "__main__":

    main()