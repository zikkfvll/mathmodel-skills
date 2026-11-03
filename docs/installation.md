# 安装与首次使用

这套工作流包含四个配套技能。完整安装时，请保留四个目录及其中的脚本、参考文件和模板。

## 在 Codex 中安装

在 Codex 中发送下面这段话，让内置安装器处理下载与安装：

```text
$skill-installer
请从 https://github.com/zikkfvll/mathmodel-skills 安装以下四个技能：
personal-mathmodel
personal-mathmodel-modeling
personal-mathmodel-coding
author-mathmodel-writing
四个目录放在同一个技能根目录，保留所有引用文件、脚本和模板。
如果已有同名技能，先检查已有版本，再说明更新方式。
```

## 手动安装

下载 [v1 完整技能包](../dist/mathmodel-skills-v1.0.zip) 并解压，将四个技能目录放到以下位置之一：

| 使用范围 | macOS / Linux | Windows |
|---|---|---|
| 个人所有项目 | `~/.agents/skills/` | `%USERPROFILE%\.agents\skills\` |
| 只在某个项目使用 | `项目根目录/.agents/skills/` | `项目根目录\.agents\skills\` |

安装后的目录应类似：

```text
.agents/skills/
├── personal-mathmodel/SKILL.md
├── personal-mathmodel-modeling/SKILL.md
├── personal-mathmodel-coding/SKILL.md
└── author-mathmodel-writing/SKILL.md
```

复制的是整个技能目录，不能只复制 `SKILL.md`，也不要把外层的 `mathmodel-skills` 仓库目录当成一个技能。已有同名目录时先备份，避免把新旧文件混在一起。

这些路径来自 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。部分较早安装器会使用 `~/.codex/skills/`；已有配置正常工作时可沿用它，四模块仍应放在同一层，避免在多个位置重复安装同名版本。

## 开始第一场比赛

安装后，在 Codex 的技能选择器中查找 `personal-mathmodel`，或在消息里输入：

```text
$personal-mathmodel
开始这次数学建模比赛。题面和附件在项目目录里。
先和我讨论整体目标、已有直觉和数据条件，再决定分问安排。
暂时不要开始正式计算。
```

再提供截止时间、当届官方格式和工具使用规定，以及已有研究或亲改文字。第一次文献检索时可以提供学校图书馆入口；账号登录由本人完成，不需要提交密码。

Codex 会发现已安装的技能；若选择器中没有出现，检查目录结构，重新打开会话，必要时重启应用。详细协作方式见 [快速上手](../personal-mathmodel/references/quick-start.md)。

## 运行条件

阅读和使用工作流本身不要求额外 Python 包。两个随附检查器使用 Python 标准库，要求 Python 3.9 或以上。具体建模所需的计算、检索、绘图和 LaTeX 工具，按当前任务准备。

自动创建并联络独立对话需要宿主提供相应工具。没有这些工具时，按启动词手动创建研究审核与执行对话，通过项目中的共享索引和交接文件协作。技能本身不提供后台调度服务。
