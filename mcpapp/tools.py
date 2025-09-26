"""
Tools for the MCP server - compatible with LangGraph workflows.
These tools provide weather information and mathematical calculations.
"""

import re
import time
import logging
from typing import Dict, Any
from functools import lru_cache

# 配置日志
logger = logging.getLogger(__name__)

@lru_cache(maxsize=256)
def weather(location: str) -> str:
    """
    Get the weather for a specific location with caching.
    
    Args:
        location (str): The location to get weather for
        
    Returns:
        str: Weather information for the location
    """
    start_time = time.time()
    
    # Clean and validate location input
    location = location.strip()
    if not location:
        location = "北京"  # Default to Beijing if no location provided
    
    # 输入验证
    if len(location) > 50:
        return "错误：地点名称过长"
    
    # 过滤特殊字符
    location = re.sub(r'[^\w\s\u4e00-\u9fff]', '', location)
    
    # Simulate weather data (in a real implementation, this would call a weather API)
    weather_data = {
        "北京": "北京今天天气晴朗，温度25°C，微风，适合外出活动。",
        "上海": "上海今天多云，温度22°C，湿度较高，建议携带雨具。",
        "广州": "广州今天阴天，温度28°C，有轻微降雨可能。",
        "深圳": "深圳今天晴转多云，温度26°C，空气质量良好。",
        "杭州": "杭州今天小雨，温度20°C，出行请注意安全。",
        "beijing": "Beijing is sunny today, 25°C with light breeze, perfect for outdoor activities.",
        "shanghai": "Shanghai is cloudy today, 22°C with high humidity, recommend bringing an umbrella.",
        "guangzhou": "Guangzhou is overcast today, 28°C with possible light rain.",
        "shenzhen": "Shenzhen is sunny turning cloudy, 26°C with good air quality.",
        "hangzhou": "Hangzhou has light rain today, 20°C, please be careful when traveling."
    }
    
    # Try to find weather data for the location (case-insensitive)
    location_lower = location.lower()
    result = None
    for key, value in weather_data.items():
        if key.lower() == location_lower or location_lower in key.lower():
            result = value
            break
    
    # If location not found in predefined data, return a generic response
    if not result:
        result = f"{location}今天天气晴朗，温度适中，是个不错的天气。"
    
    response_time = time.time() - start_time
    logger.info(f"天气查询完成: {location} (耗时: {response_time:.3f}s)")
    
    return result

def calculator(expression: str) -> str:
    """
    Calculate a mathematical expression safely with enhanced validation.
    
    Args:
        expression (str): Mathematical expression to evaluate
        
    Returns:
        str: Result of the calculation or error message
    """
    start_time = time.time()
    
    try:
        # Clean the expression
        expression = expression.strip()
        if not expression:
            return "请提供一个数学表达式"
        
        # 输入长度限制
        if len(expression) > 100:
            return "错误：表达式过长"
        
        # Remove any non-mathematical characters for safety
        # Allow digits, operators, parentheses, and decimal points
        safe_expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        if not safe_expression:
            return "无效的数学表达式"
        
        # 检查括号匹配
        if safe_expression.count('(') != safe_expression.count(')'):
            return "错误：括号不匹配"
        
        # Replace common Chinese mathematical terms
        replacements = {
            '加': '+',
            '减': '-',
            '乘': '*',
            '除': '/',
            '乘以': '*',
            '除以': '/',
            '等于': '=',
            '×': '*',
            '÷': '/',
            '＋': '+',
            '－': '-',
            '＊': '*',
            '／': '/'
        }
        
        for chinese, symbol in replacements.items():
            safe_expression = safe_expression.replace(chinese, symbol)
        
        # Remove any trailing '=' if present
        safe_expression = safe_expression.rstrip('=')
        
        # 防止恶意代码注入
        if any(keyword in safe_expression.lower() for keyword in ['import', 'exec', 'eval', '__']):
            return "错误：不安全的表达式"
        
        # Evaluate the expression safely
        result = eval(safe_expression)
        
        # 检查结果是否为数字
        if not isinstance(result, (int, float, complex)):
            return "错误：计算结果不是数字"
        
        # Format the result nicely
        if isinstance(result, float):
            if result.is_integer():
                formatted_result = str(int(result))
            else:
                formatted_result = f"{result:.6g}"  # Use general format to avoid too many decimals
        else:
            formatted_result = str(result)
        
        response_time = time.time() - start_time
        logger.info(f"计算完成: {expression} = {formatted_result} (耗时: {response_time:.3f}s)")
        
        return formatted_result
            
    except ZeroDivisionError:
        return "错误：除数不能为零"
    except SyntaxError:
        return f"错误：无效的数学表达式 '{expression}'"
    except OverflowError:
        return "错误：计算结果过大"
    except Exception as e:
        logger.error(f"计算错误: {e}")
        return f"计算错误：{str(e)}"

def get_available_tools() -> Dict[str, Any]:
    """
    Get information about available tools.
    
    Returns:
        Dict[str, Any]: Dictionary containing tool information
    """
    return {
        "weather": {
            "name": "weather",
            "description": "获取指定地点的天气信息",
            "parameters": {
                "location": {
                    "type": "string",
                    "description": "要查询天气的地点名称"
                }
            },
            "example": "weather('北京')"
        },
        "calculator": {
            "name": "calculator",
            "description": "计算数学表达式",
            "parameters": {
                "expression": {
                    "type": "string",
                    "description": "要计算的数学表达式"
                }
            },
            "example": "calculator('2 + 2')"
        }
    }

# Tool registry for easy access
TOOLS = {
    "weather": weather,
    "calculator": calculator
}

def call_tool(tool_name: str, **kwargs) -> str:
    """
    Call a tool by name with given parameters.
    
    Args:
        tool_name (str): Name of the tool to call
        **kwargs: Parameters to pass to the tool
        
    Returns:
        str: Result from the tool or error message
    """
    if tool_name not in TOOLS:
        return f"错误：未知的工具 '{tool_name}'"
    
    try:
        tool_func = TOOLS[tool_name]
        return tool_func(**kwargs)
    except Exception as e:
        return f"调用工具 '{tool_name}' 时出错：{str(e)}"