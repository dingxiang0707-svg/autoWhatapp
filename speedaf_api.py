"""
速达非API接口实现
包含下单、轨迹查询、取消订单、更新订单接口
"""

import time
import json
import requests
from typing import Dict, Any, Optional, List
from tool import triple_des_encrypt, triple_des_decrypt


class SpeedAFAPI:
    """速达非API接口类"""
    
    def __init__(self, app_code: str, secret_key: str, base_url: str = "https://uat-api.speedaf.com"):
        """
        初始化API客户端
        
        Args:
            app_code: 应用编码，需要找速达非对接人获取
            secret_key: 密钥，需要找速达非对接人获取
            base_url: API基础URL，默认为正式环境
        """
        self.app_code = app_code
        self.secret_key = secret_key
        self.base_url = base_url
        self.headers = {'Content-Type': 'text/plain'}
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送API请求的通用方法
        
        Args:
            endpoint: API端点
            data: 请求数据
            
        Returns:
            解密后的响应数据
        """
        timeline = str(int((time.time() + 0.5) * 1000))
        
        # triple_des_encrypt内部会自动添加sign并加密数据
        # sign生成规则: MD5(timeline + secretKey + data)
        encrypted_data = triple_des_encrypt(data, timeline)
        
        url = f"{self.base_url}{endpoint}?appCode={self.app_code}&timestamp={timeline}"
        
        try:
            response = requests.post(url, data=encrypted_data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success') and result.get('data'):
                # 解密响应数据
                decrypted_data = triple_des_decrypt(result['data'])
                return json.loads(decrypted_data.decode())
            else:
                raise Exception(f"API调用失败: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应数据解析失败: {str(e)}")
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        下单接口
        
        Args:
            order_data: 订单数据，包含发件人、收件人、货物信息等
            
        Returns:
            下单结果，包含运单号等信息
            
        Example:
            order_data = {
                "customOrderNo": "189795601",
                "customerCode": "860047",
                "sendName": "发件人姓名",
                "sendMobile": "发件人手机",
                "sendAddress": "发件人地址",
                "sendCountryCode": "CN",
                "acceptName": "收件人姓名",
                "acceptMobile": "收件人手机", 
                "acceptAddress": "收件人地址",
                "acceptCountryCode": "NG",
                "parcelWeight": 2.54,
                "parcelVolume": 1.52,
                "itemList": [
                    {
                        "goodsName": "商品名称",
                        "goodsQTY": 2,
                        "goodsValue": 190,
                        "goodsWeight": 1.45
                    }
                ],
                "deliveryType": "DE01",
                "payMethod": "PA01",
                "parcelType": "PT01"
            }
        """
        endpoint = "/open-api/express/order/createOrder"
        return self._make_request(endpoint, order_data)
    
    def query_track(self, mail_no_list: List[str]) -> Dict[str, Any]:
        """
        轨迹实时查询接口
        
        Args:
            mail_no_list: 运单号列表
            
        Returns:
            轨迹查询结果
            
        Example:
            mail_no_list = ["47234208672823", "47234208672824"]
        """
        endpoint = "/open-api/express/track/query"
        data = {"mailNoList": mail_no_list}
        return self._make_request(endpoint, data)
    
    def cancel_order(self, customer_code: str, bill_code: str, cancel_reason: str = "customer cancel") -> Dict[str, Any]:
        """
        取消订单接口
        
        Args:
            customer_code: 客户编码
            bill_code: 运单号
            cancel_reason: 取消原因
            
        Returns:
            取消结果
            
        Example:
            customer_code = "NG000660"
            bill_code = "NG0206830525525"
            cancel_reason = "customer cancel"
        """
        endpoint = "/open-api/express/order/cancelOrder"
        # 直接传数组，triple_des_encrypt会自动包装成 {"data": "...", "sign": "..."}
        data = [
            {
                "customerCode": customer_code,
                "billCode": bill_code,
                "cancelReason": cancel_reason
            }
        ]
        return self._make_request(endpoint, data)
    
    def update_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新订单接口
        
        Args:
            order_data: 完整的订单数据，格式与下单接口相同，必须包含customerCode和billCode
            
        Returns:
            更新结果
            
        Example:
            order_data = {
                "customerCode": "MA000027",
                "billCode": "47234208672823",
                "customOrderNo": "189795601",
                "sendName": "发件人姓名",
                "sendMobile": "发件人手机",
                "sendAddress": "发件人地址",
                "sendCountryCode": "CN",
                "acceptName": "收件人姓名",
                "acceptMobile": "收件人手机", 
                "acceptAddress": "收件人地址",
                "acceptCountryCode": "NG",
                "parcelWeight": 2.54,
                "parcelVolume": 1.52,
                "itemList": [
                    {
                        "goodsName": "商品名称",
                        "goodsQTY": 2,
                        "goodsValue": 190,
                        "goodsWeight": 1.45
                    }
                ],
                "deliveryType": "DE01",
                "payMethod": "PA01",
                "parcelType": "PT01",
                "remark": "订单已更新"
            }
        """
        endpoint = "/open-api/express/order/updateOrder"
        
        # 直接传数组，triple_des_encrypt会自动包装成 {"data": "...", "sign": "..."}
        data = [order_data]
        
        return self._make_request(endpoint, data)


class OrderBuilder:
    """订单构建器，用于方便地构建订单数据"""
    
    def __init__(self):
        self.order_data = {}
    
    def set_custom_order_no(self, custom_order_no: str):
        """设置客户订单号"""
        self.order_data["customOrderNo"] = custom_order_no
        return self
    
    def set_customer_code(self, customer_code: str):
        """设置客户编码"""
        self.order_data["customerCode"] = customer_code
        return self
    
    def set_sender(self, name: str, mobile: str, address: str, country_code: str = "CN",
                   company_name: str = "", phone: str = "", email: str = "",
                   province_code: str = "", province_name: str = "",
                   city_code: str = "", city_name: str = "",
                   district_code: str = "", district_name: str = "",
                   post_code: str = ""):
        """设置发件人信息"""
        self.order_data.update({
            "sendName": name,
            "sendMobile": mobile,
            "sendAddress": address,
            "sendCountryCode": country_code,
            "sendCompanyName": company_name,
            "sendPhone": phone,
            "sendMail": email,
            "sendProvinceCode": province_code,
            "sendProvinceName": province_name,
            "sendCityCode": city_code,
            "sendCityName": city_name,
            "sendDistrictCode": district_code,
            "sendDistrictName": district_name,
            "sendPostCode": post_code
        })
        return self
    
    def set_receiver(self, name: str, mobile: str, address: str, country_code: str,
                     company_name: str = "", phone: str = "", email: str = "",
                     province_code: str = "", province_name: str = "",
                     city_code: str = "", city_name: str = "",
                     district_code: str = "", district_name: str = "",
                     post_code: str = ""):
        """设置收件人信息"""
        self.order_data.update({
            "acceptName": name,
            "acceptMobile": mobile,
            "acceptAddress": address,
            "acceptCountryCode": country_code,
            "acceptCompanyName": company_name,
            "acceptPhone": phone,
            "acceptEmail": email,
            "acceptProvinceCode": province_code,
            "acceptProvinceName": province_name,
            "acceptCityCode": city_code,
            "acceptCityName": city_name,
            "acceptDistrictCode": district_code,
            "acceptDistrictName": district_name,
            "acceptPostCode": post_code
        })
        return self
    
    def set_parcel_info(self, weight: float, volume: float = None, length: int = None,
                        width: int = None, height: int = None, piece: int = 1):
        """设置包裹信息"""
        self.order_data.update({
            "parcelWeight": weight,
            "piece": piece
        })
        if volume is not None:
            self.order_data["parcelVolume"] = volume
        if length is not None:
            self.order_data["parcelLength"] = length
        if width is not None:
            self.order_data["parcelWidth"] = width
        if height is not None:
            self.order_data["parcelHigh"] = height
        return self
    
    def add_item(self, goods_name: str, goods_qty: int, goods_value: float,
                 goods_weight: float, goods_name_dialect: str = "",
                 goods_type: str = "IT02", battery: int = 0, bl_insure: int = 0,
                 duty_money: float = 0, goods_id: str = "", sku: str = "",
                 goods_material: str = "", goods_remark: str = "",
                 goods_rule: str = "", goods_unit_price: float = 0,
                 make_country: str = "", sale_path: str = "", unit: str = "",
                 goods_length: int = None, goods_width: int = None,
                 goods_height: int = None, goods_volume: float = None):
        """添加商品信息"""
        if "itemList" not in self.order_data:
            self.order_data["itemList"] = []
        
        item = {
            "goodsName": goods_name,
            "goodsNameDialect": goods_name_dialect or goods_name,
            "goodsQTY": goods_qty,
            "goodsValue": goods_value,
            "goodsWeight": goods_weight,
            "goodsType": goods_type,
            "battery": battery,
            "blInsure": bl_insure,
            "dutyMoney": duty_money,
            "goodsId": goods_id,
            "sku": sku,
            "goodsMaterial": goods_material,
            "goodsRemark": goods_remark,
            "goodsRule": goods_rule,
            "goodsUnitPrice": goods_unit_price,
            "makeCountry": make_country,
            "salePath": sale_path,
            "unit": unit
        }
        
        if goods_length is not None:
            item["goodsLength"] = goods_length
        if goods_width is not None:
            item["goodsWidth"] = goods_width
        if goods_height is not None:
            item["goodsHigh"] = goods_height
        if goods_volume is not None:
            item["goodsVolume"] = goods_volume
            
        self.order_data["itemList"].append(item)
        return self
    
    def set_service_options(self, delivery_type: str = "DE01", pay_method: str = "PA01",
                           parcel_type: str = "PT01", ship_type: str = "ST01",
                           transport_type: str = "TT01", platform_source: str = "TEST22",
                           cod_fee: float = 0, insure_price: float = 0,
                           shipping_fee: float = 0, remark: str = ""):
        """设置服务选项"""
        self.order_data.update({
            "deliveryType": delivery_type,
            "payMethod": pay_method,
            "parcelType": parcel_type,
            "shipType": ship_type,
            "transportType": transport_type,
            "platformSource": platform_source,
            "codFee": cod_fee,
            "insurePrice": insure_price,
            "shippingFee": shipping_fee,
            "remark": remark
        })
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建最终的订单数据"""
        # 计算总货物数量
        if "itemList" in self.order_data and self.order_data["itemList"]:
            total_qty = sum(item["goodsQTY"] for item in self.order_data["itemList"])
            self.order_data["goodsQTY"] = total_qty
        
        return self.order_data.copy()


