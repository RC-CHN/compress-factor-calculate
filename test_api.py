import requests
import json
import numpy as np

# 从我们项目中的模块导入，用于本地计算以获取预期结果
from calculator import calculate_z_factor_bisection

def run_test():
    """
    使用 gui.py 的默认数据测试 API，并与本地直接计算的结果进行比较。
    """
    print("--- 开始 API 一致性测试 ---")

    # --- 1. 从 gui.py 获取默认数据 ---
    # 这些值直接从 gui.py 中复制而来
    gas_components_internal = [
        "CH4", "N2", "CO2", "C2H6", "C3H8", "H2O", "H2S", "H2", "CO", "O2",
        "i-C4H10", "n-C4H10", "i-C5H12", "n-C5H12", "n-C6H14", "n-C7H16",
        "n-C8H18", "n-C9H20", "n-C10H22", "He", "Ar"
    ]
    default_x = np.array([
        0.961651, 0.008606, 0.004567, 0.01998, 0.003859, 0, 0, 0, 0, 0, 0,
        0.000950, 0, 0.000138, 0.000249, 0, 0, 0, 0, 0, 0
    ])
    T_work = 350.0  # K
    P_work_mpa = 10.0  # MPa

    # --- 2. 本地直接计算 (获取预期结果) ---
    print("\n[步骤 1] 直接调用本地计算核心以获取预期结果...")
    try:
        # 确保摩尔分数总和为1
        if abs(np.sum(default_x) - 1.0) > 1e-9:
            print(f"警告: 原始摩尔分数总和为 {np.sum(default_x)}，进行归一化。")
            default_x /= np.sum(default_x)

        z_expected, _, _, _, _ = calculate_z_factor_bisection(T=T_work, P0=P_work_mpa, x=default_x)
        print(f"✅ 本地直接计算 (预期 Z 因子): {z_expected:.8f}")
    except Exception as e:
        print(f"❌ 本地计算失败: {e}")
        return

    # --- 3. 准备 API 请求数据 ---
    print("\n[步骤 2] 准备发送到 API 的请求...")
    # API 使用的名称映射 (与 api.py 中一致)
    INTERNAL_TO_API_NAME_MAP = {
        'CH4': 'Methane', 'N2': 'Nitrogen', 'CO2': 'CarbonDioxide', 'C2H6': 'Ethane',
        'C3H8': 'Propane', 'H2O': 'Water', 'H2S': 'HydrogenSulfide', 'H2': 'Hydrogen',
        'CO': 'CarbonMonoxide', 'O2': 'Oxygen', 'i-C4H10': 'Isobutane', 'n-C4H10': 'Butane',
        'i-C5H12': 'Isopentane', 'n-C5H12': 'Pentane', 'n-C6H14': 'Hexane',
        'n-C7H16': 'Heptane', 'n-C8H18': 'Octane', 'n-C9H20': 'Nonane',
        'n-C10H22': 'Decane', 'He': 'Helium', 'Ar': 'Argon'
    }

    base_components_api = {}
    hydrogen_fraction = 0.0

    for i, comp_internal in enumerate(gas_components_internal):
        fraction = default_x[i]
        if fraction > 0:
            # API 的逻辑是将氢气分离出来处理
            if comp_internal == 'H2':
                hydrogen_fraction = fraction
            else:
                api_name = INTERNAL_TO_API_NAME_MAP.get(comp_internal)
                if api_name:
                    base_components_api[api_name] = fraction
    
    # API 期望压力单位是 kPa
    p_kpa = P_work_mpa * 1000.0

    api_request_data = {
        "base_components": base_components_api,
        "hydrogen_fraction": hydrogen_fraction,
        "T": T_work,
        "P_kPa": p_kpa
    }

    print("✅ API 请求数据准备完成。")
    print("请求体内容:")
    print(json.dumps(api_request_data, indent=2))

    # --- 4. 调用 API ---
    print("\n[步骤 3] 调用 FastAPI 服务...")
    api_url = "http://127.0.0.1:8000/calculate"
    # 明确禁用代理，防止系统代理设置干扰本地请求
    proxies = {
        "http": None,
        "https": None,
    }
    try:
        response = requests.post(api_url, json=api_request_data, timeout=30, proxies=proxies)
        response.raise_for_status()  # 如果状态码不是 2xx，则引发异常

        response_data = response.json()
        z_api = response_data.get("compression_factor")

        print(f"✅ API 调用成功。")
        print("API 响应内容:")
        print(json.dumps(response_data, indent=2))
        
        if z_api is not None:
            print(f"\nAPI 返回的 Z 因子: {z_api:.8f}")
        else:
            print("❌ API 响应中未找到 'compression_factor'。")

    except requests.exceptions.RequestException as e:
        print(f"❌ API 调用失败: {e}")
        print("请确保您已经通过以下命令启动了 API 服务:")
        print("uvicorn api:app --reload --host 0.0.0.0 --port 8000")
        return

    # --- 5. 比较结果 ---
    print("\n--- 最终一致性检查 ---")
    if z_api is not None:
        diff = abs(z_expected - z_api)
        print(f"预期 Z 因子: {z_expected:.8f}")
        print(f"API  Z 因子: {z_api:.8f}")
        print(f"绝对差值:   {diff:.10f}")
        if diff < 1e-7:
            print("\n结论: ✅ 测试通过！API 返回结果与本地直接计算结果高度一致。")
        else:
            print("\n结论: ❌ 测试失败！结果存在显著差异。")
    else:
        print("无法进行比较，因为未能从 API 获取 Z 因子。")


if __name__ == "__main__":
    run_test()