#!/usr/bin/env python3
"""
doc2md-cli: Word/PDF转Markdown命令行工具
基于TorchV Unstructured Java库，通过JPype实现Python调用
"""

import argparse
import os
import re
import sys
from pathlib import Path

# 检查Python版本
if sys.version_info < (3, 8):
    print("错误: 需要Python 3.8或更高版本")
    sys.exit(1)

try:
    import jpype
    import jpype.imports
except ImportError as e:
    print(f"错误: 请先安装 JPype1")
    print(f"安装命令: pip install jpype1")
    sys.exit(1)

class TorchVParser:
    """TorchV Unstructured集成包装器"""
    
    def __init__(self):
        """初始化JPype和TorchV"""
        self._init_jvm()
        self._load_torchv_classes()
    
    def _init_jvm(self):
        """初始化JVM"""
        if not jpype.isJVMStarted():
            try:
                # 获取Java路径
                java_home = os.environ.get('JAVA_HOME')
                if not java_home:
                    import subprocess
                    java_home = subprocess.check_output(['/usr/libexec/java_home']).decode().strip()
                
                jvm_path = os.path.join(java_home, "lib", "server", "libjvm.dylib")
                
                # 设置JVM参数
                jvm_args = [
                    "-Dfile.encoding=UTF-8",
                    "-Xmx1g",
                    "-Djava.awt.headless=true"
                ]
                
                # 设置classpath
                lib_dir = Path(__file__).parent / "lib"
                if not lib_dir.exists():
                    lib_dir.mkdir(exist_ok=True)
                
                jar_files = list(lib_dir.glob("*.jar"))
                if not jar_files:
                    raise RuntimeError("未找到JAR文件，请确保lib目录中包含所需的JAR文件")
                
                classpath = [str(jar) for jar in jar_files]
                
                print("正在启动JVM...")
                jpype.startJVM(jvm_path, *jvm_args, classpath=classpath, ignoreUnrecognized=True, convertStrings=True)
                print("JVM启动成功！")
                
            except Exception as e:
                raise RuntimeError(f"JVM启动失败: {e}")
    
    def _load_torchv_classes(self):
        """加载TorchV类"""
        try:
            from com.torchv.infra.unstructured import UnstructuredParser
            self.UnstructuredParser = UnstructuredParser
        except Exception as e:
            raise RuntimeError(f"加载TorchV类失败: {e}")
    
    def parse_to_markdown(self, file_path):
        """解析文档为Markdown"""
        try:
            return str(self.UnstructuredParser.toMarkdown(file_path))
        except Exception as e:
            raise RuntimeError(f"解析失败: {e}")
    
    def parse_with_tables(self, file_path):
        """解析文档为带HTML表格的Markdown"""
        try:
            return str(self.UnstructuredParser.toMarkdownWithHtmlTables(file_path))
        except Exception as e:
            raise RuntimeError(f"解析失败: {e}")
    
    def get_supported_formats(self):
        """获取支持的文件格式"""
        try:
            from com.torchv.infra.unstructured.util import UnstructuredUtils
            formats = UnstructuredUtils.getSupportedFormats()
            return [str(fmt) for fmt in formats]
        except Exception:
            return ["doc", "docx", "pdf"]  # 默认格式
            
    def extract_toc(self, file_path, max_level=3):
        """提取文档的目录结构
        
        Args:
            file_path: 文档路径
            max_level: 提取的最大标题级别
            
        Returns:
            目录结构的Markdown文本
        """
        try:
            # 尝试不同的编码方式读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                print(f"无法读取文件: {file_path}")
                return None
            
            # 提取所有标题行
            headings = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 匹配Markdown标题格式
                if line.startswith('# '):
                    headings.append((1, line[2:]))
                elif line.startswith('## '):
                    headings.append((2, line[3:]))
                elif line.startswith('### '):
                    headings.append((3, line[4:]))
                elif line.startswith('#### '):
                    headings.append((4, line[5:]))
                elif line.startswith('##### '):
                    headings.append((5, line[6:]))
                elif line.startswith('###### '):
                    headings.append((6, line[7:]))
                # 直接识别数字编号标题格式
                elif re.match(r'^\d+、\s', line):
                    headings.append((2, line))
                elif re.match(r'^\(\d+\)\s', line):
                    headings.append((3, line))
                elif re.match(r'^\d+\.\s', line):
                    headings.append((2, line))
            
            # 如果没有找到任何标题，尝试识别中文数字标题
            if not headings:
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 识别数字编号标题 (如 "1、 前期准备工作")
                    if re.match(r'^\d+、\s+', line):
                        headings.append((2, line))
                    # 识别带括号的数字标题 (如 "(1) 开展AI大模型技术学习研究")
                    elif re.match(r'^\(\d+\)\s+', line):
                        headings.append((3, line))
                    # 识别中文数字标题 (如 "一、")
                    elif re.match(r'^[一二三四五六七八九十]+、\s+', line):
                        headings.append((2, line))
                    # 识别带中文括号的标题 (如 "(一)")
                    elif re.match(r'^（[一二三四五六七八九十]+）\s+', line):
                        headings.append((3, line))
            
            # 过滤掉重复的标题，保持顺序
            seen = set()
            unique_headings = []
            for level, title in headings:
                if title not in seen:
                    seen.add(title)
                    unique_headings.append((level, title))
            
            # 构建目录
            if not unique_headings:
                return None
                
            toc_lines = ["# 目录\n"]
            for level, title in unique_headings:
                if level <= max_level:
                    indent = '  ' * (level - 1)
                    # 生成简单的锚点链接
                    anchor = re.sub(r'[^\w\u4e00-\u9fff\-]', '', title.lower().replace(' ', '-'))
                    toc_lines.append(f"{indent}- [{title}](#{anchor})")
            
            return '\n'.join(toc_lines)
            
        except Exception as e:
            print(f"提取目录时出错: {e}")
            return None
            print(f"提取目录失败: {str(e)}")
            print(traceback.format_exc())
            return "# 目录\n\n提取目录失败，请检查文档格式。"

