import string
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, PhotoImage
from ttkbootstrap import Style
from PIL import Image, ImageTk
import json
import time
import threading
import requests
import os
import datetime
import sys
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from tavily import TavilyClient
import random

class DeepSeekChat:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek For MoonOrange v1.2")
        iconDeepSeek = ImageTk.PhotoImage(Image.open(self.resource_path("deepseek.png")))
        root.iconphoto(False, iconDeepSeek)
        self.root.geometry("1200x800")

        # 初始化变量
        self.current_message = ""
        self.current_chat = []
        self.current_history = {}
        self.current_content = ""
        self.history = []
        self.log_file = "chat_history.json"
        self.load_history()
        self.api_key = "your-api-key"
        self.api_info = tk.StringVar(value="API余额: 未知")
        self.tavily_api_key = "tavily-api-key"
        self.config = {}
        self.theme_style = "litera"
        self.output_tokens_show = tk.StringVar(value="输出tokens<=")
        self.max_tokens = tk.IntVar(value=4096)
        self.config_file = "chat_config.json"
        self.load_config()
        self.thinking = False
        self.thinking_start_index = None
        self.thinking_end_index = None
        self.current_temperature = 1.0
        self.upload_file_flag = False
        self.upload_file_content = []
        self.upload_file_name = []
        self.upload_file_icons = []
        self.search_mode = tk.StringVar(value="Bing-General")

        # 预加载文件类型图标（需要准备对应的png文件）
        self.icon_images = {
            "default": ImageTk.PhotoImage(Image.open(self.resource_path("deepseekFile.png")).resize((20, 20)))
        }
        # 加载图片
        self.load_images()
        self.root.bind("<Configure>", self.on_window_resize)

        # 创建界面
        self.style = Style(theme=self.theme_style)
        self.ini_style()
        self.create_widgets()
        self.setup_bindings()
        self.input_text.focus_set()
        self.load_config()
        self.load_history()
        #messagebox.showinfo("DeepSeek For MoonOrange", "本项目完全开源于https://github.com/Orangewang124/DeepSeek-MoonOrange不能用于任何盈利目的\n如果觉得有意思就帮我Star一下呗:)")
        self.display_left_message("本项目完全开源于https://github.com/Orangewang124/DeepSeek-MoonOrange不能用于任何盈利目的\n如果觉得有意思就帮我Star一下呗:)", 10)

    def ini_style(self):
        # 自定义Combobox样式
        self.style.configure('custom.TCombobox',
                             font=('Times New Roman', 10),
                             selectbackground='white',
                             selectforeground='black',
                             fieldbackground='white',
                             background='white',
                             relief='flat')

        # 状态映射配置
        self.style.map('custom.TCombobox',
                       fieldbackground=[
                           ('hover', '#f0f0f0'),  # 鼠标悬停时输入框背景
                           ('active', 'white'),  # 激活状态保持白色
                           ('!disabled', 'white')  # 正常状态背景
                       ],
                       foreground=[
                           ('hover', 'black'),  # 鼠标悬停时文字颜色
                           ('active', 'black'),  # 激活状态颜色
                           ('!disabled', 'black')  # 正常状态颜色
                       ],
                       background=[
                           ('hover', '#f0f0f0'),  # 鼠标悬停时下拉按钮背景
                           ('active', 'white'),
                           ('!disabled', 'white')
                       ])

    def resource_path(self, relative_path):
        """ 获取资源的绝对路径 """
        if hasattr(sys, '_MEIPASS'):
            # 打包后运行时的临时目录
            base_path = sys._MEIPASS
        else:
            # 开发环境中的当前目录
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def get_api_key(self):
        """弹出输入框获取API密钥"""
        # 使用父窗口作为对话框的父组件
        api_key = simpledialog.askstring(
            "DeepSeek-API",
            "请输入您的DeepSeek-API密钥:)",
            parent=self.root,  # 根据实际父窗口调整这个参数
        )
        # 处理取消输入的情况
        if api_key is None:
            return None

        # 处理空输入的情况
        if not api_key.strip():
            self.show_error("API密钥不能为空")
            return None
        return api_key

    def load_config(self):
        """加载配置文件"""
        self.config = []
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                    if "api-key" in self.config[0]:
                        self.api_key = self.config[0]["api-key"]
                    else:
                        self.api_key = self.get_api_key()
                    if "theme_style" in self.config[0]:
                        self.theme_style = self.config[0]["theme_style"]
                    else:
                        self.theme_style = "litera"
                        self.config[0]["theme_style"] = "litera"
                    if "max_tokens" in self.config[0]:
                        if int(self.config[0]["max_tokens"])<=8192 and int(self.config[0]["max_tokens"])>0:
                            self.max_tokens.set(int(self.config[0]["max_tokens"]))
                        else:
                            self.max_tokens.set(4096)
                            self.config[0]["max_tokens"] = "4096"
                    else:
                        self.max_tokens.set(4096)
                        self.config[0]["max_tokens"] = "4096"
                    if "tavily-api-key" in self.config[0]:
                        self.tavily_api_key = self.config[0]["tavily-api-key"]
                    else:
                        self.tavily_api_key = "tavily-api-key"
                        self.config[0]["tavily-api-key"] = "tavily-api-key"
                response_code = self.update_api_balance()
                if response_code == 401:
                    self.api_key = self.get_api_key()
                    self.config[0]["api-key"] = self.api_key
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
            else:
                self.config = [{
                    "api-key": "your-api-key",
                    "max_tokens": "4096",
                    "theme_style": "litera",
                    "tavily-api-key": "tavily-api-key"
                }]
                self.api_key = self.get_api_key()
                self.config[0]["api-key"] = self.api_key
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
        except Exception as e:
            self.show_error(e)

    # 在主窗口显示后强制执行
    def show_window(self):
        self.root.deiconify()
        self.input_text.tkraise()  # 确保输入框在顶层
        self.input_text.configure(state=tk.NORMAL)
        self.input_text.focus_force()
        self.root.after(100, lambda: self.input_text.insert(tk.END, " "))
        self.root.after(200, lambda: self.input_text.delete("end-1c"))

    def verify_input_visibility(self):
        """验证输入框可见性"""
        print(f"输入框可见: {self.input_text.winfo_viewable()}")
        print(f"输入框尺寸: {self.input_text.winfo_width()}x{self.input_text.winfo_height()}")
        print(f"输入框位置: ({self.input_text.winfo_x()}, {self.input_text.winfo_y()})")

        # 强制显示边界（调试用）
        self.input_frame.configure(style='Debug.TFrame')
        self.root.update()

    def load_images(self):
        user_img = Image.open(self.resource_path("user_penguin.png")).resize((40, 40))
        deepseek_img = Image.open(self.resource_path("deepseek.png")).resize((40, 40))
        self.user_photo = ImageTk.PhotoImage(user_img)
        self.deepseek_photo = ImageTk.PhotoImage(deepseek_img)

    def create_widgets(self):
        # 历史记录面板
        self.history_frame = ttk.Frame(self.root, width=500)
        self.history_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.history_list = tk.Listbox(self.history_frame)
        self.history_list.pack(fill=tk.BOTH, expand=True)
        self.update_history_list()

        # 添加MAX_TOKENS显示和设置按钮
        self.max_tokens_frame = ttk.Frame(self.history_frame)
        self.max_tokens_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=5)

        ttk.Label(
            self.max_tokens_frame,
            textvariable=self.output_tokens_show,
            font=('宋体', 10),
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 0))

        ttk.Label(
            self.max_tokens_frame,
            textvariable=self.max_tokens,
            font=('宋体', 10),
            anchor='w'
        ).pack(side=tk.LEFT, padx=(2, 0))

        ttk.Button(
            self.max_tokens_frame,
            text="更新MAX_TOKENS",
            command=self.renew_max_tokens
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # 添加API余额显示框和更新按钮
        self.api_balance_frame = ttk.Frame(self.history_frame)
        self.api_balance_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=5)

        ttk.Label(
            self.api_balance_frame,
            textvariable=self.api_info,
            font=('宋体', 10),
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 0))

        ttk.Button(
            self.api_balance_frame,
            text="更新API",
            command=self.renew_api_key
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            self.api_balance_frame,
            text="刷新",
            command=self.update_api_balance
        ).pack(side=tk.RIGHT, padx=(0, 5))


        # 底部复选框面板（新增底部控制栏）
        self.left_control_frame = ttk.Frame(self.history_frame)
        self.left_control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=5)
        # 添加"联网引擎"标签和复选框
        ttk.Label(
            self.left_control_frame,
            text="联网引擎：",
            font=('宋体', 10),
            anchor='e'
        ).pack(side=tk.LEFT, padx=(0, 0))
        # 在界面布局部分
        search_combobox = ttk.Combobox(
            self.left_control_frame,
            textvariable=self.search_mode,
            values=[
                "Tavily-General",
                "Tavily-News",
                "Tavily-Finance",
                "Duck-General",
                "Duck-News",
                "Bing-General"
            ],
            state="readonly",
            width=12,
            style='custom.TCombobox',  # 应用自定义样式
            bootstyle='info'
        )

        # 绑定事件实现下拉列表项效果
        search_combobox.bind("<<ComboboxSelected>>", self._reset_combobox_style)
        search_combobox.bind("<Enter>", lambda e: search_combobox.config(style='custom.TCombobox'))
        search_combobox.bind("<Leave>", self._reset_combobox_style)

        # 添加到界面
        search_combobox.pack(side=tk.RIGHT, padx=0)

        # 主聊天区域
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 聊天显示区域
        self.chat_text = tk.Text(self.main_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(self.main_frame, command=self.chat_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 控制面板
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X)

        self.deep_think_var = tk.BooleanVar()
        self.search_var = tk.BooleanVar()
        self.gold_fish_var = tk.BooleanVar()
        self.memory_enhance_var = tk.BooleanVar()

        ttk.Checkbutton(self.control_frame, text="深度思考", variable=self.deep_think_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="金鱼模式", variable=self.gold_fish_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="记忆增强", variable=self.memory_enhance_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="联网模式", variable=self.search_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)

        # 温度标签
        temp_label = ttk.Label(self.control_frame, text="温度")
        temp_label.pack(side=tk.LEFT, padx=(10, 0))

        # 主容器
        temp_container = ttk.Frame(self.control_frame)
        temp_container.pack(side=tk.LEFT, padx=(0, 0))

        # 创建Canvas
        self.temp_canvas = tk.Canvas(
            temp_container,
            width=185,
            height=60,
            bg='#f5f5dc',  # 奶油色背景
            highlightthickness=0
        )
        self.temp_canvas.pack()

        # 创建渐变色带（奶油蓝到奶油红）
        self.create_cream_gradient(15, 22, 165, 32)

        # 刻度标签
        for i, val in enumerate([0, 0.5, 1.0, 1.5]):
            x = 15 + (i / 3) * 150
            self.temp_canvas.create_text(
                x, 37,
                text=str(val),
                font=("Times New Roman", 7),
                fill='#000000'
            )
        self.temp_canvas.create_text(40, 37, text="严谨", font=("黑体", 7), fill='#000000')
        self.temp_canvas.create_text(90, 37, text="默认", font=("黑体", 7), fill='#000000')
        self.temp_canvas.create_text(140, 37, text="创意", font=("黑体", 7), fill='#000000')

        # 创建指针（同心圆）
        self.pointer = self.temp_canvas.create_oval(0, 0, 0, 0, fill='white', outline='#404040', width=1)
        self.pointer_inner = self.temp_canvas.create_oval(0, 0, 0, 0, fill='#0000ff', outline='')

        # 数值气泡
        self.bubble_bg = self.temp_canvas.create_polygon(0, 0, 0, 0, fill='white', outline='#c0c0c0')
        self.bubble_text = self.temp_canvas.create_text(0, 0, text="0.00",
                                                        font=("Times New Roman", 9))

        # 事件绑定
        self.temp_canvas.bind("<Button-1>", self.on_temp_click)
        self.temp_canvas.bind("<B1-Motion>", self.on_temp_drag)

        # 初始位置
        self.update_temp_ui(self.current_temperature)

        ttk.Button(self.control_frame, text="新对话", command=self.new_chat).pack(side=tk.LEFT)
        ttk.Button(self.control_frame, text="上传文件", command=self.upload_file).pack(side=tk.LEFT)

        # 输入区域
        # 定义自定义边框样式
        self.style.configure(
            "Bordered.TFrame",
            background="#eeeeee",  # 边框颜色（与主题协调）
            borderwidth=2  # 边框厚度
        )
        self.input_frame = ttk.Frame(self.main_frame, style="Bordered.TFrame", padding=5)
        self.input_frame.pack(fill=tk.BOTH, expand=False, side=tk.BOTTOM)
        # self.input_text = tk.Text(self.input_frame, height=3, wrap=tk.WORD, font=("宋体", 12))
        # self.input_text.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)
        # 输入文本框（设置边框）
        self.input_text = tk.Text(
            self.input_frame,
            height=3,
            wrap=tk.WORD,
            font=("宋体", 12),
            foreground="black",
            highlightthickness=1,  # 边框厚度
            highlightbackground="#000000",  # 边框颜色（聚焦时）
            highlightcolor="#0078d4",  # 边框颜色（未聚焦时）
        )
        self.input_text.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)
        self.send_button = ttk.Button(self.input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

    # 更新api的状态
    def update_api_balance(self):
        url = "https://api.deepseek.com/user/balance"
        payload = {}
        headers = {
            'Accept': 'application/json',
            'Authorization': "Bearer " + self.api_key,
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        new_balance = " "
        # 状态码200是正常
        if response.status_code == 200:
            getContent = json.loads(response.text)
            if getContent["is_available"]:
                new_balance = "API余额: "+getContent["balance_infos"][0]["total_balance"] + " " + getContent["balance_infos"][0]["currency"]
            else:
                new_balance = "API状态: 不可用"
        elif response.status_code == 400:
            new_balance = "API状态: 请求错误"
        elif response.status_code == 401:
            new_balance = "API状态: 无效"
        elif response.status_code == 402:
            new_balance = "API状态: 无余额"
        elif response.status_code == 422:
            new_balance = "API状态: 参数错误"
        elif response.status_code == 429:
            new_balance = "API状态: 连接过多"
        elif response.status_code == 500:
            new_balance = "API状态: 服务器错误"
        elif response.status_code == 503:
            new_balance = "API状态: 服务器繁忙"
        else:
            new_balance = "API状态: 未知错误"
        self.api_info.set(new_balance)
        return response.status_code

    # 定义样式重置方法
    def _reset_combobox_style(self, event=None):
        """重置Combobox样式并刷新下拉列表"""
        self.style.configure('custom.TCombobox', fieldbackground='white')
        self.style.map('custom.TCombobox',
                       fieldbackground=[('!disabled', 'white')])
        event.widget.update_idletasks()

    def create_cream_gradient(self, x1, y1, x2, y2):
        """创建奶油色渐变（蓝到红）"""
        for i in range(int(x1), int(x2)):
            ratio = (i - x1) / (x2 - x1)
            r = int(142 + 113 * ratio)  # 修正颜色计算
            g = int(142 - 142 * ratio)
            b = int(255 - 255 * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.temp_canvas.create_line(
                i, y1, i, y2,
                fill=color,
                width=2
            )

    def update_temp_ui(self, temperature):
        """更新温度UI组件"""
        temperature = max(0, min(temperature, 1.5))
        # 计算位置
        x = 15 + (temperature / 1.5) * 150
        y = 27

        # 更新指针
        self.temp_canvas.coords(self.pointer, x - 8, y - 8, x + 8, y + 8)
        self.temp_canvas.coords(self.pointer_inner, x - 5, y - 5, x + 5, y + 5)

        # 更新气泡
        bubble_x, bubble_y = x, y - 15
        self.temp_canvas.coords(self.bubble_bg,
                                bubble_x - 15, bubble_y - 8,
                                bubble_x + 15, bubble_y - 8,
                                bubble_x + 15, bubble_y + 8,
                                bubble_x, bubble_y + 12,
                                bubble_x - 15, bubble_y + 8)
        self.temp_canvas.coords(self.bubble_text, bubble_x, bubble_y)
        self.temp_canvas.itemconfig(self.bubble_text, text=f"{temperature:.2f}")

        # 更新内圆颜色
        ratio = temperature / 1.5
        r = int(142 + 113 * ratio)
        g = int(142 - 142 * ratio)
        b = int(255 - 255 * ratio)
        self.temp_canvas.itemconfig(self.pointer_inner, fill=f'#{r:02x}{g:02x}{b:02x}')

    def on_temp_click(self, event):
        """点击事件处理"""
        x = max(15, min(event.x, 165))
        temperature = ((x - 15) / 150) * 1.5
        self.current_temperature = round(temperature, 2)
        self.update_temp_ui(self.current_temperature)

    def on_temp_drag(self, event):
        """拖拽事件处理"""
        self.on_temp_click(event)
        # 触发温度变化回调
        if hasattr(self, 'temperature_callback'):
            self.temperature_callback()

    def format_text(self, text, align, style=None):
        """增强文本格式化功能"""
        tags = []
        if align == "right":
            tags.append("right_align")
        elif align == "left":
            tags.append("left_align")

        if style == "thinking":
            tags.append("duration_style")
            tags.append("thinking_style_chinese")

        # 插入带样式的文本
        self.chat_text.insert(tk.END, text, tuple(tags))

    def is_english(self, char):
        if char.isalnum() or char in string.punctuation:
            return True
        return False

    def display_file_upload(self, message):
        """显示用户消息（严格右对齐布局）"""
        self.chat_text.configure(state=tk.NORMAL)
        # 用户消息文本样式
        self.chat_text.tag_configure("user_msg_chinese",
                                     justify=tk.RIGHT,
                                     rmargin=10,
                                     font=("宋体", 12),
                                     spacing2=5,
                                     wrap=tk.WORD)
        # 用户消息文本样式
        self.chat_text.tag_configure("user_msg_english",
                                     justify=tk.RIGHT,
                                     rmargin=10,
                                     font=("Times New Roman", 12),
                                     spacing2=5,
                                     wrap=tk.WORD)
        # 时间戳样式
        self.chat_text.tag_configure("timestamp_right",
                                     justify=tk.RIGHT,
                                     font=("Times New Roman", 9),
                                     foreground="#000000")
        current_index = self.chat_text.index(tk.END)
        start_line = int(current_index.split('.')[0])
        self.chat_text.insert(tk.END, "\n", "timestamp_right")
        for char_message in message:
            if self.is_english(char_message):
                self.chat_text.insert(tk.END, char_message, "user_msg_english")
            else:
                self.chat_text.insert(tk.END, char_message, "user_msg_chinese")
        current_index = self.chat_text.index(tk.END)
        end_line = int(current_index.split('.')[0])
        self.chat_text.tag_configure('right-align', justify='right')
        for i in range(start_line, end_line + 1):
            self.chat_text.tag_add('right-align', f"{i}.0", f"{i}.end")
        # 强制右对齐检测
        self.chat_text.insert(tk.END, "\n")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def display_user_message(self, message):
        """显示用户消息（严格右对齐布局）"""
        self.chat_text.configure(state=tk.NORMAL)

        # 时间戳样式
        self.chat_text.tag_configure("timestamp_right",
                                     justify=tk.RIGHT,
                                     font=("Times New Roman", 9),
                                     foreground="#000000")

        # 用户消息文本样式
        self.chat_text.tag_configure("user_msg_chinese",
                                     justify=tk.RIGHT,
                                     rmargin=10,
                                     font=("宋体", 12),
                                     spacing2=5,
                                     wrap=tk.WORD)
        # 用户消息文本样式
        self.chat_text.tag_configure("user_msg_english",
                                     justify=tk.RIGHT,
                                     rmargin=10,
                                     font=("Times New Roman", 12),
                                     spacing2=5,
                                     wrap=tk.WORD)
        # 插入时间戳
        self.chat_text.insert(tk.END, "\n")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_text.insert(tk.END, f" [{timestamp}] ", "timestamp_right")
        self.chat_text.image_create(tk.END, image=self.user_photo, padx=10)  # 头像
        current_index = self.chat_text.index(tk.END)
        start_line = int(current_index.split('.')[0])
        self.chat_text.insert(tk.END, "\n", "timestamp_right")
        for char_message in message:
            if self.is_english(char_message):
                self.chat_text.insert(tk.END, char_message, "user_msg_english")
            else:
                self.chat_text.insert(tk.END, char_message, "user_msg_chinese")
        current_index = self.chat_text.index(tk.END)
        end_line = int(current_index.split('.')[0])
        self.chat_text.tag_configure('right-align', justify='right')
        for i in range(start_line, end_line + 1):
            self.chat_text.tag_add('right-align', f"{i}.0", f"{i}.end")
        # 强制右对齐检测
        self.chat_text.insert(tk.END, "\n")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def display_assistant_response(self, current_response):
        """显示助手回复（头像下方内容）"""
        self.chat_text.configure(state=tk.NORMAL)

        # 在头像下方插入回复内容
        self.chat_text.insert(tk.END, "\n")  # 换行到头像下方

        # 设置内容缩进与头像对齐
        self.chat_text.tag_configure("response_content_chinese",
                                     font=("宋体", 12),
                                     lmargin1=5,
                                     spacing2=5,
                                     wrap=tk.WORD)
        self.chat_text.tag_configure("response_content_english",
                                     font=("Times New Roman", 12),
                                     lmargin1=5,
                                     spacing2=5,
                                     wrap=tk.WORD)
        show_content = ""
        if "reasoning_content" in current_response:
            show_content += "[思考过程]\n" + current_response["reasoning_content"]
            show_content += "\n[思考答案]\n"
        if "content" in current_response:
            show_content += current_response["content"]
        for char_message in show_content:
            if self.is_english(char_message):
                self.chat_text.insert(tk.END, char_message, "response_content_english")
            else:
                self.chat_text.insert(tk.END, char_message, "response_content_chinese")
        self.chat_text.insert(tk.END, "\n")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def display_left_message(self, message, font_size):
        """显示助手回复（头像下方内容）"""
        self.chat_text.configure(state=tk.NORMAL)

        # 设置内容缩进与头像对齐
        self.chat_text.tag_configure("response_content_chinese",
                                     font=("宋体", font_size),
                                     lmargin1=5,
                                     spacing2=5,
                                     wrap=tk.WORD)
        self.chat_text.tag_configure("response_content_english",
                                     font=("Times New Roman", font_size),
                                     lmargin1=5,
                                     spacing2=5,
                                     wrap=tk.WORD)
        for char_message in message:
            if self.is_english(char_message):
                self.chat_text.insert(tk.END, char_message, "response_content_english")
            else:
                self.chat_text.insert(tk.END, char_message, "response_content_chinese")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def setup_bindings(self):
        self.history_list.bind("<Button-1>", self.load_chat)
        self.history_list.bind("<Button-3>", self.show_context_menu)
        self.input_text.bind("<Return>", self.on_enter_pressed)
        self.root.bind("<Control-Return>", lambda e: None)
        # 添加输入框事件绑定
        self.input_text.bind("<Key>", self.on_input_change)
        self.input_text.bind("<FocusIn>", self.on_focus_in)
        self.input_text.bind("<FocusOut>", self.on_focus_out)

    def update_history_list(self):
        self.history_list.delete(0, tk.END)
        for item in self.history:
            self.history_list.insert(tk.END, item["title"])

    def display_thinking_status(self):
        """在助手头像右侧显示思考状态"""
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.image_create(tk.END, image=self.deepseek_photo, padx=10)
        # 助手消息容器
        self.chat_text.tag_configure("assistant_header",
                                     lmargin1=20,
                                     spacing1=15)

        # 插入容器和头像
        self.thinking_start_index = self.chat_text.index("end-1c")
        self.chat_text.insert(tk.END, "  ", "assistant_header")

        # 思考状态样式
        self.chat_text.tag_configure("thinking_style_chinese",
                                     font=("宋体", 10, "italic"),
                                     foreground="#000000",
                                     lmargin1=10,
                                     spacing2=3)
        # 思考状态样式
        self.chat_text.tag_configure("thinking_style_english",
                                     font=("Times New Roman", 10, "italic"),
                                     foreground="#000000",
                                     lmargin1=10,
                                     spacing2=3)
        # 插入思考状态文本
        self.chat_text.insert(tk.END, " ", "thinking_style_chinese")
        self.thinking_end_index = self.chat_text.index("end-1c")
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def hide_thinking_status(self):
        """隐藏思考状态并显示总耗时"""
        self.thinking = False
        self.chat_text.configure(state=tk.NORMAL)
        elapsed = int(time.time() - self.start_time)

        # 替换思考状态
        self.chat_text.delete(self.thinking_start_index, self.thinking_end_index)

        # 耗时信息样式
        self.chat_text.tag_configure("duration_style",
                                     font=("Times New Roman", 10, "normal"),
                                     foreground="#000000",
                                     lmargin1=10)
        # 在头像右侧插入耗时信息
        self.chat_text.insert(self.thinking_start_index,
                              f"✓ 响应耗时 {elapsed} 秒",
                              ("duration_style", "thinking_style_chinese"))

        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def update_thinking_status(self):
        """更新对话框中的思考状态"""
        if self.thinking:
            elapsed = int(time.time() - self.start_time)
            self.chat_text.configure(state=tk.NORMAL)
            self.chat_text.delete(self.thinking_start_index, self.thinking_end_index)
            self.format_text(f"思考中... 已耗时 {elapsed} 秒", align="left", style="thinking")
            self.thinking_end_index = self.chat_text.index("end-1c")
            self.chat_text.configure(state=tk.DISABLED)
            self.root.after(1000, self.update_thinking_status)

    def update_chat_log(self):
        """保存当前对话到历史记录"""
        # 当前对话已经存入历史对话了
        if len(self.current_chat) != 0:
            if self.current_message == "":
                try:
                    self.history.pop(0)
                    self.current_history["messages"] = self.current_chat
                    self.history.insert(0, self.current_history)
                    with open(self.log_file, "w", encoding="utf-8") as f:
                        json.dump(self.history, f, ensure_ascii=False)
                    self.update_history_list()
                except Exception as e:
                    self.show_error(f"保存历史记录失败: {str(e)}")
            else:
                try:
                    # 添加到当前对话
                    if self.current_chat[-1]["role"] == "user":
                        self.current_chat[-1] = {
                            "role": "user",
                            "content": self.current_message
                        }
                    else:
                        self.current_chat.append({
                            "role": "user",
                            "content": self.current_message
                        })
                    self.current_history["messages"] = self.current_chat
                    self.history.pop(0)
                    self.history.insert(0, self.current_history)
                    with open(self.log_file, "w", encoding="utf-8") as f:
                        json.dump(self.history, f, ensure_ascii=False)
                    self.update_history_list()
                except Exception as e:
                    self.show_error(f"保存历史记录失败: {str(e)}")
        # 新对话
        else:
            try:
                # 添加到当前对话
                self.current_chat.append({
                    "role": "user",
                    "content": self.current_message
                })
                # 生成对话标题（取第一条消息的前20字符）
                if len(self.current_chat[0]["content"]) >= 20:
                    title = self.current_chat[0]["content"][:20]
                else:
                    title = self.current_chat[0]["content"]
                # 添加时间戳
                self.current_history = {
                    "title": f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} {title}",
                    "messages": self.current_chat,
                }
                # 添加到历史记录并保存
                self.history.insert(0, self.current_history)
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)
                self.update_history_list()
            except Exception as e:
                self.current_chat = []
                self.current_history = {}
                self.show_error(f"保存历史记录失败: {str(e)}")

    def send_message(self, event=None):
        self.current_message = self.input_text.get("1.0", tk.END).strip()
        if not self.current_message:
            return
        # 展示用户消息
        self.display_user_message(self.current_message)  # 调整到思考状态之前
        self.update_chat_log()
        # 联网搜索
        if self.search_var.get():
            search_content = self.search_message()
            self.current_message = search_content + self.current_message
        # 上传文件
        if len(self.upload_file_content) > 0:
            file_content = "请根据下列文档内容回答问题\n"
            for i in range(len(self.upload_file_content)):
                file_content += "文档" + f"{i+1}" + ":\n" + self.upload_file_name[i] + "\n" + self.upload_file_content[i] + "\n";
                self.display_file_upload("["+self.upload_file_name[i]+"]")
            for i in range(len(self.upload_file_content)):
                self.remove_file(0)
            self.current_message = file_content + self.current_message
            self.upload_file_flag = False
        self.update_chat_log()
        # 启动思考状态
        self.thinking = True
        self.start_time = time.time()
        self.display_thinking_status()
        self.update_thinking_status()

        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        # 创建API请求线程
        thread = threading.Thread(target=self.call_deepseek_api)
        thread.start()

    def search_message(self):
        search_content = ""
        search_key_words = self.deepseek_before_search()
        search_key_words.replace("\n", "")
        search_answer = ""
        if search_key_words == "":
            search_key_words = self.current_message
        if search_key_words != "":
            search_list = []
            search_mode = self.search_mode.get()
            #联网搜索
            if search_mode == "Tavily-General":
                search_list, search_answer = self.search_tavily(search_key_words, "general")
            elif search_mode == "Tavily-News":
                search_list, search_answer = self.search_tavily(search_key_words, "news")
            elif search_mode == "Tavily-Finance":
                search_list, search_answer = self.search_tavily(search_key_words, "finance")
            elif search_mode == "Duck-General":
                search_list = self.search_duck_normal(search_key_words)
            elif search_mode == "Duck-News":
                search_list = self.search_duck_news(search_key_words)
            elif search_mode == "Bing-General":
                search_list = self.search_bing_normal(search_key_words, page=1)

            # 网页有返回
            if len(search_list) > 0:
                search_content = "请根据下列网页的内容回答下面的问题，并在回答过程中引用相关网页，在结尾列出相关网页\n"
                self.display_file_upload("已搜索到相关[" + search_key_words + "]网页:)")
                for i in range(len(search_list)):
                    search_content += "网页" + f"{i + 1}" + ":\n" + search_list[i]["title"] + search_list[i]["url"] + "\n" + "内容：" + search_list[i]["content"];
            else:
                self.display_file_upload("搜索关键词[" + search_key_words + "]失败")
            if search_answer != "":
                self.display_left_message("[搜索简答]:" + search_answer + "\n", 12)
            else:
                self.display_left_message("\n",12)
        else:
            self.display_file_upload("[关键词为空]")
        return search_content

    def call_deepseek_api(self):
        api_chat = []
        if self.gold_fish_var.get():
            api_chat.append({"role": self.current_chat[-1]["role"],
                            "content": self.current_chat[-1]["content"]
                             })
        else:
            memory_enhance_flag = self.memory_enhance_var.get()
            for temp_chat in self.current_chat:
                if "reasoning_content" in temp_chat and memory_enhance_flag:
                    api_chat.append({"role": temp_chat["role"],
                                     "content": "[思考过程]\n" + temp_chat["reasoning_content"] + "\n[思考结果]\n" + temp_chat["content"]
                                     })
                else:
                    api_chat.append({"role": temp_chat["role"],
                                     "content": temp_chat["content"]
                                     })
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "messages": api_chat,
            "model": "deepseek-chat" if not self.deep_think_var.get() else "deepseek-reasoner",
            "temperature": self.current_temperature,
            "max_tokens": self.max_tokens.get(),
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response_data = response.json()
            self.current_content = ""
            if response.status_code == 200:
                self.hide_thinking_status()
                content = ""
                reasoning_content = ""
                current_response = {}
                for choiceTemp in response_data["choices"]:
                    content += choiceTemp["message"]["content"]
                if "reasoning_content" in response_data["choices"][0]["message"]:
                    for choiceTemp in response_data["choices"]:
                        reasoning_content += choiceTemp["message"]["reasoning_content"]
                    current_response = {
                        "role": "assistant",
                        "content": content,
                        "reasoning_content": reasoning_content,
                    }
                    self.current_chat.append(current_response)
                else:
                    current_response = {
                        "role": "assistant",
                        "content": content,
                    }
                    self.current_chat.append(current_response)
                self.display_assistant_response(current_response)
                self.current_message = ""
                self.update_chat_log()
            else:
                self.input_text.insert("end", self.current_message)
                self.current_message = ""
                self.current_chat.pop()
                self.current_history["messages"] = self.current_chat
                self.hide_thinking_status()
                self.show_error("API请求失败")
                self.api_key = self.get_api_key()
                self.config[0]["api-key"] = self.api_key
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
        except Exception as e:
            self.hide_thinking_status()
            self.show_error(str(e))

    def load_history(self):
        """加载历史记录文件"""
        self.history = []
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            else:
                self.history = []
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)


        except Exception as e:
            self.show_error(f"加载历史记录失败: {str(e)}")

    def delete_history(self, index):
        """删除指定历史记录"""
        try:
            if 0 <= index < len(self.history):
                del self.history[index]
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)
                self.update_history_list()
        except Exception as e:
            self.show_error(f"删除记录失败: {str(e)}")

    def show_context_menu(self, event):
        """显示右键删除菜单"""
        index = self.history_list.nearest(event.y)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="删除", command=lambda: self.delete_history(index))
        menu.post(event.x_root, event.y_root)

    def load_chat(self, event):
        """加载历史对话"""
        index = self.history_list.nearest(event.y)
        if 0 <= index < len(self.history):
            try:
                self.current_history = self.history[index]
                dateStringTemp = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                self.current_history["title"] = dateStringTemp + self.current_history["title"][len(dateStringTemp):]
                if not self.current_chat:
                    self.history[index] = self.history[0]
                    self.history.pop(0)
                    self.history.insert(0, self.current_history)
                else:
                    self.history.pop(index)
                    self.history.insert(0, self.current_history)
                self.current_chat = self.current_history["messages"]

                while (len(self.current_chat) > 0):
                    if self.current_chat[-1]["role"] == "user":
                        # 插入输入文本框文字
                        self.input_text.insert(tk.END, self.current_chat[-1]["content"])
                        self.current_message = ""
                        self.current_chat.pop()
                    else:
                        break
                else:
                    self.current_message = ""
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)
                self.update_history_list()
            except Exception as e:
                self.show_error(f"保存历史记录失败: {str(e)}")
            self.refresh_chat_display()

    def refresh_chat_display(self):
        """刷新聊天显示"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)
        for msg in self.current_chat:
            if msg["role"] == "user":
                self.display_user_message(msg["content"])
            else:
                self.chat_text.image_create(tk.END, image=self.deepseek_photo, padx=10)
                # 助手消息容器
                self.chat_text.tag_configure("assistant_header",
                                             lmargin1=20,
                                             spacing1=15)

                # 插入容器和头像
                self.thinking_start_index = self.chat_text.index("end-1c")
                self.chat_text.insert(tk.END, "  ", "assistant_header")

                # 思考状态样式
                self.chat_text.tag_configure("thinking_style",
                                             font=("宋体", 11, "italic", "normal"),
                                             foreground="#000000",
                                             lmargin1=10,
                                             spacing2=3)

                # 插入思考状态文本
                self.chat_text.insert(tk.END, "--历史对话:)\n", "thinking_style")
                self.display_assistant_response(msg)
        self.chat_text.yview(tk.END)

    def show_error(self, message):
        """显示错误信息"""
        messagebox.showerror("错误", message)

    def new_chat(self):
        """新建对话"""
        if self.current_chat:
            self.update_chat_log()
        self.current_chat = []
        self.current_message = ""
        self.current_history = {}
        self.refresh_chat_display()

    def upload_file(self):
        if len(self.upload_file_name) >= 5:
            self.show_error("最多只能上传5个文件")
            return
        """支持txt/docx/pdf的文件上传功能"""
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        try:
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            content = ""
            # 处理Word文档
            if ext == ".docx":
                try:
                    from docx import Document
                except ImportError:
                    self.show_error("请安装python-docx库：pip install python-docx")
                    return
                doc = Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            # 处理PDF文档
            elif ext == ".pdf":
                try:
                    from PyPDF2 import PdfReader
                except ImportError:
                    self.show_error("请安装PyPDF2库：pip install PyPDF2")
                    return
                with open(file_path, "rb") as f:
                    pdf = PdfReader(f)
                    # 处理加密PDF
                    if pdf.is_encrypted:
                        try:
                            pdf.decrypt("")  # 尝试空密码解密
                        except:
                            self.show_error("无法解密受保护的PDF文件")
                            return
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            content += text + "\n"
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            if content != "":
                self.upload_file_flag = True
                self.upload_file_content.append(content.replace("\n", ""))
                self.upload_file_name.append(file_name)
                # 更新界面显示
                self.show_file_icon(self.upload_file_name[-1], ext, len(self.upload_file_content[-1]))
            else:
                self.show_error("读不到文件里的内容T-T")
        except Exception as e:
            self.show_error(f"读取文件失败: {str(e)}")

    def show_file_icon(self, filename, ext, char_count):
        """显示文件图标并绑定提示"""
        # 获取对应图标
        icon = self.icon_images.get(ext, self.icon_images["default"])

        # 创建图标标签
        icon_label = ttk.Label(self.control_frame, image=icon)
        icon_label.image = icon  # 保持引用
        icon_label.pack(side=tk.LEFT, padx=2)
        self.upload_file_icons.append(icon_label)

        # 创建气泡提示时，将tooltip存储到icon_label的属性中
        self.create_bubble_tooltip(icon_label, filename, char_count)

        # 绑定右键事件
        def on_right_click(event):
            # 动态获取当前索引
            try:
                index = self.upload_file_icons.index(event.widget)
            except ValueError:
                return

            # 创建右键菜单
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(
                label="删除",
                command=lambda: self.remove_file(index)
            )

            # 修正后的菜单定位方式
            try:
                menu.tk.call('tk_popup', menu, event.x_root, event.y_root)
            finally:
                menu.grab_release()

        icon_label.bind("<Button-3>", on_right_click)

    def create_bubble_tooltip(self, widget, filename, char_count):
        """创建气泡样式提示框"""
        # 预先计算内容
        short_name = (filename[:10] + '...') if len(filename) > 10 else filename
        file_ext = filename.split(".")[-1]
        size_str = self.format_char_count(char_count)

        # 创建提示窗口
        tooltip = tk.Toplevel(widget.winfo_toplevel())
        # 将tooltip实例附加到widget对象上
        widget.tooltip = tooltip  # 新增此行关联提示窗口
        tooltip.wm_overrideredirect(True)
        tooltip.wm_attributes("-topmost", True)
        tooltip.withdraw()

        # 使用Canvas绘制气泡
        canvas = tk.Canvas(tooltip, bg="white", highlightthickness=0)
        canvas.pack()

        # 添加文本内容
        text_id = canvas.create_text(15, 15,
                                     text=f"{short_name}\n大小: {size_str}\n类型:{file_ext}",
                                     anchor="nw",
                                     font=("宋体", 10),
                                     fill="#000000")

        # 计算气泡尺寸
        bbox = canvas.bbox(text_id)
        padding = 1
        width = bbox[2] - bbox[0] + padding * 4 + 8
        height = bbox[3] - bbox[1] + padding * 4 + 8

        # 绘制气泡背景
        canvas.config(width=width, height=height)  # 增加高度给箭头留空间
        canvas.create_rounded_rect(padding, padding, width - padding, height - padding,
                                   radius=6,
                                   fill="white",
                                   outline="#000000")
        # 重新定位文本
        canvas.delete(text_id)
        text_id = canvas.create_text(15, 15,
                                     text=f"{short_name}\n大小: {size_str}\n类型:{file_ext}",
                                     anchor="nw",
                                     font=("宋体", 9),
                                     fill="#000000")
        canvas.coords(text_id, 2 * padding + 6, 2 * padding + 4)

        # 鼠标跟踪事件
        def track_mouse(event):
            x = widget.winfo_pointerx() + 12
            y = widget.winfo_pointery() - 10
            tooltip.geometry(f"+{x}+{y}")
            if not tooltip.winfo_viewable():
                tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        # 绑定事件
        widget.bind("<Enter>", lambda e: track_mouse(e))
        widget.bind("<Leave>", hide_tooltip)
        widget.bind("<Motion>", track_mouse)

    # 添加Canvas的圆角矩形绘制方法
    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        """在Canvas上创建圆角矩形"""
        points = [x1 + radius, y1,
                  x2 - radius, y1,
                  # x2, y1,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  #   x2, y2,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  #   x1, y2,
                  x1, y2 - radius,
                  x1, y1 + radius,
                  #   x1, y1,
                  x1 + radius, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    tk.Canvas.create_rounded_rect = create_rounded_rect

    def remove_file(self, index):
        """删除指定文件"""
        if 0 <= index < len(self.upload_file_name):
            del self.upload_file_name[index]
            del self.upload_file_content[index]
            # 销毁对应图标
            icon_label = self.upload_file_icons.pop(index)
            icon_label.destroy()  # 销毁图标标签
            # 销毁关联的气泡提示窗口
            if hasattr(icon_label, 'tooltip'):
                icon_label.tooltip.destroy()  # 新增此行销毁提示
            if len(self.upload_file_name) == 0:
                self.upload_file_flag = False

    @staticmethod
    def format_char_count(count):
        """格式化字符统计"""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        if count >= 1000:
            return f"{count / 1000:.1f}K"
        return f"{count}"

    def on_enter_pressed(self, event):
        """改进的跨平台回车键处理"""
        if not event.state & (0x4 | 0x1):  # 仅处理普通回车
            self.send_message()
            return "break"  # 阻止默认换行
        return None  # 允许组合键换

    def show_thinking_status(self):
        """显示思考状态"""
        self.status_var.set("思考中... 已耗时 0 秒")
        self.start_time = time.time()
        self.update_timer()

    def update_timer(self):
        """更新计时器"""
        if self.thinking:
            elapsed = int(time.time() - self.start_time)
            self.status_var.set(f"思考中... 已耗时 {elapsed} 秒")
            self.root.after(1000, self.update_timer)

    def on_input_change(self, event):
        """实时更新输入框状态"""
        self.root.after(10, self.adjust_input_height)

    def adjust_input_height(self):
        """自动调整输入框高度"""
        lines = int(self.input_text.index('end-1c').split('.')[0])
        self.input_text.configure(height=min(max(lines, 3), 8))

    def on_focus_in(self, event):
        """获得焦点时高亮显示"""
        self.input_text.configure(highlightbackground="#409EFF", highlightthickness=1)

    def on_focus_out(self, event):
        """失去焦点时恢复样式"""
        self.input_text.configure(highlightbackground="SystemButtonFace", highlightthickness=0)

    def check_widget_hierarchy(self):
        """打印组件层级信息用于调试"""
        print("Widget hierarchy:")

        def print_children(widget, indent=0):
            print(' ' * indent + str(widget))
            for child in widget.winfo_children():
                print_children(child, indent + 2)

        print_children(self.root)

    def force_redraw(self):
        """强制重绘界面"""
        self.root.update_idletasks()
        self.root.update()

    def on_window_resize(self, event):
        """窗口大小改变时动态调整布局参数"""
        win_width = self.root.winfo_width()
        # 动态计算边距
        new_lmargin = max(1200, int(win_width))
        self.chat_text.tag_configure("right_align", lmargin1=new_lmargin)
        self.chat_text.tag_configure("timestamp_right", lmargin1=new_lmargin)

    def search_bing_normal(self, query: str, page: int = 1):
        """
        Bing 搜索爬虫
        :param query: 搜索关键词
        :param page: 页码（每页约10条结果）
        :return: 包含标题、链接、描述的字典列表
        """
        # 自定义请求头（模拟浏览器）
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            #"Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.bing.com/",
        }

        # 代理池（可选）
        PROXIES = {
            # "http": "http://your_proxy_ip:port",
            # "https": "http://your_proxy_ip:port"
        }
        base_url = "https://www.bing.com/search"
        params = {
            "q": query,
            "first": (page - 1) * 10 + 1,  # Bing 分页参数
      #      "setmkt": lang
        }

        try:
            # 发送请求（添加随机延时防止封禁）
            time.sleep(random.uniform(1, 3))
            response = requests.get(
                base_url,
                params=params,
                headers=HEADERS,
                proxies=PROXIES,
                timeout=10
            )
            response.raise_for_status()  # 检查HTTP状态码

            # 解析HTML
            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # 定位搜索结果条目（根据Bing最新HTML结构调整）
            for item in soup.select("li.b_algo"):
                title_elem = item.select_one("h2 a")
                url = title_elem.get("href") if title_elem else None
                title = title_elem.get_text(strip=True) if title_elem else "No Title"

                # 描述可能在多个位置
                description_elem = item.select_one(".b_caption p, .b_algoSlug")
                description = description_elem.get_text(strip=True) if description_elem else "No Description"
                description.replace("\n", "")
                results.append({
                    "title": title,
                    "url": url,
                    "content": description
                })
            return results
        except Exception as e:
            print(f"[ERROR] 搜索失败: {str(e)}")
            return []

    def get_tavily_api_key(self):
        """弹出输入框获取API密钥"""
        # 使用父窗口作为对话框的父组件
        api_key = simpledialog.askstring(
            "tavily-API",
            "请输入您的tavily-API密钥:)",
            parent=self.root,  # 根据实际父窗口调整这个参数
        )
        # 处理取消输入的情况
        if api_key is None:
            return None

        # 处理空输入的情况
        if not api_key.strip():
            self.show_error("API密钥不能为空")
            return None
        return api_key

    def renew_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False)
        except Exception as e:
            self.show_error(str(e))

    def search_tavily(self, search_query, topic_mode):
        search_list = []
        search_answer = ""
        if self.tavily_api_key == "" or self.tavily_api_key == "tavily-api-key":
            self.tavily_api_key = self.get_tavily_api_key()
            self.config[0]["tavily-api-key"] = self.tavily_api_key
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False)
        try:
            client = TavilyClient(self.tavily_api_key)
            response = client.search(
                query=search_query,
                topic=topic_mode,
                search_depth="advanced",
                max_results=10,
                include_answer="advanced"
            )
            search_list = response["results"]
            search_answer = response["answer"]
        except Exception as e:
            self.show_error(str(e))
            self.tavily_api_key = self.get_tavily_api_key()
            self.config[0]["tavily-api-key"] = self.tavily_api_key
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False)
        return search_list, search_answer

    def search_duck_normal(self, search_query):
        search_list = []
        try:
            search_list = DDGS().text(search_query, max_results=10, safesearch='off')
        except Exception as e:
            messagebox.showinfo("DeepSeek For MoonOrange", f"无法连接到DuckDuckGo,可能需要开启VPN:)\n失败原因:{str(e)}")
        #格式统一到"title","url","content"
        if len(search_list) > 0:
            for i in range(len(search_list)):
                search_list[i]["url"] = search_list.pop("href")
                search_list[i]["content"] = search_list.pop("body")
        return search_list

    def search_duck_news(self, search_query):
        search_list = []
        try:
            search_list = DDGS().news(search_query, max_results=10, safesearch='off')
        except Exception as e:
            messagebox.showinfo("DeepSeek For MoonOrange", f"无法连接到DuckDuckGo,可能需要开启VPN:)\n失败原因:{str(e)}")
        # 格式统一到"title","url","content"
        if len(search_list) > 0:
            for i in range(len(search_list)):
                search_list[i]["url"] = search_list.pop("href")
                search_list[i]["content"] = search_list.pop("body")
        return search_list

    def renew_max_tokens(self):
        """弹出输入框获取API密钥"""
        # 使用父窗口作为对话框的父组件
        max_tokens = simpledialog.askinteger(
            "DeepSeek-MAX-Tokens",
            "请输入输出tokens最大限制数(1至8192之间的整数):)",
            parent=self.root,  # 根据实际父窗口调整这个参数
        )
        # 处理取消输入的情况
        if max_tokens is None:
            return None

        if max_tokens > 8192 or max_tokens <= 0:
            self.show_error("需要1至8192之间的整数")
        else:
            self.max_tokens.set(max_tokens)
            try:
                self.config[0]["max_tokens"] = str(self.max_tokens.get())
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
            except Exception as e:
                self.show_error(e)


    def renew_api_key(self):
        """弹出输入框获取API密钥"""
        # 使用父窗口作为对话框的父组件
        api_key = simpledialog.askstring(
            "DeepSeek-API",
            "请输入您的DeepSeek-API密钥:)",
            parent=self.root,  # 根据实际父窗口调整这个参数
        )
        # 处理取消输入的情况
        if api_key is None:
            return None

        # 处理空输入的情况
        if not api_key.strip():
            self.show_error("API密钥不能为空")
            return None

        url = "https://api.deepseek.com/user/balance"
        payload = {}
        headers = {
            'Accept': 'application/json',
            'Authorization': "Bearer " + api_key,
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        new_balance = " "
        # 状态码200是正常
        if response.status_code == 200:
            getContent = json.loads(response.text)
            if getContent["is_available"]:
                new_balance = "API余额: " + getContent["balance_infos"][0]["total_balance"] + " " + \
                              getContent["balance_infos"][0]["currency"]
                messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
            else:
                new_balance = "API状态: 不可用"
                messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
        elif response.status_code == 400:
            new_balance = "API状态: 请求错误"
            messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
        elif response.status_code == 401:
            self.show_error("更新API失败，API状态: 无效")
        elif response.status_code == 402:
            new_balance = "API状态: 无余额"
            messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
        elif response.status_code == 422:
            new_balance = "API状态: 参数错误"
            messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
        elif response.status_code == 429:
            new_balance = "API状态: 连接过多"
            messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
        elif response.status_code == 500:
            new_balance = "API状态: 服务器错误"
            messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
        elif response.status_code == 503:
            new_balance = "API状态: 服务器繁忙"
            messagebox.showinfo("DeepSeek For MoonOrange", "更新API成功:)\n" + new_balance)
        else:
            self.show_error("更新API失败，API状态: 未知错误")
        if response.status_code not in [200, 400, 402, 422, 429, 500, 503]:
            self.api_info.set(new_balance)
            try:
                self.api_key = api_key
                self.config[0]["api-key"] = self.api_key
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
            except Exception as e:
                self.show_error(e)

    def deepseek_before_search(self):
        api_chat = []
        if self.gold_fish_var.get():
            api_chat.append({"role": self.current_chat[-1]["role"],
                             "content": self.current_chat[-1]["content"]
                             })
        else:
            memory_enhance_flag = self.memory_enhance_var.get()
            for temp_chat in self.current_chat:
                if "reasoning_content" in temp_chat and memory_enhance_flag:
                    api_chat.append({"role": temp_chat["role"],
                                     "content": "[思考过程]\n" + temp_chat["reasoning_content"] + "\n[思考结果]\n" + temp_chat[
                                         "content"]
                                     })
                else:
                    api_chat.append({"role": temp_chat["role"],
                                     "content": temp_chat["content"]
                                     })
        if api_chat[-1]["role"] == "user":
            api_chat[-1]["content"] = "如果我想知道这个问题的答案:" + api_chat[-1]["content"] + "\n我应该去网络上搜索什么内容，请不需要说明，不要有任何标点或者符号包括空格，直接给出输入搜索引擎的内容"
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "messages": api_chat,
            "model": "deepseek-chat",
            "temperature": self.current_temperature,
            "max_tokens": 20,
        }
        search_key_words = ""
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response_data = response.json()
            if response.status_code == 200:
                for choiceTemp in response_data["choices"]:
                    search_key_words += choiceTemp["message"]["content"]
            else:
                self.show_error("API请求失败")
                self.api_key = self.get_api_key()
                self.config[0]["api-key"] = self.api_key
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
        except Exception as e:
            self.show_error(str(e))
        return search_key_words

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChat(root)
    root.mainloop()
