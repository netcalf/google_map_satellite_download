import math
import os
import requests
import cv2
import numpy as np
from osgeo import gdal


def swap(a, b):
    a, b = b, a
    return a, b


class Point:
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat


class Box:
    def __init__(self, point_lt, point_rb):
        self.point_lt = point_lt
        self.point_rb = point_rb


def build_url(x, y, z):
    return "http://khms0.google.com/kh/v=893?&x={x}&y={y}&z={z}".format(x=x, y=y, z=z)


def download(x, y, z, path):
    proxies = {
        "http": "http://127.0.0.1:19180",
        "https": "http://127.0.0.1:19180"
    }
    url = build_url(x, y, z)
    response = requests.get(url, proxies=proxies)
    path = path + "\\{z}\\{x}\\".format(z=z, x=x)
    if not os.path.exists(path):
        os.makedirs(path)
    filepath = path + "\\{y}.png".format(y=y)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(response.content)
    else:
        print("network error!")


def xyz2lonlat(x, y, z):
    n = math.pow(2, z)
    lon = x / n * 360.0 - 180.0
    lat = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = lat * 180.0 / math.pi
    return lon, lat


def lonlat2xyz(lon, lat, zoom):
    n = math.pow(2, zoom)
    x = ((lon + 180) / 360) * n
    y = (1 - (math.log(math.tan(math.radians(lat)) + (1 / math.cos(math.radians(lat)))) / math.pi)) / 2 * n
    return int(x), int(y)


def cal_tiff_box(x1, y1, x2, y2, z):
    LT = xyz2lonlat(x1, y1, z)
    RB = xyz2lonlat(x2 + 1, y2 + 1, z)
    return Point(LT[0], LT[1]), Point(RB[0], RB[1])


def core():
    path = r".\map"
    point_lt = Point(117.0357972, 36.6402741)#经纬度范围：左上
    point_rb = Point(117.0387972, 36.6382741)#经纬度范围:右下
    z = 22  #地图级别，最大22级
    x1, y1 = lonlat2xyz(point_lt.lon, point_lt.lat, z)
    x2, y2 = lonlat2xyz(point_rb.lon, point_rb.lat, z)
    print(x1, y1, z)
    print(x2, y2, z)
    count = 0
    all = (x2-x1+1) * (y2-y1+1)
    for i in range(x1, x2+1):
        for j in range(y1, y2+1):
            download(i, j, z, path)
            count += 1
            print("{m}/{n}".format(m=count, n=all))
            pass
    merge(x1, y1, x2, y2, z, path)
    lt, rb = cal_tiff_box(x1, y1, x2, y2, z)
    
    cmd = "gdal_translate -of GTiff -a_srs EPSG:4326 -a_ullr {p1_lon} " \
          "{p1_lat} {p2_lon} {p2_lat}" \
          " {input} {output}".format(p1_lon=lt.lon, p1_lat=lt.lat, p2_lon=rb.lon, p2_lat=rb.lat,
                                     input=path+"//merge.png", output=path+"//output.tiff")
    
    print(cmd)
    os.system(cmd)

def merge(x1, y1, x2, y2, z, path):
    row_list = list()
    for i in range(x1, x2+1):
        col_list = list()
        for j in range(y1, y2+1):
            col_list.append(cv2.imread(path + "\\{z}\\{i}\\{j}.png".format(i=i, j=j,z=z)))
        k = np.vstack(col_list)
        row_list.append(k)
    result = np.hstack(row_list)
    cv2.imwrite(path + "//merge.png", result)


if __name__ == '__main__':
    core()


