from bs4 import BeautifulSoup
import os

def check_html(html_path):
    print("检查HTML文件信息:")
    try:
        # 检查文件是否存在
        if not os.path.exists(html_path):
            print(f"错误：文件 {html_path} 不存在")
            return
            
        # 读取HTML文件
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 打印基本信息
        print(f"文件大小: {os.path.getsize(html_path)} 字节")
        print(f"HTML标题: {soup.title.string if soup.title else '无标题'}")
        
        # 提取所有文本内容
        print("\n提取的文本内容:")
        text_content = soup.get_text(separator='\n', strip=True)
        print(f"文本长度: {len(text_content)}")
        print(f"文本内容预览:\n{text_content[:500]}")
        
        # 提取所有链接
        print("\n页面链接:")
        links = soup.find_all('a')
        print(f"链接数量: {len(links)}")
        for link in links[:5]:  # 只显示前5个链接
            print(f"- {link.get('href', '无链接')}: {link.text}")
            
        # 提取所有图片
        print("\n页面图片:")
        images = soup.find_all('img')
        print(f"图片数量: {len(images)}")
        for img in images[:5]:  # 只显示前5个图片
            print(f"- {img.get('src', '无源')}: {img.get('alt', '无描述')}")
            
    except Exception as e:
        print(f"处理HTML文件时出错: {str(e)}")

# 测试HTML读取
html_path = "/Users/cuisijia/Downloads/Hirain_PDF/vba/sendPeriodMsg.html"  # 请替换为实际的HTML文件路径
check_html(html_path) 