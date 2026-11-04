"""Streamlit 前端：单页完成 主题→大纲→正文→标题 写作流程。"""
import streamlit as st
from writer_agent import WriterAgent
import io
import requests
from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

# ==========================================
# 辅助函数：从 Unsplash 获取图片数据
# ==========================================
def get_unsplash_image(topic, unsplash_key):
    headers = {"Authorization": f"Client-ID {unsplash_key}"}
    params = {"query": topic, "per_page": 1, "orientation": "landscape", "content_filter": "high"}
    try:
        resp = requests.get("https://api.unsplash.com/search/photos", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            img_url = results[0]["urls"]["regular"]
            img_data = requests.get(img_url, timeout=10).content
            return img_data
    except Exception:
        return None
    return None

# ==========================================
# 页面配置与初始化
# ==========================================
st.set_page_config(page_title="宋楚瑶 · 自媒体写作助手", page_icon="✍️", layout="wide")

st.title("✍️ 宋楚瑶 · 自媒体写作助手")
st.caption("输入主题 → 生成大纲 → 扩写正文 → 标题候选，支持润色、翻译、导出文档与高级配图 PPT。")

with st.sidebar:
    st.header("写作设置")
    style = st.selectbox("文体", ["通用", "新闻", "散文", "营销"])
    if st.button("🔄 重置对话"):
        for key in ["agent", "outline", "article", "titles", "article_en"]:
            st.session_state.pop(key, None)
        st.rerun()

if "agent" not in st.session_state or st.session_state.get("_style") != style:
    st.session_state.agent = WriterAgent(style=style)
    st.session_state._style = style

agent: WriterAgent = st.session_state.agent

for key in ["outline", "article", "titles", "article_en"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ==========================================
# ① 主题 → 大纲
# ==========================================
st.subheader("① 输入主题，生成大纲")
topic = st.text_input("文章主题", placeholder="例如：AI 如何改变内容创作行业")

if st.button("生成大纲", type="primary", disabled=not topic.strip()):
    with st.spinner("宋楚瑶正在构思大纲…"):
        st.session_state.outline = agent.generate_outline(topic)
    st.session_state.article = ""
    st.session_state.titles = ""
    st.session_state.article_en = ""

if st.session_state.outline:
    st.session_state.outline = st.text_area("大纲（可编辑）", st.session_state.outline, height=280)

# ==========================================
# ② 大纲 → 正文
# ==========================================
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
    st.session_state.article = st.text_area("正文（可编辑）", st.session_state.article, height=420)

    # ==========================================
    # ③ 多轮修改与翻译
    # ==========================================
    st.subheader("③ 修改润色与扩展")
    col_rev, col_trans = st.columns([3, 1])
    with col_rev:
        revise_cmd = st.text_input("修改指令", placeholder="例如：把第二段改得更口语化 / 增加一个数据段落")
    with col_trans:
        st.write("") 
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

# ==========================================
# ④ 标题候选
# ==========================================
st.subheader("④ 生成标题候选")
if st.session_state.article and topic.strip():
    if st.button("生成 3 个标题"):
        with st.spinner("宋楚瑶正在拟标题…"):
            st.session_state.titles = agent.generate_titles(topic, st.session_state.article)
else:
    st.info("请先生成正文。")

if st.session_state.titles:
    st.markdown(st.session_state.titles)

# ==========================================
# ⑤ 高级扩展功能（导出、PPT、配图）
# ==========================================
if st.session_state.article and topic.strip():
    st.markdown("---")
    word_count = len(st.session_state.article)
    st.info(f"📊 **当前正文统计**：共 {word_count} 个字符（包含标点）")
    
    st.subheader("📥 导出文档与幻灯片")
    col1, col2, col3 = st.columns(3)
    
    # 导出 Markdown
    with col1:
        md_content = f"# {topic}\n\n{st.session_state.article}\n\n## 标题候选\n\n{st.session_state.titles}"
        st.download_button("下载 Markdown (.md)", data=md_content, file_name=f"{topic}.md", mime="text/markdown", use_container_width=True)
        
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
        st.download_button("下载 Word (.docx)", data=bio.getvalue(), file_name=f"{topic}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

    # 生成 PPT（带背景图高级版）
    with col3:
        try:
            unsplash_key = st.secrets.get("UNSPLASH_ACCESS_KEY", "")
            bg_image_data = get_unsplash_image(topic, unsplash_key) if unsplash_key else None
            
            prs = Presentation()
            # 1. 封面页
            title_slide = prs.slides.add_slide(prs.slide_layouts[6]) 
            if bg_image_data:
                title_slide.shapes.add_picture(io.BytesIO(bg_image_data), 0, 0, width=prs.slide_width, height=prs.slide_height)
                mask = title_slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
                mask.fill.solid()
                mask.fill.fore_color.rgb = RGBColor(0, 0, 0)
                mask.fill.transparency = 0.5 
                mask.line.fill.background() 
                
            txBox = title_slide.shapes.add_textbox(Inches(1), Inches(2.5), prs.slide_width - Inches(2), Inches(2))
            tf = txBox.text_frame
            p = tf.add_paragraph()
            p.text = topic
            p.font.size = Pt(44)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255)
            p.alignment = 1 
            
            p2 = tf.add_paragraph()
            p2.text = "由宋楚瑶 AI 智能生成"
            p2.font.size = Pt(24)
            p2.font.color.rgb = RGBColor(200, 200, 200)
            p2.alignment = 1

            # 2. 内容页
            if st.session_state.outline:
                outline_lines = st.session_state.outline.split('\n')
                current_slide = None
                text_box = None
                for line in outline_lines:
                    line = line.strip()
                    if not line: continue
                    
                    if line[0].isdigit() and '.' in line[:3]:
                        current_slide = prs.slides.add_slide(prs.slide_layouts[6])
                        if bg_image_data:
                            current_slide.shapes.add_picture(io.BytesIO(bg_image_data), 0, 0, width=prs.slide_width, height=prs.slide_height)
                            mask = current_slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
                            mask.fill.solid()
                            mask.fill.fore_color.rgb = RGBColor(0, 0, 0)
                            mask.fill.transparency = 0.6 
                            mask.line.fill.background()
                            
                        text_box = current_slide.shapes.add_textbox(Inches(0.5), Inches(0.5), prs.slide_width - Inches(1), prs.slide_height - Inches(1))
                        tf = text_box.text_frame
                        p = tf.add_paragraph()
                        p.text = line
                        p.font.size = Pt(36)
                        p.font.bold = True
                        p.font.color.rgb = RGBColor(255, 255, 255)
                        
                    elif current_slide is not None and text_box is not None:
                        p = text_box.text_frame.add_paragraph()
                        p.text = "• " + line
                        p.font.size = Pt(24)
                        p.font.color.rgb = RGBColor(220, 220, 220)
                        p.space_before = Pt(12)
            
            ppt_bio = io.BytesIO()
            prs.save(ppt_bio)
            st.download_button("下载 PPT (.pptx)", data=ppt_bio.getvalue(), file_name=f"{topic}.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
        except Exception as e:
            st.error(f"生成 PPT 失败：{e}")

    # 网页端展示配图
    st.subheader("🖼️ 文章智能配图")
    if st.button("获取一张高质量封面图"):
        with st.spinner("正在寻找配图…"):
            unsplash_key = st.secrets.get("UNSPLASH_ACCESS_KEY", "")
            if not unsplash_key:
                st.error("未配置 Unsplash Access Key")
            else:
                img_data = get_unsplash_image(topic, unsplash_key)
                if img_data:
                    st.image(img_data, caption=f"与「{topic}」相关的配图", use_column_width=True)
                else:
                    st.warning("没有找到相关图片，请换个主题试试。")
