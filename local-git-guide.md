# 本地开发与 Git 分支管理指南

本指南介绍如何在不污染远程代码仓的情况下，进行本地开发、实验和笔记记录。

## 1. 查看当前连接的远程仓库

首先，确认当前项目连接的远程仓库地址：

```bash
git remote -v
```

输出示例：
```
origin  https://github.com/shareAI-lab/learn-claude-code (fetch)
origin  https://github.com/shareAI-lab/learn-claude-code (push)
```

## 2. 创建并切换到本地分支

为了隔离您的修改（如添加注释、调试代码等），建议创建一个独立的本地分支。

**命令：**
```bash
git checkout -b local-study
```
*解释：`-b` 表示创建并切换。`local-study` 是分支名，您可以随意命名（例如 `study-notes`, `my-experiment`）。*

## 3. 在本地分支上工作与保存

在这个分支上，您可以随意修改代码。要保存修改到本地 Git 历史中：

```bash
# 添加所有修改的文件到暂存区
git add .

# 提交修改（仅保存在本地）
git commit -m "添加了我的学习笔记和调试代码"
```

## 4. 同步远程仓库的更新（可选）

如果远程仓库（main 分支）有更新，您想把这些更新合并到您的本地分支：

```bash
# 1. 切换回主分支
git checkout main

# 2. 拉取最新代码
git pull origin main

# 3. 切回您的学习分支
git checkout local-study

# 4. 将主分支的更新合并过来
git merge main
```

## 5. 重要提示：不要推送（Push）

只要您**不**执行 `git push origin local-study`，您的这个分支就永远只存在于您的这台电脑上。

*   **安全操作**：`git commit`（保存到本地历史）
*   **危险操作**：`git push`（上传到远程服务器）

这样，您就可以放心地在 `local-study` 分支上通过代码注释来记录学习心得，或者修改代码进行实验，而不用担心影响开源项目或泄露个人笔记。
