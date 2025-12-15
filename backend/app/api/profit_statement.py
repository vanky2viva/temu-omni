"""利润表管理API"""
import os
import shutil
import re
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.order import Order

router = APIRouter(prefix="/profit-statement", tags=["利润表"])

# 上传文件保存目录
UPLOAD_DIR = "/tmp/profit_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def parse_csv_file(file_path: str) -> pd.DataFrame:
    """解析CSV文件"""
    try:
        # 尝试不同的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法解析文件编码，请确保文件为UTF-8或GBK编码"
            )
        
        return df
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件解析失败: {str(e)}"
        )


def parse_excel_file(file_path: str) -> pd.DataFrame:
    """解析Excel文件"""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excel文件解析失败: {str(e)}"
        )


@router.post("/upload/collection")
async def upload_collection_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传Temu结算表
    
    支持CSV和Excel格式，需要包含PO单号和5个结算字段：
    - 销售回款
    - 销售回款已减优惠
    - 销售冲回
    - 运费回款
    - 运费回款已减优惠
    """
    # 验证文件类型
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持CSV和Excel文件(.csv, .xlsx, .xls)"
        )
    
    file_path = os.path.join(UPLOAD_DIR, f"collection_{current_user.id}_{file.filename}")
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解析文件
        if file.filename.endswith('.csv'):
            df = parse_csv_file(file_path)
        else:
            df = parse_excel_file(file_path)
        
        # 查找PO单号列（可能的列名）
        po_sn_col = None
        possible_po_cols = ['PO单号', 'PO单号', 'po单号', 'parent_order_sn', '订单号', 'order_sn']
        for col in df.columns:
            if col in possible_po_cols or 'PO' in str(col).upper():
                po_sn_col = col
                break
        
        if po_sn_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到PO单号列，请确保文件包含PO单号列"
            )
        
        # 查找5个结算字段
        field_mapping = {
            'sales_collection': ['销售回款', 'sales_collection'],
            'sales_collection_after_discount': ['销售回款已减优惠', '销售回款已减优声', 'sales_collection_after_discount'],
            'sales_reversal': ['销售冲回', 'sales_reversal'],
            'shipping_collection': ['运费回款', 'shipping_collection'],
            'shipping_collection_after_discount': ['运费回款已减优惠', '运费回款已减优声', 'shipping_collection_after_discount'],
        }
        
        found_fields = {}
        for field_key, possible_names in field_mapping.items():
            for col in df.columns:
                if col in possible_names:
                    found_fields[field_key] = col
                    break
        
        if len(found_fields) < 5:
            missing = [k for k in field_mapping.keys() if k not in found_fields]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到所有必需的结算字段，缺少: {', '.join(missing)}"
            )
        
        # 按PO单号分组合并数据
        po_data_map = {}
        for _, row in df.iterrows():
            po_sn = str(row[po_sn_col]).strip() if pd.notna(row[po_sn_col]) else None
            
            if not po_sn or po_sn == 'nan' or po_sn == '':
                continue
            
            # 提取5个字段的值
            sales_collection = float(row[found_fields['sales_collection']]) if pd.notna(row[found_fields['sales_collection']]) else 0.0
            sales_collection_after_discount = float(row[found_fields['sales_collection_after_discount']]) if pd.notna(row[found_fields['sales_collection_after_discount']]) else 0.0
            sales_reversal = float(row[found_fields['sales_reversal']]) if pd.notna(row[found_fields['sales_reversal']]) else 0.0
            shipping_collection = float(row[found_fields['shipping_collection']]) if pd.notna(row[found_fields['shipping_collection']]) else 0.0
            shipping_collection_after_discount = float(row[found_fields['shipping_collection_after_discount']]) if pd.notna(row[found_fields['shipping_collection_after_discount']]) else 0.0
            
            # 如果PO单号已存在，累加金额
            if po_sn in po_data_map:
                po_data_map[po_sn]['sales_collection'] += sales_collection
                po_data_map[po_sn]['sales_collection_after_discount'] += sales_collection_after_discount
                po_data_map[po_sn]['sales_reversal'] += sales_reversal
                po_data_map[po_sn]['shipping_collection'] += shipping_collection
                po_data_map[po_sn]['shipping_collection_after_discount'] += shipping_collection_after_discount
            else:
                po_data_map[po_sn] = {
                    'parent_order_sn': po_sn,
                    'sales_collection': sales_collection,
                    'sales_collection_after_discount': sales_collection_after_discount,
                    'sales_reversal': sales_reversal,
                    'shipping_collection': shipping_collection,
                    'shipping_collection_after_discount': shipping_collection_after_discount,
                }
        
        # 转换为列表
        data = list(po_data_map.values())
        
        return {
            "success": True,
            "message": f"成功解析{len(data)}个PO单号的结算数据",
            "data": data,
            "total": len(data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理文件失败: {str(e)}"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload/shipping")
async def upload_shipping_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传头程运费表
    
    支持CSV和Excel格式，需要包含订单号和头程运费字段
    """
    # 验证文件类型
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持CSV和Excel文件(.csv, .xlsx, .xls)"
        )
    
    file_path = os.path.join(UPLOAD_DIR, f"shipping_{current_user.id}_{file.filename}")
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解析文件
        if file.filename.endswith('.csv'):
            df = parse_csv_file(file_path)
        else:
            df = parse_excel_file(file_path)
        
        # 查找平台单号列（PO单号，父订单号）
        order_sn_col = None
        possible_order_cols = ['平台单号', 'PO单号', 'parent_order_sn', '订单号', 'order_sn', '订单编号', 'order_id', '订单ID']
        for col in df.columns:
            if col in possible_order_cols or '平台' in str(col) or 'PO' in str(col).upper():
                order_sn_col = col
                break
        
        if order_sn_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到平台单号列，请确保文件包含以下列名之一: 平台单号, PO单号, parent_order_sn"
            )
        
        # 查找合计应收列（头程运费）
        shipping_col = None
        possible_shipping_cols = ['合计应收', '合计营收', '总应收', '头程费用', '头程运费', 'shipping_cost', 'first_mile_cost', '运费', '应收金额']
        for col in df.columns:
            if col in possible_shipping_cols or '合计' in str(col) or '应收' in str(col):
                shipping_col = col
                break
        
        if shipping_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到合计应收列，请确保文件包含以下列名之一: 合计应收, 合计营收"
            )
        
        # 查找收费重列（可选）
        weight_col = None
        possible_weight_cols = ['收费重', '收费重(KG)', '收费重 (KG)', '重量', 'weight', 'chargeable_weight']
        for col in df.columns:
            if col in possible_weight_cols or ('收费' in str(col) and '重' in str(col)):
                weight_col = col
                break
        
        # 提取数据
        data = []
        for _, row in df.iterrows():
            order_sn = str(row[order_sn_col]).strip() if pd.notna(row[order_sn_col]) else None
            # 处理合计应收：可能包含¥符号，需要清理
            shipping_cost_raw = row[shipping_col] if pd.notna(row[shipping_col]) else 0.0
            if isinstance(shipping_cost_raw, str):
                # 移除¥符号和空格
                shipping_cost_raw = shipping_cost_raw.replace('¥', '').replace('￥', '').replace(',', '').strip()
            shipping_cost = float(shipping_cost_raw) if shipping_cost_raw else 0.0
            
            # 提取收费重（如果有）
            chargeable_weight = None
            if weight_col and pd.notna(row[weight_col]):
                try:
                    weight_value = row[weight_col]
                    if isinstance(weight_value, str):
                        weight_value = weight_value.replace('KG', '').replace('kg', '').strip()
                    chargeable_weight = float(weight_value)
                except:
                    chargeable_weight = None
            
            if order_sn:
                item = {
                    "parent_order_sn": order_sn,  # 使用parent_order_sn作为键，因为这是平台父订单号
                    "order_sn": order_sn,  # 保留order_sn用于兼容
                    "shipping_cost": shipping_cost
                }
                if chargeable_weight is not None:
                    item["chargeable_weight"] = chargeable_weight
                data.append(item)
        
        return {
            "success": True,
            "message": f"成功解析{len(data)}条头程运费记录",
            "data": data,
            "total": len(data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理文件失败: {str(e)}"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload/last-mile-shipping")
async def upload_last_mile_shipping_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传尾程运费表
    
    支持CSV和Excel格式，需要包含订单号和尾程运费字段
    """
    # 验证文件类型
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持CSV和Excel文件(.csv, .xlsx, .xls)"
        )
    
    file_path = os.path.join(UPLOAD_DIR, f"last_mile_shipping_{current_user.id}_{file.filename}")
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解析文件
        if file.filename.endswith('.csv'):
            df = parse_csv_file(file_path)
        else:
            df = parse_excel_file(file_path)
        
        # 查找订单号列
        order_sn_col = None
        possible_order_cols = ['订单号', 'order_sn', '订单编号', 'order_id', '订单ID', 'PO单号', 'parent_order_sn']
        for col in df.columns:
            if col in possible_order_cols:
                order_sn_col = col
                break
        
        if order_sn_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到订单号列，请确保文件包含以下列名之一: {', '.join(possible_order_cols)}"
            )
        
        # 查找尾程运费列
        shipping_col = None
        possible_shipping_cols = ['尾程费用', '尾程运费', 'last_mile_cost', 'last_mile_shipping', '尾程', 'last_mile']
        for col in df.columns:
            if col in possible_shipping_cols:
                shipping_col = col
                break
        
        if shipping_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到尾程运费列，请确保文件包含以下列名之一: {', '.join(possible_shipping_cols)}"
            )
        
        # 提取数据
        data = []
        for _, row in df.iterrows():
            order_sn = str(row[order_sn_col]).strip() if pd.notna(row[order_sn_col]) else None
            last_mile_cost = float(row[shipping_col]) if pd.notna(row[shipping_col]) else 0.0
            
            if order_sn:
                data.append({
                    "order_sn": order_sn,
                    "last_mile_cost": last_mile_cost
                })
        
        return {
            "success": True,
            "message": f"成功解析{len(data)}条尾程运费记录",
            "data": data,
            "total": len(data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理文件失败: {str(e)}"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload/deduction")
async def upload_deduction_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传延迟扣款表
    
    支持CSV和Excel格式，需要包含订单号和扣款金额字段
    """
    # 验证文件类型
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持CSV和Excel文件(.csv, .xlsx, .xls)"
        )
    
    file_path = os.path.join(UPLOAD_DIR, f"deduction_{current_user.id}_{file.filename}")
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解析文件
        if file.filename.endswith('.csv'):
            df = parse_csv_file(file_path)
        else:
            df = parse_excel_file(file_path)
        
        # 查找订单编号列（平台父订单号）
        order_sn_col = None
        possible_order_cols = ['订单编号', '订单号', 'PO单号', 'parent_order_sn', 'order_sn', 'order_id', '订单ID']
        for col in df.columns:
            if col in possible_order_cols or '订单' in str(col) or 'PO' in str(col).upper():
                order_sn_col = col
                break
        
        if order_sn_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到订单编号列，请确保文件包含以下列名之一: 订单编号, 订单号, PO单号"
            )
        
        # 查找支出金额列（扣款金额）
        deduction_col = None
        possible_deduction_cols = ['支出金额', '扣款金额', '罚款', '延迟扣款', 'deduction', 'penalty', '罚款金额', '支出']
        for col in df.columns:
            if col in possible_deduction_cols or '支出' in str(col) or '扣款' in str(col):
                deduction_col = col
                break
        
        if deduction_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到支出金额列，请确保文件包含以下列名之一: 支出金额, 扣款金额"
            )
        
        # 提取数据，按订单编号分组累加扣款金额（同一订单可能有多次扣款）
        deduction_map = {}
        for _, row in df.iterrows():
            order_sn = str(row[order_sn_col]).strip() if pd.notna(row[order_sn_col]) else None
            if not order_sn or order_sn == 'nan' or order_sn == '':
                continue
            
            # 处理支出金额：可能包含符号，需要清理
            deduction_raw = row[deduction_col] if pd.notna(row[deduction_col]) else 0.0
            if isinstance(deduction_raw, str):
                # 移除可能的符号和空格
                deduction_raw = deduction_raw.replace('¥', '').replace('￥', '').replace(',', '').replace('-', '').strip()
            deduction = abs(float(deduction_raw)) if deduction_raw else 0.0  # 取绝对值，确保为正数
            
            # 按订单编号累加扣款金额
            if order_sn in deduction_map:
                deduction_map[order_sn] += deduction
            else:
                deduction_map[order_sn] = deduction
        
        # 转换为列表
        data = []
        for order_sn, total_deduction in deduction_map.items():
            data.append({
                "parent_order_sn": order_sn,  # 使用parent_order_sn作为键，因为这是平台父订单号
                "order_sn": order_sn,  # 保留order_sn用于兼容
                "deduction": total_deduction
            })
        
        return {
            "success": True,
            "message": f"成功解析{len(data)}条扣款记录",
            "data": data,
            "total": len(data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理文件失败: {str(e)}"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload/order-list")
async def upload_order_list_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传订单列表
    
    支持CSV和Excel格式，需要包含：
    - 订单号（用于匹配系统内的父订单号）
    - 包裹号
    - 收货地址信息（国家、城市、省份、邮编、详细地址）
    
    根据订单号匹配系统内的父订单号(parent_order_sn)，然后更新包裹号和收货地址信息到数据库
    """
    # 验证文件类型
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持CSV和Excel文件(.csv, .xlsx, .xls)"
        )
    
    file_path = os.path.join(UPLOAD_DIR, f"order_list_{current_user.id}_{file.filename}")
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解析文件
        if file.filename.endswith('.csv'):
            df = parse_csv_file(file_path)
        else:
            df = parse_excel_file(file_path)
        
        # 查找订单号列
        order_sn_col = None
        possible_order_cols = ['订单号', 'order_sn', '订单编号', 'order_id', '订单ID', 'PO单号', 'parent_order_sn', '平台单号']
        for col in df.columns:
            if col in possible_order_cols or '订单' in str(col) or 'PO' in str(col).upper() or 'order' in str(col).lower():
                order_sn_col = col
                break
        
        if order_sn_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"未找到订单号列，请确保文件包含以下列名之一: {', '.join(possible_order_cols)}"
            )
        
        # 查找包裹号列
        package_sn_col = None
        possible_package_cols = ['包裹号', 'package_sn', '包裹编号', '物流单号', 'tracking_number', '运单号']
        
        # 首先尝试按列名匹配
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in possible_package_cols or '包裹' in col_str or 'package' in col_str.lower() or '物流' in col_str:
                package_sn_col = col
                break
        
        # 如果没找到，尝试按列索引查找（Excel中的Y列通常是索引24或列名就是Y）
        if not package_sn_col:
            # 检查是否有名为'Y'的列
            if 'Y' in df.columns:
                package_sn_col = 'Y'
            # 或者尝试通过索引查找（如果列名是数字或Excel列标识）
            else:
                # 尝试找到可能的包裹号列（通常包含PK-前缀或类似格式）
                for idx, col in enumerate(df.columns):
                    # 检查这一列的前几行数据，看是否包含包裹号格式（如PK-开头）
                    col_str = str(col).strip()
                    sample_values = df[col].dropna().head(5).astype(str).tolist()
                    # 如果样本值中包含PK-开头的数据，很可能是包裹号列
                    if any('PK-' in val or 'pk-' in val.lower() for val in sample_values):
                        package_sn_col = col
                        break
                    # 如果列名是Y或类似Excel列标识
                    if col_str == 'Y' or col_str.upper() == 'Y':
                        package_sn_col = col
                        break
        
        # 查找收货地址相关列
        address_cols = {
            'shipping_country': ['收货国家', '国家', 'country', 'shipping_country', '收货国'],
            'shipping_province': ['收货省份', '省份', '州', 'province', 'state', 'shipping_province'],
            'shipping_city': ['收货城市', '城市', 'city', 'shipping_city'],
            'shipping_postal_code': ['收货邮编', '邮编', 'postal_code', 'zip_code', 'shipping_postal_code', '邮政编码'],
            'shipping_address': ['收货地址', '详细地址', '地址', 'address', 'shipping_address', '收货详细地址', '完整地址'],
        }
        
        found_address_cols = {}
        for field_key, possible_names in address_cols.items():
            for col in df.columns:
                if col in possible_names or any(keyword in str(col) for keyword in possible_names):
                    found_address_cols[field_key] = col
                    break
        
        # 至少需要订单号，包裹号和地址信息可选
        # 如果没有找到包裹号和地址信息列，给出警告但继续处理（可能只更新订单号匹配信息）
        if not package_sn_col and not found_address_cols:
            # 不抛出错误，允许只有订单号的文件上传（虽然不会更新任何信息）
            pass
        
        # 处理数据：按订单号分组，合并包裹号和地址信息
        order_data_map = {}
        for _, row in df.iterrows():
            order_sn = str(row[order_sn_col]).strip() if pd.notna(row[order_sn_col]) else None
            if not order_sn or order_sn == 'nan' or order_sn == '':
                continue
            
            # 提取包裹号
            package_sn = None
            if package_sn_col:
                try:
                    if pd.notna(row[package_sn_col]):
                        package_sn_raw = row[package_sn_col]
                        package_sn = str(package_sn_raw).strip()
                        # 过滤掉无效值
                        if package_sn in ['nan', 'None', '--', '', 'null', 'NULL']:
                            package_sn = None
                except (KeyError, AttributeError):
                    # 如果列不存在或无法访问，跳过
                    package_sn = None
            
            # 提取地址信息
            address_info = {}
            for field_key, col_name in found_address_cols.items():
                if pd.notna(row[col_name]):
                    value = str(row[col_name]).strip()
                    if value and value != 'nan':
                        address_info[field_key] = value
            
            # 如果订单号已存在，合并信息（优先使用非空值）
            if order_sn in order_data_map:
                existing = order_data_map[order_sn]
                # 如果新数据有包裹号且旧数据没有，或者新数据的包裹号与旧数据不同，则更新
                if package_sn:
                    if not existing.get('package_sn') or existing.get('package_sn') != package_sn:
                        existing['package_sn'] = package_sn
                for key, value in address_info.items():
                    if value and (not existing.get(key) or existing.get(key) != value):
                        existing[key] = value
            else:
                order_data_map[order_sn] = {
                    'order_sn': order_sn,
                    'package_sn': package_sn,
                    **address_info
                }
        
        # 匹配系统内的订单并更新
        updated_count = 0
        matched_count = 0
        unmatched_orders = []
        
        for order_data in order_data_map.values():
            order_sn = order_data['order_sn']
            
            # 查询系统内匹配的订单（优先匹配parent_order_sn，如果没有则匹配order_sn）
            matched_orders = db.query(Order).filter(
                or_(
                    Order.parent_order_sn == order_sn,
                    Order.order_sn == order_sn
                )
            ).all()
            
            if not matched_orders:
                # 尝试模糊匹配：如果订单号包含PO-前缀，尝试去除前缀后匹配
                if order_sn.startswith('PO-'):
                    without_prefix = order_sn[3:]  # 去掉 "PO-"
                    matched_orders = db.query(Order).filter(
                        or_(
                            Order.parent_order_sn == without_prefix,
                            Order.order_sn == without_prefix
                        )
                    ).all()
                    
                    if not matched_orders and '-' in without_prefix:
                        # 尝试提取数字部分匹配
                        parts = without_prefix.split('-', 1)
                        if len(parts) == 2:
                            number_part = parts[1]
                            matched_orders = db.query(Order).filter(
                                or_(
                                    Order.parent_order_sn.like(f"%{number_part}"),
                                    Order.order_sn.like(f"%{number_part}")
                                )
                            ).all()
                            # 刷新所有订单对象，确保获取最新的数据
                            for order in matched_orders:
                                db.refresh(order)
            
            if matched_orders:
                matched_count += 1
                # 更新所有匹配的订单
                for order in matched_orders:
                    updated = False
                    
                    # 更新包裹号（如果上传的数据中有包裹号，则更新）
                    if order_data.get('package_sn'):
                        package_sn_value = str(order_data['package_sn']).strip()
                        # 过滤掉无效值
                        if package_sn_value and package_sn_value != 'nan' and package_sn_value != 'None' and package_sn_value != '--' and package_sn_value.lower() != 'null':
                            # 只有当值不同时才更新（允许覆盖已有值）
                            current_package_sn = str(order.package_sn).strip() if order.package_sn else ''
                            if current_package_sn != package_sn_value:
                                order.package_sn = package_sn_value
                                updated = True
                    
                    # 更新收货地址信息（如果上传的数据中有地址信息，则更新）
                    if order_data.get('shipping_country'):
                        country_value = str(order_data['shipping_country']).strip()
                        if country_value and country_value != 'nan' and order.shipping_country != country_value:
                            order.shipping_country = country_value
                            updated = True
                    
                    if order_data.get('shipping_province'):
                        province_value = str(order_data['shipping_province']).strip()
                        if province_value and province_value != 'nan' and order.shipping_province != province_value:
                            order.shipping_province = province_value
                            updated = True
                    
                    if order_data.get('shipping_city'):
                        city_value = str(order_data['shipping_city']).strip()
                        if city_value and city_value != 'nan' and order.shipping_city != city_value:
                            order.shipping_city = city_value
                            updated = True
                    
                    if order_data.get('shipping_postal_code'):
                        postal_value = str(order_data['shipping_postal_code']).strip()
                        if postal_value and postal_value != 'nan' and order.shipping_postal_code != postal_value:
                            order.shipping_postal_code = postal_value
                            updated = True
                    
                    if order_data.get('shipping_address'):
                        address_value = str(order_data['shipping_address']).strip()
                        if address_value and address_value != 'nan' and order.shipping_address != address_value:
                            order.shipping_address = address_value
                            updated = True
                    
                    if updated:
                        updated_count += 1
                        order.updated_at = datetime.utcnow()
            else:
                unmatched_orders.append(order_sn)
        
        # 提交更改
        db.commit()
        
        # 构建详细消息
        message_parts = [f"成功处理{len(order_data_map)}条订单记录"]
        if matched_count > 0:
            message_parts.append(f"匹配到{matched_count}个订单")
        if updated_count > 0:
            message_parts.append(f"更新了{updated_count}条记录")
        else:
            message_parts.append("但未更新任何记录")
            if not package_sn_col:
                message_parts.append(f"（原因：未找到包裹号列，已尝试的列名：{', '.join(possible_package_cols)}，或请确保Y列包含包裹号数据）")
            elif matched_count > 0:
                # 检查是否有包裹号数据
                has_package_data = any(order_data.get('package_sn') for order_data in order_data_map.values())
                if not has_package_data:
                    message_parts.append(f"（原因：找到包裹号列'{package_sn_col}'，但该列数据为空或无效）")
                else:
                    message_parts.append("（原因：匹配的订单已有相同包裹号，或包裹号数据格式不正确）")
        
        if len(unmatched_orders) > 0:
            message_parts.append(f"，{len(unmatched_orders)}条未匹配")
        
        # 统计有包裹号数据的记录数
        records_with_package = sum(1 for order_data in order_data_map.values() if order_data.get('package_sn'))
        
        return {
            "success": True,
            "message": "".join(message_parts),
            "data": {
                "total": len(order_data_map),
                "matched": matched_count,
                "updated": updated_count,
                "unmatched": len(unmatched_orders),
                "unmatched_orders": unmatched_orders[:100],  # 只返回前100个未匹配的订单号
                "has_package_sn_col": package_sn_col is not None,
                "package_sn_col_name": package_sn_col if package_sn_col else None,  # 返回识别到的包裹号列名
                "records_with_package": records_with_package,  # 有包裹号数据的记录数
                "has_address_cols": len(found_address_cols) > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理文件失败: {str(e)}"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/calculate")
async def calculate_profit(
    collection_data: List[Dict[str, Any]],
    shipping_data: List[Dict[str, Any]],
    deduction_data: List[Dict[str, Any]],
    last_mile_shipping_data: Optional[List[Dict[str, Any]]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算利润
    
    根据上传的结算表、头程运费表、延迟扣款表、尾程运费表，与订单匹配并计算最终利润
    结算表使用PO单号（parent_order_sn）匹配，按父订单号合并计算
    """
    try:
        # 在开始计算前，先提交所有未提交的更改，并清除会话缓存
        # 这确保能获取到最新的订单数据（包括刚刚更新的包裹号）
        db.commit()
        db.expire_all()
        
        if last_mile_shipping_data is None:
            last_mile_shipping_data = []
        
        # 构建父订单号到结算数据的映射（结算表使用parent_order_sn）
        settlement_map = {}
        for item in collection_data:
            parent_order_sn = item.get("parent_order_sn")
            if parent_order_sn:
                settlement_map[parent_order_sn] = item
        
        # 构建父订单号到头程运费、扣款和尾程运费的映射
        # 头程运费使用parent_order_sn匹配（平台单号）
        shipping_map = {}
        shipping_weight_map = {}  # 收费重映射
        for item in shipping_data:
            parent_sn = item.get("parent_order_sn") or item.get("order_sn", "")
            if parent_sn:
                shipping_map[parent_sn] = item.get("shipping_cost", 0.0)
                if "chargeable_weight" in item:
                    shipping_weight_map[parent_sn] = item.get("chargeable_weight")
        
        # 扣款使用parent_order_sn匹配（订单编号 = 平台父订单号）
        deduction_map = {}
        for item in deduction_data:
            parent_sn = item.get("parent_order_sn") or item.get("order_sn", "")
            if parent_sn:
                # 如果同一订单有多次扣款，累加
                if parent_sn in deduction_map:
                    deduction_map[parent_sn] += item.get("deduction", 0.0)
                else:
                    deduction_map[parent_sn] = item.get("deduction", 0.0)
        last_mile_shipping_map = {item.get("order_sn", item.get("parent_order_sn", "")): item.get("last_mile_cost", 0.0) for item in last_mile_shipping_data}
        
        # 获取所有父订单号
        all_parent_order_sns = set(settlement_map.keys())
        
        if not all_parent_order_sns:
            return {
                "success": True,
                "message": "没有结算数据",
                "data": {
                    "items": [],
                    "summary": {
                        "total_orders": 0,
                        "matched_orders": 0,
                        "unmatched_orders": 0,
                        "total_revenue": 0.0,
                        "total_cost": 0.0,
                        "total_profit": 0.0,
                        "average_profit_rate": 0.0,
                    }
                }
            }
        
        # 查询匹配的订单（使用parent_order_sn匹配）
        # 注意：使用 refresh=True 确保获取最新的数据库数据，包括包裹号等字段
        matched_orders_by_parent = {}
        
        # 精确匹配parent_order_sn（优先使用）
        # 在查询前先提交更改并清除会话缓存，确保获取最新数据
        db.commit()  # 先提交所有未提交的更改（包括之前上传订单列表的更新）
        db.expire_all()  # 清除所有对象缓存，强制重新加载
        
        orders = db.query(Order).filter(
            Order.parent_order_sn.in_(all_parent_order_sns)
        ).all()
        
        # 刷新所有订单对象，确保获取最新的数据（包括包裹号）
        for order in orders:
            db.refresh(order)  # 刷新订单对象以获取最新数据
        
        # 按parent_order_sn分组订单
        for order in orders:
            if order.parent_order_sn:
                if order.parent_order_sn not in matched_orders_by_parent:
                    matched_orders_by_parent[order.parent_order_sn] = []
                matched_orders_by_parent[order.parent_order_sn].append(order)
        
        # 对于未匹配的，尝试更严格的匹配（仅作为备选方案）
        unmatched_parent_sns = [sn for sn in all_parent_order_sns if sn not in matched_orders_by_parent]
        if unmatched_parent_sns:
            for parent_sn in unmatched_parent_sns:
                # 尝试去除PO-前缀后精确匹配
                # PO单号格式通常是：PO-211-20290008576630519
                if parent_sn.startswith('PO-'):
                    # 去除PO-前缀
                    without_prefix = parent_sn[3:]  # 去掉 "PO-"
                    # 尝试精确匹配去除前缀后的值
                    exact_match_orders = db.query(Order).filter(
                        Order.parent_order_sn == without_prefix
                    ).all()
                    # 刷新所有订单对象，确保获取最新的数据（包括包裹号）
                    for order in exact_match_orders:
                        db.refresh(order)
                    if exact_match_orders:
                        matched_orders_by_parent[parent_sn] = exact_match_orders
                        continue
                    
                    # 如果还有"-"，提取完整的数字部分进行严格匹配
                    if '-' in without_prefix:
                        parts = without_prefix.split('-', 1)
                        if len(parts) == 2:
                            number_part = parts[1]  # 取第二部分（纯数字，如：20290008576630519）
                            
                            # 只匹配以这个完整数字串结尾的订单号，且确保是精确匹配
                            # 使用LIKE匹配以数字结尾的订单号
                            potential_orders = db.query(Order).filter(
                                Order.parent_order_sn.like(f"%{number_part}")
                            ).all()
                            
                            # 刷新潜在匹配的订单对象
                            for order in potential_orders:
                                db.refresh(order)
                            
                            # 严格过滤：确保匹配的订单号完全符合预期
                            filtered_orders = []
                            for order in potential_orders:
                                if order.parent_order_sn:
                                    # 1. 订单号必须以这个数字串结尾
                                    if not order.parent_order_sn.endswith(number_part):
                                        continue
                                    
                                    # 2. 长度差异不超过10个字符（允许前缀差异，如PO-211-）
                                    if abs(len(order.parent_order_sn) - len(parent_sn)) > 10:
                                        continue
                                    
                                    # 3. 提取订单号中的数字部分，确保包含完整的数字串
                                    order_numbers = re.findall(r'\d+', order.parent_order_sn)
                                    if number_part not in order_numbers:
                                        continue
                                    
                                    # 4. 如果订单号也以PO-开头，确保格式一致
                                    if order.parent_order_sn.startswith('PO-'):
                                        # 提取PO单号中的数字部分进行比较
                                        order_without_po = order.parent_order_sn[3:]
                                        if '-' in order_without_po:
                                            order_parts = order_without_po.split('-', 1)
                                            if len(order_parts) == 2 and order_parts[1] == number_part:
                                                # 进一步检查：前缀部分应该相同（如211）
                                                # 对于PO-211-20290008576630519，只匹配PO-211-20290008576630519
                                                if order_parts[0] == parts[0]:
                                                    filtered_orders.append(order)
                                    else:
                                        # 如果订单号不以PO-开头，但以数字串结尾，也接受
                                        if order.parent_order_sn.endswith(number_part):
                                            filtered_orders.append(order)
                            
                            # 刷新所有过滤后的订单对象，确保获取最新的数据（包括包裹号）
                            for order in filtered_orders:
                                db.refresh(order)
                            
                            # 只接受唯一匹配，避免误匹配多个订单
                            if len(filtered_orders) == 1:
                                matched_orders_by_parent[parent_sn] = filtered_orders
                                continue
                            elif len(filtered_orders) > 1:
                                # 如果有多个匹配，优先选择格式完全一致的（前缀相同）
                                exact_format_matches = []
                                for o in filtered_orders:
                                    if o.parent_order_sn.startswith('PO-'):
                                        o_without_po = o.parent_order_sn[3:]
                                        if '-' in o_without_po:
                                            o_parts = o_without_po.split('-', 1)
                                            if len(o_parts) == 2 and o_parts[0] == parts[0] and o_parts[1] == number_part:
                                                exact_format_matches.append(o)
                                
                                # 刷新格式完全一致的匹配订单
                                for order in exact_format_matches:
                                    db.refresh(order)
                                
                                # 如果找到格式完全一致的匹配，使用它
                                if len(exact_format_matches) == 1:
                                    matched_orders_by_parent[parent_sn] = exact_format_matches
                                    continue
                                # 如果有多个格式完全一致的匹配，说明数据有问题，不匹配
                                # 这样可以避免误匹配
        
        # 计算利润（处理所有结算数据，包括取消订单）
        results = []
        total_profit = 0.0
        total_revenue = 0.0
        total_cost = 0.0
        
        for parent_order_sn in all_parent_order_sns:
            settlement = settlement_map.get(parent_order_sn, {})
            
            # 计算收入：收入=销售回款+销售回款已减金额+销售冲回（值为负）+运费回款-运费回款已减优惠
            sales_collection = settlement.get('sales_collection', 0.0)
            sales_collection_after_discount = settlement.get('sales_collection_after_discount', 0.0)
            # 销售冲回：如果值为正，转为负数；如果已经是负数，直接使用
            sales_reversal_raw = settlement.get('sales_reversal', 0.0)
            sales_reversal = -abs(sales_reversal_raw) if sales_reversal_raw != 0 else 0.0  # 确保为负数
            shipping_collection = settlement.get('shipping_collection', 0.0)
            shipping_collection_after_discount = settlement.get('shipping_collection_after_discount', 0.0)
            revenue = sales_collection + sales_collection_after_discount + sales_reversal + shipping_collection - shipping_collection_after_discount
            
            # 获取匹配的订单（包括取消订单，都要匹配）
            matched_orders = matched_orders_by_parent.get(parent_order_sn, [])
            
            # 无论是否匹配到订单，只要有结算数据就显示（包括取消订单）
            # 如果最终收入为0（考虑浮点数精度，允许小的误差），说明订单被冲回，没有实际发货，进货成本为0
            if abs(revenue) < 0.01:  # 收入为0或接近0（取消订单）
                total_product_cost = 0.0
                total_quantity = sum(order.quantity for order in matched_orders) if matched_orders else 0
            elif matched_orders:
                # 根据SKU设置固定成本价
                SKU_COST_MAP = {
                    'LBB3-1-US': 105.0,
                    'LBB4-A-US': 82.0,
                    'LBB4-B-US': 82.0,
                }
                
                # 按父订单号合并计算：根据SKU和数量计算成本
                total_product_cost = 0.0
                total_quantity = sum(order.quantity for order in matched_orders)
                
                for order in matched_orders:
                    sku = order.product_sku or ''
                    quantity = order.quantity or 0
                    
                    # 根据SKU匹配成本价，如果未匹配到则使用0
                    unit_cost = SKU_COST_MAP.get(sku, 0.0)
                    order_cost = unit_cost * quantity
                    total_product_cost += order_cost
            else:
                # 没有匹配到订单，但仍有结算数据（可能是取消订单或其他情况）
                total_product_cost = 0.0
                total_quantity = 0
            
            # 获取头程运费、尾程运费和扣款（使用父订单号）
            shipping_cost = shipping_map.get(parent_order_sn, 0.0)
            chargeable_weight = shipping_weight_map.get(parent_order_sn)  # 收费重
            last_mile_cost = last_mile_shipping_map.get(parent_order_sn, 0.0)
            deduction = deduction_map.get(parent_order_sn, 0.0)
            
            # 计算总成本
            total_order_cost = total_product_cost + shipping_cost + last_mile_cost + deduction
            
            # 计算利润
            profit = revenue - total_order_cost
            
            # 获取商品信息和包裹号（如果有匹配的订单）
            if matched_orders:
                order_ids = [order.id for order in matched_orders]
                
                # 先提交所有更改，然后清除会话缓存，确保获取最新数据
                db.commit()  # 确保所有未提交的更改都已提交
                db.expire_all()  # 使所有对象过期，强制重新加载
                
                # 方法1: 使用原始SQL查询直接获取包裹号，绕过ORM缓存
                package_sn = None
                if order_ids:
                    try:
                        # 使用参数化查询（安全）
                        # 构建占位符
                        placeholders = ','.join([':id' + str(i) for i in range(len(order_ids))])
                        params = {f'id{i}': order_id for i, order_id in enumerate(order_ids)}
                        
                        package_sn_query = text(f"""
                            SELECT package_sn 
                            FROM orders 
                            WHERE id IN ({placeholders})
                            AND package_sn IS NOT NULL 
                            AND package_sn != '' 
                            AND package_sn != 'nan'
                            AND package_sn != 'None'
                            AND package_sn != '--'
                            AND TRIM(package_sn) != ''
                            LIMIT 1
                        """)
                        result = db.execute(package_sn_query, params)
                        package_sn_row = result.first()
                        if package_sn_row and package_sn_row[0]:
                            package_sn = str(package_sn_row[0]).strip()
                            if not package_sn or package_sn in ['nan', 'None', '--', 'null', 'NULL']:
                                package_sn = None
                    except Exception:
                        # 如果SQL查询失败，回退到ORM查询
                        package_sn = None
                
                # 方法2: 如果SQL查询失败或没有结果，使用ORM查询（备用方案）
                if not package_sn:
                    # 重新查询订单，使用 with_for_update 确保获取最新数据
                    fresh_orders = db.query(Order).filter(Order.id.in_(order_ids)).all()
                    for order in fresh_orders:
                        db.refresh(order)  # 强制刷新每个订单对象
                        if order.package_sn:
                            pkg_sn = order.package_sn.strip() if isinstance(order.package_sn, str) else str(order.package_sn).strip()
                            if pkg_sn and pkg_sn not in ['nan', 'None', '--', '', 'null', 'NULL']:
                                package_sn = pkg_sn
                                break
                
                # 创建ID到订单的映射（用于获取其他信息）
                fresh_orders_map = {}
                if not fresh_orders:
                    fresh_orders = db.query(Order).filter(Order.id.in_(order_ids)).all()
                for order in fresh_orders:
                    db.refresh(order)
                    fresh_orders_map[order.id] = order
                
                # 使用最新查询的订单数据
                product_names = list(set([fresh_orders_map[o.id].product_name for o in matched_orders if fresh_orders_map.get(o.id) and fresh_orders_map[o.id].product_name]))
                skus = list(set([fresh_orders_map[o.id].product_sku for o in matched_orders if fresh_orders_map.get(o.id) and fresh_orders_map[o.id].product_sku]))
                matched_order_sns = [fresh_orders_map[o.id].order_sn for o in matched_orders if fresh_orders_map.get(o.id)]
                matched_parent_order_sns = [fresh_orders_map[o.id].parent_order_sn for o in matched_orders if fresh_orders_map.get(o.id) and fresh_orders_map[o.id].parent_order_sn]
            else:
                product_names = []
                skus = []
                matched_order_sns = []
                matched_parent_order_sns = []
                package_sn = None
            
            # 所有结算数据都显示在结果中（包括取消订单和未匹配的订单）
            results.append({
                "parent_order_sn": parent_order_sn,
                "matched_order_ids": [order.id for order in matched_orders] if matched_orders else [],
                "matched_order_count": len(matched_orders),
                "matched_order_sns": matched_order_sns,  # 用于调试
                "matched_parent_order_sns": list(set(matched_parent_order_sns)),  # 用于调试，显示实际匹配的parent_order_sn
                "product_name": product_names[0] if product_names else None,
                "product_names": product_names if len(product_names) > 1 else None,
                "sku": skus[0] if skus else None,
                "skus": skus if len(skus) > 1 else None,
                "quantity": total_quantity,
                "revenue": revenue,  # 收入（回款）
                "sales_collection": settlement.get('sales_collection', 0.0),
                "sales_collection_after_discount": sales_collection_after_discount,
                "sales_reversal": sales_reversal,
                "shipping_collection": settlement.get('shipping_collection', 0.0),
                "shipping_collection_after_discount": shipping_collection_after_discount,
                    "product_cost": total_product_cost,  # 进货成本（合并）
                    "shipping_cost": shipping_cost,  # 头程运费
                    "chargeable_weight": chargeable_weight,  # 收费重（KG）
                    "last_mile_cost": last_mile_cost,  # 尾程运费
                    "deduction": deduction,  # 扣款
                    "total_cost": total_order_cost,  # 总成本
                    "profit": profit,  # 利润
                    "profit_rate": (profit / revenue * 100) if revenue > 0 else 0.0,  # 利润率
                    "package_sn": package_sn,  # 包裹号
            })
            
            total_revenue += revenue
            total_cost += total_order_cost
            total_profit += profit
        
        # 只返回匹配到的订单
        return {
            "success": True,
            "message": f"成功计算{len(results)}个父订单的利润",
            "data": {
                "items": results,
                "summary": {
                    "total_orders": len(results),
                    "matched_orders": len(results),
                    "unmatched_orders": len(all_parent_order_sns) - len(results),
                    "total_revenue": total_revenue,
                    "total_cost": total_cost,
                    "total_profit": total_profit,
                    "average_profit_rate": (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0,
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算利润失败: {str(e)}"
        )
