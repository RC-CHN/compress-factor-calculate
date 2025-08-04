import math
from constants import *

def calculate_z_factor_linear_scan(T, P0, x, step=0.000001, max_iterations=1000000, tolerance=0.00001, log_callback=None):
    """
    使用线性扫描法计算天然气压缩因子Z。
    """
    # 将 numpy 数组转换为 python 列表 (如果需要)
    if not isinstance(x, list):
        x_list = x.tolist()
    else:
        x_list = x
        
    E_list, G_list, Q_list, F_list, S_list, W_list, K_list, M_list = E.tolist(), G.tolist(), Q.tolist(), F.tolist(), S.tolist(), W.tolist(), K.tolist(), M.tolist()
    a_list, u_list, g_list, q_list, f_list, s_list, w_list = a.tolist(), u.tolist(), g.tolist(), q.tolist(), f.tolist(), s.tolist(), w.tolist()
    b_list, c_list, k_list = b.tolist(), c.tolist(), k.tolist()
    Ex_list, Gx_list, Ux_list, Kx_list = Ex.tolist(), Gx.tolist(), Ux.tolist(), Kx.tolist()

    # Part 1: 计算第二维利系数 B
    B_calc = 0.0
    for n in range(18):
        ZJCS = T**(-u_list[n])
        sum_val = 0
        for i in range(N):
            for j in range(N):
                Eij = Ex_list[i][j] * math.sqrt(E_list[i] * E_list[j])
                Gij = Gx_list[i][j] * (G_list[i] + G_list[j]) / 2
                Bij = ((Gij + 1 - g_list[n])**g_list[n]) * \
                      ((Q_list[i] * Q_list[j] + 1 - q_list[n])**q_list[n]) * \
                      ((math.sqrt(F_list[i] * F_list[j]) + 1 - f_list[n])**f_list[n]) * \
                      ((S_list[i] * S_list[j] + 1 - s_list[n])**s_list[n]) * \
                      ((W_list[i] * W_list[j] + 1 - w_list[n])**w_list[n])
                sum_val += x_list[i] * x_list[j] * Bij * (Eij**u_list[n]) * ((K_list[i] * K_list[j])**1.5)
        B_calc += a_list[n] * ZJCS * sum_val

    # Part 2 & 3: 计算中间变量
    F0 = sum(x_list[i]**2 * F_list[i] for i in range(N))
    Q0 = sum(x_list[i] * Q_list[i] for i in range(N))
    sum1_G = sum(x_list[i] * G_list[i] for i in range(N))
    G0_term = sum(x_list[i] * x_list[j] * (Gx_list[i][j] - 1) * (G_list[i] + G_list[j]) for i in range(N - 1) for j in range(i + 1, N))
    G0 = sum1_G + G0_term
    sum2_E = sum(x_list[i] * E_list[i]**2.5 for i in range(N))
    U0_term = sum(x_list[i] * x_list[j] * (Ux_list[i][j]**5 - 1) * ((E_list[i] * E_list[j])**2.5) for i in range(N - 1) for j in range(i + 1, N))
    U0 = (sum2_E**2 + U0_term)**0.2
    sum1_K = sum(x_list[i] * K_list[i]**2.5 for i in range(N))
    sum2_K_term = sum(x_list[i] * x_list[j] * (Kx_list[i][j]**5 - 1) * ((K_list[i] * K_list[j])**2.5) for i in range(N - 1) for j in range(i + 1, N))
    K0 = (sum1_K**2 + 2 * sum2_K_term)**0.2

    # Part 4 & 5: 迭代计算压力 P
    SUM1 = sum(a_list[n] * ((G0 + 1 - g_list[n])**g_list[n]) * (((Q0**2) + 1 - q_list[n])**q_list[n]) * \
               ((F0 + 1 - f_list[n])**f_list[n]) * (U0**u_list[n]) * (T**(-u_list[n])) for n in range(12, 18))

    if log_callback:
        log_callback(f"开始压力迭代计算 (线性扫描, 步长: {step})...\n")
    
    iteration_count = 0
    pm = 0.01
    P = 0.0
    
    while iteration_count < max_iterations:
        pr = (K0**3) * pm
        SUM2 = 0
        for n in range(12, 58):
            Cn = a_list[n] * ((G0 + 1 - g_list[n])**g_list[n]) * \
                 (((Q0**2) + 1 - q_list[n])**q_list[n]) * \
                 ((F0 + 1 - f_list[n])**f_list[n]) * \
                 (U0**u_list[n]) * (T**(-u_list[n]))
            term = (b_list[n] - c_list[n] * k_list[n] * (pr**k_list[n])) * (pr**b_list[n]) * math.exp(-c_list[n] * (pr**k_list[n]))
            SUM2 += Cn * term
        P = pm * R * T * (1 + B_calc * pm - pr * SUM1 + SUM2)
        
        if abs(P - P0) < tolerance:
            break
            
        pm += step
        iteration_count += 1
        
        if log_callback and iteration_count % 5000 == 0:
            log_message = f"  迭代 {iteration_count} 次, pm={pm:.6f}, P={P:.6f}, 差值={abs(P - P0):.10f}\n"
            log_callback(log_message)

    if iteration_count == max_iterations and log_callback:
        log_callback("警告: 已达到最大迭代次数，结果可能不准确。\n")
    elif log_callback:
        log_callback(f"迭代完成，共 {iteration_count} 次。\n")

    # Part 6: 计算最终结果
    Z = P0 / (pm * R * T)
    M0 = sum(x_list[i] * M_list[i] for i in range(N))
    p_density = M0 * pm

    return Z, pm, pr, p_density, iteration_count

if __name__ == '__main__':
    import numpy as np
    T_in = 293.15
    P0_in = 0.101325
    x_in = np.array([0.961651, 0.008606, 0.004567, 0.01998, 0.003859, 0,
                     0, 0, 0, 0, 0, 0.000950, 0, 0.000138, 0.000249, 0, 0, 0, 0, 0, 0])
    
    print("\n--- 测试线性扫描法 (步长: 0.000001) ---")
    calculate_z_factor_linear_scan(T_in, P0_in, x_in, step=0.000001, log_callback=print)
    
    print("\n--- 测试线性扫描法 (步长: 0.00001) ---")
    calculate_z_factor_linear_scan(T_in, P0_in, x_in, step=0.00001, log_callback=print)