import os
import numpy as np
import math

def Var_And_SD(folder_path):
    # 输出文件路径
    output_file = os.path.join(folder_path, "Var_and_SD.txt")
    # 遍历文件夹中的所有文件
    with open(output_file, 'w') as result_file:
        for filename in os.listdir(folder_path):
            if filename.startswith("remote_read_counter") and filename.endswith(".txt"):
                file_path = os.path.join(folder_path, filename)

                # 读取文件内容
                with open(file_path, 'r') as file:
                    lines = file.readlines()

                # 跳过空文件
                if len(lines) < 2:
                    continue

                # 提取数据（从第二行开始的所有第二列数据）
                values = []
                for line in lines[1:]:
                    if line.strip():  # 跳过空行
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                value = int(parts[1])
                                values.append(value)
                            except ValueError:
                                print(f"跳过无效行: {line.strip()}")

                # 检查是否有足够的数据进行计算（至少需要3个数据点）
                if len(values) < 3:
                    print(f"文件 {filename} 中有效数据不足3个，跳过计算")
                    continue
                
                # 去除一个最大值和一个最小值
                values_sorted = sorted(values)
                # 如果有多个相同的最小值或最大值，只去除一个
                filtered_values = values_sorted[1:-1]  # 去除第一个和最后一个

                # 计算样本均值
                n = len(filtered_values)
                mean = sum(filtered_values) / n

                # 计算样本方差 (除以n-1)
                variance = sum((x - mean) ** 2 for x in filtered_values) / (n - 1)

                # 计算样本标准差
                std_deviation = math.sqrt(variance)

                # 将结果写入文件
                result_file.write(f"{filename}\n")
                result_file.write(f"平均数：{mean:.4f}\n")
                result_file.write(f"样本方差：{variance:.4f}\n")
                result_file.write(f"样本标准差：{std_deviation:.4f}\n")
                print(f"已处理文件: {filename}")
    print(f"所有计算结果已保存到: {output_file}")
#Var_And_SD("60X")