# mo-examples

[English](README.md) | 简体中文

InHand Mo 系列单板计算机的应用演示与示例项目。

相关仓库：[Mo62A](https://github.com/inhandnet/Mo62A)（Mo 62A 板级支持与系统镜像）、[mo-docs](https://github.com/inhandnet/mo-docs)（产品文档）。

## 状态

本仓库目前是骨架：目录结构、贡献规范以及 CI 与发布流水线已就绪，内容将分阶段加入。每个占位目录中的 `README.md` 说明了该目录将要存放的内容。

## 目录结构

- `ai/` — Edge AI demos
- `camera/` — Camera examples
- `peripherals/` — Peripheral examples
- `network/` — Networking examples
- `r5f/` — R5F examples
- `ros2/` — ROS 2 examples
- `scripts/` — 仓库维护脚本（提交信息检查、变更记录生成）
- `.githooks/` — 本地提交信息检查钩子
- `.github/` — Issue 表单、PR 模板与 GitHub Actions 工作流

## 参与贡献

通过 PR 提交到 `master`。提交信息规范、PR 流程与本地钩子启用方法见 [CONTRIBUTING.md](CONTRIBUTING.md)（`git config core.hooksPath .githooks`）。PR 必须通过 `commit-message` 与 `ci` 两项检查后才能合并。产品使用问题请到[社区论坛](https://community.inhand.com)提问。

## 发布与标签

推送形如 `V<major>.<minor>.<patch>` 或 `V<major>.<minor>.<patch>-rc<n>` 的附注标签即触发发布工作流：校验标签、根据双语提交信息生成中英文变更记录、打包源码归档（含 SPDX SBOM 与 SHA-256 校验和）并创建以标签命名的 GitHub Release；`-rc` 标签发布为预发布版本。

## 安全

请勿在公开 Issue 中报告安全漏洞，见 [SECURITY.md](SECURITY.md)。

## 许可证

见 [LICENSE](LICENSE)。
