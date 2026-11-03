# 只检查当前任务需要的环境

在正式计算、绘图、编译或导出前，按当前方案选需要的检查；新机器、切换项目环境或实际出现依赖问题时再查。不要每次讨论都重查，也不把缺少无关工具变成开题门槛。优先复用现有项目的解释器和已核环境记录，只重查变化项。

先从本轮请求和方案判断要做什么。明确只写Markdown，就不问用户选择编译器；方法还在讨论，不启动环境安装。计算依赖可从已确认方案、脚本导入或项目直接依赖中确定，不让用户填写整套工具表。

## 按任务调用

工具为 [scripts/check_environment.py](../scripts/check_environment.py)，只用Python标准库。辅助脚本要求Python 3.9及以上；本包实际验证环境为Python 3.12.14，3.9语法/API下限不等于所有版本或平台均已实跑。先用项目已有的兼容解释器，不要求升级到最新版。示例中的Python应替换为项目已有解释器；本项目使用`.venv/bin/python`。`--task`可以重复，只选本轮确实要做的工作。

|任务|检查什么|不会因此要求什么|
|---|---|---|
|`md`|这个环境检查不为纯Markdown编辑增加外部依赖|不查科学包、编译器或导图工具|
|`compute`|选定Python和明确声明的导入模块|不默认安装numpy/pandas/scipy整套包；未声明依赖时只确认Python，具体依赖保持未核|
|`plot`|选定Python与绘图库，默认导入matplotlib，可用`--plot-library`换成实际采用的库|不新增图形设计任务，不检查全部图形工具|
|`latex`|已选引擎的实际可执行程序及版本响应|不同时要求XeLaTeX、Tectonic、Typst；不自动编译论文、下载宏包或检查所有字体|
|`pdf-view`|一个已有PDF页面转换工具的版本响应|不安装全部转换工具，不冒称已经看过PDF|
|`diagram`|需要时才查指定或可找到的DrawIO命令|不把流程图变成每问必交项|

```text
python check_environment.py --task md
python check_environment.py --task compute --python /项目/.venv/bin/python --require-module numpy --require-module scipy
python check_environment.py --task plot --python /项目/.venv/bin/python
python check_environment.py --task latex --engine tectonic --compiler /已有工具/tectonic --task pdf-view
```

`--require-module`使用真实导入名，例如`sklearn`，不是`pip`需求表达式或任意命令。只导入受信任的项目依赖；第三方模块的初始化本身会运行代码。工具在临时目录使用隔离子进程，禁写Python字节码，Matplotlib配置指向临时位置，但不声称控制了任意第三方模块的所有行为。

需要报告时加`--json /本轮审核/环境检查.json`；工具只额外写这个明确指定的报告，不覆盖源码或修改环境。不要把报告目标指向已有配置。每项探测默认最多10秒，`--timeout`可在0至60秒之间调整；超时、版本命令失败或结构化结果不完整都记未核，不当作通过。

## 看结果后怎么推进

- `requested_checks_ready`／退出0：本次所选的版本或导入检查完成。它不表示数值算法、数据、实际绘图或论文已经验证。
- `current_task_missing_dependency`／退出1：某个当前任务需要的程序未找到或模块导入失败。指出具体项、使用的解释器和影响，选择已有兼容工具或提出只补该依赖的办法；不依赖它的工作可继续。
- `needs_details_or_verification`／退出3：例如计算未声明依赖、排版未选引擎，或探测失败/超时。先从项目现有记录补清，不反复向用户索要已有信息，不把未核项说成已具备。
- 退出2：参数、报告写入等使工具未完成，先解决该执行问题。

缺依赖时不自动安装、升级、改系统Python或替换用户环境。按当前用户授权提供具体解决办法；需要安装的外部变化再遵实际权限处理。这里的状态只服务当前任务，不增加额外的方案审批或全链验收。

## 哪些事仍需实际做

命令存在、`--version`成功、包可导入、合成小样成功、真实结果正确是不同证据。本工具只做到前几项中的版本与导入探测：不会运行模型、处理比赛数据、导出新图、编译论文、验证中文字体回退或检查图表可读性。LaTeX宏包、类兼容性、数据输入和实际页面仍按写作/执行规则核查。

本轮在当前macOS项目环境做了定向运行；不据此保证其他平台、学校资源或整场比赛均可运行。既有全项目`verify_environment.py`可在真正需要全面互操作检查时单独使用，不作为每次工作必经步骤。
