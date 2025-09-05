import requests

cookies = {
    'legalNotice': '%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D',
    'cck1': '%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D',
    '_pk_ses.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839': '*',
    '_pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839': 'afbddb297a39ebfa.1756802275.1.1756975992.1756971630.',
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en,zh;q=0.9,zh-CN;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': 'https://chem.echa.europa.eu/substance-search?searchText=aspirin',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    # 'Cookie': 'legalNotice=%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D; cck1=%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D; _pk_ses.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839=*; _pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839=afbddb297a39ebfa.1756802275.1.1756975992.1756971630.',
}

def search_substance_rml_id(search_text, verbose=False):
    """
    根据搜索文本获取物质的rmlId
    
    Args:
        search_text (str): 搜索文本（如CAS号、物质名称等）
        verbose (bool): 是否打印详细信息，默认为 False
    
    Returns:
        dict: 包含以下字段的字典
            - rml_id (str): 第一个搜索结果的rmlId，如果没有找到则为None
            - substance_info (dict): 第一个搜索结果的完整物质信息，如果没有找到则为None
            - total_items (int): 搜索结果总数
            - raw_response (dict): 原始API响应数据
    """
    params = {
        'pageIndex': '1',
        'pageSize': '100',
        'searchText': search_text,
    }

    response = requests.get(
        'https://chem.echa.europa.eu/api-substance/v1/substance', 
        params=params, 
        cookies=cookies, 
        headers=headers
    )

    response_data = response.json()
    
    result = {
        'rml_id': None,
        'substance_info': None,
        'total_items': 0,
        'raw_response': response_data
    }

    if 'items' in response_data and response_data['items']:
        # 获取第一个搜索结果
        first_item = response_data['items'][0]
        if 'substanceIndex' in first_item and 'rmlId' in first_item['substanceIndex']:
            result['rml_id'] = first_item['substanceIndex']['rmlId']
            result['substance_info'] = first_item
        
        result['total_items'] = response_data.get('state', {}).get('totalItems', 0)
        
        if verbose:
            print(f"搜索文本: {search_text}")
            print(f"找到 {result['total_items']} 个结果")
            print(f"第一个结果的 rmlId: {result['rml_id']}")
            if result['substance_info'] and 'substanceIndex' in result['substance_info']:
                substance_index = result['substance_info']['substanceIndex']
                print(f"物质名称: {substance_index.get('rmlName', 'N/A')}")
                print(f"EC号: {substance_index.get('rmlEc', 'N/A')}")
                print(f"CAS号: {substance_index.get('rmlCas', 'N/A')}")
    else:
        if verbose:
            print(f"搜索文本: {search_text}")
            print("没有找到任何结果")

    if verbose:
        print(f"\n原始完整响应:")
        print(response_data)

    return result


# 如果直接运行此脚本，则执行测试
if __name__ == "__main__":
    result = search_substance_rml_id('25104-18-1', verbose=True)
    print(f"\n函数返回结果:")
    print(f"RML ID: {result['rml_id']}")
    print(f"总结果数: {result['total_items']}")
