# 🎱 双色球麒麟四幻图精准分析平台

**全自动更新 · 免费托管 · 手机电脑均可访问**

## ✨ 功能特点

- 🔄 **全自动更新**：GitHub Actions 定时抓取官方开奖数据，无需手动操作
- 📱 **响应式设计**：手机、平板、电脑均可正常访问
- 🏠 **免费托管**：GitHub Pages 完全免费，全球 CDN 加速
- 📊 **多维度分析**：四幻图、九转连环图、达芬奇密码、五尾围蓝等
- 🔍 **自动复盘**：每期自动验证上期条件命中情况

## 🚀 部署步骤（5 分钟搞定）

### 第一步：创建 GitHub 仓库

1. 注册/登录 [GitHub](https://github.com)
2. 点击右上角 **+** → **New repository**
3. 仓库名填 `ssq-qilin`（或任意名称）
4. 选择 **Public**（公开才能免费用 Pages）
5. 点击 **Create repository**

### 第二步：上传文件

把本项目所有文件上传到仓库根目录：

```
ssq-qilin/
├── index.html                              # 主页面
├── data.json                               # 开奖数据（自动更新）
├── .github/workflows/update-data.yml       # 自动更新脚本
└── README.md                               # 说明文档
```

**上传方式（任选其一）：**

**方式 A：网页直接上传**
1. 在仓库页面点击 "uploading an existing file"
2. 把所有文件拖进去，点 Commit

**方式 B：Git 命令行**
```bash
git clone https://github.com/你的用户名/ssq-qilin.git
cd ssq-qilin
# 把项目文件复制到这个目录
git add .
git commit -m "初始部署"
git push
```

### 第三步：开启 GitHub Pages

1. 进入仓库 → **Settings** → **Pages**
2. Source 选择 **Deploy from a branch**
3. Branch 选择 **main**，文件夹选 **/ (root)**
4. 点 **Save**
5. 等待 1-2 分钟，页面会显示你的网站地址：
   `https://你的用户名.github.io/ssq-qilin/`

### 第四步：开启自动更新

1. 进入仓库 → **Actions** 标签页
2. 如果看到 "I understand my workflows, go ahead and enable them"，点 **Enable**
3. 完成！系统会在每周二、四、日晚 22:30 自动更新数据

## 📱 手机访问

部署完成后，直接在手机浏览器输入网址即可访问。
建议添加到手机主屏幕（浏览器菜单 → 添加到主屏幕），体验类似 APP。

## 🔧 手动更新

如果需要立即更新数据：

1. 进入仓库 → **Actions** 标签页
2. 点击左侧 **Auto Update SSQ Data**
3. 点击 **Run workflow** → **Run workflow**
4. 等待 1 分钟即可

## 📝 数据格式

`data.json` 格式如下：

```json
{
  "latest": [
    {"period": "2026080", "date": "2026-07-14", "red": [4,5,11,19,27,32], "blue": 1},
    {"period": "2026079", "date": "2026-07-12", "red": [1,11,17,22,24,29], "blue": 4},
    {"period": "2026078", "date": "2026-07-09", "red": [7,11,14,16,27,28], "blue": 6}
  ],
  "updated": "2026-07-16T15:30:00+08:00"
}
```

## ⚠️ 免责声明

双色球开奖完全随机，所有分析演算仅作数据参考，不构成任何投注建议。请理性购彩。

## 🔮 后续扩展

如需添加新的分析条件，只需修改 `index.html` 中的 JavaScript 代码即可，数据层完全解耦。
