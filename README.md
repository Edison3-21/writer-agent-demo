markdown
# 智能写作助手 Demo（ModelScope-Agent + DashScope + Streamlit）

本项目是基于 ModelScope-Agent 框架开发的“自媒体文章助手” demo。参考了课程 PPT Ch5 §1 的角色模板（小唐），实现了从主题到成文的完整创作链路，并支持多轮对话修改与多文体切换。

## 一、运行说明

1. 环境准备：建议使用 Python 3.10 或 3.11。
2. 安装依赖：
   ```bash
   pip install modelscope-agent dashscope streamlit python-dotenv
配置 API Key：

将 .env.example 重命名为 .env。

在 .env 文件中填入您的 DashScope API Key：DASHSCOPE_API_KEY=sk-您的真实密钥。

启动应用：

bash
streamlit run streamlit_app.py
在浏览器（通常是 http://localhost:8501）中即可访问并使用。

二、功能实现（对应作业要求）
核心功能 1：输入主题 → 自动生成 Markdown 格式的大纲。

核心功能 2：大纲（支持用户编辑） → 自动扩写生成正文（约 800-1200 字）。

核心功能 3：基于正文内容 → 生成 3 个风格各异的标题候选，并附带推荐理由。

加分项 1（多轮修改）：在正文生成后，用户可通过输入修改指令（如“把开头改得更吸引人”），对当前版本进行局部/全局重写。

加分项 2（UI 美观）：使用 Streamlit 单页布局，分步骤交互（①-④），包含加载动画（Spinner）、可编辑文本框、侧边栏重置等功能。

加分项 3（多文体支持）：支持“通用 / 新闻 / 散文 / 营销” 4 种文体，通过注入不同 Prompt 控制输出风格。

三、PPT Ch5 §1 内容对应
本项目的核心设计直接继承了 PPT 中“小唐”的角色设定：

writer_agent.py 中的 BASE_ROLE 保留了“才情横溢的文人身份”及“一键生成 + 修正润色能力”。

面向自媒体文章场景，通过结构化 prompt 实现了大纲、正文、标题的专项生成。

四、AI 协作记录（必须披露）
AI 生成部分：writer_agent.py 的底层 _run 方法及基础调用逻辑、streamlit_app.py 的页面骨架由 Claude 生成初稿。

人工修改部分：角色模板与 PPT 原文对齐；STYLE_PROMPTS（文体约束）手工编写；多轮修改逻辑改为显式保存内容后传入 revise()；Streamlit 中大纲/正文可编辑回写逻辑为手工调整。

使用的核心 Prompt：“用 ModelScope-Agent RolePlay 写一个写作助手，三个方法：生成大纲、生成正文、生成标题，instruction 用中文角色模板。”

五、实验反思与环境踩坑记录
依赖冲突解决：在环境搭建过程中，遇到了新版本 langchain 移除 langchain.schema 路径导致的 ModuleNotFoundError。通过将 langchain 降级至 0.0.267，并同步固定 langchain-community 等依赖版本，成功解决了该兼容性问题。

Numpy/Pandas 版本冲突：由于较新的 pandas 强制要求 numpy>=2.0.2，导致底层库编译报错。通过升级 numpy 并限制 pandas 版本（<3.0）得以解决。

多轮修改的 Token 消耗：RolePlay 的对话记忆是隐式的，做多轮修改时如果完全依赖它，用户看不到“改了哪一版”。显式保存 st.session_state.article 并每次把全文传入 revise()，虽然 token 消耗略高，但可控性明显更好。

版本控制：本项目已使用 Git 进行版本控制，初始 commit 信息为：feat: 智能写作助手 demo 完整版。