"""文件解析服务（用于 ForgGPT）"""
import os
import json
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger


class FileParseService:
    """文件解析服务类"""
    
    @staticmethod
    def parse_file(file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        解析文件（Excel/CSV/JSON）
        
        Args:
            file_path: 文件路径
            file_type: 文件类型（自动识别，可手动指定）
            
        Returns:
            解析结果字典
        """
        try:
            # 如果没有指定文件类型，根据扩展名自动识别
            if not file_type:
                file_ext = Path(file_path).suffix.lower()
                if file_ext in ['.xlsx', '.xls']:
                    file_type = 'excel'
                elif file_ext == '.csv':
                    file_type = 'csv'
                elif file_ext == '.json':
                    file_type = 'json'
                else:
                    raise ValueError(f"不支持的文件类型: {file_ext}")
            
            # 根据文件类型解析
            if file_type == 'excel':
                return FileParseService._parse_excel(file_path)
            elif file_type == 'csv':
                return FileParseService._parse_csv(file_path)
            elif file_type == 'json':
                return FileParseService._parse_json(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
                
        except Exception as e:
            logger.error(f"解析文件失败: {e}")
            raise
    
    @staticmethod
    def _parse_excel(file_path: str) -> Dict[str, Any]:
        """
        解析Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            解析结果字典
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 获取基本信息
            rows_count = len(df)
            columns_count = len(df.columns)
            column_names = df.columns.tolist()
            
            # 获取数据类型
            data_types = {}
            for col in column_names:
                dtype = str(df[col].dtype)
                # 简化数据类型名称
                if 'int' in dtype:
                    data_types[col] = 'integer'
                elif 'float' in dtype:
                    data_types[col] = 'float'
                elif 'datetime' in dtype or 'date' in dtype:
                    data_types[col] = 'datetime'
                elif 'bool' in dtype:
                    data_types[col] = 'boolean'
                else:
                    data_types[col] = 'string'
            
            # 获取数据摘要（前5行）
            sample_data = df.head(5).to_dict(orient='records')
            
            # 获取统计信息（数值列的统计）
            statistics = {}
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_columns:
                for col in numeric_columns:
                    statistics[col] = {
                        'count': int(df[col].count()),
                        'mean': float(df[col].mean()) if df[col].count() > 0 else None,
                        'min': float(df[col].min()) if df[col].count() > 0 else None,
                        'max': float(df[col].max()) if df[col].count() > 0 else None,
                        'std': float(df[col].std()) if df[col].count() > 0 else None,
                    }
            
            # 检查空值
            null_counts = {}
            for col in column_names:
                null_count = int(df[col].isnull().sum())
                if null_count > 0:
                    null_counts[col] = null_count
            
            return {
                "success": True,
                "file_type": "excel",
                "rows": rows_count,
                "columns": columns_count,
                "column_names": column_names,
                "data_types": data_types,
                "sample_data": sample_data,
                "statistics": statistics,
                "null_counts": null_counts,
                "summary": f"Excel文件，{rows_count}行 × {columns_count}列"
            }
            
        except Exception as e:
            logger.error(f"解析Excel文件失败: {e}")
            raise
    
    @staticmethod
    def _parse_csv(file_path: str) -> Dict[str, Any]:
        """
        解析CSV文件
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            解析结果字典
        """
        try:
            # 读取CSV文件（尝试不同的编码）
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            df = None
            encoding_used = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("无法读取CSV文件，尝试了多种编码格式")
            
            # 获取基本信息
            rows_count = len(df)
            columns_count = len(df.columns)
            column_names = df.columns.tolist()
            
            # 获取数据类型
            data_types = {}
            for col in column_names:
                dtype = str(df[col].dtype)
                if 'int' in dtype:
                    data_types[col] = 'integer'
                elif 'float' in dtype:
                    data_types[col] = 'float'
                elif 'datetime' in dtype or 'date' in dtype:
                    data_types[col] = 'datetime'
                elif 'bool' in dtype:
                    data_types[col] = 'boolean'
                else:
                    data_types[col] = 'string'
            
            # 获取数据摘要（前5行）
            sample_data = df.head(5).to_dict(orient='records')
            
            # 获取统计信息
            statistics = {}
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_columns:
                for col in numeric_columns:
                    statistics[col] = {
                        'count': int(df[col].count()),
                        'mean': float(df[col].mean()) if df[col].count() > 0 else None,
                        'min': float(df[col].min()) if df[col].count() > 0 else None,
                        'max': float(df[col].max()) if df[col].count() > 0 else None,
                        'std': float(df[col].std()) if df[col].count() > 0 else None,
                    }
            
            # 检查空值
            null_counts = {}
            for col in column_names:
                null_count = int(df[col].isnull().sum())
                if null_count > 0:
                    null_counts[col] = null_count
            
            return {
                "success": True,
                "file_type": "csv",
                "encoding": encoding_used,
                "rows": rows_count,
                "columns": columns_count,
                "column_names": column_names,
                "data_types": data_types,
                "sample_data": sample_data,
                "statistics": statistics,
                "null_counts": null_counts,
                "summary": f"CSV文件，{rows_count}行 × {columns_count}列"
            }
            
        except Exception as e:
            logger.error(f"解析CSV文件失败: {e}")
            raise
    
    @staticmethod
    def _parse_json(file_path: str) -> Dict[str, Any]:
        """
        解析JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析结果字典
        """
        try:
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 判断JSON格式（数组或对象）
            if isinstance(data, list):
                # 如果是数组，转换为DataFrame分析
                if len(data) > 0:
                    df = pd.DataFrame(data)
                    rows_count = len(df)
                    columns_count = len(df.columns)
                    column_names = df.columns.tolist()
                    
                    # 获取数据类型
                    data_types = {}
                    for col in column_names:
                        dtype = str(df[col].dtype)
                        if 'int' in dtype:
                            data_types[col] = 'integer'
                        elif 'float' in dtype:
                            data_types[col] = 'float'
                        elif 'datetime' in dtype or 'date' in dtype:
                            data_types[col] = 'datetime'
                        elif 'bool' in dtype:
                            data_types[col] = 'boolean'
                        else:
                            data_types[col] = 'string'
                    
                    # 获取数据摘要（前5条）
                    sample_data = df.head(5).to_dict(orient='records')
                    
                    # 统计信息
                    statistics = {}
                    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_columns:
                        for col in numeric_columns:
                            statistics[col] = {
                                'count': int(df[col].count()),
                                'mean': float(df[col].mean()) if df[col].count() > 0 else None,
                                'min': float(df[col].min()) if df[col].count() > 0 else None,
                                'max': float(df[col].max()) if df[col].count() > 0 else None,
                                'std': float(df[col].std()) if df[col].count() > 0 else None,
                            }
                else:
                    rows_count = 0
                    columns_count = 0
                    column_names = []
                    data_types = {}
                    sample_data = []
                    statistics = {}
            else:
                # 如果是对象，分析其结构
                rows_count = 1
                columns_count = len(data.keys())
                column_names = list(data.keys())
                data_types = {}
                for key, value in data.items():
                    if isinstance(value, int):
                        data_types[key] = 'integer'
                    elif isinstance(value, float):
                        data_types[key] = 'float'
                    elif isinstance(value, bool):
                        data_types[key] = 'boolean'
                    elif isinstance(value, str):
                        data_types[key] = 'string'
                    elif isinstance(value, (list, dict)):
                        data_types[key] = 'object'
                    else:
                        data_types[key] = 'unknown'
                sample_data = [data]
                statistics = {}
            
            return {
                "success": True,
                "file_type": "json",
                "rows": rows_count,
                "columns": columns_count,
                "column_names": column_names,
                "data_types": data_types,
                "sample_data": sample_data,
                "statistics": statistics,
                "summary": f"JSON文件，{rows_count}条记录"
            }
            
        except Exception as e:
            logger.error(f"解析JSON文件失败: {e}")
            raise

