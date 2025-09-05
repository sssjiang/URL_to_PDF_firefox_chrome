#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取7 toxicological information部分中text内容为"S-01 | Summary"的链接
"""

from bs4 import BeautifulSoup
import os

def extract_s01_summary_links(html_file_path):
    """
    从HTML文件中提取toxicological information部分的S-01 | Summary链接
    
    Args:
        html_file_path (str): HTML文件路径
        
    Returns:
        list: 包含所有符合条件的href值的数组
    """
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 {html_file_path}")
        return []
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return []
    
    # 解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 找到id="id_7_Toxicologicalinformation"的div
    toxicological_div = soup.find('div', id='id_7_Toxicologicalinformation')
    
    if not toxicological_div:
        print("错误：未找到id='id_7_Toxicologicalinformation'的div元素")
        return []
    
    print(f"成功找到toxicological information部分")
    
    # 在这个div内查找所有包含"S-01 | Summary"的span元素
    # 使用lambda函数处理可能包含换行符和制表符的文本
    s01_spans = toxicological_div.find_all('span', string=lambda text: text and 'S-01 | Summary' in text.strip())
    
    print(f"找到 {len(s01_spans)} 个包含'S-01 | Summary'的span元素")
    
    href_list = []
    
    for i, span in enumerate(s01_spans, 1):
        print(f"\n处理第 {i} 个span元素...")
        
        # 从span元素开始，向上查找第一个父类标签为a的元素
        current_element = span
        found_a_tag = None
        
        while current_element.parent:
            current_element = current_element.parent
            if current_element.name == 'a' and current_element.get('href'):
                found_a_tag = current_element
                break
        
        if found_a_tag:
            href_value = found_a_tag.get('href')
            href_list.append(href_value)
            print(f"  - 找到href: {href_value}")
        else:
            print(f"  - 未找到包含href的父级a标签")
    
    return href_list

def save_links_to_file(links, output_file='toxicological_s01_links.txt'):
    """将链接保存到文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Toxicological Information - S-01 Summary Links\n")
            f.write(f"# 提取时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总数: {len(links)}\n\n")
            
            for i, link in enumerate(links, 1):
                f.write(f"{i}. {link}\n")
        
        print(f"\n链接已保存到文件: {output_file}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False

def main():
    """主函数"""
    # HTML文件路径
    html_file_path = os.path.join(os.path.dirname(__file__), 'dosser_detail.html')
    
    print("开始提取toxicological information部分的S-01 | Summary链接...")
    print(f"HTML文件路径: {html_file_path}")
    print("=" * 60)
    
    # 提取链接
    href_links = extract_s01_summary_links(html_file_path)
    
    print("\n" + "=" * 60)
    print("提取结果:")
    print(f"总共找到 {len(href_links)} 个符合条件的链接:")
    
    for i, href in enumerate(href_links, 1):
        print(f"{i}. {href}")
    
    # 保存到文件
    if href_links:
        save_links_to_file(href_links)
    
    # 返回结果数组
    return href_links

if __name__ == "__main__":
    result_links = main()
    
    # 可以将结果保存到文件或进行其他处理
    if result_links:
        print(f"\n提取完成！共获得 {len(result_links)} 个链接。")
    else:
        print("\n未找到任何符合条件的链接。")
