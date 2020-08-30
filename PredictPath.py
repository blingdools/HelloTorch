"""

Predict Path

Usage:
  PredictPath.py [--pre] [--cor]
  PredictPath.py (-h | --help)

Options:
  -h --help     Show this screen
  --pre         Predict Path
  --cor         Generate Correlation

"""


import pandas as pd
import numpy as np

from sklearn import linear_model
from docopt import docopt


if __name__ == '__main__':
    arguments = docopt(__doc__)

    # 计算数据集Sheet标签
    file = pd.ExcelFile('./data/Path/situation_0821.xlsx')
    sheets_name = file.sheet_names

    # 构建完整数据集
    df = pd.read_excel('./data/Path/situation_0821.xlsx', sheet_name=sheets_name)
    dataset = []
    lon_lat_data_y = []
    for v in df:
        data_item = df[v]
        data_item = data_item[data_item.keys().to_numpy()].to_numpy()
        # 经纬度时序数据
        lon_lat_data_y_item = data_item[:, 9:11]
        dataset.append(data_item)
        lon_lat_data_y.append(np.array(lon_lat_data_y_item, dtype=np.float))
    dataset = np.array(dataset)
    lon_lat_data_y = np.array(lon_lat_data_y)
    lon_lat_data_x = []
    # 构建时序标签
    for i in range(lon_lat_data_y.shape[0]):
        data_len = lon_lat_data_y[i].shape[0]
        data_y = np.arange(0, data_len)
        lon_lat_data_x.append(data_y)
    lon_lat_data_x = np.array(lon_lat_data_x)

    if arguments["--pre"]:
        # 表格纵轴
        pred_y_index = []
        pred_data = []

        for i in range(lon_lat_data_y.shape[0]):
            lon_lat_data_y_item = lon_lat_data_y[i]
            lon_lat_data_x_item = lon_lat_data_x[i].reshape(-1, 1)
            # 获取对象唯一编号
            name = dataset[i][0][0]

            # 构建线性回归模型
            line_reg = linear_model.LinearRegression()
            # 拟合现有数据
            line_reg.fit(lon_lat_data_x_item, lon_lat_data_y_item)

            # 数据预测
            start = lon_lat_data_x_item.shape[0]
            lon_lat_data_pred = []
            # 计算后100步的预测值
            for i in range(100):
                lon_lat_data_x_item_pred = np.array(lon_lat_data_x_item.shape[0] + i).reshape(-1, 1)
                lon_lat_data_y_item_pred = line_reg.predict(lon_lat_data_x_item_pred)
                lon_lat_data_item_pred_data = lon_lat_data_y_item_pred[0]
                lon_lat_data_pred.append(lon_lat_data_item_pred_data)
            lon_lat_data_item_coef_data = line_reg.coef_.flatten()
            lon_lat_data_item_intercept_data = line_reg.intercept_
            lon_lat_data_pred = np.array(lon_lat_data_pred).flatten()

            # 构建保存数据
            pred_data.append(np.hstack((np.hstack((lon_lat_data_pred, lon_lat_data_item_coef_data)),
                                        lon_lat_data_item_intercept_data)))
            pred_y_index.append(name)

        # 创建数据的列标题
        columns_name = []
        for i in range(100):
            columns_name.append('longitude-{0}'.format(i + 1))
            columns_name.append('latitude-{0}'.format(i + 1))
        columns_name.append('coef_1')
        columns_name.append('coef_2')
        columns_name.append('intercept_1')
        columns_name.append('intercept_2s')
        # 创建数据
        df = pd.DataFrame(pred_data, index=pred_y_index, columns=columns_name)
        # 写入Excel文件
        df.to_excel('./out/pred_data.xlsx', sheet_name='pred_data')

        print('Predict Data Finish...')

    if arguments["--cor"]:
        # 相似性矩阵
        sim_arr = []
        # 表格纵轴
        sim_index = []
        for i in range(len(lon_lat_data_y)):
            lon_lat_data_item = lon_lat_data_y[i]
            sim_arr_item = []
            # 获取对象唯一编号
            name = dataset[i][0][0]
            sim_index.append(name)
            for k in range(len(lon_lat_data_y)):
                if i == k:
                    sim_arr_item.append(-9999)
                    # sim_arr_item.append(str(1))
                    continue

                # 获得要计算相关性的对象
                lon_lat_data_com = lon_lat_data_y[k]

                # 计算余弦相似性
                sum_sim = 0
                # 数据长短不一时取短的
                data_len = min(len(lon_lat_data_item), len(lon_lat_data_com))
                last_dis = None
                for j in range(data_len):
                    A = lon_lat_data_item[j]
                    B = lon_lat_data_com[j]
                    # 计算欧式距离
                    dis = np.linalg.norm(A - B)
                    if last_dis is None:
                        last_dis = dis
                    else:
                        # 计算距离的变化
                        diff = dis - last_dis
                        sum_sim = sum_sim + diff
                sim = sum_sim / data_len
                # 保存相似性数据
                sim_arr_item.append(sim)
                # sim_arr_item.append(str(sim))
            # 保存相似性数据
            sim_arr.append(sim_arr_item)

        sim_arr = np.array(sim_arr)
        sim_arr = sim_arr.flatten()
        delete_index = []
        for i in range(len(sheets_name)):
            delete_index.append(i * (len(sheets_name) + 1))
        sim_arr_tmp = np.delete(sim_arr, delete_index)
        # 归一化数据
        sim_min, sim_max = np.min(sim_arr_tmp), np.max(sim_arr_tmp)
        # 限制数据小于
        sim_arr_tmp = (1 - (sim_arr_tmp - sim_min) / (sim_max - sim_min)) * 0.99

        # 插入自相关的值
        insert_index = []
        for i in range(len(sheets_name)):
            insert_index.append(i * len(sheets_name))
        sim_arr = np.insert(sim_arr_tmp, insert_index, 1)
        # 重新变为二维数组
        sim_arr = sim_arr.reshape(-1, len(sheets_name))

        # 创建数据
        df = pd.DataFrame(sim_arr, index=sim_index, columns=sim_index)
        # 写入Excel文件
        df.to_excel('./out/sim_data.xlsx', sheet_name='sim_data')

        print('Calculate Similarity Finish...')