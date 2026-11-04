"""Streamlit 前端：单页完成 主题→大纲→正文→标题 写作流程。"""
import streamlit as st
from writer_agent import WriterAgent
import io
import requests
from docx import Document

st.set_page_config(page_title="宋楚瑶 · 自媒体写作助手", page_icon="✍️", layout="wide")

st.title("✍️ 宋楚瑶 · 自媒体写作助手")
st.caption("输入主题 → 生成大纲 → 扩写正文 → 标题候选，支持修改润色、双语翻译与文档导出。")

# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("写作设置")
    style = st.selectbox("文体", ["通用", "新闻", "散文", "营销"])
    if st.button("🔄 重置对话"):
        for key in ["agent", "outline", "article", "titles", "article_en"]:
            st.session_state.pop(key, None)
        st.rerun()

# ---------- Agent 初始化 ----------
if "agent" not in st.session_state or st.session_state.get("_style") != style:
    st.session_state.agent = WriterAgent(style=style)
    st.session_state._style = style

agent: WriterAgent = st.session_state.agent

for key in ["outline", "article", "titles", "article_en"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------- ① 主题 → 大纲 ----------
st.subheader("① 输入主题，生成大纲")
topic = st.text_input("文章主题", placeholder="例如：AI 如何改变内容创作行业")

if st.button("生成大纲", type="primary", disabled=not topic.strip()):
    with st.spinner("宋楚瑶正在构思大纲…"):
        st.session_state.outline = agent.generate_outline(topic)
    st.session_state.article = ""
    st.session_state.titles = ""
    st.session_state.article_en = ""

if st.session_state.outline:
    st.session_state.outline = st.text_area(
        "大纲（可编辑）", st.session_state.outline, height=280
    )

# ---------- ② 大纲 → 正文 ----------
st.subheader("② 根据大纲生成正文")
if st.session_state.outline and topic.strip():
    if st.button("生成正文", type="primary"):
        with st.spinner("宋楚瑶正在撰写正文…"):
            st.session_state.article = agent.generate_article(topic, st.session_state.outline)
        st.session_state.titles = ""
        st.session_state.article_en = ""
else:
    st.info("请先生成大纲。")

if st.session_state.article:
    st.session_state.article = st.text_area(
        "正文（可编辑）", st.session_state.article, height=420
    )

    # ---------- ③ 多轮修改与翻译 ----------
    st.subheader("③ 修改润色与扩展")
    
    col_rev, col_trans = st.columns([3, 1])
    with col_rev:
        revise_cmd = st.text_input("修改指令", placeholder="例如：把第二段改得更口语化 / 增加一个数据段落")
    with col_trans:
        st.write("") # 占位对齐
        if st.button("🌐 翻译成英文"):
            with st.spinner("宋楚瑶正在翻译中…"):
                st.session_state.article_en = agent.translate_to_english(st.session_state.article)
            st.rerun()

    if revise_cmd:
        if st.button("执行修改"):
            with st.spinner("宋楚瑶正在修改…"):
                st.session_state.article = agent.revise(st.session_state.article, revise_cmd)
            st.rerun()

    if st.session_state.article_en:
        st.text_area("英文版正文", st.session_state.article_en, height=300)

# ---------- ④ 标题候选 ----------
st.subheader("④ 生成标题候选")
if st.session_state.article and topic.strip():
    if st.button("生成 3 个标题"):
        with st.spinner("宋楚瑶正在拟标题…"):
            st.session_state.titles = agent.generate_titles(topic, st.session_state.article)
else:
    st.info("请先生成正文。")

if st.session_state.titles:
    st.markdown(st.session_state.titles)

# ---------- ⑤ 高级扩展功能（配图、统计、导出） ----------
if st.session_state.article and topic.strip():
    st.markdown("---")
    
    # 字数统计
    word_count = len(st.session_state.article)
    st.info(f"📊 **当前正文统计**：共 {word_count} 个字符（包含标点）")
    
    st.subheader("📥 导出文档")
    col1, col2 = st.columns(2)
    
    # 导出 Markdown
    with col1:
        md_content = f"# {topic}\n\n{st.session_state.article}\n\n## 标题候选\n\n{st.session_state.titles}"
        st.download_button(
            label="下载 Markdown (.md)",
            data=md_content,
            file_name=f"{topic}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
    # 导出 Word
    with col2:
        doc = Document()
        doc.add_heading(topic, level=1)
        for paragraph in st.session_state.article.split('\n'):
            if paragraph.strip():
                doc.add_paragraph(paragraph)
        if st.session_state.titles:
            doc.add_heading("标题候选", level=2)
            for title_line in st.session_state.titles.split('\n'):
                if title_line.strip():
                    doc.add_paragraph(title_line)
        bio = io.BytesIO()
        doc.save(bio)
        st.download_button(
            label="下载 Word (.docx)",
            data=bio.getvalue(),
            file_name=f"{topic}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    # 智能配图
    st.subheader("🖼️ 文章智能配图")
    if st.button("获取一张高质量封面图"):
        with st.spinner("正在寻找配图…"):
            try:
                img_url = f"https://source.unsplash.com/800x400/?{topic},writing"
                st.image(img_url, caption=f"与「{topic}」相关的配图", use_column_width=True)
            except Exception as e:
                st.error(f"获取图片失败，请重试。错误: {e}")
