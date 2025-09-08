import math
from typing import Any
from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器
mcp = FastMCP("calculator")

@mcp.tool()
def add(a: float, b: float) -> float:
    """两个数相加
    
    Args:
        a: 第一个数
        b: 第二个数
    
    Returns:
        两数之和
    """
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """两个数相减
    
    Args:
        a: 被减数
        b: 减数
    
    Returns:
        两数之差
    """
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """两个数相乘
    
    Args:
        a: 第一个数
        b: 第二个数
    
    Returns:
        两数之积
    """
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """两个数相除
    
    Args:
        a: 被除数
        b: 除数
    
    Returns:
        两数之商
    """
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """计算幂
    
    Args:
        base: 底数
        exponent: 指数
    
    Returns:
        base的exponent次幂
    """
    return math.pow(base, exponent)

@mcp.tool()
def square_root(number: float) -> float:
    """计算平方根
    
    Args:
        number: 要计算平方根的数
    
    Returns:
        平方根
    """
    if number < 0:
        raise ValueError("不能计算负数的平方根")
    return math.sqrt(number)

@mcp.tool()
def factorial(n: int) -> int:
    """计算阶乘
    
    Args:
        n: 要计算阶乘的整数
    
    Returns:
        n的阶乘
    """
    if n < 0:
        raise ValueError("不能计算负数的阶乘")
    return math.factorial(n)

@mcp.tool()
def sin(angle: float) -> float:
    """计算正弦值（角度制）
    
    Args:
        angle: 角度（度）
    
    Returns:
        正弦值
    """
    return math.sin(math.radians(angle))

@mcp.tool()
def cos(angle: float) -> float:
    """计算余弦值（角度制）
    
    Args:
        angle: 角度（度）
    
    Returns:
        余弦值
    """
    return math.cos(math.radians(angle))

@mcp.tool()
def tan(angle: float) -> float:
    """计算正切值（角度制）
    
    Args:
        angle: 角度（度）
    
    Returns:
        正切值
    """
    return math.tan(math.radians(angle))

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio')
