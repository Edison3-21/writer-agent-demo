"""Streamlit 前端：单页完成 主题→大纲→正文→标题 写作流程。"""
import streamlit as st
from writer_agent import WriterAgent
import io
import requests
import random
from docx import Document
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from PIL import Image

# ==========================================
# 辅助函数：从 Unsplash 获取随机图片
# ==========================================
def get_unsplash_image(topic, unsplash_key):
    if not unsplash_key:
        return None
    headers = {"Authorization": f"Client-ID {unsplash_key}"}
    # 随机取 1-10 页中的某一张，避免每次都一样
    params = {"query": topic, "per_page": 1, "page": random.randint(1, 10), "orientation": "landscape", "content_filter": "high"}
    try:
        resp = requests.get("https://api.unsplash.com/search/photos", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            img_url = results[0]["urls"]["regular"]
            img_data = requests.get(img_url, timeout=10).content
            # 强制转为标准 RGB 防止 pptx 报错
            img = Image.open(io.BytesIO(img_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=90)
            return output.getvalue()
    except Exception as e:
        print(f"Image error: {e}")
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

    # 生成 PPT（正文智能提取·左图右文版）
    with col3:
        if st.button("生成并下载 PPT (.pptx)"):
            with st.spinner("正在提取正文并排版 PPT..."):
                try:
                    unsplash_key = st.secrets.get("UNSPLASH_ACCESS_KEY", "")
                    search_query = topic if topic.isascii() else "nature landscape"

                    prs = Presentation()
                    slide_width = prs.slide_width
                    slide_height = prs.slide_height
                    left_width = int(slide_width * 0.45)

                    def create_slide():
                        slide = prs.slides.add_slide(prs.slide_layouts[6])
                        img_data = get_unsplash_image(search_query, unsplash_key)
                        
                        if img_data:
                            slide.shapes.add_picture(io.BytesIO(img_data), 0, 0, width=left_width, height=slide_height)
                            right_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left_width, 0, slide_width - left_width, slide_height)
                            right_bg.fill.solid()
                            right_bg.fill.fore_color.rgb = RGBColor(30, 30, 30)
                            right_bg.line.fill.background()
                        else:
                            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, slide_width, slide_height)
                            bg.fill.solid()
                            bg.fill.fore_color.rgb = RGBColor(255, 255, 255)
                            bg.line.fill.background()
                        return slide, (img_data is not None)

                    # --- 1. 封面页 ---
                    title_slide, has_img = create_slide()
                    txBox = title_slide.shapes.add_textbox(left_width + Inches(0.5), Inches(2.5), slide_width - left_width - Inches(1), Inches(2))
                    txBox.text_frame.word_wrap = True
                    tf = txBox.text_frame
                    p = tf.add_paragraph()
                    p.text = topic
                    p.font.size = Pt(36)
                    p.font.bold = True
                    p.font.color.rgb = RGBColor(255, 255, 255) if has_img else RGBColor(0, 0, 0)
                    p.alignment = PP_ALIGN.LEFT
                    
                    p2 = tf.add_paragraph()
                    p2.text = "由宋楚瑶 AI 智能生成"
                    p2.font.size = Pt(20)
                    p2.font.color.rgb = RGBColor(180, 180, 180) if has_img else RGBColor(100, 100, 100)
                    p2.alignment = PP_ALIGN.LEFT
                    p2.space_before = Pt(20)

                    # --- 2. 内容页（从正文中智能提取） ---
                    article_text = st.session_state.article.strip()
                    if article_text:
                        # 按换行符切分正文，过滤掉空行和只有标点的行
                        paragraphs = [p.strip() for p in article_text.split('\n') if len(p.strip()) > 5]
                        
                        # 把段落分组，每 3 段作为一页 PPT（避免一页字太多）
                        chunk_size = 3
                        for i in range(0, len(paragraphs), chunk_size):
                            chunk = paragraphs[i:i+chunk_size]
                            current_slide, has_img = create_slide()
                            
                            text_box = current_slide.shapes.add_textbox(left_width + Inches(0.5), Inches(0.5), slide_width - left_width - Inches(1), slide_height - Inches(1))
                            text_box.text_frame.word_wrap = True
                            tf = text_box.text_frame
                            
                            # 取这一段的第一句话或者前 15 个字作为 PPT 的标题
                            first_para = chunk[0]
                            title_text = first_para.split('。')[0]
                            if len(title_text) > 15: 
                                title_text = title_text[:15] + "..."
                            
                            # 插入标题
                            p_title = tf.add_paragraph()
                            p_title.text = title_text
                            p_title.font.size = Pt(28)
                            p_title.font.bold = True
                            p_title.font.color.rgb = RGBColor(255, 255, 255) if has_img else RGBColor(0, 0, 0)
                            p_title.space_after = Pt(15)
                            
                            # 插入正文段落
                            for para in chunk:
                                # 如果段落太长，截断防止溢出
                                if len(para) > 120:
                                    para = para[:120] + "..."
                                
                                p_body = tf.add_paragraph()
                                p_body.text = para
                                p_body.font.size = Pt(16) # 字号调小，塞下更多字
                                p_body.font.color.rgb = RGBColor(200, 200, 200) if has_img else RGBColor(50, 50, 50)
                                p_body.space_before = Pt(12)

                    ppt_bio = io.BytesIO()
                    prs.save(ppt_bio)
                    
                    st.success("✅ 提取正文版 PPT 生成成功！")
                    st.download_button("⬇️ 点击下载 PPT", data=ppt_bio.getvalue(), file_name=f"{topic}.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
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
                img_data = get_unsplash_image(topic if topic.isascii() else "nature landscape", unsplash_key)
                if img_data:
                    st.image(img_data, caption=f"与「{topic}」相关的配图", use_column_width=True)
                else:
                    st.warning("没有找到相关图片，请换个主题试试。")
