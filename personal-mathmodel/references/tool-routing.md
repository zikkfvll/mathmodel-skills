# 专项工具的按需选用

按当前任务选择需要的能力。先发现环境中可用的工具和技能，再读取相关SKILL及必要参考，不将所有专项技能常驻加载。下表中的名称是可选示例，并非本工作流的安装依赖；缺少某个第三方技能时，可使用具备相同能力的工具。

| 功能 | 适合按需调用 | 集成规则 |
| --- | --- | --- |
| 题意、变量、模型与验证 | 2analysis-modeling、scientific-brainstorming、scientific-critical-thinking | 使用问题定义和风险判断；个人两轮讨论与交付合同优先，不启动上游全链 |
| 真实计算与结果 | 3coding-visual | 实现确认路线、保存实际结果，遵每问两入口偏好；不套固定报告链 |
| 论文图设计和检查 | nature-figure | 集中样式、实际尺寸、多面板对齐、字体与适用碰撞检查、矢量导出；工具未做检查不报通过 |
| 文献发现、精读、引用 | nature-academic-search、paper-lookup、literature-review；关键单篇再nature-paper-xray、nature-ref-verifier | 首次实际检索按[学校接入规则](../../personal-mathmodel-modeling/references/institutional-library.md)询问或复用学校入口；采用六线与资格标准，读原文、定位证据，复用阅读卡 |
| 正文获取 | nature-downloader | 沿用共享学校资源并核当次权限，用户本人登录；正文/SI选择不重复问，检查实际内容并保留失败路径 |
| 写作与排版 | author-mathmodel-writing；nature-writing、nature-polishing、5writing按需 | 默认新LaTeX稿沿用个人当前论文模板；已有稿保留其引擎与工程，官方要求优先，不扩大至其他赛事布局 |
| PDF和DOCX | pdf；documents仅有Word材料时 | 公式/图页定向渲染，整稿适用页面检查；不强迫双格式 |
| 数据质量与表格 | data-analytics:analyze-data-quality、validate-data；spreadsheets有真实工作簿任务时 | 一次口径与共享索引，异常不自动删除；不因CSV就另建工作簿 |
| 机器学习 | scikit-learn；SHAP/statsmodels等仅确需 | 核标签与独立样本、划分和公平对照；不自动复用Q3的GP |
| 空间与栅格 | geomaster；实际用GeoDataFrame时geopandas | 核CRS、分辨率、仿射、NoData和垂直单位，公共空间预处理复用 |
| 当前任务的环境就绪 | 随包check_environment.py；见[任务环境说明](task-environment.md) | 只核当前计算、绘图或所选编译任务的必要工具；不安装、不联网，不把工具存在当任务完成 |
| 资源预算 | get-available-resources在明显大任务前 | 帮助选择规模和预算，小任务不反复探测 |
| 独立审阅与提交一致性 | 写作技能随包低级错误检查器；nature-reviewer；6verity按需辅助文本/版式 | 关键检查缺失时保留未核状态；文本或版式自检不替代独立复算 |
| 流程图和其他引擎 | 4drawio、typst-author仅任务需要时 | 仅在用户任务需要时使用，不固定新增图或更换引擎 |

目标环境缺专项技能时，先按本包已有规则完成有把握的工作；确需工具时说明具体依赖和未覆盖处。工具是否安装、是否能调用、是否完成实际任务分别核对。

