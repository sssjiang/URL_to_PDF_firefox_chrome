# 修改后的功能示例

## 文件命名格式对比

### 修改前
```
ID_1539_drugs.com.pdf
ID_1540_drugs.com.pdf
ID_1541_drugs.com.pdf
```

### 修改后
```
1539.pdf              # 正常页面
1540_(error).pdf      # 错误页面（如Page Not Found）
1541.pdf              # 正常页面
```

## 错误检测示例

脚本运行时的输出示例：

```
Processing link 1/10 (ID: 1539)
Opening: https://www.drugs.com/lisinopril.html
Page title: Lisinopril: Uses, Dosage, Side Effects & Warnings - Drugs.com
✓ Valid page detected for ID 1539
✓ Renamed and moved mozilla.pdf to: 1539.pdf (245867 bytes)
✓ Successfully processed ID 1539

Processing link 2/10 (ID: 1540)
Opening: https://www.drugs.com/invalid-page-123.html
Page title: Page Not Found - 404 Error - Drugs.com
Error detected in title: 'page not found' found
⚠️  Error page detected for ID 1540
✓ Renamed and moved mozilla.pdf to: 1540_(error).pdf (56234 bytes)
✓ Successfully processed ID 1540 (error page)
```

## 输出目录结构

```
drugs_com_pdfs_mozilla_renamed/
├── 1539.pdf          # 正常的药物信息页面
├── 1540_(error).pdf  # 错误页面（404、页面不存在等）
├── 1541.pdf          # 正常的药物信息页面
├── 1542_(error).pdf  # 另一个错误页面
└── 1543.pdf          # 正常的药物信息页面
```

## 主要改进

1. **简洁命名**：`1539.pdf` 而不是 `ID_1539_drugs.com.pdf`
2. **错误标识**：`1540_(error).pdf` 清楚标示问题页面
3. **智能检测**：自动识别页面错误，无需手动判断
4. **易于管理**：文件名直接对应Excel中的ID，便于查找和管理
