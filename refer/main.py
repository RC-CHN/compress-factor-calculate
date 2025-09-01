import CoolProp.CoolProp as CP
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict

# --- 计算逻辑从脚本移植 ---

def calculate_compression_factor(components: Dict[str, float], T: float, P_kPa: float) -> float:
    """
    使用GERG-2008方程计算天然气混合物的压缩因子。
    
    参数:
    components: dict, 组分名称（标准名称）和摩尔分数的字典
    T: float, 温度（单位：K）
    P_kPa: float, 压力（单位：kPa）
    
    返回:
    Z: float, 压缩因子
    """
    # 将kPa转换为Pa（CoolProp需要Pa作为单位）
    P_Pa = P_kPa * 1000.0
    
    # 构建组分列表和摩尔分数列表
    fluid_names = list(components.keys())
    fractions = list(components.values())
    
    # 创建混合物的抽象状态对象，使用HEOS后端
    mixture = CP.AbstractState("HEOS", "&".join(fluid_names))
    
    # 设置摩尔分数
    mixture.set_mole_fractions(fractions)
    
    # 设置温度和压力
    mixture.update(CP.PT_INPUTS, P_Pa, T)
    
    # 获取压缩因子
    Z = mixture.compressibility_factor()
    return Z

def adjust_compositions_with_hydrogen(base_components: Dict[str, float], hydrogen_fraction: float) -> Dict[str, float]:
    """
    调整组分比例以包含氢气
    """
    if hydrogen_fraction <= 0:
        return base_components
    
    # 计算基础组分的总和
    base_total = sum(base_components.values())
    
    # 如果基础组分总和为0，则全部为氢气
    if base_total == 0 and hydrogen_fraction > 0:
        return {'Hydrogen': hydrogen_fraction}
    
    # 调整基础组分的比例
    scale_factor = (1.0 - hydrogen_fraction) / base_total
    adjusted_components = {}
    
    for comp, frac in base_components.items():
        adjusted_components[comp] = frac * scale_factor
    
    # 添加氢气
    adjusted_components['Hydrogen'] = hydrogen_fraction
    
    return adjusted_components

# --- FastAPI 应用定义 ---

app = FastAPI(
    title="GERG-2008 Compression Factor Calculator",
    description="一个使用CoolProp和GERG-2008方程计算含氢天然气压缩因子的API。",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic 模型定义 ---

class CalculationRequest(BaseModel):
    base_components: Dict[str, float] = Field(..., example={"Methane": 0.9, "Ethane": 0.1})
    hydrogen_fraction: float = Field(0.0, ge=0.0, le=1.0, description="氢气的摩尔分数")
    T: float = Field(..., example=288.15, description="温度 (K)")
    P_kPa: float = Field(..., example=1013.25, description="压力 (kPa)")

class CalculationResponse(BaseModel):
    final_components: Dict[str, float]
    compression_factor: float

# --- API 端点定义 ---

@app.post("/calculate", response_model=CalculationResponse)
def calculate(request: CalculationRequest):
    """
    计算给定组分、温度和压力下的气体压缩因子。

    - **base_components**: 基础天然气组分及其摩尔分数（不含氢气）。
    - **hydrogen_fraction**: 要添加的氢气的摩尔分数。
    - **T**: 绝对温度 (Kelvin)。
    - **P_kPa**: 绝对压力 (kPa)。

    API会根据氢气分数自动调整组分，然后使用GERG-2008方程计算压缩因子。

    **可用基础组分参考:**

    | CoolProp 标准名称 | 中文名称 | 分子式 |
    | :--- | :--- | :--- |
    | Methane | 甲烷 | CH₄ |
    | Nitrogen | 氮气 | N₂ |
    | CarbonDioxide | 二氧化碳 | CO₂ |
    | Ethane | 乙烷 | C₂H₆ |
    | Propane | 丙烷 | C₃H₈ |
    | Water | 水 | H₂O |
    | HydrogenSulfide | 硫化氢 | H₂S |
    | CarbonMonoxide | 一氧化碳 | CO |
    | Oxygen | 氧气 | O₂ |
    | Isobutane | 异丁烷 | C₄H₁₀ |
    | Butane | 正丁烷 | C₄H₁₀ |
    | Isopentane | 异戊烷 | C₅H₁₂ |
    | Pentane | 正戊烷 | C₅H₁₂ |
    | Hexane | 己烷 | C₆H₁₄ |
    | Heptane | 庚烷 | C₇H₁₆ |
    | Octane | 辛烷 | C₈H₁₈ |
    | Nonane | 壬烷 | C₉H₂₀ |
    | Decane | 癸烷 | C₁₀H₂₂ |
    | Helium | 氦气 | He |
    | Argon | 氩气 | Ar |
    """
    # 调整组分以包含氢气
    final_components = adjust_compositions_with_hydrogen(request.base_components, request.hydrogen_fraction)
    
    # 计算压缩因子
    compression_factor = calculate_compression_factor(final_components, request.T, request.P_kPa)
    
    return {
        "final_components": final_components,
        "compression_factor": compression_factor,
    }