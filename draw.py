import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as sts
import pandas as pd


def turn_2d_to_1d(lis):
    res = []
    for i in range(len(lis)):
        res.append(lis[i][0])
    return res


def get_line(num):
    df = pd.read_excel("test.xlsx", usecols=num, names=None)  # 读取项目名称和行业领域两列，并不要列名
    df_li = df.values.tolist()
    return turn_2d_to_1d(df_li)


if __name__ == '__main__':
    """
    x = get_line(0)
    y = get_line(1)
    z = get_line(2)
    #plt.show()

    # 双对数坐标下
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_adjustable("datalim")

    ax.plot(x, y,'r-.')
    ax.plot(x, z, 'b-.')
    ax.set_xlim(1, 256)
    ax.set_ylim(1e-2, 16)
    #ax.grid()
    plt.draw()
    plt.show()
    """
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 用来正常显示中文标签

    labels = ['用户间通信', '椭圆曲线计算', '其他']
    sizes = [56.47, 42.39, 1.14]
    explode = (0, 0, 0)
    plt.pie(sizes, fexplode=explode, labels=labels, autopct='%1.1f%%', shadow=False, startangle=150)
    plt.title("SPDZ-sacrifice(并行)各部分所占比例")
    plt.show()
