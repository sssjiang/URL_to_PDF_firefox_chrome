#!/usr/bin/env python3
"""
筛选Excel文件，只保留每个domain只有1行数据的记录。

功能：
- 排除有多行数据的域名（只保留domain计数为1的行）

用法：
    python filter_domains.py [input_file] [output_file]
    
默认：
    input_file: aitep_references_need_fulltext_with_domain.xlsx
    output_file: aitep_references_filtered.xlsx
"""

import sys
import pandas as pd
from pathlib import Path
from typing import List, Optional


def filter_domains(input_file: str, output_file: str) -> None:
    """
    读取Excel文件，筛选出每个domain只有1行数据的记录。
    
    Args:
        input_file: 输入Excel文件路径
        output_file: 输出Excel文件路径
    """
    try:
        # 读取Excel文件
        print(f"正在读取文件: {input_file}")
        df = pd.read_excel(input_file)
        
        print(f"原始数据行数: {len(df)}")
        print(f"列名: {list(df.columns)}")
        
        # 检查是否有domain列
        if 'domain' not in df.columns:
            print("错误: Excel文件中没有找到'domain'列")
            return
        
        # 显示域名统计
        print("\n域名统计 (原始数据):")
        domain_counts = df['domain'].value_counts()
        print(f"总共有 {len(domain_counts)} 个不同的域名")
        
        # 统计各种情况的域名数量
        single_count_domains = domain_counts[domain_counts == 1]
        multi_count_domains = domain_counts[domain_counts > 1]
        
        print(f"只有1行数据的域名: {len(single_count_domains)} 个")
        print(f"有多行数据的域名: {len(multi_count_domains)} 个")
        
        # 显示有多行数据的域名（前10个）
        if len(multi_count_domains) > 0:
            print(f"\n有多行数据的域名 (前10个，将被排除):")
            for domain, count in multi_count_domains.head(10).items():
                print(f"  {domain}: {count} 行")
        
        # 只保留domain计数为1的行
        single_occurrence_domains = single_count_domains.index.tolist()
        filtered_df = df[df['domain'].isin(single_occurrence_domains)]
        
        print(f"\n筛选后剩余行数: {len(filtered_df)}")
        print(f"总共排除的行数: {len(df) - len(filtered_df)}")
        
        # 显示最终保留的域名统计
        if len(filtered_df) > 0:
            print(f"\n最终保留的域名统计 (前15个):")
            final_domain_counts = filtered_df['domain'].value_counts()
            for domain, count in final_domain_counts.head(15).items():
                print(f"  {domain}: {count} 行")
        
        # 保存到新的Excel文件
        print(f"\n正在保存到: {output_file}")
        filtered_df.to_excel(output_file, index=False)
        
        print(f"✓ 成功！筛选后的数据已保存到: {output_file}")
        print(f"✓ 最终保留了 {len(filtered_df)} 行数据，每个domain都只有1行")
        
    except FileNotFoundError:
        print(f"错误: 找不到输入文件 {input_file}")
    except Exception as e:
        print(f"错误: {e}")


def main():
    """主函数"""
    # 默认路径
    workspace_dir = Path(__file__).resolve().parent
    default_input = workspace_dir / "aitep_references_need_fulltext_with_domain.xlsx"
    default_output = workspace_dir / "aitep_references_filtered.xlsx"
    
    # 命令行参数
    input_file = sys.argv[1] if len(sys.argv) > 1 else str(default_input)
    output_file = sys.argv[2] if len(sys.argv) > 2 else str(default_output)
    
    print("=== Excel域名筛选工具 ===")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print("筛选规则: 只保留domain计数为1的行")
    
    # 执行过滤
    filter_domains(input_file, output_file)


if __name__ == "__main__":
    main()
