import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
import threading
import time
import queue

from calculator import calculate_z_factor_bisection
from calculator_pure import calculate_z_factor_linear_scan

class GasCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("天然气压缩因子计算器")
        self.geometry("1100x850") # 调整窗口大小以容纳更多控件

        self.gas_components = [
            "CH4", "N2", "CO2", "C2H6", "C3H8", "H2O", "H2S", "H2", "CO", "O2",
            "i-C4H10", "n-C4H10", "i-C5H12", "n-C5H12", "n-C6H14", "n-C7H16",
            "n-C8H18", "n-C9H20", "n-C10H22", "He", "Ar"
        ]
        self.default_x = [
            0.961651, 0.008606, 0.004567, 0.01998, 0.003859, 0, 0, 0, 0, 0, 0,
            0.000950, 0, 0.000138, 0.000249, 0, 0, 0, 0, 0, 0
        ]

        self.entries = {}
        self.log_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.z_work = None # 用于存储工况Z因子
        self.z_base = None # 用于存储标况Z因子
        self.create_widgets()
        self.on_solver_change()

    def create_widgets(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_pane, padding="10")
        main_pane.add(left_frame, weight=1)

        right_frame = ttk.Frame(main_pane, padding="10")
        main_pane.add(right_frame, weight=3)

        # --- 左侧框架内容 ---
        params_frame = ttk.LabelFrame(left_frame, text="输入参数", padding="10")
        params_frame.pack(fill=tk.X, pady=5)

        # --- 工况参数 ---
        work_conditions_frame = ttk.LabelFrame(params_frame, text="工况参数", padding="5")
        work_conditions_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        ttk.Label(work_conditions_frame, text="工况温度 (Tk, K):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.temp_work_entry = ttk.Entry(work_conditions_frame)
        self.temp_work_entry.insert(0, "350.0") # 示例工况温度
        self.temp_work_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(work_conditions_frame, text="工况压力 (Pk, MPa):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.pressure_work_entry = ttk.Entry(work_conditions_frame)
        self.pressure_work_entry.insert(0, "10.0") # 示例工况压力
        self.pressure_work_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(work_conditions_frame, text="工况流量 (m³/h):").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.flow_work_entry = ttk.Entry(work_conditions_frame)
        self.flow_work_entry.insert(0, "1000") # 示例工况流量
        self.flow_work_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        # --- 标况参数 ---
        standard_conditions_frame = ttk.LabelFrame(params_frame, text="标况参数", padding="5")
        standard_conditions_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        ttk.Label(standard_conditions_frame, text="标况温度 (Tb, K):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.temp_base_entry = ttk.Entry(standard_conditions_frame)
        self.temp_base_entry.insert(0, "293.15")
        self.temp_base_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Label(standard_conditions_frame, text="标况压力 (Pb, MPa):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.pressure_base_entry = ttk.Entry(standard_conditions_frame)
        self.pressure_base_entry.insert(0, "0.101325")
        self.pressure_base_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        components_frame = ttk.LabelFrame(left_frame, text="气体组分摩尔分数 (x)", padding="10")
        components_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        canvas = tk.Canvas(components_frame)
        scrollbar = ttk.Scrollbar(components_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        for i, comp in enumerate(self.gas_components):
            ttk.Label(scrollable_frame, text=f"{comp}:").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            entry = ttk.Entry(scrollable_frame, width=20)
            entry.insert(0, str(self.default_x[i]))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            self.entries[comp] = entry
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- 右侧框架内容 ---
        # 将 “最终结果” 移动到右侧顶部
        final_result_frame = ttk.LabelFrame(right_frame, text="最终结果", padding="10")
        final_result_frame.pack(fill=tk.X, pady=5)
        final_result_frame.columnconfigure(1, weight=1)

        ttk.Label(final_result_frame, text="工况 Z 因子:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.z_work_entry = ttk.Entry(final_result_frame, state="readonly")
        self.z_work_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(final_result_frame, text="标况 Z 因子:").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.z_base_entry = ttk.Entry(final_result_frame, state="readonly")
        self.z_base_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        ttk.Label(final_result_frame, text="标况流量 (Nm³/h):").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        self.flow_base_entry = ttk.Entry(final_result_frame, state="readonly")
        self.flow_base_entry.grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        # 日志区域
        log_frame = ttk.LabelFrame(right_frame, text="计算过程日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.result_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled")
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 将 “控制与操作” 移动到右侧底部
        control_frame = ttk.LabelFrame(right_frame, text="控制与操作", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        ttk.Label(control_frame, text="选择求解方法:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.solver_method = ttk.Combobox(control_frame, values=["二分法", "线性扫描法"], state="readonly")
        self.solver_method.current(0)
        self.solver_method.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.solver_method.bind("<<ComboboxSelected>>", self.on_solver_change)
        
        ttk.Label(control_frame, text="线性扫描步长:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.step_entry = ttk.Entry(control_frame)
        self.step_entry.insert(0, "0.000001")
        self.step_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(control_frame, text="最大迭代次数:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.max_iter_entry = ttk.Entry(control_frame)
        self.max_iter_entry.insert(0, "100000")
        self.max_iter_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(control_frame, text="收敛容差:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.tolerance_entry = ttk.Entry(control_frame)
        self.tolerance_entry.insert(0, "0.00001")
        self.tolerance_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        start_button = ttk.Button(control_frame, text="开始计算", command=self.start_calculation)
        start_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        reset_button = ttk.Button(control_frame, text="重置为默认值", command=self.reset_defaults)
        reset_button.grid(row=5, column=0, columnspan=2, pady=5)

    def on_solver_change(self, event=None):
        if self.solver_method.get() == "线性扫描法":
            self.step_entry.config(state="normal")
        else:
            self.step_entry.config(state="disabled")

    def reset_defaults(self):
        # 重置工况参数
        self.temp_work_entry.delete(0, tk.END)
        self.temp_work_entry.insert(0, "350.0")
        self.pressure_work_entry.delete(0, tk.END)
        self.pressure_work_entry.insert(0, "10.0")
        self.flow_work_entry.delete(0, tk.END)
        self.flow_work_entry.insert(0, "1000")
        # 重置标况参数
        self.temp_base_entry.delete(0, tk.END)
        self.temp_base_entry.insert(0, "293.15")
        self.pressure_base_entry.delete(0, tk.END)
        self.pressure_base_entry.insert(0, "0.101325")
        
        self.step_entry.delete(0, tk.END)
        self.step_entry.insert(0, "0.000001")
        self.max_iter_entry.delete(0, tk.END)
        self.max_iter_entry.insert(0, "100000")
        self.tolerance_entry.delete(0, tk.END)
        self.tolerance_entry.insert(0, "0.00001")
        for i, comp in enumerate(self.gas_components):
            self.entries[comp].delete(0, tk.END)
            self.entries[comp].insert(0, str(self.default_x[i]))

    def start_calculation(self):
        try:
            # 读取工况和标况参数
            T_work = float(self.temp_work_entry.get())
            P_work = float(self.pressure_work_entry.get())
            T_base = float(self.temp_base_entry.get())
            P_base = float(self.pressure_base_entry.get())
            Q_work = float(self.flow_work_entry.get())
            
            x = np.array([float(self.entries[comp].get()) for comp in self.gas_components])
            method = self.solver_method.get()
            step = float(self.step_entry.get()) if method == "线性扫描法" else 0
            max_iters = int(self.max_iter_entry.get())
            tolerance = float(self.tolerance_entry.get())

            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"初始化计算任务...\n")
            self.result_text.config(state="disabled")

            # 清空旧的结果
            self.z_work = None
            self.z_base = None
            for entry in [self.z_work_entry, self.z_base_entry, self.flow_base_entry]:
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.config(state="readonly")
            
            # 创建并启动工况计算线程
            thread_work = threading.Thread(target=self.run_calculation_thread,
                                           args=("工况", T_work, P_work, x, method, step, max_iters, tolerance),
                                           daemon=True)
            thread_work.start()

            # 创建并启动标况计算线程
            thread_base = threading.Thread(target=self.run_calculation_thread,
                                           args=("标况", T_base, P_base, x, method, step, max_iters, tolerance),
                                           daemon=True)
            thread_base.start()

            self.process_log_queue()
            self.process_result_queue() # 启动结果队列处理器

        except ValueError:
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "错误: 请确保所有输入均为有效的数字。")
            self.result_text.config(state="disabled")

    def process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg is None:
                    return
                self.result_text.config(state="normal")
                self.result_text.insert(tk.END, msg)
                self.result_text.see(tk.END)
                self.result_text.config(state="disabled")
        except queue.Empty:
            self.after(100, self.process_log_queue)

    def process_result_queue(self):
        try:
            condition_name, z_value = self.result_queue.get_nowait()
            
            # 更新Z因子显示
            if condition_name == "工况":
                self.z_work = z_value
                self.z_work_entry.config(state="normal")
                self.z_work_entry.delete(0, tk.END)
                self.z_work_entry.insert(0, f"{self.z_work:.6f}")
                self.z_work_entry.config(state="readonly")
            else: # 标况
                self.z_base = z_value
                self.z_base_entry.config(state="normal")
                self.z_base_entry.delete(0, tk.END)
                self.z_base_entry.insert(0, f"{self.z_base:.6f}")
                self.z_base_entry.config(state="readonly")
            
            # 如果两个Z因子都已获得，则计算标况流量
            if self.z_work is not None and self.z_base is not None:
                self.calculate_standard_flow()

        except queue.Empty:
            pass # 队列为空，什么都不做
        finally:
            self.after(100, self.process_result_queue)

    def calculate_standard_flow(self):
        try:
            # 从输入框读取参数
            P_work = float(self.pressure_work_entry.get())
            T_work = float(self.temp_work_entry.get())
            Q_work = float(self.flow_work_entry.get())
            P_base = float(self.pressure_base_entry.get())
            T_base = float(self.temp_base_entry.get())
            
            # 应用换算公式
            Q_base = Q_work * (P_work / P_base) * (T_base / T_work) * (self.z_base / self.z_work)
            
            # 更新UI
            self.flow_base_entry.config(state="normal")
            self.flow_base_entry.delete(0, tk.END)
            self.flow_base_entry.insert(0, f"{Q_base:.4f}")
            self.flow_base_entry.config(state="readonly")

        except (ValueError, TypeError):
            # 如果任何值无效或为None，则清空结果
            self.flow_base_entry.config(state="normal")
            self.flow_base_entry.delete(0, tk.END)
            self.flow_base_entry.config(state="readonly")

    def run_calculation_thread(self, condition_name, T, P0, x, method, step, max_iters, tolerance):
        # 使用闭包来为日志自动添加前缀
        def log_with_prefix(message):
            self.log_queue.put(f"[{condition_name}] {message}")

        log_with_prefix(f"开始使用 {method} 进行计算 (T={T}K, P={P0}MPa)...\n")
        start_time = time.time()
        
        try:
            if method == "二分法":
                Z, pm, pr, p_density, iters = calculate_z_factor_bisection(T, P0, x, max_iterations=max_iters, tolerance=tolerance, log_callback=log_with_prefix)
            elif method == "线性扫描法":
                Z, pm, pr, p_density, iters = calculate_z_factor_linear_scan(T, P0, x, step=step, max_iterations=max_iters, tolerance=tolerance, log_callback=log_with_prefix)
            else:
                log_with_prefix("错误: 未知的求解方法\n")
                return
            
            # 成功计算后，将结果放入结果队列
            self.result_queue.put((condition_name, Z))
            duration = time.time() - start_time

            result_str = (
                f"\n计算完成！\n\n"
                f"--- 详细结果 ---\n"
                f"压缩因子 (Z): {Z:.6f}\n"
                f"摩尔密度 (pm): {pm:.6f}\n"
                f"对比密度 (pr): {pr:.3f}\n"
                f"质量密度 (p): {p_density:.3f}\n\n"
                f"--- 性能 ---\n"
                f"总迭代次数: {iters}\n"
                f"计算耗时: {duration:.6f} 秒\n"
                f"---------------------------------\n"
            )
        except Exception as e:
            result_str = f"\n计算出错: {e}\n"

        log_with_prefix(result_str)

if __name__ == "__main__":
    app = GasCalculatorApp()
    app.mainloop()