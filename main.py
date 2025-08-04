import numpy as np
import calculator
from constants import T, P0, x, N  # 从常量模块导入所有需要的数据

def main():
    """
    主函数，用于执行天然气压缩因子的计算
    """
    print("计算开始...")
    print(f"输入条件 (来自 constants.py):")
    print(f"  温度 = {T} K")
    print(f"  压力 = {P0} MPa")
    print(f"  气体组分 (摩尔分数): \n{x}")
    print("-" * 30)

    # 2. 调用计算函数
    # N 也是从 constants.py 导入的
    results = calculator.calculate_properties(T, P0, x, N)

    # 3. 打印结果
    if results:
        print("计算完成!")
        print(f"压缩因子 (Z): {results['Z']:.6f}")
        print(f"计算收敛压力 (P): {results['P_calculated']:.6f} MPa")
        print(f"摩尔密度 (pm): {results['pm']:.6f} mol/L")
        print(f"对比密度 (pr): {results['pr']:.6f}")
        print(f"质量密度 (rho): {results['rho']:.6f} kg/m^3")
    else:
        print("计算未能收敛，无法获取结果。")

if __name__ == "__main__":
    main()