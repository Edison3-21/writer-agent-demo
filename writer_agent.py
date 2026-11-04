"""
智能写作助手核心模块。
基于 ModelScope-Agent RolePlay，角色模板参考 PPT Ch5 §1 “小唐”设定。
"""
import os
import streamlit as st  # <--- 加上这一行
from dotenv import load_dotenv
from modelscope_agent.agents.role_play import RolePlay

# 加上下面这三行！
if "DASHSCOPE_API_KEY" in st.secrets:
    os.environ["DASHSCOPE_API_KEY"] = st.secrets["DASHSCOPE_API_KEY"]
load_dotenv()

BASE_ROLE = (
    "你是宋楚瑶，一位才情横溢的自媒体文章助手。"
    "你擅长根据用户给出的主题，快速产出结构清晰、文采得当的自媒体内容。"
    "你的能力包括：一键生成大纲、根据大纲撰写正文、生成多个标题候选。"
)

STYLE_PROMPTS = {
    "通用": "",
    "新闻": "文体为新闻稿。语言客观准确，结构遵循倒金字塔，先交代核心事实，再补充细节与背景。",
    "散文": "文体为散文。语言富有文学性与画面感，注重情绪流动与意象营造。",
    "营销": "文体为营销软文。语言有感染力与行动号召力，突出痛点与价值主张。",
}

def _build_instruction(style: str) -> str:
    instruction = BASE_ROLE
    if STYLE_PROMPTS.get(style):
        instruction += " " + STYLE_PROMPTS[style]
    instruction += " 输出内容必须使用中文。"
    return instruction

class WriterAgent:
    def __init__(self, style: str = "通用", model: str = "qwen-max"):
        self.style = style
        llm_config = {"model": model, "model_server": "dashscope"}
        self.bot = RolePlay(
            function_list=[],
            llm=llm_config,
            instruction=_build_instruction(style),
        )

    def _run(self, prompt: str) -> str:
        response = self.bot.run(prompt)
        text = ""
        for chunk in response:
            text += chunk
        return text.strip()

    def generate_outline(self, topic: str) -> str:
        prompt = (
            f"请为主题「{topic}」生成一份自媒体文章大纲。"
            "用 Markdown 有序列表输出，包含一级标题和每个部分的二级要点。"
            "大纲应逻辑清晰、层次分明，适合后续直接扩写为正文。"
        )
        return self._run(prompt)

    def generate_article(self, topic: str, outline: str) -> str:
        prompt = (
            f"主题是「{topic}」。请根据以下大纲撰写一篇完整的自媒体文章正文。\n\n"
            f"大纲：\n{outline}\n\n"
            "要求：严格遵循大纲结构，内容充实，过渡自然，篇幅约 800-1200 字。"
        )
        return self._run(prompt)

    def generate_titles(self, topic: str, article: str) -> str:
        prompt = (
            f"下面是一篇关于「{topic}」的文章正文。请生成 3 个标题候选。\n\n"
            f"正文：\n{article[:1500]}\n\n"
            "输出为编号列表，每个标题不超过 30 字，风格各异，附一句推荐理由。"
        )
        return self._run(prompt)

    def revise(self, current_text: str, instruction: str) -> str:
        prompt = (
            f"以下是当前文章内容：\n\n{current_text}\n\n"
            f"请按以下要求修改：{instruction}\n\n"
            "直接输出修改后的完整内容，不要解释。"
        )
        return self._run(prompt)
