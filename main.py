import tkinter as tk
from tkinter import ttk
import os
import threading
import subprocess
import sys
import winpexpect
import easygui
import time
import requests
from bs4 import BeautifulSoup as bsp
from zipfile import ZipFile
import Xiaomi
from boot_patch import Patch

class _Main():
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("500x600")
        self.root.title("ROOTBOX@github/BaiXinSuper")
        self.root.resizable(0, 0)
        self.txt_box = tk.Text(self.root, width=500)
        self.txt_box.place(x=0, y=300)
        self.b_h = 30
        self.b_w = 90

        self.check_adb_BTN = ttk.Button(self.root, text="检测ADB",
                                        command=lambda: self.do_thread(self.check_adb))  # x间隔100 ，y间隔50
        self.check_adb_BTN.place(x=0, y=30, height=self.b_h, width=self.b_w)

        self.reboot_to_fastboot_BTN = ttk.Button(self.root, text="重启到Fastboot", state="disable",
                                                 command=lambda: self.do_thread(lambda: self.do_cmd("adb reboot fastboot")))  # x间隔100 ，y间隔50
        self.reboot_to_fastboot_BTN.place(
            x=100, y=30, height=self.b_h, width=self.b_w)

        self.get_rom_pack_BTN = ttk.Button(self.root, text="获取ROM包", state="disable",
                                           command=lambda: self.do_thread(self.get_rom))
        self.get_rom_pack_BTN.place(
            x=200, y=30, height=self.b_h, width=self.b_w)

        self.unpack_boot_BTN = ttk.Button(
            self.root, text="提取BOOT", state="disable", command=lambda: self.do_thread(self.unpack_boot))
        self.unpack_boot_BTN.place(
            x=300, y=30, height=self.b_h, width=self.b_w)

        self.patch_boot_BTN = ttk.Button(
            self.root, text="修补BOOT", state="disable", command=lambda: self.do_thread(self.patch_boot))
        self.patch_boot_BTN.place(
            x=400, y=30, height=self.b_h, width=self.b_w)

        self.check_fastboot_BTN = ttk.Button(self.root, text="检测fastboot",
                                             command=lambda: self.do_thread(self.check_fastboot))  # x间隔100 ，y间隔50
        self.check_fastboot_BTN.place(
            x=0, y=80, height=self.b_h, width=self.b_w)

        self.flush_img_BTN = ttk.Button(self.root, text="刷入boot",
                                        command=lambda: self.do_thread(self.flush_boot))  # x间隔100 ，y间隔50
        self.flush_img_BTN.place(
            x=100, y=80, height=self.b_h, width=self.b_w)

        self.lock_adb_btns()
        self.lock_fastboot_btns()
        self.root.mainloop()

    def clear_text(self):
        self.txt_box['state'] = 'normal'
        self.txt_box.delete("1.0", tk.END)
        self.txt_box['state'] = 'disable'

    def add_text(self, msg):
        self.txt_box['state'] = 'normal'
        if "\n" in msg:
            self.txt_box.insert(tk.END, f"{msg}")
        else:
            self.txt_box.insert(tk.END, f"{msg}\n")
        self.txt_box['state'] = 'disable'

    def do_thread(self, a):
        t = threading.Thread(target=a)
        t.daemon = True
        t.start()

    def do_fastboot(self, cmd: str) -> bool:
        child = winpexpect.winspawn(cmd)
        while True:
            try:
                child.expect('\n', timeout=60)
                self.add_text(child.before)
            except winpexpect.EOF:
                break
            except winpexpect.TIMEOUT:
                continue

        return True

    def get_rom(self):
        self.clear_text()
        self.do_cmd("adb shell getprop ro.product.device")
        x = self.txt_box.get("1.0", tk.END).replace("\r", '').split("\n")
        x.remove("")
        if x[0]:
            x = f"https://xiaomirom.com/series/{x[0]}"
            self.add_text(x)
        self.add_text("开始检测型号")
        self.do_cmd("adb shell getprop ro.product.model")
        m = self.txt_box.get("1.0", tk.END).replace("\r", '').split("\n")
        m = list(filter(None, m))
        m=m[-1]
        Xiaomi._MAIN(self.add_text,self.do_cmd,self.txt_box,self.download,self.do_thread,x,m)




        

    def download(self, url,win=None):
        if win:
            win.destroy()
        old_title = self.root.title()

        self.add_text(f"正在从{url}获取ROM包")
        res = requests.get(url, stream=True)
        total_size = int(res.headers.get("content-length", 0))
        pbar = ttk.Progressbar(self.root, length=500)
        self.txt_box.window_create("end", window=pbar, align="center")
        pbar["maximum"] = total_size
        start_time = time.time()
        # progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
        with open('ROM.zip', 'wb') as f:
            for data in res.iter_content(1024):
                f.write(data)
                pbar["value"] += len(data)
                percent = pbar["value"] / total_size * 100
                speed = pbar["value"] / (time.time() - start_time)
                self.root.title(
                    f"[{round(percent,2)}% {round(speed/1048576,2)}Mb/s] {old_title}")
            f.close()
        res.close()

    def do_cmd(self, cmd: any):
        os.environ['PYTHONUNBUFFERED'] = '1'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        sys.stdout.flush()
        while p.poll() is None:
            out = p.stdout.readline()
            if out:
                try:
                    self.add_text(out.decode('gbk'))
                except:
                    self.add_text(out.decode('utf-8'))
        return 0

    def root(self, arg1, arg2):
        t = threading.Thread(target=lambda: self.do_fastboot(arg1, arg2))
        t.daemon = True
        t.start()

    def do_root(self, arg1, arg2):
        x = self.fastboot(f"fastboot flash {arg1} {arg2}")
        if x:
            self.fastboot("fastboot reboot")

    def check_adb(self):
        self.clear_text()
        self.do_cmd("adb devices")
        x = self.txt_box.get("1.0", tk.END).replace("\r", '').replace(
            "List of devices attached\n", '').split("\n")
        # print(x)
        x = list(filter(None, x))

        if x and x[0]:
            x = x[0].split("\t")
            if x[1] == "offline":
                self.root.title(f"ROOTBOX@github/BaiXinSuper ADB设备离线")
                self.add_text("请重新插手机")
            else:
                self.root.title(
                    f"ROOTBOX@github/BaiXinSuper ADB Attached {x[0]}")
                self.clear_text()
                self.do_cmd("adb shell getprop ro.product.manufacturer")
                x = self.txt_box.get("1.0", tk.END).replace(
                    "\r", '').split("\n")
                x = list(filter(None, x))
                self.unlock_adb_btns()
                self.clear_text()
                if x[0] != "Xiaomi":
                    self.get_rom_pack_BTN['state'] = 'disable'
                    self.add_text("你的设备不小米设备，此应用不担保一定可用")
        else:
            self.root.title(f"ROOTBOX@github/BaiXinSuper 暂无连接ADB设备")
            self.add_text("如果已连接设备但是无反应\n请前往目录下面的 drivers文件夹安装对应的驱动即可")

    def patch_boot(self):
        if os.path.exists("boot.img"):
            
            p = Patch(self.add_text)
            p.setmagiskboot("./lib/magiskboot")
            p.patchboot("./boot.img")
            self.add_text("- OK")
        else:
            self.add_text("未发现boot.img")

    def flush_boot(self):
        if os.path.exists("new-boot.img"):
            self.do_fastboot("fastboot flash boot new-boot.img")
        else:
            self.add_text("未发现new-boot.img")

    def unpack_boot(self):
        self.clear_text()
        if os.path.exists('./payload.bin'):
            self.add_text("获取到Payload，将提取BOOT IMAGE")
            self.do_cmd("dumper.exe -p boot -o .\ .\payload.bin")
            self.clear_text()
            self.add_text("已提取boot")
        elif os.path.exists("./ROM.zip"):
            self.add_text("将从ROM.zip内提取")
            with ZipFile('./ROM.zip', 'r') as f:
                try:
                    f.extract("boot.img")
                    self.add_text("已提取boot")
                except:
                    self.add_text("将从ROM.zip内提取payload ----会有点久")
                    f.extract("payload.bin")
                    return self.unpack_boot()
        else:
            self.add_text("未找到ROM.zip")

    def unlock_adb_btns(self):
        # x=[self.get_rom_pack_BTN,self.reboot_to_fastboot_BTN]
        x = [self.get_rom_pack_BTN, self.unpack_boot_BTN,
             self.patch_boot_BTN, self.reboot_to_fastboot_BTN]
        for i in x:
            i['state'] = 'normal'
        self.lock_fastboot_btns()

    def unlock_fastboot_btns(self):
        x = [self.flush_img_BTN]
        for i in x:
            i['state'] = 'normal'
        self.lock_adb_btns()

    def lock_adb_btns(self):
        x = [self.get_rom_pack_BTN, self.unpack_boot_BTN,
             self.patch_boot_BTN, self.reboot_to_fastboot_BTN]
        for i in x:
            i['state'] = 'disable'

    def lock_fastboot_btns(self):
        x = [self.flush_img_BTN]
        for i in x:
            i['state'] = 'disable'

    def check_fastboot(self):
        self.clear_text()
        self.do_cmd("fastboot devices")
        x = self.txt_box.get("1.0", tk.END).replace("\r", '').split("\n")
        # print(x)
        x.remove("")
        if x[0]:
            self.root.title(
                f"ROOTBOX@github/BaiXinSuper Fastboot Attached {x[0]}")
            # self.unlock_adb_btns()
        else:
            self.root.title(f"ROOTBOX@github/BaiXinSuper 暂无连接Fastboot设备")
            self.add_text("如果已连接设备但是无反应\n请前往目录下面的 drivers文件夹安装对应的驱动即可")


with open("readme.md", 'r', encoding="utf-8") as f:
    if easygui.ccbox(msg=f.read(), title="请认真仔细阅读如下条款", choices=['同意并继续', "拒绝且退出"]):
        main = _Main()
    f.close()
