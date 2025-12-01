# setuptools-nodejs

一个用于将 Node.js 前端项目打包到 Python 包中的 setuptools 扩展，特别适用于 Flask、FastAPI 等 Python 后端框架的全栈应用打包。

> **设计灵感**：本项目参考了 [setuptools-rust](https://github.com/PyO3/setuptools-rust) 和 [setuptools-scm](https://github.com/pypa/setuptools-scm) 的设计思路，采用了类似的扩展模式和配置方法，以实现与 Python 打包生态系统的无缝集成。

[中文文档](README_CN.md) | [English Documentation](README.md)

## 项目概述

`setuptools-nodejs` 扩展 setuptools，用于自动构建 Node.js 前端项目并将其构建产物包含在 Python 包中。它非常适合包含使用 React、Vue、Angular 等框架构建的前端组件的全栈 Python 应用程序。

## 项目实现入口点

### 主要入口文件
- `setuptools_nodejs.setuptools_ext.pyprojecttoml_config` - 配置解析入口
- `setuptools_nodejs.build.build_nodejs` - 构建命令实现
- `setuptools_nodejs.extension.NodeJSExtension` - 前端项目配置类

### 项目结构
```
setuptools-nodejs/
├── src/setuptools_nodejs/
│   ├── setuptools_ext.py    # setuptools 集成和配置解析
│   ├── extension.py         # NodeJSExtension 类定义
│   ├── build.py            # 构建命令实现
│   ├── command.py          # 命令基类
│   ├── clean.py            # 清理命令
│   └── _utils.py           # 工具函数
├── examples/vue-helloworld/ # 工作示例项目
│   ├── browser/            # Vue 前端项目
│   │   ├── package.json    # 前端依赖配置
│   │   ├── vite.config.ts  # Vite 构建配置
│   │   └── src/            # 前端源代码
│   ├── python/             # Python 包
│   └── pyproject.toml      # 项目配置
└── tests/                  # 测试文件
```

## 快速开始

### 1. 配置您的项目

在 `pyproject.toml` 中添加以下配置：

```toml
[build-system]
requires = ["setuptools", "setuptools-nodejs"]
build-backend = "setuptools.build_meta"

[project]
name = "my-fullstack-app"
version = "0.1.0"

[tool.setuptools-nodejs]
frontend-projects = [
    {target = "my-frontend", source_dir = "frontend", artifacts_dir = "dist"}
]
```

### 2. 构建您的包

```bash
python -m build
```

这将自动：
1. 使用 npm 构建您的前端项目（`npm install` 和 `npm run build`）
2. 将构建产物复制到包目录
3. 将所有内容打包到 Python wheel 或 sdist 中

## 配置示例

### 基本配置（基于 vue-helloworld 示例）

```toml
[build-system]
requires = ["setuptools", "setuptools-nodejs"]
build-backend = "setuptools.build_meta"

[project]
name = "vue-helloword"
version = "0.1.0"
description = "Test project for setuptools-nodejs integration"

[tool.setuptools-nodejs]
frontend-projects = [
    {target = "vue-helloword", source_dir = "browser", artifacts_dir = "dist"}
]

[tool.setuptools.packages.find]
where = ["python"]
```

### 多个前端项目及输出目录

```toml
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "admin-panel", source_dir = "admin", artifacts_dir = "dist", output_dir = "my_package/admin"},
    {target = "client-app", source_dir = "client", artifacts_dir = "build", output_dir = "my_package/client"}
]
```

### 高级配置

```toml
[tool.setuptools-nodejs]
frontend-projects = [
    {
        target = "my-app",
        source_dir = "frontend",
        artifacts_dir = "dist",
        args = ["--production"],  # 额外的 npm 参数
        quiet = false,            # 显示 npm 输出
        optional = false          # 如果前端构建失败则中止构建
    }
]
```

## 当前实现的功能

### ✅ 已实现且正常工作
- **前端自动构建**：自动运行 `npm install` 和 `npm run build`
- **构建产物复制**：将前端构建产物自动复制到 Python 包中
- **多项目支持**：支持配置多个前端项目
- **配置解析**：正确解析 `pyproject.toml` 中的配置
- **Vue 项目支持**：vue-helloworld 示例已验证可正常工作
- **基础错误处理**：基本的构建错误处理

### 命令行工具

```bash
# 使用 pyproject.toml 配置构建前端
python -m setuptools_nodejs build

# 不安装依赖进行构建
python -m setuptools_nodejs build --no-install

# 构建前清理输出目录
python -m setuptools_nodejs build --clean

# 详细日志输出
python -m setuptools_nodejs build --verbose
```

## 未实现功能和 TODO 列表

### ❌ 有代码但未测试/未完全实现

1. **框架自动检测功能**
   - `_detect_artifacts_dir` 方法存在但未经过充分测试
   - Vue 检测：仅检查配置文件存在性，不解析实际配置
   - Angular 检测：尝试解析 `angular.json` 但错误处理简单
   - React 检测：仅检查是否有 "build" 脚本，不解析输出目录
   - **需要添加测试用例验证检测逻辑**

2. **版本检查功能**
   - `get_node_version()` 和 `get_npm_version()` 方法存在但从未被调用
   - 在构建过程中没有实际验证 Node.js 和 npm 版本
   - **需要实现版本检查逻辑并添加调用**

3. **依赖声明**
   - 版本检查需要 `semantic_version` 包但未在依赖中声明
   - **需要在 pyproject.toml 中添加依赖声明**

### 优先级 TODO
- [ ] 为框架自动检测功能添加测试用例
- [ ] 实现 Node.js 和 npm 版本检查功能
- [ ] 在构建过程中实际调用版本检查方法
- [ ] 添加 `semantic_version` 依赖声明
- [ ] 改进框架检测的错误处理和用户反馈
- [ ] **npm 版本验证**：在构建前添加适当的 npm 版本检查
- [ ] **框架特定的构建产物检测**：
  - [ ] Vue.js：正确解析 `vite.config.*` 和 `vue.config.js` 以获取输出目录
  - [ ] Angular：完成 `angular.json` 解析并改进错误处理
  - [ ] React：解析 `package.json` 构建脚本和配置文件以获取输出路径
- [ ] **增强的配置验证**：在构建前验证所有配置参数
- [ ] **更好的错误消息**：为常见问题提供更详细的信息性错误消息

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/TuvokYang/setuptools-nodejs
cd setuptools-nodejs

# 可编辑模式
pip install -e .

# 运行测试
pytest
```

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件。

## 支持

如果您遇到任何问题或有疑问，请：
1. 查看[文档](https://github.com/TuvokYang/setuptools-nodejs#readme)
2. 搜索[现有问题](https://github.com/TuvokYang/setuptools-nodejs/issues)
3. 创建[新问题](https://github.com/TuvokYang/setuptools-nodejs/issues/new)
