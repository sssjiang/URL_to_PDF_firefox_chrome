# AITEP自动上传 - 快速开始指南

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install selenium>=4.0.0
```

### 2. 安装ChromeDriver (macOS)
```bash
brew install chromedriver
```

### 3. 运行脚本
```bash
python3 auto_upload.py
```

## 📁 文件要求

确保您的PDF文件位于：`/Users/zelinjiang/Downloads/journal/`

文件名格式：`{id}.pdf` （例如：`1526.pdf`, `2853.pdf`）

## 🔧 脚本功能

✅ 自动读取journal目录中的PDF文件  
✅ 提取文件名中的ID  
✅ 打开Chrome浏览器  
✅ 访问 `https://aitep.probot.hk/en/APIs/references/{id}`  
✅ 点击上传按钮 (class: `css-1p3hq3p ant-btn ant-btn-primary ant-btn-sm`)  
✅ 点击"Select File"按钮  
✅ 选择并上传PDF文件  
✅ 点击"OK"确认上传  
✅ 生成详细日志文件  

## 📊 日志输出

脚本会创建带时间戳的日志文件：`upload_log_YYYYMMDD_HHMMSS.txt`

包含：
- 每个文件的处理状态
- 成功/失败统计
- 详细的错误信息

## 🎯 当前目录文件

根据扫描，您的journal目录包含 **165个PDF文件**，包括：
- 1526.pdf → 2853.pdf 等数字ID文件
- 一个大写扩展名文件：2853.PDF

所有文件都会被自动处理！

## ⚙️ 可选参数

**后台运行（无界面）：**
```bash
python3 auto_upload.py --headless
```

## 🛠️ 故障排除

**如果Chrome启动失败：**
```bash
# 检查chromedriver
which chromedriver

# 重新安装
brew reinstall chromedriver
```

**如果目录权限问题：**
```bash
ls -la /Users/zelinjiang/Downloads/journal/
```

## 📞 需要帮助？

查看详细文档：`UPLOAD_AUTOMATION_README.md`
