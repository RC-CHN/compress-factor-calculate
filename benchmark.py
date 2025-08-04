import time
import numpy as np
from calculator import calculate_z_factor
from calculator_pure import calculate_z_factor_pure
from calculator_optimized import calculate_z_factor_optimized

def run_benchmark(T, P0, x, max_iterations, tolerance):
    """
    运行并比较三个版本计算函数的性能：
    1. 原始 Numpy 版本
    2. 纯 Python 版本
    3. 优化版 Numpy 版本
    """
    print(f"--- 开始性能基准测试 (最大迭代: {max_iterations}, 精度: {tolerance}) ---")

    # 测试原始 Numpy 版本
    print("\n[1] 正在运行原始 Numpy 版本...")
    start_time_numpy = time.time()
    z_numpy, _, _, _ = calculate_z_factor(T, P0, x, max_iterations, tolerance)
    end_time_numpy = time.time()
    duration_numpy = end_time_numpy - start_time_numpy
    print(f"原始 Numpy 版本计算结果 Z = {z_numpy}")
    print(f"原始 Numpy 版本执行时间: {duration_numpy:.6f} 秒")

    # 测试纯 Python 版本
    print("\n[2] 正在运行纯 Python 版本...")
    start_time_pure = time.time()
    z_pure, _, _, _ = calculate_z_factor_pure(T, P0, x, max_iterations, tolerance)
    end_time_pure = time.time()
    duration_pure = end_time_pure - start_time_pure
    print(f"纯 Python 版本计算结果 Z = {z_pure}")
    print(f"纯 Python 版本执行时间: {duration_pure:.6f} 秒")

    # 测试优化版 Numpy 版本
    print("\n[3] 正在运行优化版 Numpy 版本...")
    start_time_optimized = time.time()
    z_optimized, _, _, _ = calculate_z_factor_optimized(T, P0, x, max_iterations, tolerance)
    end_time_optimized = time.time()
    duration_optimized = end_time_optimized - start_time_optimized
    print(f"优化版 Numpy 版本计算结果 Z = {z_optimized}")
    print(f"优化版 Numpy 版本执行时间: {duration_optimized:.6f} 秒")

    # 性能对比
    print("\n--- 最终性能对比 ---")
    durations = {
        "原始 Numpy": duration_numpy,
        "纯 Python": duration_pure,
        "优化版 Numpy": duration_optimized
    }
    
    sorted_versions = sorted(durations.items(), key=lambda item: item[1])
    
    print("性能排名:")
    for i, (version, duration) in enumerate(sorted_versions):
        print(f"{i+1}. {version}: {duration:.6f} 秒")

    fastest_version, fastest_time = sorted_versions[0]
    slowest_version, slowest_time = sorted_versions[-1]

    if fastest_time > 0:
        speedup = slowest_time / fastest_time
        print(f"\n最快的版本 ({fastest_version}) 相比最慢的版本 ({slowest_version}) 快了 {speedup:.2f} 倍。")

if __name__ == '__main__':
    # 可配置的输入参数
    T_in = 293.15
    P0_in = 0.101325
    x_in = np.array([0.961651, 0.008606, 0.004567, 0.01998, 0.003859, 0,
                     0, 0, 0, 0, 0, 0.000950, 0, 0.000138, 0.000249, 0, 0, 0, 0, 0, 0])
    
    # 运行多组测试
    tolerances = [1e-5, 1e-7, 1e-9]
    max_iter = 500000 # 设置一个足够大的迭代上限

    for tol in tolerances:
        run_benchmark(T_in, P0_in, x_in, max_iter, tol)
        print("\n" + "="*70 + "\n")