import numpy as np
from constants import *

def calculate_z_factor():
    """
    根据 AGA8-92DC 模型计算天然气压缩因子Z。
    此函数将MATLAB脚本的逻辑翻译为Python。
    """
    print("开始计算...")

    # Part 1: 计算第二维利系数 B
    # 使用向量化操作替代双重 for 循环
    B_calc = 0.0
    E_outer = np.sqrt(np.outer(E, E))
    G_outer = np.add.outer(G, G) / 2
    Q_outer = np.outer(Q, Q)
    F_outer_sqrt = np.sqrt(np.outer(F, F))
    S_outer = np.outer(S, S)
    W_outer = np.outer(W, W)
    K_outer_pow1_5 = np.outer(K, K)**1.5
    x_outer = np.outer(x, x)

    for n in range(18):
        ZJCS = T**(-u[n])
        Eij = Ex * E_outer
        Gij = Gx * G_outer
        
        Bij = ((Gij + 1 - g[n])**g[n]) * \
              ((Q_outer + 1 - q[n])**q[n]) * \
              ((F_outer_sqrt + 1 - f[n])**f[n]) * \
              ((S_outer + 1 - s[n])**s[n]) * \
              ((W_outer + 1 - w[n])**w[n])
        
        sum_val = np.sum(x_outer * Bij * (Eij**u[n]) * K_outer_pow1_5)
        B_calc += a[n] * ZJCS * sum_val
    
    # 在常量文件中 B=0, 这里我们使用计算出的值
    # 如果需要保留文件中的B，注释掉下面这行
    # B = B_calc

    print(f"计算出的第二维利系数 B = {B_calc}")

    # Part 2: 计算 Cn 所需的中间变量
    F0 = np.sum(x**2 * F)
    Q0 = np.sum(x * Q)
    sum1_G = np.sum(x * G)
    sum2_E = np.sum(x * E**2.5)

    # 使用上三角矩阵求和来替代双重 for 循环
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
    pm = 0.01  # 摩尔密度初始猜测值
    P = 0.0    # 压力初始值

    # 计算 SUM1 (n=13 to 18)
    SUM1 = 0
    # MATLAB n=13:18 对应 Python range(12, 18)
    for n in range(12, 18):
        Cn = a[n] * ((G0 + 1 - g[n])**g[n]) * \
             (((Q0**2) + 1 - q[n])**q[n]) * \
             ((F0 + 1 - f[n])**f[n]) * \
             (U0**u[n]) * (T**(-u[n]))
        SUM1 += Cn
    
    print("开始压力迭代计算...")
    iteration_count = 0
    max_iterations = 1000000 # 防止死循环

    while abs(P - P0) >= 0.00001 and iteration_count < max_iterations:
        pm += 0.000001
        pr = (K0**3) * pm
        
        SUM2 = 0
        # MATLAB n=13:58 对应 Python range(12, 58)
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

    # 输出结果
    print("\n--- 计算结果 ---")
    print(f"Z={Z:.6f},pm={pm:.3f},pr={pr:.3f},p={p_density:.3f}")
    return Z, pm, pr, p_density

if __name__ == '__main__':
    calculate_z_factor()