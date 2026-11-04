import streamlit as st
from writer_agent import WriterAgent
import io
from docx import Document
"""Streamlit 前端：单页完成 主题→大纲→正文→标题 写作流程。"""
import streamlit as st
from writer_agent import WriterAgent

st.set_page_config(page_title="宋楚瑶 · 自媒体写作助手", page_icon="✍️", layout="wide")

st.title("✍️ 宋楚瑶 · 自媒体写作助手")
st.caption("输入主题 → 生成大纲 → 扩写正文 → 标题候选，支持修改润色。")

with st.sidebar:
    st.header("写作设置")
    style = st.selectbox("文体", ["通用", "新闻", "散文", "营销"])
    if st.button("🔄 重置对话"):
        for key in ["agent", "outline", "article", "titles"]:
            st.session_state.pop(key, None)
        st.rerun()

if "agent" not in st.session_state or st.session_state.get("_style") != style:
    st.session_state.agent = WriterAgent(style=style)
    st.session_state._style = style

agent: WriterAgent = st.session_state.agent

for key in ["outline", "article", "titles"]:
    if key not in st.session_state:
        st.session_state[key] = ""

st.subheader("① 输入主题，生成大纲")
topic = st.text_input("文章主题", placeholder="例如：AI 如何改变内容创作行业")

if st.button("生成大纲", type="primary", disabled=not topic.strip()):
    with st.spinner("小唐正在构思大纲…"):
        st.session_state.outline = agent.generate_outline(topic)
    st.session_state.article = ""
    st.session_state.titles = ""

if st.session_state.outline:
    st.session_state.outline = st.text_area(
        "大纲（可编辑）", st.session_state.outline, height=280
    )

st.subheader("② 根据大纲生成正文")
if st.session_state.outline and topic.strip():
    if st.button("生成正文", type="primary"):
        with st.spinner("宋楚瑶正在撰写正文…"):
            st.session_state.article = agent.generate_article(topic, st.session_state.outline)
        st.session_state.titles = ""
else:
    st.info("请先生成大纲。")

if st.session_state.article:
    st.session_state.article = st.text_area(
        "正文（可编辑）", st.session_state.article, height=420
    )

    st.subheader("③ 修改润色")
    revise_cmd = st.text_input("修改指令", placeholder="例如：把第二段改得更口语化 / 增加一个数据段落")
    if st.button("执行修改", disabled=not revise_cmd.strip()):
        with st.spinner("宋楚瑶正在修改…"):
            st.session_state.article = agent.revise(st.session_state.article, revise_cmd)
        st.rerun()

st.subheader("④ 生成标题候选")
if st.session_state.article and topic.strip():
    if st.button("生成 3 个标题"):
        with st.spinner("小唐正在拟标题…"):
            st.session_state.titles = agent.generate_titles(topic, st.session_state.article)
else:
    st.info("请先生成正文。")

if st.session_state.titles:
    st.markdown(st.session_state.titles)
    # ---------- 文档导出功能 ----------
if st.session_state.article and topic.strip():
    st.markdown("---")
    st.subheader("📥 导出文档")
    
    col1, col2 = st.columns(2)
    
    # 1. 导出 Markdown
    with col1:
        md_content = f"# {topic}\n\n{st.session_state.article}\n\n## 标题候选\n\n{st.session_state.titles}"
        st.download_button(
            label="下载 Markdown (.md)",
            data=md_content,
            file_name=f"{topic}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
    # 2. 导出 Word
    with col2:
        # 在内存中创建 Word 文档
        doc = Document()
        doc.add_heading(topic, level=1)
        
        # 按段落写入正文
        for paragraph in st.session_state.article.split('\n'):
            if paragraph.strip():
                doc.add_paragraph(paragraph)
                
        # 如果有标题候选，加在最后
        if st.session_state.titles:
            doc.add_heading("标题候选", level=2)
            for title_line in st.session_state.titles.split('\n'):
                if title_line.strip():
                    doc.add_paragraph(title_line)
                    
        # 保存到内存中
        bio = io.BytesIO()
        doc.save(bio)
        
        st.download_button(
            label="下载 Word (.docx)",
            data=bio.getvalue(),
            file_name=f"{topic}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
