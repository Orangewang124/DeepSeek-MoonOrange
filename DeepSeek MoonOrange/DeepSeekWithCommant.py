import string
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font
from ttkbootstrap import Style  # 第三方美化库
from PIL import Image, ImageTk  # 图像处理库
import json
import time
import threading  # 多线程支持
import requests  # HTTP请求库
import os
import datetime
import sys
from bs4 import BeautifulSoup  # HTML解析库
from duckduckgo_search import DDGS  # 搜索引擎库
from tavily import TavilyClient  # 搜索API客户端
import random

class DeepSeekChat:
    def __init__(self, root):
        # 初始化主窗口
        self.root = root
        self.root.title("DeepSeek For MoonOrange")
        root.iconbitmap(self.resource_path("deepseek.ico"))  # 设置窗口图标
        self.root.geometry("1200x800")  # 初始窗口尺寸

        # 初始化变量
        self.current_message = ""  # 当前输入消息
        self.current_chat = []  # 当前聊天记录
        self.current_history = {}  # 当前会话历史
        self.current_content = ""  # 当前内容
        self.history = []  # 历史会话记录
        self.log_file = "chat_history.json"  # 历史记录存储文件
        self.load_history()  # 加载历史记录
        
        # API相关配置
        self.api_key = "your-api-key"  # DeepSeek API密钥占位符
        self.tavily_api_key = "tavily-api-key"  # Tavily搜索API密钥占位符
        self.config = {}  # 配置字典
        self.theme_style = "litera"  # 默认主题样式
        self.config_file = "chat_config.json"  # 配置文件
        
        # 状态控制变量
        self.thinking = False  # 是否正在处理中
        self.thinking_start_index = None  # 处理中消息起始位置
        self.thinking_end_index = None  # 处理中消息结束位置
        self.current_temperature = 1.0  # 模型温度参数
        self.upload_file_flag = False  # 文件上传标志
        self.upload_file_content = []  # 上传文件内容
        self.upload_file_name = []  # 上传文件名
        self.upload_file_icons = []  # 文件图标缓存
        self.search_mode = tk.StringVar(value="Bing-General")  # 搜索模式选择

        # 预加载文件类型图标
        self.icon_images = {
            "default": ImageTk.PhotoImage(
                Image.open(self.resource_path("deepseekFile.png")).resize((20, 20))
            )
        }
        self.load_images()  # 加载其他图片资源

        # 窗口调整事件绑定
        self.root.bind("<Configure>", self.on_window_resize)

        # 界面初始化
        self.style = Style(theme=self.theme_style)  # 应用ttkbootstrap样式
        self.ini_style()  # 自定义样式初始化
        self.create_widgets()  # 创建界面组件
        self.setup_bindings()  # 设置事件绑定
        self.input_text.focus_set()  # 焦点设置到输入框

        # 加载配置和历史记录
        self.load_config()
        self.load_history()

        # 显示初始提示信息
        self.display_left_message(
            "本项目完全开源于https://github.com/Orangewang124/DeepSeek-MoonOrange不能用于任何盈利目的\n如果觉得有意思就帮我Star一下呗:)", 
            10
        )

    def ini_style(self):
        """自定义界面样式配置"""
        # Combobox样式配置
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
                          ('hover', '#f0f0f0'),  # 鼠标悬停背景色
                          ('active', 'white'),   # 激活状态背景
                          ('!disabled', 'white') # 正常状态背景
                      ],
                      foreground=[
                          ('hover', 'black'),  # 悬停文字颜色
                          ('active', 'black'), 
                          ('!disabled', 'black')
                      ],
                      background=[
                          ('hover', '#f0f0f0'),  # 下拉按钮背景
                          ('active', 'white'),
                          ('!disabled', 'white')
                      ])

    def resource_path(self, relative_path):
        """获取资源文件的绝对路径（支持打包后的路径）"""
        if hasattr(sys, '_MEIPASS'):
            # 打包后的临时目录
            base_path = sys._MEIPASS  
        else:
            # 开发环境当前目录
            base_path = os.path.abspath(".")  
        return os.path.join(base_path, relative_path)

    def get_api_key(self):
        """获取API密钥的对话框"""
        api_key = simpledialog.askstring(
            "DeepSeek-API",
            "请输入您的DeepSeek-API密钥:)",
            parent=self.root  # 父窗口设置
        )
        
        # 处理取消输入
        if api_key is None:
            return None  
            
        # 处理空输入
        if not api_key.strip():
            self.show_error("API密钥不能为空")
            return None
            
        return api_key
    
    def load_config(self):
        """加载应用程序配置"""
        self.config = []  # 初始化配置列表
        try:
            # 检查配置文件是否存在
            if os.path.exists(self.config_file):
                # 读取配置文件
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                    
                    # 检查并获取API密钥
                    if "api-key" in self.config[0]:
                        self.api_key = self.config[0]["api-key"]
                    else:
                        # 如果配置中没有API密钥则弹出输入框获取
                        self.api_key = self.get_api_key()
                        
                    # 检查并获取主题样式
                    if "theme_style" in self.config[0]:
                        self.theme_style = self.config[0]["theme_style"]
                    else:
                        # 使用默认主题
                        self.theme_style = "litera"
                        self.config[0]["theme_style"] = "litera"
                        
                    # 检查并获取Tavily搜索API密钥
                    if "tavily-api-key" in self.config[0]:
                        self.tavily_api_key = self.config[0]["tavily-api-key"]
                    else:
                        # 使用默认占位符
                        self.tavily_api_key = "tavily-api-key"
                        self.config[0]["tavily-api-key"] = "tavily-api-key"
                
                # 二次验证API密钥是否为默认值
                if self.api_key == "your-api-key":
                    self.api_key = self.get_api_key()
                    self.config[0]["api-key"] = self.api_key
                
                # 保存更新后的配置
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
            else:
                # 创建默认配置文件
                self.config = [{
                    "api-key": "your-api-key",
                    "theme_style": "litera",
                    "tavily-api-key": "tavily-api-key"
                }]
                # 初始化时获取API密钥
                self.api_key = self.get_api_key()
                self.config[0]["api-key"] = self.api_key
                # 写入新配置文件
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False)
        except Exception as e:
            self.show_error(e)  # 显示错误信息

    # 在主窗口显示后强制执行
    def show_window(self):
        """显示主窗口并初始化输入框状态"""
        self.root.deiconify()  # 显示被隐藏的窗口
        self.input_text.tkraise()  # 确保输入框在视图最上层
        self.input_text.configure(state=tk.NORMAL)  # 启用输入框
        self.input_text.focus_force()  # 强制聚焦到输入框
        
        # 通过延迟操作确保输入框正常工作
        self.root.after(100, lambda: self.input_text.insert(tk.END, " "))  # 插入空格
        self.root.after(200, lambda: self.input_text.delete("end-1c"))  # 删除空格

    def verify_input_visibility(self):
        """调试方法：验证输入框可见性和布局参数"""
        print(f"输入框可见: {self.input_text.winfo_viewable()}")
        print(f"输入框尺寸: {self.input_text.winfo_width()}x{self.input_text.winfo_height()}")
        print(f"输入框位置: ({self.input_text.winfo_x()}, {self.input_text.winfo_y()})")
        
        # 调试用样式（需提前定义Debug.TFrame样式）
        self.input_frame.configure(style='Debug.TFrame')
        self.root.update()  # 强制刷新界面

    def load_images(self):
        """加载界面所需的图片资源"""
        # 加载用户头像（需准备user_penguin.png文件）
        user_img = Image.open(self.resource_path("user_penguin.png")).resize((40, 40))
        # 加载DeepSeek机器人头像（需准备deepseek.png文件）
        deepseek_img = Image.open(self.resource_path("deepseek.png")).resize((40, 40))
        
        # 转换为Tkinter可用的图片格式
        self.user_photo = ImageTk.PhotoImage(user_img)
        self.deepseek_photo = ImageTk.PhotoImage(deepseek_img)
    
    def create_widgets(self):
        """创建应用程序界面组件"""
        
        # 历史记录面板
        self.history_frame = ttk.Frame(self.root, width=500)  # 左侧历史记录区域
        self.history_frame.pack(side=tk.LEFT, fill=tk.Y)  # 固定在左侧，垂直填充
        self.history_list = tk.Listbox(self.history_frame)  # 历史记录列表
        self.history_list.pack(fill=tk.BOTH, expand=True)  # 填充整个区域
        self.update_history_list()  # 更新历史记录列表内容

        # 底部复选框面板（新增底部控制栏）
        self.left_control_frame = ttk.Frame(self.history_frame)  # 底部控制栏容器
        self.left_control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=5)  # 固定在底部

        # 添加"联网引擎"标签和复选框
        ttk.Label(
            self.left_control_frame,
            text="联网引擎：",
            font=('宋体', 10),
            anchor='e'  # 文本右对齐
        ).pack(side=tk.LEFT, padx=(0, 0))  # 固定在左侧

        # 在界面布局部分
        search_combobox = ttk.Combobox(
            self.left_control_frame,
            textvariable=self.search_mode,  # 绑定搜索模式变量
            values=[
                "Tavily-General",  # Tavily通用搜索
                "Tavily-News",     # Tavily新闻搜索
                "Tavily-Finance",  # Tavily财经搜索
                "Duck-General",    # DuckDuckGo通用搜索
                "Duck-News",      # DuckDuckGo新闻搜索
                "Bing-General"    # Bing通用搜索
            ],
            state="readonly",  # 只读模式
            width=12,           # 宽度
            style='custom.TCombobox',  # 应用自定义样式
            bootstyle='info'    # 使用info主题
        )
        # 绑定事件实现下拉列表项效果
        search_combobox.bind("<<ComboboxSelected>>", self._reset_combobox_style)  # 选择事件
        search_combobox.bind("<Enter>", lambda e: search_combobox.config(style='custom.TCombobox'))  # 鼠标进入
        search_combobox.bind("<Leave>", self._reset_combobox_style)  # 鼠标离开
        search_combobox.pack(side=tk.RIGHT, padx=0)  # 固定在右侧

        # 主聊天区域
        self.main_frame = ttk.Frame(self.root)  # 右侧主聊天区域
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)  # 填充剩余空间

        # 聊天显示区域
        self.chat_text = tk.Text(self.main_frame, wrap=tk.WORD)  # 聊天内容显示区域
        scrollbar = ttk.Scrollbar(self.main_frame, command=self.chat_text.yview)  # 滚动条
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)  # 固定在右侧
        self.chat_text.configure(yscrollcommand=scrollbar.set)  # 绑定滚动条
        self.chat_text.pack(fill=tk.BOTH, expand=True)  # 填充整个区域

        # 控制面板
        self.control_frame = ttk.Frame(self.main_frame)  # 底部控制面板
        self.control_frame.pack(fill=tk.X)  # 水平填充

        # 定义控制选项变量
        self.deep_think_var = tk.BooleanVar()  # 深度思考模式
        self.search_var = tk.BooleanVar()      # 联网模式
        self.gold_fish_var = tk.BooleanVar()   # 金鱼模式
        self.memory_enhance_var = tk.BooleanVar()  # 记忆增强模式

        # 添加控制选项复选框
        ttk.Checkbutton(self.control_frame, text="深度思考", variable=self.deep_think_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="金鱼模式", variable=self.gold_fish_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="记忆增强", variable=self.memory_enhance_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="联网模式", variable=self.search_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)

        # 温度标签
        temp_label = ttk.Label(self.control_frame, text="温度")  # 温度控制标签
        temp_label.pack(side=tk.LEFT, padx=(10, 0))  # 固定在左侧

        # 主容器
        temp_container = ttk.Frame(self.control_frame)  # 温度控制容器
        temp_container.pack(side=tk.LEFT, padx=(0, 0))  # 固定在左侧

        # 创建Canvas
        self.temp_canvas = tk.Canvas(
            temp_container,
            width=185,  # 宽度
            height=60,  # 高度
            bg='#f5f5dc',  # 奶油色背景
            highlightthickness=0  # 无边框
        )
        self.temp_canvas.pack()

        # 创建渐变色带（奶油蓝到奶油红）
        self.create_cream_gradient(15, 22, 165, 32)

        # 刻度标签
        for i, val in enumerate([0, 0.5, 1.0, 1.5]):
            x = 15 + (i / 3) * 150  # 计算刻度位置
            self.temp_canvas.create_text(
                x, 37,
                text=str(val),
                font=("Times New Roman", 7),
                fill='#000000'
            )
        # 添加描述性文本
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
        self.temp_canvas.bind("<Button-1>", self.on_temp_click)  # 鼠标点击
        self.temp_canvas.bind("<B1-Motion>", self.on_temp_drag)  # 鼠标拖动

        # 初始位置
        self.update_temp_ui(self.current_temperature)

        # 添加功能按钮
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

        # 发送按钮
        self.send_button = ttk.Button(self.input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)
    
    # 定义样式重置方法
    def _reset_combobox_style(self, event=None):
        """重置Combobox样式并刷新下拉列表"""
        self.style.configure('custom.TCombobox', fieldbackground='white')  # 设置背景为白色
        self.style.map('custom.TCombobox',
                       fieldbackground=[('!disabled', 'white')])  # 确保非禁用状态背景为白色
        event.widget.update_idletasks()  # 强制刷新组件

    def create_cream_gradient(self, x1, y1, x2, y2):
        """创建奶油色渐变（蓝到红）"""
        for i in range(int(x1), int(x2)):
            ratio = (i - x1) / (x2 - x1)  # 计算当前点的比例
            r = int(142 + 113 * ratio)  # 红色分量计算
            g = int(142 - 142 * ratio)  # 绿色分量计算
            b = int(255 - 255 * ratio)  # 蓝色分量计算
            color = f'#{r:02x}{g:02x}{b:02x}'  # 生成十六进制颜色值
            self.temp_canvas.create_line(
                i, y1, i, y2,
                fill=color,  # 设置线条颜色
                width=2  # 线条宽度
            )

    def update_temp_ui(self, temperature):
        """更新温度UI组件"""
        temperature = max(0, min(temperature, 1.5))  # 限制温度范围在0到1.5之间
        # 计算指针位置
        x = 15 + (temperature / 1.5) * 150
        y = 27
        # 更新指针位置
        self.temp_canvas.coords(self.pointer, x - 8, y - 8, x + 8, y + 8)  # 外圆
        self.temp_canvas.coords(self.pointer_inner, x - 5, y - 5, x + 5, y + 5)  # 内圆
        # 更新气泡位置
        bubble_x, bubble_y = x, y - 15
        self.temp_canvas.coords(self.bubble_bg,
                                bubble_x - 15, bubble_y - 8,
                                bubble_x + 15, bubble_y - 8,
                                bubble_x + 15, bubble_y + 8,
                                bubble_x, bubble_y + 12,
                                bubble_x - 15, bubble_y + 8)  # 气泡多边形
        self.temp_canvas.coords(self.bubble_text, bubble_x, bubble_y)  # 气泡文本
        self.temp_canvas.itemconfig(self.bubble_text, text=f"{temperature:.2f}")  # 更新文本
        # 更新内圆颜色
        ratio = temperature / 1.5
        r = int(142 + 113 * ratio)
        g = int(142 - 142 * ratio)
        b = int(255 - 255 * ratio)
        self.temp_canvas.itemconfig(self.pointer_inner, fill=f'#{r:02x}{g:02x}{b:02x}')  # 设置内圆颜色

    def on_temp_click(self, event):
        """点击事件处理"""
        x = max(15, min(event.x, 165))  # 限制点击范围
        temperature = ((x - 15) / 150) * 1.5  # 计算温度值
        self.current_temperature = round(temperature, 2)  # 四舍五入保留两位小数
        self.update_temp_ui(self.current_temperature)  # 更新UI

    def on_temp_drag(self, event):
        """拖拽事件处理"""
        self.on_temp_click(event)  # 调用点击事件处理
        # 触发温度变化回调
        if hasattr(self, 'temperature_callback'):
            self.temperature_callback()  # 执行回调函数

    def format_text(self, text, align, style=None):
        """增强文本格式化功能"""
        tags = []
        if align == "right":
            tags.append("right_align")  # 右对齐标签
        elif align == "left":
            tags.append("left_align")  # 左对齐标签
        if style == "thinking":
            tags.append("duration_style")  # 思考样式标签
            tags.append("thinking_style_chinese")  # 中文思考样式标签
        # 插入带样式的文本
        self.chat_text.insert(tk.END, text, tuple(tags))

    def is_english(self, char):
        """判断字符是否为英文"""
        if char.isalnum() or char in string.punctuation:
            return True
        return False

    def display_file_upload(self, message):
        """显示用户消息（严格右对齐布局）"""
        self.chat_text.configure(state=tk.NORMAL)  # 启用文本编辑
        # 用户消息文本样式（中文）
        self.chat_text.tag_configure("user_msg_chinese",
                                     justify=tk.RIGHT,  # 右对齐
                                     rmargin=10,  # 右边距
                                     font=("宋体", 12),  # 字体
                                     spacing2=5,  # 行间距
                                     wrap=tk.WORD)  # 自动换行
        # 用户消息文本样式（英文）
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
                                     foreground="#000000")  # 前景色
        current_index = self.chat_text.index(tk.END)  # 获取当前文本末尾位置
        start_line = int(current_index.split('.')[0])  # 获取起始行号
        self.chat_text.insert(tk.END, "\n", "timestamp_right")  # 插入时间戳
        for char_message in message:
            if self.is_english(char_message):
                self.chat_text.insert(tk.END, char_message, "user_msg_english")  # 插入英文消息
            else:
                self.chat_text.insert(tk.END, char_message, "user_msg_chinese")  # 插入中文消息
        current_index = self.chat_text.index(tk.END)
        end_line = int(current_index.split('.')[0])  # 获取结束行号
        self.chat_text.tag_configure('right-align', justify='right')  # 配置右对齐标签
        for i in range(start_line, end_line + 1):
            self.chat_text.tag_add('right-align', f"{i}.0", f"{i}.end")  # 应用右对齐标签
        # 强制右对齐检测
        self.chat_text.insert(tk.END, "\n")
        self.chat_text.see(tk.END)  # 滚动到末尾
        self.chat_text.configure(state=tk.DISABLED)  # 禁用文本编辑
    
    def display_user_message(self, message):
        """显示用户消息（严格右对齐布局）"""
        self.chat_text.configure(state=tk.NORMAL)  # 启用文本编辑

        # 时间戳样式
        self.chat_text.tag_configure("timestamp_right",
                                     justify=tk.RIGHT,  # 右对齐
                                     font=("Times New Roman", 9),  # 字体
                                     foreground="#000000")  # 前景色

        # 用户消息文本样式（中文）
        self.chat_text.tag_configure("user_msg_chinese",
                                     justify=tk.RIGHT,  # 右对齐
                                     rmargin=10,  # 右边距
                                     font=("宋体", 12),  # 字体
                                     spacing2=5,  # 行间距
                                     wrap=tk.WORD)  # 自动换行

        # 用户消息文本样式（英文）
        self.chat_text.tag_configure("user_msg_english",
                                     justify=tk.RIGHT,
                                     rmargin=10,
                                     font=("Times New Roman", 12),
                                     spacing2=5,
                                     wrap=tk.WORD)

        # 插入时间戳
        self.chat_text.insert(tk.END, "\n")  # 换行
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")  # 获取当前时间
        self.chat_text.insert(tk.END, f" [{timestamp}] ", "timestamp_right")  # 插入时间戳
        self.chat_text.image_create(tk.END, image=self.user_photo, padx=10)  # 插入用户头像

        # 记录消息起始行
        current_index = self.chat_text.index(tk.END)
        start_line = int(current_index.split('.')[0])
        self.chat_text.insert(tk.END, "\n", "timestamp_right")  # 换行

        # 插入消息内容
        for char_message in message:
            if self.is_english(char_message):  # 判断是否为英文
                self.chat_text.insert(tk.END, char_message, "user_msg_english")  # 插入英文消息
            else:
                self.chat_text.insert(tk.END, char_message, "user_msg_chinese")  # 插入中文消息

        # 记录消息结束行
        current_index = self.chat_text.index(tk.END)
        end_line = int(current_index.split('.')[0])

        # 配置右对齐标签
        self.chat_text.tag_configure('right-align', justify='right')
        # 应用右对齐标签
        for i in range(start_line, end_line + 1):
            self.chat_text.tag_add('right-align', f"{i}.0", f"{i}.end")

        # 强制右对齐检测
        self.chat_text.insert(tk.END, "\n")
        self.chat_text.see(tk.END)  # 滚动到末尾
        self.chat_text.configure(state=tk.DISABLED)  # 禁用文本编辑

    def display_assistant_response(self, current_response):
        """显示助手回复（头像下方内容）"""
        self.chat_text.configure(state=tk.NORMAL)  # 启用文本编辑

        # 在头像下方插入回复内容
        self.chat_text.insert(tk.END, "\n")  # 换行到头像下方

        # 设置内容缩进与头像对齐
        self.chat_text.tag_configure("response_content_chinese",
                                     font=("宋体", 12),  # 中文字体
                                     lmargin1=5,  # 左边距
                                     spacing2=5,  # 行间距
                                     wrap=tk.WORD)  # 自动换行
        self.chat_text.tag_configure("response_content_english",
                                     font=("Times New Roman", 12),  # 英文字体
                                     lmargin1=5,
                                     spacing2=5,
                                     wrap=tk.WORD)

        # 构建显示内容
        show_content = ""
        if "reasoning_content" in current_response:  # 如果有思考过程
            show_content += "[思考过程]\n" + current_response["reasoning_content"]
            show_content += "\n[思考答案]\n"
        if "content" in current_response:  # 如果有最终答案
            show_content += current_response["content"]

        # 插入内容
        for char_message in show_content:
            if self.is_english(char_message):  # 判断是否为英文
                self.chat_text.insert(tk.END, char_message, "response_content_english")  # 插入英文内容
            else:
                self.chat_text.insert(tk.END, char_message, "response_content_chinese")  # 插入中文内容

        self.chat_text.insert(tk.END, "\n")  # 换行
        self.chat_text.see(tk.END)  # 滚动到末尾
        self.chat_text.configure(state=tk.DISABLED)  # 禁用文本编辑

    def display_left_message(self, message, font_size):
        """显示助手回复（头像下方内容）"""
        self.chat_text.configure(state=tk.NORMAL)  # 启用文本编辑

        # 设置内容缩进与头像对齐
        self.chat_text.tag_configure("response_content_chinese",
                                     font=("宋体", font_size),  # 中文字体
                                     lmargin1=5,  # 左边距
                                     spacing2=5,  # 行间距
                                     wrap=tk.WORD)  # 自动换行
        self.chat_text.tag_configure("response_content_english",
                                     font=("Times New Roman", font_size),  # 英文字体
                                     lmargin1=5,
                                     spacing2=5,
                                     wrap=tk.WORD)

        # 插入内容
        for char_message in message:
            if self.is_english(char_message):  # 判断是否为英文
                self.chat_text.insert(tk.END, char_message, "response_content_english")  # 插入英文内容
            else:
                self.chat_text.insert(tk.END, char_message, "response_content_chinese")  # 插入中文内容

        self.chat_text.see(tk.END)  # 滚动到末尾
        self.chat_text.configure(state=tk.DISABLED)  # 禁用文本编辑

    def setup_bindings(self):
        """设置界面事件绑定"""
        self.history_list.bind("<Button-1>", self.load_chat)  # 左键点击历史记录
        self.history_list.bind("<Button-3>", self.show_context_menu)  # 右键点击历史记录
        self.input_text.bind("<Return>", self.on_enter_pressed)  # 回车键事件
        self.root.bind("<Control-Return>", lambda e: None)  # 屏蔽Ctrl+回车
        # 添加输入框事件绑定
        self.input_text.bind("<Key>", self.on_input_change)  # 输入框内容变化
        self.input_text.bind("<FocusIn>", self.on_focus_in)  # 输入框获得焦点
        self.input_text.bind("<FocusOut>", self.on_focus_out)  # 输入框失去焦点

    def update_history_list(self):
        """更新历史记录列表"""
        self.history_list.delete(0, tk.END)  # 清空历史记录列表
        for item in self.history:
            self.history_list.insert(tk.END, item["title"])  # 插入历史记录标题

    def display_thinking_status(self):
        """在助手头像右侧显示思考状态"""
        self.chat_text.configure(state=tk.NORMAL)  # 启用文本编辑
        self.chat_text.image_create(tk.END, image=self.deepseek_photo, padx=10)  # 插入助手头像
        # 助手消息容器
        self.chat_text.tag_configure("assistant_header",
                                     lmargin1=20,  # 左边距
                                     spacing1=15)  # 段落间距
        # 插入容器和头像
        self.thinking_start_index = self.chat_text.index("end-1c")  # 记录思考状态起始位置
        self.chat_text.insert(tk.END, "  ", "assistant_header")  # 插入空白占位
        # 思考状态样式（中文）
        self.chat_text.tag_configure("thinking_style_chinese",
                                     font=("宋体", 10, "italic"),  # 斜体
                                     foreground="#000000",  # 前景色
                                     lmargin1=10,  # 左边距
                                     spacing2=3)  # 行间距
        # 思考状态样式（英文）
        self.chat_text.tag_configure("thinking_style_english",
                                     font=("Times New Roman", 10, "italic"),
                                     foreground="#000000",
                                     lmargin1=10,
                                     spacing2=3)
        # 插入思考状态文本
        self.chat_text.insert(tk.END, " ", "thinking_style_chinese")  # 插入占位符
        self.thinking_end_index = self.chat_text.index("end-1c")  # 记录思考状态结束位置
        self.chat_text.see(tk.END)  # 滚动到末尾
        self.chat_text.configure(state=tk.DISABLED)  # 禁用文本编辑

    def hide_thinking_status(self):
        """隐藏思考状态并显示总耗时"""
        self.thinking = False  # 结束思考状态
        self.chat_text.configure(state=tk.NORMAL)  # 启用文本编辑
        elapsed = int(time.time() - self.start_time)  # 计算耗时
        # 替换思考状态
        self.chat_text.delete(self.thinking_start_index, self.thinking_end_index)  # 删除思考状态文本
        # 耗时信息样式
        self.chat_text.tag_configure("duration_style",
                                     font=("Times New Roman", 10, "normal"),  # 正常字体
                                     foreground="#000000",  # 前景色
                                     lmargin1=10)  # 左边距
        # 在头像右侧插入耗时信息
        self.chat_text.insert(self.thinking_start_index,
                              f"✓ 响应耗时 {elapsed} 秒",  # 显示耗时
                              ("duration_style", "thinking_style_chinese"))  # 应用样式
        self.chat_text.see(tk.END)  # 滚动到末尾
        self.chat_text.configure(state=tk.DISABLED)  # 禁用文本编辑

    def update_thinking_status(self):
        """更新对话框中的思考状态"""
        if self.thinking:  # 如果处于思考状态
            elapsed = int(time.time() - self.start_time)  # 计算耗时
            self.chat_text.configure(state=tk.NORMAL)  # 启用文本编辑
            self.chat_text.delete(self.thinking_start_index, self.thinking_end_index)  # 删除旧状态
            self.format_text(f"思考中... 已耗时 {elapsed} 秒", align="left", style="thinking")  # 插入新状态
            self.thinking_end_index = self.chat_text.index("end-1c")  # 更新结束位置
            self.chat_text.configure(state=tk.DISABLED)  # 禁用文本编辑
            self.root.after(1000, self.update_thinking_status)  # 1秒后再次更新

    def update_chat_log(self):
        """保存当前对话到历史记录"""
        # 当前对话已经存入历史对话了
        if len(self.current_chat) != 0:
            if self.current_message == "":  # 如果当前消息为空
                try:
                    self.history.pop(0)  # 移除旧记录
                    self.current_history["messages"] = self.current_chat  # 更新消息内容
                    self.history.insert(0, self.current_history)  # 插入新记录
                    with open(self.log_file, "w", encoding="utf-8") as f:
                        json.dump(self.history, f, ensure_ascii=False)  # 保存到文件
                    self.update_history_list()  # 更新历史记录列表
                except Exception as e:
                    self.show_error(f"保存历史记录失败: {str(e)}")  # 显示错误信息
            else:
                try:
                    # 添加到当前对话
                    if self.current_chat[-1]["role"] == "user":  # 如果最后一条消息是用户消息
                        self.current_chat[-1] = {
                            "role": "user",
                            "content": self.current_message  # 更新内容
                        }
                    else:
                        self.current_chat.append({  # 添加新消息
                            "role": "user",
                            "content": self.current_message
                        })
                    self.current_history["messages"] = self.current_chat  # 更新消息内容
                    self.history.pop(0)  # 移除旧记录
                    self.history.insert(0, self.current_history)  # 插入新记录
                    with open(self.log_file, "w", encoding="utf-8") as f:
                        json.dump(self.history, f, ensure_ascii=False)  # 保存到文件
                    self.update_history_list()  # 更新历史记录列表
                except Exception as e:
                    self.show_error(f"保存历史记录失败: {str(e)}")  # 显示错误信息
        # 新对话
        else:
            try:
                # 添加到当前对话
                self.current_chat.append({
                    "role": "user",
                    "content": self.current_message  # 添加新消息
                })
                # 生成对话标题（取第一条消息的前20字符）
                if len(self.current_chat[0]["content"]) >= 20:
                    title = self.current_chat[0]["content"][:20]  # 截取前20字符
                else:
                    title = self.current_chat[0]["content"]  # 使用完整内容
                # 添加时间戳
                self.current_history = {
                    "title": f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} {title}",  # 标题
                    "messages": self.current_chat,  # 消息内容
                }
                # 添加到历史记录并保存
                self.history.insert(0, self.current_history)  # 插入新记录
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)  # 保存到文件
                self.update_history_list()  # 更新历史记录列表
            except Exception as e:
                self.current_chat = []  # 清空当前对话
                self.current_history = {}  # 清空当前历史
                self.show_error(f"保存历史记录失败: {str(e)}")  # 显示错误信息

    def send_message(self, event=None):
        # 获取输入框中的消息内容，并去除首尾空白字符
        self.current_message = self.input_text.get("1.0", tk.END).strip()

        # 如果消息为空，直接返回
        if not self.current_message:
            return

        # 展示用户发送的消息
        self.display_user_message(self.current_message)  # 调整到思考状态之前

        # 更新聊天记录
        self.update_chat_log()

        # 如果开启了搜索功能，进行联网搜索
        if self.search_var.get():
            search_content = self.search_message()
            # 将搜索内容添加到当前消息中
            self.current_message = search_content + self.current_message

        # 如果有上传的文件内容，处理文件内容
        if len(self.upload_file_content) > 0:
            file_content = "请根据下列文档内容回答问题\n"
            # 遍历所有上传的文件，生成文件内容字符串
            for i in range(len(self.upload_file_content)):
                file_content += "文档" + f"{i+1}" + ":\n" + self.upload_file_name[i] + "\n" + self.upload_file_content[i] + "\n"
                # 展示文件上传信息
                self.display_file_upload("["+self.upload_file_name[i]+"]")
            
            # 移除所有已处理的文件
            for i in range(len(self.upload_file_content)):
                self.remove_file(0)
            
            # 将文件内容添加到当前消息中
            self.current_message = file_content + self.current_message
            self.upload_file_flag = False

        # 更新聊天记录
        self.update_chat_log()

        # 启动思考状态
        self.thinking = True
        self.start_time = time.time()
        self.display_thinking_status()
        self.update_thinking_status()

        # 清空输入框
        self.input_text.delete("1.0", tk.END)

        # 创建API请求线程，调用DeepSeek API
        thread = threading.Thread(target=self.call_deepseek_api)
        thread.start()

    def search_message(self):
        search_content = ""
        # 获取搜索关键词
        search_key_words = self.deepseek_before_search()
        search_key_words.replace("\n", "")
        search_answer = ""

        # 如果关键词为空，使用当前消息作为关键词
        if search_key_words == "":
            search_key_words = self.current_message

        if search_key_words != "":
            search_list = []
            # 获取搜索模式
            search_mode = self.search_mode.get()
            
            # 根据不同的搜索模式进行联网搜索
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
            
            # 如果搜索到结果，生成搜索内容
            if len(search_list) > 0:
                search_content = "请根据下列网页的内容回答下面的问题，并在回答过程中引用相关网页，在结尾列出相关网页\n"
                self.display_file_upload("已搜索到相关[" + search_key_words + "]网页:)")
                for i in range(len(search_list)):
                    search_content += "网页" + f"{i + 1}" + ":\n" + search_list[i]["title"] + search_list[i]["url"] + "\n" + "内容：" + search_list[i]["content"]
            else:
                self.display_file_upload("搜索关键词[" + search_key_words + "]失败")
            
            # 如果有搜索简答，展示简答内容
            if search_answer != "":
                self.display_left_message("[搜索简答]:" + search_answer + "\n", 12)
            else:
                self.display_left_message("\n",12)
        else:
            self.display_file_upload("[关键词为空]")

        return search_content

    def call_deepseek_api(self):
        api_chat = []

        # 如果开启了金鱼模式，只发送最后一条消息
        if self.gold_fish_var.get():
            api_chat.append({"role": self.current_chat[-1]["role"],
                            "content": self.current_chat[-1]["content"]
                            })
        else:
            # 如果开启了记忆增强模式，发送带有思考过程的消息
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

        # 设置API请求头
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json"
        }

        # 设置API请求体
        payload = {
            "messages": api_chat,
            "model": "deepseek-chat" if not self.deep_think_var.get() else "deepseek-reasoner",
            "temperature": self.current_temperature,
            "max_tokens": 8192,
        }

        try:
            # 发送API请求
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response_data = response.json()
            self.current_content = ""
            
            # 如果请求成功，处理返回的内容
            if response.status_code == 200:
                self.hide_thinking_status()
                content = ""
                reasoning_content = ""
                current_response = {}
                for choiceTemp in response_data["choices"]:
                    content += choiceTemp["message"]["content"]
                
                # 如果有思考过程，处理思考过程
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
                
                # 展示助手的回复
                self.display_assistant_response(current_response)
                self.current_message = ""
                self.update_chat_log()
            else:
                # 如果请求失败，恢复输入框内容并显示错误信息
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
            # 捕获异常并显示错误信息
            self.hide_thinking_status()
            self.show_error(str(e))

    def load_history(self):
        """加载历史记录文件"""
        self.history = []  # 初始化历史记录列表
        try:
            # 检查历史记录文件是否存在
            if os.path.exists(self.log_file):
                # 如果存在，读取文件内容并加载到self.history中
                with open(self.log_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            else:
                # 如果文件不存在，初始化空的历史记录并创建文件
                self.history = []
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)
        except Exception as e:
            # 捕获异常并显示错误信息
            self.show_error(f"加载历史记录失败: {str(e)}")

    def delete_history(self, index):
        """删除指定历史记录"""
        try:
            # 检查索引是否有效
            if 0 <= index < len(self.history):
                # 删除指定索引的历史记录
                del self.history[index]
                # 将更新后的历史记录写入文件
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)
                # 更新历史记录列表的显示
                self.update_history_list()
        except Exception as e:
            # 捕获异常并显示错误信息
            self.show_error(f"删除记录失败: {str(e)}")

    def show_context_menu(self, event):
        """显示右键删除菜单"""
        # 获取鼠标点击位置对应的历史记录索引
        index = self.history_list.nearest(event.y)
        # 创建右键菜单
        menu = tk.Menu(self.root, tearoff=0)
        # 添加删除选项，点击后调用delete_history方法
        menu.add_command(label="删除", command=lambda: self.delete_history(index))
        # 在鼠标点击位置显示菜单
        menu.post(event.x_root, event.y_root)

    def load_chat(self, event):
        """加载历史对话"""
        # 获取鼠标点击位置对应的历史记录索引
        index = self.history_list.nearest(event.y)
        if 0 <= index < len(self.history):
            try:
                # 加载指定索引的历史记录
                self.current_history = self.history[index]
                # 更新历史记录的标题（添加当前时间）
                dateStringTemp = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                self.current_history["title"] = dateStringTemp + self.current_history["title"][len(dateStringTemp):]
                
                # 如果当前聊天记录为空，调整历史记录的顺序
                if not self.current_chat:
                    self.history[index] = self.history[0]
                    self.history.pop(0)
                    self.history.insert(0, self.current_history)
                else:
                    # 将当前历史记录移动到列表的最前面
                    self.history.pop(index)
                    self.history.insert(0, self.current_history)
                
                # 加载历史记录中的消息
                self.current_chat = self.current_history["messages"]
                # 将用户消息插入输入框
                while (len(self.current_chat) > 0):
                    if self.current_chat[-1]["role"] == "user":
                        self.input_text.insert(tk.END, self.current_chat[-1]["content"])
                        self.current_message = ""
                        self.current_chat.pop()
                    else:
                        break
                else:
                    self.current_message = ""
                
                # 将更新后的历史记录写入文件
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, ensure_ascii=False)
                # 更新历史记录列表的显示
                self.update_history_list()
            except Exception as e:
                # 捕获异常并显示错误信息
                self.show_error(f"保存历史记录失败: {str(e)}")
            # 刷新聊天显示
            self.refresh_chat_display()

    def refresh_chat_display(self):
        """刷新聊天显示"""
        # 设置聊天文本框为可编辑状态
        self.chat_text.config(state=tk.NORMAL)
        # 清空聊天文本框内容
        self.chat_text.delete("1.0", tk.END)
        # 设置聊天文本框为不可编辑状态
        self.chat_text.config(state=tk.DISABLED)
        
        # 遍历当前聊天记录，显示消息
        for msg in self.current_chat:
            if msg["role"] == "user":
                # 显示用户消息
                self.display_user_message(msg["content"])
            else:
                # 显示助手消息
                self.chat_text.image_create(tk.END, image=self.deepseek_photo, padx=10)
                # 配置助手消息的样式
                self.chat_text.tag_configure("assistant_header",
                                            lmargin1=20,
                                            spacing1=15)
                # 插入助手头像和消息容器
                self.thinking_start_index = self.chat_text.index("end-1c")
                self.chat_text.insert(tk.END, "  ", "assistant_header")
                # 配置思考状态样式
                self.chat_text.tag_configure("thinking_style",
                                            font=("宋体", 11, "italic", "normal"),
                                            foreground="#000000",
                                            lmargin1=10,
                                            spacing2=3)
                # 插入思考状态文本
                self.chat_text.insert(tk.END, "--历史对话:)\n", "thinking_style")
                # 显示助手回复
                self.display_assistant_response(msg)
        # 滚动到聊天框底部
        self.chat_text.yview(tk.END)

    def show_error(self, message):
        """显示错误信息"""
        # 弹出错误提示框
        messagebox.showerror("错误", message)

    ### **`new_chat` 方法**
    def new_chat(self):
        """新建对话"""
        if self.current_chat:
            self.update_chat_log()  # 如果当前有聊天记录，先更新聊天日志
        self.current_chat = []  # 清空当前聊天记录
        self.current_message = ""  # 清空当前消息
        self.current_history = {}  # 清空当前历史记录
        self.refresh_chat_display()  # 刷新聊天显示
    #### **功能说明**：
    # - 用于创建一个新的聊天会话。
    # - 如果当前有聊天记录，会先调用 `update_chat_log` 方法保存当前聊天记录。
    # - 清空当前聊天记录、消息和历史记录，并刷新聊天界面。


    ### **`upload_file` 方法**

    def upload_file(self):
        if len(self.upload_file_name) >= 5:
            self.show_error("最多只能上传5个文件")  # 如果已上传文件数量超过5个，提示错误
            return
        """支持txt/docx/pdf的文件上传功能"""
        file_path = filedialog.askopenfilename()  # 打开文件选择对话框，获取文件路径
        if not file_path:
            return  # 如果用户未选择文件，直接返回
        try:
            file_name = os.path.basename(file_path)  # 获取文件名
            ext = os.path.splitext(file_path)[1].lower()  # 获取文件扩展名并转为小写
            content = ""  # 初始化文件内容
            # 处理Word文档
            if ext == ".docx":
                try:
                    from docx import Document  # 导入docx库
                except ImportError:
                    self.show_error("请安装python-docx库：pip install python-docx")  # 如果未安装库，提示错误
                    return
                doc = Document(file_path)  # 读取Word文档
                content = "\n".join([para.text for para in doc.paragraphs])  # 提取文档内容
            # 处理PDF文档
            elif ext == ".pdf":
                try:
                    from PyPDF2 import PdfReader  # 导入PyPDF2库
                except ImportError:
                    self.show_error("请安装PyPDF2库：pip install PyPDF2")  # 如果未安装库，提示错误
                    return
                with open(file_path, "rb") as f:
                    pdf = PdfReader(f)  # 读取PDF文件
                    # 处理加密PDF
                    if pdf.is_encrypted:
                        try:
                            pdf.decrypt("")  # 尝试空密码解密
                        except:
                            self.show_error("无法解密受保护的PDF文件")  # 如果解密失败，提示错误
                            return
                    for page in pdf.pages:
                        text = page.extract_text()  # 提取每一页的文本
                        if text:
                            content += text + "\n"  # 将文本内容拼接
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()  # 读取普通文本文件（如txt）
            if content != "":
                self.upload_file_flag = True  # 标记文件已上传
                self.upload_file_content.append(content.replace("\n", ""))  # 将文件内容添加到上传文件内容列表
                self.upload_file_name.append(file_name)  # 将文件名添加到上传文件名列表
                # 更新界面显示
                self.show_file_icon(self.upload_file_name[-1], ext, len(self.upload_file_content[-1]))
            else:
                self.show_error("读不到文件里的内容T-T")  # 如果文件内容为空，提示错误
        except Exception as e:
            self.show_error(f"读取文件失败: {str(e)}")  # 捕获异常并提示错误

    #### **功能说明**：
    # - 支持上传 `.txt`、`.docx` 和 `.pdf` 文件。
    # - 限制最多上传 5 个文件。
    # - 读取文件内容并存储到 `self.upload_file_content` 和 `self.upload_file_name` 列表中。
    # - 如果文件内容为空或读取失败，会提示错误。
    # - 调用 `show_file_icon` 方法在界面上显示文件图标。


    ### ** `show_file_icon` 方法**
    def show_file_icon(self, filename, ext, char_count):
        """显示文件图标并绑定提示"""
        # 获取对应图标
        icon = self.icon_images.get(ext, self.icon_images["default"])  # 根据文件扩展名获取图标，默认使用默认图标
        # 创建图标标签
        icon_label = ttk.Label(self.control_frame, image=icon)
        icon_label.image = icon  # 保持引用
        icon_label.pack(side=tk.LEFT, padx=2)  # 将图标添加到界面
        self.upload_file_icons.append(icon_label)  # 将图标标签添加到上传文件图标列表
        # 创建气泡提示时，将tooltip存储到icon_label的属性中
        self.create_bubble_tooltip(icon_label, filename, char_count)  # 绑定气泡提示
        # 绑定右键事件
        def on_right_click(event):
            # 动态获取当前索引
            try:
                index = self.upload_file_icons.index(event.widget)  # 获取点击的图标索引
            except ValueError:
                return
            # 创建右键菜单
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(
                label="删除",
                command=lambda: self.remove_file(index)  # 绑定删除功能
            )
            # 修正后的菜单定位方式
            try:
                menu.tk.call('tk_popup', menu, event.x_root, event.y_root)  # 显示右键菜单
            finally:
                menu.grab_release()
        icon_label.bind("<Button-3>", on_right_click)  # 绑定右键点击事件
    
    ### **`create_bubble_tooltip` 方法**
    def create_bubble_tooltip(self, widget, filename, char_count):
        """创建气泡样式提示框"""
        # 预先计算内容
        short_name = (filename[:10] + '...') if len(filename) > 10 else filename  # 截取文件名前10个字符
        file_ext = filename.split(".")[-1]  # 获取文件扩展名
        size_str = self.format_char_count(char_count)  # 格式化文件大小
        # 创建提示窗口
        tooltip = tk.Toplevel(widget.winfo_toplevel())  # 创建一个顶层窗口
        # 将tooltip实例附加到widget对象上
        widget.tooltip = tooltip  # 新增此行关联提示窗口
        tooltip.wm_overrideredirect(True)  # 去除窗口边框
        tooltip.wm_attributes("-topmost", True)  # 置顶窗口
        tooltip.withdraw()  # 隐藏窗口
        # 使用Canvas绘制气泡
        canvas = tk.Canvas(tooltip, bg="white", highlightthickness=0)  # 创建Canvas
        canvas.pack()
        # 添加文本内容
        text_id = canvas.create_text(15, 15,
                                    text=f"{short_name}\n大小: {size_str}\n类型:{file_ext}",
                                    anchor="nw",
                                    font=("宋体", 10),
                                    fill="#000000")
        # 计算气泡尺寸
        bbox = canvas.bbox(text_id)  # 获取文本的边界框
        padding = 1
        width = bbox[2] - bbox[0] + padding * 4 + 8  # 计算气泡宽度
        height = bbox[3] - bbox[1] + padding * 4 + 8  # 计算气泡高度
        # 绘制气泡背景
        canvas.config(width=width, height=height)  # 增加高度给箭头留空间
        canvas.create_rounded_rect(padding, padding, width - padding, height - padding,
                                radius=6,
                                fill="white",
                                outline="#000000")  # 绘制圆角矩形
        # 重新定位文本
        canvas.delete(text_id)  # 删除之前的文本
        text_id = canvas.create_text(15, 15,
                                    text=f"{short_name}\n大小: {size_str}\n类型:{file_ext}",
                                    anchor="nw",
                                    font=("宋体", 9),
                                    fill="#000000")
        canvas.coords(text_id, 2 * padding + 6, 2 * padding + 4)  # 重新定位文本
        # 鼠标跟踪事件
        def track_mouse(event):
            x = widget.winfo_pointerx() + 12  # 获取鼠标X坐标
            y = widget.winfo_pointery() - 10  # 获取鼠标Y坐标
            tooltip.geometry(f"+{x}+{y}")  # 设置提示框位置
            if not tooltip.winfo_viewable():
                tooltip.deiconify()  # 显示提示框
        def hide_tooltip(event):
            tooltip.withdraw()  # 隐藏提示框
        # 绑定事件
        widget.bind("<Enter>", lambda e: track_mouse(e))  # 鼠标进入时显示提示框
        widget.bind("<Leave>", hide_tooltip)  # 鼠标离开时隐藏提示框
        widget.bind("<Motion>", track_mouse)  # 鼠标移动时更新提示框位置

    #### **功能说明**：
    # - 创建一个气泡样式的提示框，显示文件名、文件大小和文件类型。
    # - 使用 `Canvas` 绘制圆角矩形背景，并动态调整提示框的位置。
    # - 当鼠标进入、离开或移动时，提示框会显示或隐藏，并跟随鼠标位置。

    ### **`create_rounded_rect` 方法**
    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        """在Canvas上创建圆角矩形"""
        points = [x1 + radius, y1,
                x2 - radius, y1,
                x2, y1 + radius,
                x2, y2 - radius,
                x2 - radius, y2,
                x1 + radius, y2,
                x1, y2 - radius,
                x1, y1 + radius,
                x1 + radius, y1]
        return self.create_polygon(points, **kwargs, smooth=True)  # 创建平滑的多边形
    tk.Canvas.create_rounded_rect = create_rounded_rect  # 将方法绑定到Canvas类

    #### **功能说明**：
    # - 在 `Canvas` 上绘制一个圆角矩形。
    # - 通过计算圆角的控制点，生成平滑的多边形。
    # - 将该方法绑定到 `tk.Canvas` 类，方便直接调用。

    ### ** `remove_file` 方法**
    def remove_file(self, index):
        """删除指定文件"""
        if 0 <= index < len(self.upload_file_name):
            del self.upload_file_name[index]  # 删除文件名
            del self.upload_file_content[index]  # 删除文件内容
            # 销毁对应图标
            icon_label = self.upload_file_icons.pop(index)  # 移除图标标签
            icon_label.destroy()  # 销毁图标标签
            # 销毁关联的气泡提示窗口
            if hasattr(icon_label, 'tooltip'):
                icon_label.tooltip.destroy()  # 新增此行销毁提示
            if len(self.upload_file_name) == 0:
                self.upload_file_flag = False  # 如果没有文件，重置上传标志

    #### **功能说明**：
    # - 删除指定索引的文件，包括文件名、文件内容和图标。
    # - 销毁与图标关联的气泡提示框。
    # - 如果没有文件，重置上传标志。

    ### ** `format_char_count` 方法**
    @staticmethod
    def format_char_count(count):
        """格式化字符统计"""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"  # 转换为M（百万）单位
        if count >= 1000:
            return f"{count / 1000:.1f}K"  # 转换为K（千）单位
        return f"{count}"  # 直接返回字符数

    #### **功能说明**：
    # - 将字符数格式化为更易读的形式（如 `1.2M` 或 `1.5K`）。
    # - 根据字符数的大小，自动选择合适的单位。


    ### ** `on_enter_pressed` 方法**
    def on_enter_pressed(self, event):
        """改进的跨平台回车键处理"""
        if not event.state & (0x4 | 0x1):  # 仅处理普通回车
            self.send_message()  # 调用发送消息方法
            return "break"  # 阻止默认换行
        return None  # 允许组合键换行

    #### **功能说明**：
    # - 处理回车键事件，用于发送消息。
    # - 仅处理普通回车键（不处理组合键如 `Ctrl+Enter`）。
    # - 阻止默认的换行行为，确保回车键用于发送消息。

    ### ** `show_thinking_status` 方法**
    def show_thinking_status(self):
        """显示思考状态"""
        self.status_var.set("思考中... 已耗时 0 秒")  # 设置状态栏显示“思考中...”
        self.start_time = time.time()  # 记录开始时间
        self.update_timer()  # 启动计时器

    #### **功能说明**：
    # - 显示“思考中...”状态，并记录当前时间作为开始时间。
    # - 调用 `update_timer` 方法启动计时器，实时更新思考耗时。

    ### **`update_timer` 方法**
    def update_timer(self):
        """更新计时器"""
        if self.thinking:  # 如果处于思考状态
            elapsed = int(time.time() - self.start_time)  # 计算已耗时
            self.status_var.set(f"思考中... 已耗时 {elapsed} 秒")  # 更新状态栏显示
            self.root.after(1000, self.update_timer)  # 1秒后再次调用自身
    #### **功能说明**：
    # - 实时更新思考状态的耗时。
    # - 每隔 1 秒调用一次自身，实现动态计时。

    ### **`on_input_change` 方法**
    def on_input_change(self, event):
        """实时更新输入框状态"""
        self.root.after(10, self.adjust_input_height)  # 10毫秒后调用adjust_input_height

    #### **功能说明**：
    # - 监听输入框内容变化事件。
    # - 延迟 10 毫秒后调用 `adjust_input_height` 方法，调整输入框高度。

    ### **`adjust_input_height` 方法**
    def adjust_input_height(self):
        """自动调整输入框高度"""
        lines = int(self.input_text.index('end-1c').split('.')[0])  # 获取输入框行数
        self.input_text.configure(height=min(max(lines, 3), 8))  # 设置输入框高度（3到8行之间）

    #### **功能说明**：
    # - 根据输入框内容的行数，动态调整输入框的高度。
    # - 高度范围限制在 3 到 8 行之间。

    ### **`on_focus_in` 和 `on_focus_out` 方法**
    def on_focus_in(self, event):
        """获得焦点时高亮显示"""
        self.input_text.configure(highlightbackground="#409EFF", highlightthickness=1)  # 设置高亮边框

    def on_focus_out(self, event):
        """失去焦点时恢复样式"""
        self.input_text.configure(highlightbackground="SystemButtonFace", highlightthickness=0)  # 恢复默认样式

    #### **功能说明**：
    # - **`on_focus_in`**：当输入框获得焦点时，显示蓝色高亮边框。
    # - **`on_focus_out`**：当输入框失去焦点时，恢复默认样式。

    ### **`check_widget_hierarchy` 方法**
    def check_widget_hierarchy(self):
        """打印组件层级信息用于调试"""
        print("Widget hierarchy:")
        def print_children(widget, indent=0):
            print(' ' * indent + str(widget))  # 打印当前组件
            for child in widget.winfo_children():
                print_children(child, indent + 2)  # 递归打印子组件
        print_children(self.root)  # 从根组件开始打印

    #### **功能说明**：
    # - 打印当前界面的组件层级结构，用于调试。
    # - 递归遍历所有子组件，并以缩进形式显示层级关系。

    ### ** `force_redraw` 方法**
    def force_redraw(self):
        """强制重绘界面"""
        self.root.update_idletasks()  # 更新所有待处理的任务
        self.root.update()  # 强制刷新界面

    #### **功能说明**：
    # - 强制刷新界面，确保所有界面更新立即生效。

    ### ** `on_window_resize` 方法**
    def on_window_resize(self, event):
        """窗口大小改变时动态调整布局参数"""
        win_width = self.root.winfo_width()  # 获取窗口宽度
        # 动态计算边距
        new_lmargin = max(1200, int(win_width))  # 计算新的左边距
        self.chat_text.tag_configure("right_align", lmargin1=new_lmargin)  # 更新右对齐标签的左边距
        self.chat_text.tag_configure("timestamp_right", lmargin1=new_lmargin)  # 更新时间戳标签的左边距

    #### **功能说明**：
    # - 当窗口大小改变时，动态调整聊天框的布局参数。
    # - 根据窗口宽度重新计算左边距，并更新相关标签的样式。

    ### **`search_bing_normal` 方法**
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

    #### **功能说明**：
    # - 实现 Bing 搜索功能，返回包含标题、链接和描述的搜索结果列表。
    # - 使用 `requests` 库发送 HTTP 请求，并通过 `BeautifulSoup` 解析 HTML。
    # - 支持分页搜索，每页返回约 10 条结果。
    # - 添加随机延时和自定义请求头，防止被 Bing 封禁。

    ### `get_tavily_api_key` 方法
    def get_tavily_api_key(self):
        """弹出输入框获取API密钥"""
        api_key = simpledialog.askstring(
            "tavily-API",
            "请输入您的tavily-API密钥:)",
            parent=self.root,
        )
        if api_key is None:
            return None
        if not api_key.strip():
            self.show_error("API密钥不能为空")
            return None
        return api_key
    # - **功能**: 该方法用于弹出一个输入框，提示用户输入Tavily API密钥。
    # - **流程**:
    #   1. 使用`simpledialog.askstring`弹出一个输入框，提示用户输入Tavily API密钥。
    #   2. 如果用户取消输入或输入为空，返回`None`并显示错误信息。
    #   3. 否则，返回用户输入的API密钥。

    ### `renew_config` 方法
    def renew_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False)
        except Exception as e:
            self.show_error(str(e))
    # - **功能**: 该方法用于将当前的配置写入配置文件。
    # - **流程**:
    #   1. 打开配置文件（`self.config_file`），并将当前的配置（`self.config`）以JSON格式写入文件。
    #   2. 如果写入过程中发生异常，捕获异常并显示错误信息。

    ### `search_tavily` 方法
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
    # - **功能**: 该方法用于通过Tavily API进行搜索。
    # - **流程**:
    #   1. 检查Tavily API密钥是否为空或为默认值，如果是，则调用`get_tavily_api_key`方法获取新的API密钥，并更新配置文件。
    #   2. 使用Tavily API进行搜索，获取搜索结果和答案。
    #   3. 如果搜索过程中发生异常，捕获异常并显示错误信息，然后重新获取API密钥并更新配置文件。
    #   4. 返回搜索结果列表和答案。

    ### `search_duck_normal` 和 `search_duck_news` 方法
    def search_duck_normal(self, search_query):
        search_list = []
        try:
            search_list = DDGS().text(search_query, max_results=10, safesearch='off')
        except Exception as e:
            messagebox.showinfo("DeepSeek For MoonOrange", f"无法连接到DuckDuckGo,可能需要开启VPN:)\n失败原因:{str(e)}")
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
        if len(search_list) > 0:
            for i in range(len(search_list)):
                search_list[i]["url"] = search_list.pop("href")
                search_list[i]["content"] = search_list.pop("body")
        return search_list
    # - **功能**: 这两个方法分别用于通过DuckDuckGo进行普通搜索和新闻搜索。
    # - **流程**:
    #   1. 使用DuckDuckGo API进行搜索，获取搜索结果。
    #   2. 如果搜索过程中发生异常，捕获异常并显示错误信息。
    #   3. 对搜索结果进行格式统一，将`href`和`body`字段分别映射到`url`和`content`字段。
    #   4. 返回搜索结果列表。

    ### `deepseek_before_search` 方法
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
    # - **功能**: 该方法用于在搜索之前与DeepSeek API进行交互，生成搜索关键词。
    # - **流程**:
    #   1. 根据当前聊天记录和用户设置，构建一个API请求的消息列表。
    #   2. 如果最后一条消息是用户发送的，将其内容修改为生成搜索关键词的提示。
    #   3. 使用DeepSeek API发送请求，获取生成的搜索关键词。
    #   4. 如果请求失败，捕获异常并显示错误信息，然后重新获取API密钥并更新配置文件。
    #   5. 返回生成的搜索关键词。

###主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekChat(root)
    root.mainloop()
# - **功能**: 这是程序的入口点，创建一个Tkinter窗口并启动主循环。
# - **流程**:
#   1. 创建一个Tkinter根窗口。
#   2. 实例化`DeepSeekChat`类，并将根窗口作为参数传递。
#   3. 启动Tkinter的主事件循环，等待用户交互。