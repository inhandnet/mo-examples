# mo-examples

[English](README.md) | 简体中文

InHand Mo 系列单板计算机的应用演示与示例项目。

相关仓库：[Mo62A](https://github.com/inhandnet/Mo62A)（Mo 62A 板级支持与系统镜像）、[mo-docs](https://github.com/inhandnet/mo-docs)（产品文档）。

## 状态

目录结构、贡献规范以及 CI 与发布流水线已就绪。`ai/` 与 `camera/` 已加入第一批示例（来自 Mo62A 仓库与 mo-docs 教程包）；`peripherals/`、`network/`、`r5f/`、`ros2/` 仍为占位目录，其 `README.md` 说明将要存放的内容。示例迁入本仓库时未重新编译或重新运行，各目录 README 写明了验证范围与对应镜像版本。目录发布不增加实机验证结论。

## 目录结构

- `ai/` — Edge AI 示例：C/C++ SDK 示例（`edgeai-cpp/`）、Python ONNX Runtime 冒烟测试（`python-smoke/`）、区域占用教程应用（`zone-demo/`）
- `camera/` — 摄像头示例：IMX219 CSI 实时预览（`imx219-preview/`）
- `peripherals/` — Peripheral examples
- `network/` — Networking examples
- `r5f/` — R5F 示例（占位，P2 阶段）
- `ros2/` — ROS 2 示例（占位，P2 阶段）
- `scripts/` — 仓库维护脚本（提交信息检查、变更记录生成）
- `.githooks/` — 本地提交信息检查钩子
- `.github/` — Issue 表单、PR 模板与 GitHub Actions 工作流

## 参与贡献

通过 PR 提交到 `master`。提交信息规范、PR 流程与本地钩子启用方法见 [CONTRIBUTING.md](CONTRIBUTING.md)（`git config core.hooksPath .githooks`）。PR 必须通过 `commit-message` 与 `ci` 两项检查后才能合并。使用本仓库的 GitHub Issues 提交可复现问题和功能建议。

## 发布与标签

新发布仅使用已通过检查的 master 提交上的普通附注标签 `VX.Y.Z`；只有 developer 发布网站 RC。工作流校验目录数据、生成源码包和 SPDX SBOM，在 release.json 中记录源码提交与目录哈希，计算 SHA-256，全部附件就绪后公开 Release。历史 RC 保留不变。Changelog 中英文标题固定，条目保留英文。

## 安全

请勿在公开 Issue 中报告安全漏洞，见 [SECURITY.md](SECURITY.md)。

## 许可证

见 [LICENSE](LICENSE)。

## 统一网站接入

examples.json 只列出已有源码工程、入口、镜像/模型依赖和教程路由，空占位目录不算示例；源码可用不代表新一轮实机验收通过。 developer 固定源码版本后统一校验和渲染，本仓库不部署文档网站。

Node 22 下运行 `node scripts/check-catalog.mjs` 和 `node --test tests/*.test.mjs`。validation/ 是 developer 已提交规则的固定副本，通过哈希核验，不手工编辑。集成预览在 developer 中运行 `npm run preview -- --source mo-examples=/path/to/mo-examples`。
