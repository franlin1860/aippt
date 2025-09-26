#!/usr/bin/env python3
"""
MCP客户端自动化测试脚本
用于验证代码优化后的功能完整性
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client import process_user_input

class MCPTester:
    def __init__(self):
        self.test_results = []
        self.start_time = None
        
    def log_test(self, test_name: str, success: bool, response: str = "", duration: float = 0):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "response": response[:200] + "..." if len(response) > 200 else response,
            "duration": duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if not success:
            print(f"   Error: {response}")
        elif response:
            print(f"   Response: {response}")
        print()

    async def test_weather_queries(self):
        """测试天气查询功能"""
        weather_tests = [
            ("北京天气", "北京"),
            ("上海的天气怎么样", "上海"),
            ("广州天气预报", "广州"),
            ("深圳今天天气", "深圳"),
            ("杭州weather", "杭州")
        ]
        
        for query, expected_city in weather_tests:
            start_time = time.time()
            try:
                response = await process_user_input(query)
                duration = time.time() - start_time
                
                # 检查响应是否包含预期城市和天气信息
                success = (expected_city in response and 
                          ("温度" in response or "天气" in response or "°C" in response))
                
                self.log_test(f"天气查询: {query}", success, response, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"天气查询: {query}", False, str(e), duration)

    async def test_calculator_queries(self):
        """测试计算器功能"""
        calc_tests = [
            ("1+1", "2"),
            ("10*5", "50"),
            ("100/4", "25"),
            ("2的3次方", "8"),
            ("计算 15 + 25", "40"),
            ("sqrt(16)", "4"),
            ("sin(0)", "0"),
            ("(2+3)*4", "20")
        ]
        
        for query, expected in calc_tests:
            start_time = time.time()
            try:
                response = await process_user_input(query)
                duration = time.time() - start_time
                
                # 检查响应是否包含预期结果
                success = expected in response or str(float(expected)) in response
                
                self.log_test(f"计算器: {query}", success, response, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"计算器: {query}", False, str(e), duration)

    async def test_general_queries(self):
        """测试一般对话功能"""
        general_tests = [
            "你好",
            "你是谁",
            "你能做什么",
            "帮我介绍一下你的功能",
            "今天心情不错"
        ]
        
        for query in general_tests:
            start_time = time.time()
            try:
                response = await process_user_input(query)
                duration = time.time() - start_time
                
                # 检查是否有合理的响应
                success = len(response) > 10 and "错误" not in response
                
                self.log_test(f"一般对话: {query}", success, response, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(f"一般对话: {query}", False, str(e), duration)

    async def test_error_handling(self):
        """测试错误处理"""
        error_tests = [
            "1/0",  # 除零错误
            "invalid_function()",  # 无效函数
            "北京天气" * 100,  # 超长输入
            "",  # 空输入
            "计算 abc + def"  # 无效计算
        ]
        
        for query in error_tests:
            start_time = time.time()
            try:
                response = await process_user_input(query)
                duration = time.time() - start_time
                
                # 错误处理测试：应该有友好的错误信息，不应该崩溃
                success = "错误" in response or "无法" in response or "抱歉" in response
                
                self.log_test(f"错误处理: {query[:20]}...", success, response, duration)
                
            except Exception as e:
                duration = time.time() - start_time
                # 对于错误处理测试，异常也算是一种处理方式
                self.log_test(f"错误处理: {query[:20]}...", True, f"异常处理: {str(e)}", duration)

    async def test_performance(self):
        """测试性能"""
        print("🚀 性能测试开始...")
        
        # 并发测试
        concurrent_queries = ["北京天气", "1+1", "你好"] * 3
        
        start_time = time.time()
        tasks = [process_user_input(query) for query in concurrent_queries]
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            success_count = sum(1 for r in responses if not isinstance(r, Exception))
            success_rate = success_count / len(responses) * 100
            
            avg_response_time = duration / len(responses)
            
            success = success_rate >= 80 and avg_response_time < 2.0
            
            self.log_test(
                f"并发性能测试 ({len(concurrent_queries)}个请求)", 
                success, 
                f"成功率: {success_rate:.1f}%, 平均响应时间: {avg_response_time:.2f}s", 
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("并发性能测试", False, str(e), duration)

    def print_summary(self):
        """打印测试总结"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        avg_duration = sum(result["duration"] for result in self.test_results) / total_tests if total_tests > 0 else 0
        
        print("=" * 60)
        print("📊 测试总结报告")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests} ✅")
        print(f"失败测试: {failed_tests} ❌")
        print(f"成功率: {success_rate:.1f}%")
        print(f"平均响应时间: {avg_duration:.2f}s")
        print()
        
        if failed_tests > 0:
            print("❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['response']}")
            print()
        
        # 性能评估
        if success_rate >= 90:
            print("🎉 测试结果: 优秀")
        elif success_rate >= 80:
            print("👍 测试结果: 良好")
        elif success_rate >= 70:
            print("⚠️  测试结果: 一般")
        else:
            print("🚨 测试结果: 需要改进")
        
        print("=" * 60)

async def main():
    """主测试函数"""
    print("🧪 MCP项目回归测试开始")
    print("=" * 60)
    
    tester = MCPTester()
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    await asyncio.sleep(2)
    
    try:
        # 执行各项测试
        await tester.test_weather_queries()
        await tester.test_calculator_queries()
        await tester.test_general_queries()
        await tester.test_error_handling()
        await tester.test_performance()
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
    
    finally:
        # 打印测试总结
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())