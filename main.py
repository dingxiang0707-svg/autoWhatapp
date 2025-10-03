"""
SpeedAF Web API Service
用于部署在 Zeabur，供 n8n 调用的 RESTful API 服务
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from speedaf_api import SpeedAFAPI, OrderBuilder

app = FastAPI(
    title="SpeedAF API Service",
    description="SpeedAF 速达非物流 API 服务",
    version="1.0.0"
)

# 允许跨域（n8n 可能需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 SpeedAF API 客户端（从环境变量读取配置）
import os

APP_CODE = os.getenv("SPEEDAF_APP_CODE", "11111111")
SECRET_KEY = os.getenv("SPEEDAF_SECRET_KEY", "uYMGr8eU")
BASE_URL = os.getenv("SPEEDAF_BASE_URL", "https://uat-api.speedaf.com")

speedaf_api = SpeedAFAPI(
    app_code=APP_CODE,
    secret_key=SECRET_KEY,
    base_url=BASE_URL
)


# ========== 数据模型定义 ==========

class SenderInfo(BaseModel):
    """发件人信息"""
    name: str = Field(..., description="发件人姓名")
    mobile: str = Field(..., description="发件人手机")
    address: str = Field(..., description="发件人地址")
    country_code: str = Field(default="CN", description="国家代码")
    company_name: Optional[str] = Field(default="", description="公司名称")
    phone: Optional[str] = Field(default="", description="固定电话")
    email: Optional[str] = Field(default="", description="邮箱")


class ReceiverInfo(BaseModel):
    """收件人信息"""
    name: str = Field(..., description="收件人姓名")
    mobile: str = Field(..., description="收件人手机")
    address: str = Field(..., description="收件人地址")
    country_code: str = Field(..., description="国家代码")
    company_name: Optional[str] = Field(default="", description="公司名称")
    phone: Optional[str] = Field(default="", description="固定电话")
    email: Optional[str] = Field(default="", description="邮箱")


class ParcelInfo(BaseModel):
    """包裹信息"""
    weight: float = Field(..., description="重量(KG)")
    volume: Optional[float] = Field(default=None, description="体积")
    length: Optional[int] = Field(default=None, description="长度(CM)")
    width: Optional[int] = Field(default=None, description="宽度(CM)")
    height: Optional[int] = Field(default=None, description="高度(CM)")
    piece: int = Field(default=1, description="件数")


class ItemInfo(BaseModel):
    """商品信息"""
    goods_name: str = Field(..., description="商品名称")
    goods_qty: int = Field(..., description="商品数量")
    goods_value: float = Field(..., description="商品价值")
    goods_weight: float = Field(..., description="商品重量")
    goods_name_dialect: Optional[str] = Field(default="", description="商品当地语言名称")
    goods_type: str = Field(default="IT02", description="商品类型")
    sku: Optional[str] = Field(default="", description="SKU")


class ServiceOptions(BaseModel):
    """服务选项"""
    delivery_type: str = Field(default="DE01", description="派送类型")
    pay_method: str = Field(default="PA01", description="支付方式")
    parcel_type: str = Field(default="PT01", description="包裹类型")
    remark: Optional[str] = Field(default="", description="备注")


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    custom_order_no: str = Field(..., description="客户订单号")
    customer_code: str = Field(..., description="客户编码")
    sender: SenderInfo = Field(..., description="发件人信息")
    receiver: ReceiverInfo = Field(..., description="收件人信息")
    parcel: ParcelInfo = Field(..., description="包裹信息")
    items: List[ItemInfo] = Field(..., description="商品列表")
    service: Optional[ServiceOptions] = Field(default=None, description="服务选项")


class TrackQueryRequest(BaseModel):
    """轨迹查询请求"""
    mail_no_list: List[str] = Field(..., description="运单号列表")


class CancelOrderRequest(BaseModel):
    """取消订单请求"""
    customer_code: str = Field(..., description="客户编码")
    bill_code: str = Field(..., description="运单号")
    cancel_reason: str = Field(default="customer cancel", description="取消原因")


class UpdateOrderRequest(BaseModel):
    """更新订单请求"""
    bill_code: str = Field(..., description="运单号")
    customer_code: str = Field(..., description="客户编码")
    custom_order_no: Optional[str] = Field(default=None, description="客户订单号")
    sender: Optional[SenderInfo] = Field(default=None, description="发件人信息")
    receiver: Optional[ReceiverInfo] = Field(default=None, description="收件人信息")
    parcel: Optional[ParcelInfo] = Field(default=None, description="包裹信息")
    items: Optional[List[ItemInfo]] = Field(default=None, description="商品列表")
    service: Optional[ServiceOptions] = Field(default=None, description="服务选项")


# ========== API 端点 ==========

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "service": "SpeedAF API Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": int(time.time())}


@app.post("/api/order/create", summary="创建订单")
async def create_order(request: CreateOrderRequest):
    """
    创建物流订单
    
    - **custom_order_no**: 客户订单号（唯一）
    - **customer_code**: 客户编码
    - **sender**: 发件人信息
    - **receiver**: 收件人信息
    - **parcel**: 包裹信息
    - **items**: 商品列表
    - **service**: 服务选项（可选）
    """
    try:
        # 使用 OrderBuilder 构建订单
        builder = (OrderBuilder()
                   .set_custom_order_no(request.custom_order_no)
                   .set_customer_code(request.customer_code)
                   .set_sender(
                       name=request.sender.name,
                       mobile=request.sender.mobile,
                       address=request.sender.address,
                       country_code=request.sender.country_code,
                       company_name=request.sender.company_name,
                       phone=request.sender.phone,
                       email=request.sender.email
                   )
                   .set_receiver(
                       name=request.receiver.name,
                       mobile=request.receiver.mobile,
                       address=request.receiver.address,
                       country_code=request.receiver.country_code,
                       company_name=request.receiver.company_name,
                       phone=request.receiver.phone,
                       email=request.receiver.email
                   )
                   .set_parcel_info(
                       weight=request.parcel.weight,
                       volume=request.parcel.volume,
                       length=request.parcel.length,
                       width=request.parcel.width,
                       height=request.parcel.height,
                       piece=request.parcel.piece
                   ))
        
        # 添加商品
        for item in request.items:
            builder.add_item(
                goods_name=item.goods_name,
                goods_qty=item.goods_qty,
                goods_value=item.goods_value,
                goods_weight=item.goods_weight,
                goods_name_dialect=item.goods_name_dialect,
                goods_type=item.goods_type,
                sku=item.sku
            )
        
        # 设置服务选项
        if request.service:
            builder.set_service_options(
                delivery_type=request.service.delivery_type,
                pay_method=request.service.pay_method,
                parcel_type=request.service.parcel_type,
                remark=request.service.remark
            )
        else:
            builder.set_service_options()
        
        order_data = builder.build()
        
        # 调用 SpeedAF API
        result = speedaf_api.create_order(order_data)
        
        return {
            "success": True,
            "data": result,
            "message": "订单创建成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/track/query", summary="查询物流轨迹")
async def query_track(request: TrackQueryRequest):
    """
    查询物流轨迹
    
    - **mail_no_list**: 运单号列表
    """
    try:
        result = speedaf_api.query_track(request.mail_no_list)
        
        return {
            "success": True,
            "data": result,
            "message": "查询成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/order/cancel", summary="取消订单")
async def cancel_order(request: CancelOrderRequest):
    """
    取消订单
    
    - **customer_code**: 客户编码
    - **bill_code**: 运单号
    - **cancel_reason**: 取消原因
    """
    try:
        result = speedaf_api.cancel_order(
            customer_code=request.customer_code,
            bill_code=request.bill_code,
            cancel_reason=request.cancel_reason
        )
        
        return {
            "success": True,
            "data": result,
            "message": "取消请求已提交"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/order/update", summary="更新订单")
async def update_order(request: UpdateOrderRequest):
    """
    更新订单信息
    
    - **bill_code**: 运单号（必填）
    - **customer_code**: 客户编码（必填）
    - 其他字段为可选，只更新提供的字段
    """
    try:
        # 构建更新数据
        update_data = {
            "billCode": request.bill_code,
            "customerCode": request.customer_code
        }
        
        if request.custom_order_no:
            update_data["customOrderNo"] = request.custom_order_no
        
        if request.sender:
            update_data.update({
                "sendName": request.sender.name,
                "sendMobile": request.sender.mobile,
                "sendAddress": request.sender.address,
                "sendCountryCode": request.sender.country_code
            })
        
        if request.receiver:
            update_data.update({
                "acceptName": request.receiver.name,
                "acceptMobile": request.receiver.mobile,
                "acceptAddress": request.receiver.address,
                "acceptCountryCode": request.receiver.country_code
            })
        
        if request.parcel:
            update_data["parcelWeight"] = request.parcel.weight
            if request.parcel.volume:
                update_data["parcelVolume"] = request.parcel.volume
        
        if request.items:
            update_data["itemList"] = [
                {
                    "goodsName": item.goods_name,
                    "goodsQTY": item.goods_qty,
                    "goodsValue": item.goods_value,
                    "goodsWeight": item.goods_weight
                }
                for item in request.items
            ]
        
        if request.service:
            update_data["remark"] = request.service.remark
        
        result = speedaf_api.update_order(update_data)
        
        return {
            "success": True,
            "data": result,
            "message": "订单更新成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(app, host="0.0.0.0", port=8000)
    
if __name__ == "__main__":
    import uvicorn
    import os
    
    # 读取 Zeabur 的 PORT 环境变量，如果没有则默认 8080
    port = int(os.getenv("PORT", 8080))
    print(f"Starting server on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
