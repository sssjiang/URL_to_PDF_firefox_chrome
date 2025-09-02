#!/usr/bin/env python3
"""
测试脚本：验证修改后的Firefox自动化脚本功能
"""

import sys
import os
from pathlib import Path

# 添加当前目录到路径以便导入
sys.path.append(str(Path(__file__).parent))

try:
    from auto_operation_down_drugs_com_firefox import (
        get_drugs_com_links_with_ids,
        move_and_rename_mozilla_pdf
    )
    import pandas as pd
except ImportError as e:
    print(f"Import error: {e}")
    print("请确保已安装 pandas, selenium 等必需的库")
    sys.exit(1)


def test_excel_reading():
    """测试Excel文件读取功能"""
    print("=== 测试Excel文件读取 ===")
    
    workspace_dir = Path(__file__).parent
    excel_path = workspace_dir / "aitep_references_need_fulltext_with_domain.xlsx"
    
    if not excel_path.exists():
        print(f"Excel文件不存在: {excel_path}")
        return False
    
    try:
        # 测试新的函数
        drugs_data = get_drugs_com_links_with_ids(str(excel_path))
        
        if drugs_data:
            print(f"✓ 成功读取 {len(drugs_data)} 条 www.drugs.com 链接")
            print("前3条数据示例:")
            for i, data in enumerate(drugs_data[:3]):
                print(f"  {i+1}. ID: {data['id']}, Link: {data['link'][:60]}...")
            return True
        else:
            print("✗ 未找到任何 www.drugs.com 链接")
            return False
            
    except Exception as e:
        print(f"✗ 读取Excel文件时出错: {e}")
        return False


def test_file_rename():
    """测试文件重命名功能"""
    print("\n=== 测试文件重命名功能 ===")
    
    workspace_dir = Path(__file__).parent
    test_dir = workspace_dir / "test_rename"
    test_dir.mkdir(exist_ok=True)
    
    # 创建一个测试的mozilla.pdf文件
    test_mozilla_path = workspace_dir / "mozilla.pdf"
    test_content = b"Test PDF content"
    
    try:
        # 测试正常页面重命名
        print("测试正常页面重命名...")
        with open(test_mozilla_path, 'wb') as f:
            f.write(test_content)
        
        success = move_and_rename_mozilla_pdf(
            str(workspace_dir),
            str(test_dir), 
            "123",
            False  # 正常页面
        )
        
        expected_file = test_dir / "123.pdf"
        if success and expected_file.exists():
            print(f"✓ 正常页面重命名成功: {expected_file.name}")
            expected_file.unlink()
        else:
            print("✗ 正常页面重命名失败")
            return False
        
        # 测试错误页面重命名
        print("测试错误页面重命名...")
        with open(test_mozilla_path, 'wb') as f:
            f.write(test_content)
        
        success = move_and_rename_mozilla_pdf(
            str(workspace_dir),
            str(test_dir), 
            "456",
            True  # 错误页面
        )
        
        expected_file = test_dir / "456_(error).pdf"
        if success and expected_file.exists():
            print(f"✓ 错误页面重命名成功: {expected_file.name}")
            expected_file.unlink()
            return True
        else:
            print("✗ 错误页面重命名失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试文件重命名时出错: {e}")
        return False
    finally:
        # 清理
        if test_mozilla_path.exists():
            test_mozilla_path.unlink()
        if test_dir.exists():
            try:
                test_dir.rmdir()
            except:
                pass


def test_error_detection():
    """测试错误页面检测功能（模拟测试）"""
    print("\n=== 测试错误页面检测功能 ===")
    
    try:
        from auto_operation_down_drugs_com_firefox import check_page_for_errors
        print("✓ 错误检测函数导入成功")
        print("注意: 错误检测功能需要实际的浏览器环境才能完全测试")
        return True
    except ImportError as e:
        print(f"✗ 错误检测函数导入失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("开始测试修改后的Firefox自动化脚本功能...\n")
    
    # 测试Excel读取
    excel_test_passed = test_excel_reading()
    
    # 测试文件重命名
    rename_test_passed = test_file_rename()
    
    # 测试错误检测
    error_detect_passed = test_error_detection()
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"Excel读取测试: {'✓ 通过' if excel_test_passed else '✗ 失败'}")
    print(f"文件重命名测试: {'✓ 通过' if rename_test_passed else '✗ 失败'}")
    print(f"错误检测测试: {'✓ 通过' if error_detect_passed else '✗ 失败'}")
    
    if excel_test_passed and rename_test_passed and error_detect_passed:
        print("\n🎉 所有测试通过！修改后的脚本应该可以正常工作。")
        print("\n使用方法:")
        print("python auto_operation_down_drugs_com_firefox.py")
        print("或者:")
        print("python auto_operation_down_drugs_com_firefox.py your_excel_file.xlsx")
        print("\n新功能:")
        print("- 简化的文件命名: {ID}.pdf")
        print("- 错误页面自动检测")
        print("- 错误页面特殊命名: {ID}_(error).pdf")
        print("- PDF文件保存在 'drugs_com_pdfs_mozilla_renamed' 文件夹中")
        print("- 每次运行不会覆盖之前的文件")
    else:
        print("\n⚠️  部分测试失败，请检查相关配置。")


if __name__ == "__main__":
    main()
