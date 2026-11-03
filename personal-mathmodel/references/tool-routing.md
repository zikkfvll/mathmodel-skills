# 本次比赛功能的按需集成

集成的是实际有用的功能与调用时机，不复制几十份第三方技能常驻加载，也不把已安装当已使用。发现当次技能目录和工具，读取被选中技能的当前SKILL及必要参考；不写死旧版本缓存路径，不因引用技能就安装依赖或扩大工作。

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
| 独立审阅与提交一致性 | 写作技能随包低级错误检查器；nature-reviewer；6verity按需辅助文本/版式 | 本项目独立复算与pending规则优先，不能因说明缺编译/视觉原因就PASS |
| 流程图和其他引擎 | 4drawio、typst-author仅任务需要时 | 不是本次已验证的必经工具，不固定新增图或更换引擎 |

历史证据：nature-figure本体相关脚本、Q3 scikit GP训练比较、地理DEM处理、PDF渲染、资源检测和LaTeX分页有实际功能记录。1start、4drawio、Typst、SHAP及部分统计技能仅见安装/静读/建议，不能声称此前实际全用过。author写作技能此前是未安装审核稿，当前包继承其规则，不伪造历史调用。

目标环境缺专项技能时，先按本包已有规则完成有把握的工作；确需工具时说明具体依赖和未覆盖处。不得把“有SKILL文件”当下载、编译、科学正确或权限验证的证据。

