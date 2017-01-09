# -*- coding:utf-8 -*-

"""
    解析日志文件
    把多行异常记录作为一条信息。 整条信息以\r\n分开，内部多行以\n 分开
"""

import re
import sys


class FileObject(object):

    def __init__(self, f):
        self.f = f

    def format_line_info(self, data_arr):
        line_info = ""
        if len(data_arr) > 1:
            line_info = "\n".join(data_arr)
        else:
            line_info = data_arr[0]

        data = "{}\r\n".format(line_info)

        return data

    def read_line(self):
        data = self.f.readline()
        line_data = []
        while data:
            if self.is_line(data):
                if line_data:
                    yield self.format_line_info(line_data)
                    line_data = []
                line_data.append(data[:-1])
            else:
                line_data.append(data[:-1])
            data = self.f.readline()
        if line_data:
            yield self.format_line_info(line_data)

    def is_line(self, line):

        groups = re.match("\d{4}-\d{2}-\d{2}", line)
        if groups:
            return True
        else:
            return False


def main():
    #path = "/Users/mingleiguo/Documents/api.log"

    path = sys.argv[1]
    print sys.argv
    f = open(path, "r")
    f_obj = FileObject(f)
    num = 0
    for line in f_obj.read_line():
        if line:
            num += 1

    print num

if __name__ == "__main__":

    main()
