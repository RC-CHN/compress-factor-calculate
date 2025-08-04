import numpy as np
from constants import *

def calculate_z_factor_optimized(T, P0, x, max_iterations=1000000, tolerance=0.00001):
    """
    根据 AGA8-92DC 模型计算天然气压缩因子Z (优化Numpy实现)。
    此版本旨在通过减少大型中间矩阵的创建来优化性能。
    """
    print("开始优化版 Numpy 计算...")

    # Part 1: 计算第二维利系数 B (混合模式)
    B_calc = 0.0
    for n in range(18):
        ZJCS = T**(-u[n])
        sum_val = 0
        for i in range(N):
            for j in range(N):
                Eij = Ex[i, j] * np.sqrt(E[i] * E[j])
                Gij = Gx[i, j] * (G[i] + G[j]) / 2
                
                Bij = ((Gij + 1 - g[n])**g[n]) * \
                      ((Q[i] * Q[j] + 1 - q[n])**q[n]) * \
                      ((np.sqrt(F[i] * F[j]) + 1 - f[n])**f[n]) * \
                      ((S[i] * S[j] + 1 - s[n])**s[n]) * \
                      ((W[i] * W[j] + 1 - w[n])**w[n])
                
                sum_val += x[i] * x[j] * Bij * (Eij**u[n]) * ((K[i] * K[j])**1.5)
        B_calc += a[n] * ZJCS * sum_val

    print(f"计算出的第二维利系数 B = {B_calc}")

    # Part 2: 计算 Cn 所需的中间变量 (与原版Numpy相同)
    x_outer = np.outer(x, x)
    F0 = np.sum(x**2 * F)
    Q0 = np.sum(x * Q)
    sum1_G = np.sum(x * G)
    sum2_E = np.sum(x * E**2.5)

    G0_term = np.triu(x_outer * (Gx - 1) * np.add.outer(G, G), k=1)
    G0 = sum1_G + np.sum(G0_term)

    U0_term = np.triu(x_outer * (Ux**5 - 1) * (np.outer(E, E)**2.5), k=1)
    U0 = (sum2_E**2 + np.sum(U0_term))**0.2

    print("中间变量计算完成: F0, Q0, G0, U0")

    # Part 3: 计算 K0
    sum1_K = np.sum(x * K**2.5)
    sum2_K_term = np.triu(x_outer * (Kx**5 - 1) * (np.outer(K, K)**2.5), k=1)
    K0 = (sum1_K**2 + 2 * np.sum(sum2_K_term))**0.2
    print(f"K0 计算完成: K0 = {K0}")

    # Part 4 & 5: 迭代计算压力 P
    pm = 0.01
    P = 0.0
    
    SUM1 = 0
    for n in range(12, 18):
        Cn = a[n] * ((G0 + 1 - g[n])**g[n]) * \
             (((Q0**2) + 1 - q[n])**q[n]) * \
             ((F0 + 1 - f[n])**f[n]) * \
             (U0**u[n]) * (T**(-u[n]))
        SUM1 += Cn

    print("开始压力迭代计算...")
    iteration_count = 0

    while abs(P - P0) >= tolerance and iteration_count < max_iterations:
        pm += 0.000001
        pr = (K0**3) * pm
        
        SUM2 = 0
        for n in range(12, 58):
            Cn = a[n] * ((G0 + 1 - g[n])**g[n]) * \
                 (((Q0**2) + 1 - q[n])**q[n]) * \
                 ((F0 + 1 - f[n])**f[n]) * \
                 (U0**u[n]) * (T**(-u[n]))
            
            term = (b[n] - c[n] * k[n] * (pr**k[n])) * (pr**b[n]) * np.exp(-c[n] * (pr**k[n]))
            SUM2 += Cn * term
            
        P = pm * R * T * (1 + B_calc * pm - pr * SUM1 + SUM2)
        iteration_count += 1

    if iteration_count == max_iterations:
        print("警告: 已达到最大迭代次数，结果可能不准确。")
    else:
        print(f"迭代完成，共 {iteration_count} 次。")

    # Part 6: 计算最终结果
    Z = P0 / (pm * R * T)
    M0 = np.sum(x * M)
    p_density = M0 * pm

    print("\n--- 计算结果 ---")
    print(f"Z={Z:.6f},pm={pm:.3f},pr={pr:.3f},p={p_density:.3f}")
    return Z, pm, pr, p_density

if __name__ == '__main__':
    # 默认参数
    T_in = 293.15
    P0_in = 0.101325
    x_in = np.array([0.961651, 0.008606, 0.004567, 0.01998, 0.003859, 0,
                     0, 0, 0, 0, 0, 0.000950, 0, 0.000138, 0.000249, 0, 0, 0, 0, 0, 0])
    calculate_z_factor_optimized(T_in, P0_in, x_in)