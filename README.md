# wowaddonscompatible

Hermes Agent **skill** for porting / fixing World of Warcraft addons on the current
retail patch (12.x Midnight era) — the accumulated, field-tested playbook behind the
[QueFrame](https://github.com/leafcentre/QueFrame) port of X-Perl / Z-Perl.

一份面向 WoW 插件（12.0 / 12.1）迁移与修复的 Hermes Agent 技能库，是
QueFrame（X-Perl / Z-Perl 的 12.1 移植版）开发过程中沉淀下来的实战笔记。

## 内容 / Contents

| 文件 | 说明 |
|---|---|
| `SKILL.md` | 主技能：TOC/Interface 规则、secret values 处理、frame 嵌入 taint、Aura 容器迁移、整包改名流程、BugGrabber 取证、验证清单 |
| `references/12x-api-replacements.md` | 已核实的 12.x 被移除 API → 替代 API 对照表 |
| `references/live-client-measurement.md` | 无法直接驱动游戏客户端时，如何从落盘文件/存档/pixel 取证（session 边界、SavedVariables 探针、日志） |
| `tools/sanitize.py` | 把本机 skill 目录导出成本仓库内容的脱敏脚本（映射表刻意不入库） |

## 脱敏说明 / Sanitized content

本仓库内容由本机运行的 skill 目录自动导出，导出时会把机器相关信息替换为占位符：

| 占位符 | 代表 |
|---|---|
| `<home>` | 用户主目录（原文含具体用户名） |
| `<wow-install>` | 游戏安装盘符与路径 |
| `<hermes-skills>` | Hermes skills 根目录 |
| `<local-proxy>` | 本机代理端口 |

导出用 `tools/sanitize.py`，替换映射表放在仓库之外，因此仓库里不含被替换的原文。
凡是被替换过的机器信息都不会出现在本仓库的任何提交中（历史已重写为单次提交）。

## 怎么用 / Usage

作为 Hermes Agent 的 skill 使用，把仓库内容放进 skills 目录即可：

```bash
git clone https://github.com/leafcentre/wowaddonscompatible.git \
  <hermes-skills>/gaming/wowaddonscompatible
```

主要覆盖的问题类型：

- 12.x 强制 interface 版本匹配（`## Interface: 120100`），主 TOC 改了但子模块 TOC 漏改
- Secret Values：战斗/副本语境下 `UnitHealth`/`UnitClass`/`UnitGUID`/施法信息等是 secret，
  哪些运算会报错、哪些 API 可以接收 secret 直接显示
- `issecretvalue` 与 `canaccessvalue` 的双重判定（只测前者会让功能静默降级）
- 嵌入 / 重设父级 Blizzard 模板 frame 造成的 taint（`tainted by 'X'` 指向谁就改谁）
- 12.1 `SecureAuraHeaderTemplate` 移除后的 `AuraContainer`/`AuraButton` 迁移
- 整包改名（重建品牌）的有序替换策略与坑（自我 `DisableAddOn`、被 `= nil` 清掉又被调用的全局）
- 无 live client 时的取证方法：SavedVariables 探针、颜色像素采样、BugGrabber session 分辨

## 状态 / Status

持续更新的个人笔记，非官方文档；结论以「已在 12.1 实机验证」和「静态推断」区分标注。
Issues / PR 欢迎，但内容以实战结论为准。

## License

MIT
