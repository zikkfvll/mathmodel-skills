# 个人数学建模工作流 Skills v1

一套面向数学建模竞赛的 Codex 技能：让使用者参与方法设计，让不同问题共享资料，让计算、审核和论文写作衔接起来。

适合希望与 AI 一起讨论和完成研究、同时保留方法判断权的个人或团队。可以从完整比赛开始，也可以只处理某一问、实现已定模型，或修改已有论文。

## 工作方式

**自由讨论 → AI 检索与阅读 → 使用者补充 → 第二轮讨论 → 确定方案 → 实现与独立复核 → 论文与交接**

总控负责开局的大方向和各问之间的关系。每问分别使用研究审核与执行两个对话：研究审核方与使用者共同决定具体方法，执行方负责运行、绘图和返修。总控在一问结束后梳理对后问的影响，无需重复批准本问方案。

资料字典、结果版本和跨问接口保存在共享索引中。新对话先读取相关交接材料，需要核实细节时再回查原件，减少重复读取大附件。

## 四个模块

| 模块 | 适合处理的任务 |
|---|---|
| [personal-mathmodel](personal-mathmodel/SKILL.md) | 开始比赛、组织分问对话、恢复阶段、协调共享资料和跨问影响 |
| [personal-mathmodel-modeling](personal-mathmodel-modeling/SKILL.md) | 理解题意、讨论直觉、学习论文、比较方法、确定模型与验证设计 |
| [personal-mathmodel-coding](personal-mathmodel-coding/SKILL.md) | 实现已确认方案、求解、保存结果、独立重绘论文图、按审核意见返修 |
| [author-mathmodel-writing](author-mathmodel-writing/SKILL.md) | 学习作者文风和同方法表达，完成正文、LaTeX 排版与稿件检查 |

模块按任务加载，不必让每个对话读完整套参考资料。

## 快速开始

[下载完整技能包](dist/mathmodel-skills-v1.0.zip) · [安装说明](docs/installation.md) · [使用指南](personal-mathmodel/references/quick-start.md)

先按 [安装说明](docs/installation.md) 安装四个模块，并保持目录名称和同层关系。在支持技能的 Codex 对话中调用：

```text
$personal-mathmodel
按这套工作流开始本次比赛。题面和附件在……，截止时间是……。
先讨论总体方向，不急着选模型或开始计算。
```

之后可以直接说：

```text
开 Q1，先聊目标、直觉和数据能支持什么。
开 Q2，沿用 Q1 确认的数据口径和接口。
模型已经确定，请按方案实现，分析和绘图分开。
只修改这一段正文，参考同方法论文的表达，保留现有结果。
```

具体分工、阶段恢复和常用请求见 [使用指南](personal-mathmodel/references/quick-start.md)。

## 文献学习与方法设计

围绕具体一问，分别搜索 Nature、SCI 中科院 1/2 区、CCF-A、国赛、研赛和美赛六类来源。科研论文通常看近四年；竞赛论文通常看近三年，筛选国赛和研赛一二等奖、美赛 O/F 奖，并定位相关小问的设计。强相关科研文献等例外在采用前讨论。

每问合计约 20 篇是可按相关性、获取条件和比赛时间调整的学习目标。先由 AI 交实际检索与阅读成果，再由使用者补充学校电子图书馆入口、论文和想法，之后一起收敛方案。全文取得、实际阅读和方法适用性分别记录。

详细规则见 [论文学习](personal-mathmodel-modeling/references/research-literature.md) 与 [检索和下载渠道](personal-mathmodel-modeling/references/channels.md)。

## 配套资源

- [通用方法短卡](personal-mathmodel-modeling/references/method-reference.md)：帮助讨论方法职责、数据条件和必要验证。
- [论文写作案例](author-mathmodel-writing/references/writing-examples/index.md)：三篇论文、六个段落级学习示例，包含原文定位和写作分析。
- [个人 LaTeX 模板](author-mathmodel-writing/assets/current-paper-latex/使用说明.md)：摘要、目录、分问建模与求解、模型评价、文献和附录；附 [七页样张](author-mathmodel-writing/assets/current-paper-latex/模板样张.pdf)。
- [任务环境检查](personal-mathmodel/references/task-environment.md)：按计算、绘图或编译任务检查所需工具。
- [稿件静态检查](author-mathmodel-writing/references/low-level-checks.md)：辅助发现占位符、文件依赖和部分引用问题。

完整比赛案例、学习笔记和独立模板入口维护在 [mathmodel-learning](https://github.com/zikkfvll/mathmodel-learning)。

## 使用条件

技能提供协作规则与辅助资源。自动建立或恢复多个对话需要当前 Codex 环境提供相应工具；没有这些工具时，可以手动建立对话并通过共享文件交接。检索、机构访问、编译和绘图也需要相应工具与权限。

辅助脚本使用 Python 标准库，要求 Python 3.9 及以上。科学结果仍需实际运行与独立判断；静态检查不能替代数学核验、引用核实或 PDF 页面检查。论文模板使用前应核对当届官方格式。

来源与第三方材料说明见 [NOTICE](NOTICE.md)。
