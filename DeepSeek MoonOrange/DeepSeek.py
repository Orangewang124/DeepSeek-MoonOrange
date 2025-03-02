import string
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, font
from ttkbootstrap import Style
from PIL import Image, ImageTk
import json
import time
import threading
import requests
import os
import datetime
import sys

class DeepSeekChat:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek For MoonOrange")
        root.iconbitmap(self.resource_path("deepseek.ico"))
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
        self.config = {}
        self.theme_style = "litera"
        self.config_file = "chat_config.json"
        self.load_config()
        self.thinking = False
        self.thinking_start_index = None
        self.thinking_end_index = None

        # 加载图片
        self.load_images()
        self.root.bind("<Configure>", self.on_window_resize)

        # 创建界面
        self.style = Style(theme=self.theme_style)
        self.create_widgets()
        self.setup_bindings()
        self.input_text.focus_set()
        self.load_config()
        self.load_history()

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
            "请输入您的API密钥:)",
            parent=self.root,  # 根据实际父窗口调整这个参数
        )
        print(api_key)
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
                    self.api_key = self.config[0]["api-key"]
                    self.theme_style = self.config[0]["theme_style"]
                if self.api_key == "your-api-key":
                    self.api_key = self.get_api_key()
                    self.config[0]["api-key"] = self.api_key
                    with open(self.config_file, "w", encoding="utf-8") as f:
                        json.dump(self.config, f, ensure_ascii=False)
            else:
                self.config = [{
                    "api-key": "your-api-key",
                    "theme_style": "litera"
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

        # 主聊天区域
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 聊天显示区域
        self.chat_text = tk.Text(self.main_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(self.main_frame, command=self.chat_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 控制面板（修改复选框样式）
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X)

        self.deep_think_var = tk.BooleanVar()
        self.search_var = tk.BooleanVar()
        self.gold_fish_var = tk.BooleanVar()
        self.memory_enhance_var = tk.BooleanVar()
        ttk.Checkbutton(self.control_frame, text="深度思考", variable=self.deep_think_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="联网搜索", variable=self.search_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="金鱼模式", variable=self.gold_fish_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(self.control_frame, text="记忆增强", variable=self.memory_enhance_var,
                        bootstyle='success-round-toggle').pack(side=tk.LEFT, padx=5)
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
        for i in range(start_line, end_line+1):
            self.chat_text.tag_add('right-align', f"{i}.0",  f"{i}.end")
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
        # 先显示用户消息
        self.display_user_message(self.current_message)  # 调整到思考状态之前
        self.update_chat_log()
        # 启动思考状态
        self.thinking = True
        self.start_time = time.time()
        self.display_thinking_status()
        self.update_thinking_status()

        # 清空输入框
        self.input_text.delete("1.0", tk.END)
        # 创建API请求线程
        thread = threading.Thread(target=self.call_deepseek_api, args=(self.current_message,))
        thread.start()

    def call_deepseek_api(self, message):
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
                                    "content": "[思考过程]\n"+temp_chat["reasoning_content"]+"\n[思考结果]\n"+temp_chat["content"]
                                    })
                else:
                    api_chat.append({"role": temp_chat["role"],
                                    "content": temp_chat["content"]
                                    })
        headers = {
            "Authorization": "Bearer "+self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "messages": api_chat,
            "model": "deepseek-chat" if not self.deep_think_var.get() else "deepseek-reasoner",
            "search": self.search_var.get()
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
                while(self.current_chat[-1]["role"] == "user"):
                    # 插入输入文本框文字
                    self.input_text.insert(tk.END, self.current_chat[-1]["content"])
                    self.current_message = ""
                    self.current_chat.pop()
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
        """文件上传功能"""
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.input_text.insert(tk.END, f"\n[附件内容]\n{content}")
            except Exception as e:
                self.show_error(f"读取文件失败: {str(e)}")

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


if __name__ == "__main__":
    root = tk.Tk()
    print(font.families(root))
    app = DeepSeekChat(root)
    root.mainloop()
