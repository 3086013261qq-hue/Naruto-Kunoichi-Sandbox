# Naruto-Kunoichi-Sandbox

《火影姬世界》资料库工程。

## 正式资料结构

正式世界书资料只维护四类：

- `worldbook/settings/`：设定（AU核心设定、技能体系、核心规则、输出/记忆规则）
- `worldbook/timeline/`：时间线
- `worldbook/characters/`：角色
- `worldbook/locations/`：地点

`docs/` 与 `qa/` 只用于施工记录和质量检查，不属于第五类世界书正文。

## 当前施工原则

1. 资料库阶段不组装完整角色卡。
2. 原 PNG/JSON 仅作为溯源基线；后续修改以 `worldbook/` 下四类资料为正式工作源。
3. 角色、地点、时间线与设定分离维护，避免一处改动牵连整卡。
4. 新增《火影姬世界》AU内容只归入 `settings/`；角色回装与角色精修另行进行。
