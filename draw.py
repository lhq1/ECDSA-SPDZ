import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.font_manager
#print([f.name for f in matplotlib.font_manager.fontManager.ttflist])

def turn_2d_to_1d(lis):
    res = []
    for i in range(len(lis)):
        res.append(lis[i][0])
    return res


def get_line(num):
    df = pd.read_excel("SPDZ-ECDSA多次结果.xlsx", usecols=[num], names=None,engine='openpyxl')  # 读取项目名称和行业领域两列，并不要列名
    df_li = df.values.tolist()
    return turn_2d_to_1d(df_li)


if __name__ == '__main__':

    x = get_line(0)
    y0 = get_line(1)
    y1 = get_line(2)
    y2 = get_line(3)
    y3 = get_line(4)
    #plt.show()
    # 双对数坐标下
    plt.rcParams['font.sans-serif'] = 'Microsoft YaHei'  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False
    """
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_adjustable("datalim")
    ax.plot(x, y0,marker='.',label='SPDZ-sacrifice')
    ax.plot(x, y1,marker='o',label='SPDZ')
    ax.plot(x, y2,marker='*',label='SPDZ-sacrifice(并行)')
    ax.plot(x, y3, marker='x',label='SPDZ(并行)')
    ax.set_xlim(1, 256)
    ax.set_ylim(1e-2, 16)
    ax.set_xlabel('次数')
    ax.set_ylabel('时间(s)')
    ax.set_title("四种方案下多次ECDSA运行时间")
    #ax.grid()
    plt.legend()
    plt.draw()
    plt.savefig("ECDSA-multi.png", dpi=300, bbox_inches='tight')
    plt.show()
    """
    #plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 用来正常显示中文标签

    labels = ['用户间通信', '椭圆曲线计算', '其他']
    sizes = [49.0, 49.9, 1.1]
    explode = (0, 0, 0)
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=False, startangle=150)
    plt.title("SPDZ(并行)各部分所占比例")
    plt.savefig('SPDZ-p-ratio.png',dpi=300,bbox_inches='tight')
    plt.show()
