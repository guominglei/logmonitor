#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
    同时监听多个日志文件
    多进程版本
"""

import os
import sys
import signal
import raven
import pyinotify

from multiprocessing import Process
from log_util import FileObject
from conf import DNS_DICT


class ProcessSingleFile(pyinotify.ProcessEvent):

    def __init__(self, log, sender, tags, *args, **kwargs):
        if isinstance(log, FileObject):
            self.log = log
        else:
            self.log = FileObject(log)
        self.tags = tags
        self.sender = sender
        super(ProcessSingleFile, self).__init__(*args, **kwargs)

    def process_IN_MODIFY(self, event):
        for line in self.log.read_line():
            self.sender.captureMessage(line, tags=self.tags)


class SentryLog(object):

    def __init__(self, project, dns_config, server_name,
                 server_ip, basedir="/opt/sports"):

        if not dns_config:
            sys.exit()

        self.project = project
        self.dns_config = dns_config
        self.server_name = server_name
        self.server_ip = server_ip
        self.basedir = basedir

        self.__init_info()
        self.__init_sender()

        self.wm = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(self.wm)

    def __init_sender(self):

        dns = self.dns_config.get("dns")
        if dns:
            self.sender = raven.Client(dns)

    def __init_info(self):
        """
            根据dns配置，初始化日志文件信息
        """
        tag = {}
        log_path = ""
        log_file = None
        log_template = "{}/{}/logs/{}.log"

        config_logpath = self.dns_config.get("log_path")

        if not config_logpath:
            log_path = log_template.format(
                self.basedir, self.project, self.project
            )
        else:
            log_path = config_logpath

        if os.path.exists(log_path):
            tag = {
                "name": self.server_name,
                "ip": self.server_ip,
                "project": self.project,
                "path": log_path
            }
            # 标签
            self.tags = tag
            # 日志文件路径
            self.log_path = log_path
            # 日志文件
            tail_f = self.__tail_log(log_path)
            self.log_file = tail_f
        else:
            print "log_path: {} not find".format(log_path)

    def __tail_log(self, log_path):

        file = open(log_path, 'r')
        st_results = os.stat(log_path)
        st_size = st_results[6]
        file.seek(st_size)

        return FileObject(file)

    def monitor_start(self):

        self.wm.add_watch(
            self.log_path, pyinotify.IN_MODIFY,
            proc_fun=ProcessSingleFile(self.log_file, self.sender, self.tags),
            rec=False, auto_add=False, do_glob=False,
            exclude_filter=lambda path: False)

        self.notifier.loop()

    def monitor_stop(self):
        self.notifier.stop()

    def monitor_restart(self):
        self.notifier.stop()
        self.notifier.loop()


def main():

    log_list = []
    if len(sys.argv) == 4:
        server_name, server_ip, basedir = sys.argv[1:]
        for project, dns_config in DNS_DICT.items():
            sentry_log = SentryLog(
                project, dns_config, server_name, server_ip, basedir
            )
            log_list.append(sentry_log)

    elif len(sys.argv) == 3:
        server_name, server_ip = sys.argv[1:]
        for project, dns_config in DNS_DICT.items():
            sentry_log = SentryLog(
                project, dns_config, server_name, server_ip)
            log_list.append(sentry_log)
    else:
        print "params error"
        print "python xx.py server_name server_ip, basedir"
        sys.exit()

    def stop_worker(sig_num, addtion):
        os.killpg(os.getpgid(os.getpid()), signal.SIGKILL)

    signal.signal(signal.SIGTERM, stop_worker)

    workers = []
    for log in log_list:
        process = Process(target=log.monitor_start)
        process.daemon = True
        process.start()
        workers.append(process)

    try:
        for worker in workers:
            worker.join()
    except:
        pass


if __name__ == "__main__":

    main()

