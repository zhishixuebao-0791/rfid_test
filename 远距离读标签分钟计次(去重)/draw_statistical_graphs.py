import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from matplotlib.ticker import MaxNLocator
# 设置中文字体支持（如果需要显示中文）
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号
# 绘制柱状图
def Draw_Histogram(folder_path):
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.startswith("remote_read_counter") and filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            # 读取文件内容
            with open(file_path, 'r') as file:
                lines = file.readlines()
            # 提取图表标题（第一行）
            if not lines:
                continue
            chart_title = lines[0].strip()
            # 提取数据
            minutes = []
            values = []
            for line in lines[1:]:
                if line.strip():  # 跳过空行
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            minute = int(parts[0])
                            value = int(parts[1])
                            minutes.append(minute)
                            values.append(value)
                        except ValueError:
                            print(f"跳过无效行: {line.strip()}")
            if not minutes:
                print(f"文件 {filename} 中没有有效数据")
                continue
            # 创建柱状图
            plt.figure(figsize=(12, 6))
            bars = plt.bar(minutes, values, color='skyblue', alpha=0.7)
            # 在柱子上方添加数值标签
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                        f'{int(height)}', ha='center', va='bottom')
            # 设置图表标题和标签
            plt.title(chart_title, fontsize=16)
            plt.xlabel('60分钟盘存(盘1分钟停止1分钟):one minute', fontsize=12)
            plt.ylabel('1分钟盘存到的标签数量:Pcs', fontsize=12)
            # 设置x轴刻度为整数
            plt.xticks(minutes)
            # 设置y轴刻度为整数
            ax = plt.gca()
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            # 添加网格线
            plt.grid(axis='y', alpha=0.75)
            # 调整布局
            plt.tight_layout()
            # 保存图表
            output_filename = f"{os.path.splitext(filename)[0]}_chart.png"
            output_path = os.path.join(folder_path, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"已保存图表: {output_path}")
            # 显示图表（可选）
            # plt.show()
            # 关闭当前图形，避免内存泄漏
            plt.close()
    print("所有图表已生成完成！")