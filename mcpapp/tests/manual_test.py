#!/usr/bin/env python3
"""
MCP项目手动测试脚本
用于详细验证各个工具的功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client import process_user_input

async def test_weather_functionality():
    """详细测试天气功能"""
    print("🌤️  天气查询功能测试")
    print("=" * 50)
    
    weather_queries = [
        "北京天气",
        "上海的天气怎么样",
        "广州天气预报",
        "深圳今天天气如何",
        "杭州weather",
        "天津的天气情况"
    ]
    
    for query in weather_queries:
        print(f"\n🔍 查询: {query}")
        try:
            response = await process_user_input(query)
            print(f"✅ 响应: {response}")
            
            # 验证响应内容
            if "温度" in response or "°C" in response or "天气" in response:
                print("✅ 包含天气信息")
            else:
                print("⚠️  响应可能不包含预期的天气信息")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        print("-" * 30)

async def test_calculator_functionality():
    """详细测试计算器功能"""
    print("\n🧮 计算器功能测试")
    print("=" * 50)
    
    calc_queries = [
        ("1+1", "2"),
        ("10*5", "50"),
        ("100/4", "25"),
        ("2^3", "8"),
        ("sqrt(16)", "4"),
        ("sin(0)", "0"),
        ("cos(0)", "1"),
        ("(2+3)*4", "20"),
        ("15 + 25", "40"),
        ("计算 100 - 30", "70")
    ]
    
    for query, expected in calc_queries:
        print(f"\n🔍 计算: {query} (期望: {expected})")
        try:
            response = await process_user_input(query)
            print(f"✅ 响应: {response}")
            
            # 验证计算结果
            if expected in response or str(float(expected)) in response:
                print("✅ 计算结果正确")
            else:
                print(f"⚠️  计算结果可能不正确，期望包含: {expected}")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        print("-" * 30)

async def test_general_conversation():
    """测试一般对话功能"""
    print("\n💬 一般对话功能测试")
    print("=" * 50)
    
    general_queries = [
        "你好",
        "你是谁",
        "你能做什么",
        "帮我介绍一下你的功能",
        "今天心情不错",
        "谢谢你的帮助"
    ]
    
    for query in general_queries:
        print(f"\n🔍 对话: {query}")
        try:
            response = await process_user_input(query)
            print(f"✅ 响应: {response}")
            
            # 验证响应合理性
            if len(response) > 5 and "错误" not in response:
                print("✅ 响应合理")
            else:
                print("⚠️  响应可能不够合理")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        print("-" * 30)

async def test_error_scenarios():
    """测试错误场景处理"""
    print("\n🚨 错误处理测试")
    print("=" * 50)
    
    error_scenarios = [
        ("1/0", "除零错误"),
        ("invalid_function()", "无效函数"),
        ("", "空输入"),
        ("计算 abc + def", "无效表达式"),
        ("北京天气" * 50, "超长输入"),
        ("@#$%^&*()", "特殊字符")
    ]
    
    for query, scenario in error_scenarios:
        print(f"\n🔍 错误场景: {scenario}")
        print(f"输入: {query[:50]}{'...' if len(query) > 50 else ''}")
        try:
            response = await process_user_input(query)
            print(f"✅ 响应: {response}")
            
            # 验证错误处理
            if "错误" in response or "抱歉" in response or "无法" in response or len(response) > 10:
                print("✅ 错误处理合理")
            else:
                print("⚠️  错误处理可能不够友好")
                
        except Exception as e:
            print(f"✅ 异常处理: {e}")
        
        print("-" * 30)

async def test_performance_scenarios():
    """测试性能场景"""
    print("\n⚡ 性能测试")
    print("=" * 50)
    
    import time
    
    # 单个请求响应时间测试
    print("\n📊 单个请求响应时间测试:")
    test_queries = ["北京天气", "1+1", "你好"]
    
    for query in test_queries:
        start_time = time.time()
        try:
            response = await process_user_input(query)
            duration = time.time() - start_time
            print(f"✅ {query}: {duration:.2f}s")
            
            if duration < 5.0:
                print("✅ 响应时间良好")
            elif duration < 10.0:
                print("⚠️  响应时间一般")
            else:
                print("❌ 响应时间较慢")
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {query}: {duration:.2f}s (错误: {e})")
        
        print("-" * 20)
    
    # 连续请求测试
    print("\n📊 连续请求测试:")
    start_time = time.time()
    success_count = 0
    total_requests = 5
    
    for i in range(total_requests):
        try:
            response = await process_user_input(f"测试请求 {i+1}")
            success_count += 1
            print(f"✅ 请求 {i+1}: 成功")
        except Exception as e:
            print(f"❌ 请求 {i+1}: 失败 ({e})")
    
    total_duration = time.time() - start_time
    success_rate = success_count / total_requests * 100
    avg_time = total_duration / total_requests
    
    print(f"\n📈 连续请求结果:")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均响应时间: {avg_time:.2f}s")
    print(f"总耗时: {total_duration:.2f}s")

async def main():
    """主测试函数"""
    print("🧪 MCP项目手动功能测试")
    print("=" * 60)
    
    try:
        # 等待服务器准备
        print("⏳ 等待服务器准备...")
        await asyncio.sleep(2)
        
        # 执行各项测试
        await test_weather_functionality()
        await test_calculator_functionality()
        await test_general_conversation()
        await test_error_scenarios()
        await test_performance_scenarios()
        
        print("\n🎉 所有测试完成!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())