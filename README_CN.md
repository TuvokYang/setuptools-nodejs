# setuptools-nodejs

一个用于构建 Node.js 前端项目并将其与 Python 代码打包的 setuptools 扩展。

[English Documentation](README.md) | [中文文档](README_CN.md)

## 概述

`setuptools-nodejs` 扩展了 setuptools，可以自动构建 Node.js 前端项目并将构建产物包含在 Python 包中。它非常适合包含使用 React、Vue、Angular 等框架构建的前端组件的全栈 Python 应用程序。

## 特性

- 🔧 **自动前端构建**: 在 Python 包构建过程中构建前端项目
- 📦 **无缝集成**: 与标准 Python 打包工具（`build`、`pip`、`twine`）配合使用
- ⚙️ **简单配置**: 在 `pyproject.toml` 中配置所有内容
- 🛠️ **灵活命令**: 用于开发构建的独立 CLI
- 📝 **结构化日志**: 使用 Python 标准日志模块的全面日志记录
- 🔄 **增量支持**: 可选的清理构建和依赖跳过
- 🗂️ **智能文件过滤**: 自动从源码分发中排除 `node_modules`

## 安装

```bash
pip install setuptools-nodejs
```

## 快速开始

### 1. 配置您的项目

在 `pyproject.toml` 中添加以下内容：

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

## 配置

### 基本配置

```toml
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "my-frontend", source_dir = "frontend", artifacts_dir = "dist"}
]
```

### 多个前端项目

```toml
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "admin-panel", source_dir = "admin", artifacts_dir = "dist"},
    {target = "client-app", source_dir = "client", artifacts_dir = "build"}
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
        optional = false          # 如果前端构建失败则构建失败
    }
]
```

## 使用方法

### 命令行界面

#### 构建前端

```bash
# 使用 pyproject.toml 中的配置构建前端
python -m setuptools_nodejs build

# 不安装依赖进行构建
python -m setuptools_nodejs build --no-install

# 在构建前清理输出目录
python -m setuptools_nodejs build --clean

# 详细日志
python -m setuptools_nodejs build --verbose
```

#### 验证配置

```bash
python -m setuptools_nodejs validate
```

#### 清理输出

```bash
python -m setuptools_nodejs clean
```

### Python 构建集成

当您使用标准工具构建 Python 包时，前端构建会自动进行：

```bash
# 构建 wheel（包含前端）
python -m build --wheel

# 构建源码分发（包含前端）
python -m build --sdist
```

### 构建配置设置

您可以使用配置设置来控制构建行为：

```bash
# 跳过前端构建
python -m build --config-setting=skip_frontend_build=true

# 即使前端失败也继续构建
python -m build --config-setting=fail_on_frontend_error=false
```

## 项目结构示例

### 基础全栈应用

```
my-app/
├── frontend/              # React/Vue 前端
│   ├── package.json
│   ├── src/
│   └── public/
├── my_app/               # Python 包
│   ├── __init__.py
│   └── static/           # ← 构建的前端文件放在这里
└── pyproject.toml
```

### 多个前端项目

```
my-project/
├── admin-frontend/       # 管理面板
│   └── package.json
├── client-frontend/      # 客户端应用
│   └── package.json
├── my_package/
│   ├── __init__.py
│   ├── admin/            # ← 管理前端
│   └── client/           # ← 客户端前端
└── pyproject.toml
```

## 错误处理

### 常见问题

1. **找不到 Node.js**: 确保 Node.js 和 npm 已安装并在您的 PATH 中
2. **缺少配置**: 确保 pyproject.toml 中存在 `[tool.setuptools-nodejs]` 部分
3. **构建失败**: 检查前端构建日志以获取具体错误

### 调试

启用详细日志以查看详细的构建信息：

```bash
python -m setuptools_nodejs build --verbose
```

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone https://gitlab.ee-yyk.com/tools/setuptools-nodejs
cd setuptools-nodejs

# 以开发模式安装
pip install -e ".[dev]"

# 运行测试
pytest
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov

# 运行特定测试文件
pytest tests/test_config.py
```

## 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 添加测试
5. 提交 pull request

## 许可证

本项目采用 MIT 许可证 - 有关详细信息，请参阅 LICENSE 文件。

## 支持

如果您遇到任何问题或有疑问，请：

1. 查看[文档](https://gitlab.ee-yyk.com/tools/setuptools-nodejs#readme)
2. 搜索[现有问题](https://gitlab.ee-yyk.com/tools/setuptools-nodejs/issues)
3. 创建[新问题](https://gitlab.ee-yyk.com/tools/setuptools-nodejs/issues/new)

## 致谢

- 灵感来源于简化全栈 Python 应用程序打包的需求
- 基于优秀的 setuptools 库构建
- 感谢所有贡献者和用户
