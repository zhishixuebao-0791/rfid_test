import matplotlib.pyplot as plt
import numpy as np
import math
import os
import re
row = 3
column = 3
# 可显示的最大数量 = row*column
def read_file(path_txt):
    fig = plt.figure(figsize=(20,10))#设置画布的大小
    i = 1 # 起始位置
    for root,dirs,files in os.walk('.\\' + path_txt):
        for file in files:
            if file.startswith(path_txt) and file.endswith(".txt"):
                if path_txt in file:
                    print(file)
                    ax = fig.add_subplot(row, column, i)#往图形窗口添加子图
                    # if pattern.match(stripped_line):
                    plot_fig(ax,path_txt,file)
                    plt.title(file)#设置图标标题
                    i = i + 1
                    if i>= (row*column):
                        break
    output_filename = path_txt+"_chart.png"
    output_path = os.path.join(path_txt, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"已保存图表: {output_path}")
    #plt.show()  #显示图形
    plt.close()
    print("所有图表已生成完成！")

def plot_fig(ax, path_txt,file):
    source_f = open(path_txt + "\\" + file, "r")
    b = source_f.readlines()
    pattern = re.compile(r'^\d{2},\d{2},\d{2},0x[0-9a-fA-F]+$')
    lines = len(b)
    print("lines = " + str(lines))
    out = []
    for a in b:
        a = a.strip()#删除末尾/r/n
        if pattern.match(a):
            a = a.split(',')#split() 函数用于将字符串按照指定的分隔符拆分成多个子字符串，并将这些子字符串存储在列表中。
            a = int(a[3], 16)
            out.append(a)
    if(not len(out)):
        print("serial port number error!")
        exit(1)
    del out[0]
    del out[-1]
    index = np.arange(len(out))
    ax.plot(index, out)