# 使用示例和测试代码
if __name__ == "__main__":
    # 初始化API客户端
    api = SpeedAFAPI(
        app_code="11111111",
        secret_key="uYMGr8eU",
        base_url="https://uat-api.speedaf.com"  # UAT测试环境
    )
    
    # 使用OrderBuilder构建订单
    order = (OrderBuilder()
             .set_custom_order_no("TEST" + str(int(time.time())))
             .set_customer_code("MA000027")
             .set_sender(
                 name="张三",
                 mobile="13800138000", 
                 address="北京市朝阳区测试地址",
                 country_code="CN"
             )
             .set_receiver(
                 name="John Doe",
                 mobile="1778922222",
                 address="Lagos Test Address",
                 country_code="NG"
             )
             .set_parcel_info(weight=2.54, volume=1.52, piece=1)
             .add_item(
                 goods_name="测试商品",
                 goods_qty=2,
                 goods_value=190,
                 goods_weight=1.45
             )
             .set_service_options()
             .build())
    
    try:
        # 测试下单接口
        print("测试下单接口...")
        result = api.create_order(order)
        print("下单成功:", result)
        
        # 如果下单成功，测试其他接口
        if 'billCode' in result:
            bill_code = result['billCode']
            print(f"获得运单号: {bill_code}")
            
            # 测试轨迹查询
            print("\n测试轨迹查询接口...")
            track_result = api.query_track([bill_code])
            print("轨迹查询结果:", track_result)
            
            # 测试取消订单
            print("\n测试取消订单接口...")
            cancel_result = api.cancel_order("MA000027", bill_code, "customer cancel")
            print("取消订单结果:", cancel_result)
            
            # 测试更新订单
            print("\n测试更新订单接口...")
            # 构建完整的订单数据用于更新
            update_order_data = order.copy()
            update_order_data["billCode"] = bill_code
            update_order_data["acceptName"] = "Updated Name"
            update_order_data["remark"] = "订单已更新"
            
            update_result = api.update_order(update_order_data)
            print("更新订单结果:", update_result)
            
    except Exception as e:
        print(f"测试失败: {str(e)}")