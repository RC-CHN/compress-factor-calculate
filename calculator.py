import numpy as np
import constants as const

def calculate_B(T, x, N):
    """
    计算第二维利系数 B (对应 AGA8-92DC 方程 (3))

    Args:
        T (float): 温度 (K)
        x (np.array): 各组分的摩尔分数数组
        N (int): 组分数量

    Returns:
        float: 第二维利系数 B
    """
    B = 0.0
    
    # 预先计算 Eij 和 Gij 矩阵，避免在主循环中重复计算
    Eij = const.Ex * np.sqrt(np.outer(const.E, const.E))
    Gij = const.Gx * (np.add.outer(const.G, const.G) / 2)
    
    # K(i)*K(j) 的外积
    K_prod = np.outer(const.K, const.K)

    for n in range(18): # n 从 0 到 17，对应 MATLAB 的 1 到 18
        ZJCS = T ** (-const.u[n])
        
        # 使用 NumPy 的向量化操作代替内层循环
        Bij = (
            (Gij + 1 - const.g[n]) ** const.g[n] *
            (np.outer(const.Q, const.Q) + 1 - const.q[n]) ** const.q[n] *
            (np.sqrt(np.outer(const.F, const.F)) + 1 - const.f[n]) ** const.f[n] *
            (np.outer(const.S, const.S) + 1 - const.s[n]) ** const.s[n] *
            (np.outer(const.W, const.W) + 1 - const.w[n]) ** const.w[n]
        )
        
        term_matrix = Bij * (Eij ** const.u[n]) * (K_prod ** 1.5)
        
        # x(i)*x(j) 的外积
        x_prod = np.outer(x, x)
        
        # 计算总和
        sum_val = np.sum(x_prod * term_matrix)
        
        B += const.a[n] * ZJCS * sum_val
        
    return B


def calculate_intermediate_params(x, N):
    """
    计算混合物参数 F0, Q0, G0, U0 (对应 AGA8-92DC 方程 (5) 到 (8))

    Args:
        x (np.array): 各组分的摩尔分数数组
        N (int): 组分数量

    Returns:
        tuple: 包含 F0, Q0, G0, U0 的元组
    """
    F0 = np.sum(x**2 * const.F)
    Q0 = np.sum(x * const.Q)
    
    # G0 的计算
    sum1_G0 = np.sum(x * const.G)
    sum2_G0 = 0.0
    # 使用 np.triu_indices 来获取上三角矩阵的索引，避免重复计算和 i=j 的情况
    for i, j in zip(*np.triu_indices(N, k=1)):
        sum2_G0 += x[i] * x[j] * (const.Gx[i, j] - 1) * (const.G[i] + const.G[j])
    G0 = sum1_G0 + sum2_G0

    # U0 的计算
    sum1_U0 = np.sum(x * const.E**2.5)**2
    sum2_U0 = 0.0
    for i, j in zip(*np.triu_indices(N, k=1)):
        sum2_U0 += x[i] * x[j] * (const.Ux[i, j]**5 - 1) * ((const.E[i] * const.E[j])**2.5)
    U0 = (sum1_U0 + sum2_U0)**0.2 # 对应 (sum^2 + U0)^0.2

    return F0, Q0, G0, U0


def calculate_K0(x, N):
    """
    计算混合摩尔体积参数 K0 (对应 AGA8-92DC 方程 (4))

    Args:
        x (np.array): 各组分的摩尔分数数组
        N (int): 组分数量

    Returns:
        float: 混合摩尔体积参数 K0
    """
    sum1 = np.sum(x * const.K**2.5)**2
    
    sum2 = 0.0
    for i, j in zip(*np.triu_indices(N, k=1)):
        sum2 += x[i] * x[j] * (const.Kx[i, j]**5 - 1) * ((const.K[i] * const.K[j])**2.5)
        
    K0 = (sum1 + 2 * sum2)**0.2
    return K0


def calculate_properties(T, P0, x, N, tolerance=1e-5, max_iterations=1000):
    """
    通过迭代计算压力，求解压缩因子 Z 和其他气体性质

    Args:
        T (float): 温度 (K)
        P0 (float): 初始压力 (MPa)
        x (np.array): 各组分的摩尔分数数组
        N (int): 组分数量
        tolerance (float): 压力收敛容差
        max_iterations (int): 最大迭代次数

    Returns:
        dict: 包含 Z, P, pm, pr, p 的结果字典，如果未收敛则返回 None
    """
    # 1. 调用辅助函数计算不变量
    B = calculate_B(T, x, N)
    F0, Q0, G0, U0 = calculate_intermediate_params(x, N)
    K0 = calculate_K0(x, N)

    # 2. 计算 Cn (n=13-18) 的和 SUM1
    SUM1 = 0
    # n 从 12 到 17 (对应 MATLAB 13 到 18)
    for n in range(12, 18):
        Cn = const.a[n] * \
             ((G0 + 1 - const.g[n])**const.g[n]) * \
             (((Q0**2) + 1 - const.q[n])**const.q[n]) * \
             ((F0 + 1 - const.f[n])**const.f[n]) * \
             (U0**const.u[n]) * \
             (T**(-const.u[n]))
        SUM1 += Cn

    # 3. 迭代求解 pm 和 P
    pm = 0.01  # 初始摩尔密度
    P = 0
    
    for _ in range(max_iterations):
        pr = (K0**3) * pm  # 对比密度

        # 计算 SUM2
        SUM2 = 0
        # n 从 12 到 57 (对应 MATLAB 13 到 58)
        for n in range(12, 58):
            Cn = const.a[n] * \
                 ((G0 + 1 - const.g[n])**const.g[n]) * \
                 (((Q0**2) + 1 - const.q[n])**const.q[n]) * \
                 ((F0 + 1 - const.f[n])**const.f[n]) * \
                 (U0**const.u[n]) * \
                 (T**(-const.u[n]))
            
            term = (const.b[n] - const.c[n] * const.k[n] * (pr**const.k[n])) * \
                   (pr**const.b[n]) * np.exp(-const.c[n] * (pr**const.k[n]))
            SUM2 += Cn * term

        # 计算压力 P
        P = pm * const.R * T * (1 + B * pm - pr * SUM1 + SUM2)

        if abs(P - P0) <= tolerance:
            # 4. 计算最终结果
            Z = P0 / (pm * const.R * T)
            M0 = np.sum(x * const.M)
            rho = M0 * pm  # 质量密度

            return {
                "Z": Z,
                "P_calculated": P,
                "pm": pm,
                "pr": pr,
                "rho": rho
            }
        
        # 更新 pm 以进行下一次迭代 (这里使用一个简单的增量，实际应用中可能有更复杂的求解器)
        # MATLAB 代码中是 pm = pm + 0.000001，这是一个非常简单的线性搜索
        pm += 0.000001

    print("Warning: Calculation did not converge within max iterations.")
    return None