class Doc2MdConverter:
    """Word/PDF转Markdown转换器"""
    
    def __init__(self):
        self.parser = TorchVParser()
    
    def convert(self, input_file: str, output_file: str, with_tables=True, generate_toc=False) -> bool:
        """转换文档为Markdown
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            with_tables: 是否使用HTML表格
            generate_toc: 是否生成目录文件
            
        Returns:
            转换是否成功
        """
        try:
            # 验证输入文件
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"文件不存在: {input_file}")
            
            # 验证文件格式
            supported_formats = self.parser.get_supported_formats()
            file_ext = Path(input_file).suffix.lower().lstrip('.')
            if file_ext not in supported_formats:
                raise ValueError(f"不支持的格式: {file_ext}，支持: {supported_formats}")
            
            # 执行转换
            print(f"正在处理: {input_file}")
            if with_tables:
                markdown_content = self.parser.parse_with_tables(input_file)
            else:
                markdown_content = self.parser.parse_to_markdown(input_file)
            
            # 写入输出文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"转换完成: {output_file}")
            
            # 如果需要生成目录文件
            if generate_toc:
                self.generate_toc_file(input_file, output_file)
                
            return True
            
        except Exception as e:
            print(f"转换失败: {str(e)}")
            return False
    
    def generate_toc_file(self, input_file: str, output_file: str) -> bool:
        """生成文档目录文件
        
        Args:
            input_file: 输入文件路径
            output_file: 原始输出文件路径（用于确定目录文件路径）
            
        Returns:
            生成是否成功
        """
        try:
            # 提取目录 - 从已经转换的Markdown文件中提取
            toc_content = self.parser.extract_toc(output_file)
            
            # 生成目录文件路径
            output_path = Path(output_file)
            toc_file = output_path.parent / f"{output_path.stem}-目录.md"
            
            # 写入目录文件
            with open(toc_file, 'w', encoding='utf-8') as f:
                f.write(toc_content)
                
            print(f"目录文件生成完成: {toc_file}")
            return True
            
        except Exception as e:
            print(f"生成目录文件失败: {str(e)}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Word/PDF转Markdown工具')
    parser.add_argument('input_file', help='输入的Word/PDF文件路径')
    parser.add_argument('-o', '--output', help='输出文件名 (默认: 输入文件名.md)')
    parser.add_argument('-d', '--directory', help='输出目录 (默认: 当前目录)')
    parser.add_argument('--no-tables', action='store_true', 
                       help='不使用HTML表格格式（纯Markdown）')
    parser.add_argument('--toc', action='store_true',
                       help='生成目录文件（提取一级和二级标题）')
    
    args = parser.parse_args()
    
    # 处理输入路径
    input_path = Path(args.input_file)
    
    # 处理输出路径
    if args.output:
        output_filename = args.output
    else:
        output_filename = input_path.stem + '.md'
    
    if args.directory:
        output_path = Path(args.directory) / output_filename
    else:
        output_path = input_path.parent / output_filename
    
    # 创建输出目录
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 执行转换
    try:
        converter = Doc2MdConverter()
        success = converter.convert(
            str(input_path), 
            str(output_path), 
            with_tables=not args.no_tables,
            generate_toc=args.toc
        )
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()