import requests
import os

cookies = {
    'legalNotice': '%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D',
    'cck1': '%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D',
    '_pk_ses.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839': '*',
    '_pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839': 'afbddb297a39ebfa.1756802275.1.1756976634.1756971630.',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en,zh;q=0.9,zh-CN;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'iframe',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    # 'Cookie': 'legalNotice=%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D; cck1=%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D; _pk_ses.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839=*; _pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839=afbddb297a39ebfa.1756802275.1.1756976634.1756971630.',
}

def get_dosser_detail_html(asset_external_id, save_to_file=True, output_filename=None, verbose=False):
    """
    获取dosser详情页面的HTML内容
    
    Args:
        asset_external_id (str): 资产外部ID（如：'2c770589-dbbf-4dfc-a0f3-d9162b85bb4d'）
        save_to_file (bool): 是否保存为文件，默认为 True
        output_filename (str): 输出文件名，默认为 'dosser_detail_{asset_external_id}.html'
        verbose (bool): 是否打印详细信息，默认为 False
    
    Returns:
        dict: 包含以下字段的字典
            - html_content (str): HTML页面内容
            - status_code (int): HTTP响应状态码
            - url (str): 请求的URL
            - saved_file (str): 保存的文件路径（如果save_to_file为True）
            - success (bool): 请求是否成功
    """
    # 构造URL
    url = f'https://chem.echa.europa.eu/html-pages/{asset_external_id}/index.html'
    
    result = {
        'html_content': None,
        'status_code': None,
        'url': url,
        'saved_file': None,
        'success': False
    }
    
    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        result['status_code'] = response.status_code
        result['html_content'] = response.text
        
        if response.status_code == 200:
            result['success'] = True
            
            if save_to_file:
                if output_filename is None:
                    output_filename = f'dosser_detail_{asset_external_id}.html'
                
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                result['saved_file'] = os.path.abspath(output_filename)
                
                if verbose:
                    print(f"成功获取dosser详情页面")
                    print(f"Asset External ID: {asset_external_id}")
                    print(f"URL: {url}")
                    print(f"状态码: {response.status_code}")
                    print(f"HTML内容长度: {len(response.text)} 字符")
                    print(f"保存文件: {result['saved_file']}")
            else:
                if verbose:
                    print(f"成功获取dosser详情页面")
                    print(f"Asset External ID: {asset_external_id}")
                    print(f"URL: {url}")
                    print(f"状态码: {response.status_code}")
                    print(f"HTML内容长度: {len(response.text)} 字符")
        else:
            if verbose:
                print(f"请求失败")
                print(f"Asset External ID: {asset_external_id}")
                print(f"URL: {url}")
                print(f"状态码: {response.status_code}")
                
    except Exception as e:
        if verbose:
            print(f"请求过程中发生错误: {str(e)}")
            print(f"Asset External ID: {asset_external_id}")
            print(f"URL: {url}")
    
    return result


# 如果直接运行此脚本，则执行测试
if __name__ == "__main__":
    result = get_dosser_detail_html('2c770589-dbbf-4dfc-a0f3-d9162b85bb4d', verbose=True)
    print(f"\n函数返回结果:")
    print(f"请求成功: {result['success']}")
    print(f"状态码: {result['status_code']}")
    print(f"保存文件: {result['saved_file']}")
    if result['html_content']:
        print(f"HTML内容前100字符: {result['html_content'][:100]}...")