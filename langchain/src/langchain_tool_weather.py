from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import requests
from colorama import Fore, Style
import sys
import json
from datetime import datetime, timedelta

class WeatherInput(BaseModel):
    """天气查询的输入参数"""
    city: str = Field(description="要查询天气的城市名称")
    days: Optional[int] = Field(default=1, description="查询未来几天的天气，默认为1天")

class WeatherTool(BaseTool):
    """天气查询工具"""
    name: str = "weather"
    description: str = "查询指定城市的天气情况"
    args_schema: Type[BaseModel] = WeatherInput
    
    def _run(self, city: str, days: int = 1) -> str:
        """执行天气查询"""
        try:
            # 使用OpenWeatherMap API
            api_key = "YOUR_OPENWEATHERMAP_API_KEY"  # 替换为您的OpenWeatherMap API key
            base_url = "http://api.openweathermap.org/data/2.5"
            
            # 获取城市坐标
            geocoding_url = f"{base_url}/weather"
            geocoding_params = {
                "q": city,
                "appid": api_key,
                "units": "metric",  # 使用摄氏度
                "lang": "zh_cn"     # 使用中文
            }
            
            print(f"{Fore.CYAN}正在获取{city}的天气信息...{Style.RESET_ALL}")
            print(f"请求URL: {geocoding_url}")
            print(f"请求参数: {geocoding_params}")
            
            response = requests.get(geocoding_url, params=geocoding_params)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                return f"解析天气信息响应失败：{str(e)}\n响应内容：{response.text}"
            
            if response.status_code != 200:
                return f"查询天气失败：{data.get('message', '未知错误')}"
            
            # 格式化天气信息
            weather_info = []
            
            # 当前天气
            current_weather = (
                f"当前天气：{data['weather'][0]['description']}\n"
                f"温度：{data['main']['temp']}°C\n"
                f"体感温度：{data['main']['feels_like']}°C\n"
                f"最高温度：{data['main']['temp_max']}°C\n"
                f"最低温度：{data['main']['temp_min']}°C\n"
                f"湿度：{data['main']['humidity']}%\n"
                f"风速：{data['wind']['speed']} m/s\n"
                f"{'-'*30}"
            )
            weather_info.append(current_weather)
            
            # 如果需要未来几天的预报
            if days > 1:
                forecast_url = f"{base_url}/forecast"
                forecast_params = {
                    "q": city,
                    "appid": api_key,
                    "units": "metric",
                    "lang": "zh_cn"
                }
                
                forecast_response = requests.get(forecast_url, params=forecast_params)
                forecast_data = forecast_response.json()
                
                if forecast_response.status_code == 200:
                    # 按日期分组预报数据
                    forecasts = {}
                    for item in forecast_data['list']:
                        date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                        if date not in forecasts:
                            forecasts[date] = []
                        forecasts[date].append(item)
                    
                    # 只取前days天的预报
                    for date in sorted(forecasts.keys())[:days]:
                        daily_forecast = forecasts[date]
                        # 取中午的预报作为当天的代表
                        noon_forecast = next((f for f in daily_forecast 
                                           if datetime.fromtimestamp(f['dt']).hour == 12), 
                                          daily_forecast[0])
                        
                        weather_info.append(
                            f"日期：{date}\n"
                            f"天气：{noon_forecast['weather'][0]['description']}\n"
                            f"温度：{noon_forecast['main']['temp']}°C\n"
                            f"最高温度：{noon_forecast['main']['temp_max']}°C\n"
                            f"最低温度：{noon_forecast['main']['temp_min']}°C\n"
                            f"湿度：{noon_forecast['main']['humidity']}%\n"
                            f"风速：{noon_forecast['wind']['speed']} m/s\n"
                            f"{'-'*30}"
                        )
            
            return "\n".join(weather_info)
            
        except Exception as e:
            import traceback
            return f"查询出错：{str(e)}\n详细错误信息：{traceback.format_exc()}"

    async def _arun(self, city: str, days: int = 1) -> str:
        """异步执行天气查询"""
        # 这里可以添加异步实现
        return self._run(city, days)

def main():
    """主函数"""
    try:
        # 创建天气查询工具
        weather_tool = WeatherTool()
        
        # 测试天气查询
        print(f"{Fore.CYAN}开始测试天气查询...{Style.RESET_ALL}")
        
        # 查询北京未来3天的天气
        result = weather_tool.run({"city": "北京", "days": 3})
        print(f"\n{Fore.GREEN}查询结果：{Style.RESET_ALL}")
        print(result)
        
    except Exception as e:
        print(f"{Fore.RED}错误：程序运行出错 - {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
