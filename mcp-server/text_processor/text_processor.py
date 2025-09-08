import re
from typing import List
from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器
mcp = FastMCP("text_processor")

@mcp.tool()
def count_words(text: str) -> int:
    """统计文本中的单词数量
    
    Args:
        text: 要统计的文本
    
    Returns:
        单词数量
    """
    words = text.split()
    return len(words)

@mcp.tool()
def count_characters(text: str, include_spaces: bool = True) -> int:
    """统计文本中的字符数量
    
    Args:
        text: 要统计的文本
        include_spaces: 是否包含空格
    
    Returns:
        字符数量
    """
    if include_spaces:
        return len(text)
    else:
        return len(text.replace(" ", ""))

@mcp.tool()
def to_uppercase(text: str) -> str:
    """将文本转换为大写
    
    Args:
        text: 要转换的文本
    
    Returns:
        大写文本
    """
    return text.upper()

@mcp.tool()
def to_lowercase(text: str) -> str:
    """将文本转换为小写
    
    Args:
        text: 要转换的文本
    
    Returns:
        小写文本
    """
    return text.lower()

@mcp.tool()
def reverse_text(text: str) -> str:
    """反转文本
    
    Args:
        text: 要反转的文本
    
    Returns:
        反转后的文本
    """
    return text[::-1]

@mcp.tool()
def remove_duplicates(text: str) -> str:
    """移除文本中的重复单词
    
    Args:
        text: 要处理的文本
    
    Returns:
        移除重复单词后的文本
    """
    words = text.split()
    unique_words = []
    seen = set()
    
    for word in words:
        if word.lower() not in seen:
            unique_words.append(word)
            seen.add(word.lower())
    
    return " ".join(unique_words)

@mcp.tool()
def extract_emails(text: str) -> List[str]:
    """从文本中提取邮箱地址
    
    Args:
        text: 要搜索的文本
    
    Returns:
        找到的邮箱地址列表
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails

@mcp.tool()
def extract_urls(text: str) -> List[str]:
    """从文本中提取URL
    
    Args:
        text: 要搜索的文本
    
    Returns:
        找到的URL列表
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls

@mcp.tool()
def replace_text(text: str, old: str, new: str) -> str:
    """替换文本中的指定内容
    
    Args:
        text: 原始文本
        old: 要替换的文本
        new: 新文本
    
    Returns:
        替换后的文本
    """
    return text.replace(old, new)

@mcp.tool()
def split_sentences(text: str) -> List[str]:
    """将文本分割为句子
    
    Args:
        text: 要分割的文本
    
    Returns:
        句子列表
    """
    # 简单的句子分割，基于句号、问号、感叹号
    sentences = re.split(r'[.!?]+', text)
    # 移除空字符串并去除首尾空格
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

@mcp.tool()
def word_frequency(text: str) -> dict:
    """统计文本中每个单词的出现频率
    
    Args:
        text: 要分析的文本
    
    Returns:
        单词频率字典
    """
    # 转换为小写并分割单词
    words = text.lower().split()
    
    # 移除标点符号
    cleaned_words = []
    for word in words:
        cleaned_word = re.sub(r'[^\w]', '', word)
        if cleaned_word:
            cleaned_words.append(cleaned_word)
    
    # 统计频率
    frequency = {}
    for word in cleaned_words:
        frequency[word] = frequency.get(word, 0) + 1
    
    # 按频率排序
    sorted_frequency = dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))
    return sorted_frequency

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio')
