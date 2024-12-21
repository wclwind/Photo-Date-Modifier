import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timezone
import os
from PIL import Image
import json
import re
import win32file
import win32con
import webbrowser
import sys
import subprocess 



class DateFormatProcessor:
    def format_to_regex(self, format_str):
        regex = format_str
        regex = regex.replace("YYYY", r"(\d{4})")
        regex = regex.replace("MM", r"(\d{2})")
        regex = regex.replace("DD", r"(\d{2})")
        regex = regex.replace("hh", r"(\d{2})")
        regex = regex.replace("mm", r"(\d{2})")
        regex = regex.replace("ss", r"(\d{2})")
        # 允许在日期时间格式前后有其他字符
        return r".*?" + regex + r".*?"
    
    def extract_date_from_filename(self, filename, format_str):
        regex = self.format_to_regex(format_str)
        match = re.search(regex, filename)
        
        if match:
            format_parts = re.findall(r"(YYYY|MM|DD|hh|mm|ss)", format_str)
            date_parts = match.groups()
            
            date_dict = {
                'YYYY': '2000',
                'MM': '01',
                'DD': '01',
                'hh': '00',
                'mm': '00',
                'ss': '00'  # 默认秒数为00
            }
            
            for part, value in zip(format_parts, date_parts):
                date_dict[part] = value
            
            # 修改返回格式以包含秒
            return f"{date_dict['YYYY']}-{date_dict['MM']}-{date_dict['DD']} {date_dict['hh']}:{date_dict['mm']}:{date_dict['ss']}"
        return None

class DateFormatConfig:
    def __init__(self, parent, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("日期格式配置")
        self.window.geometry("500x650")
        self.callback = callback
        self.format_processor = DateFormatProcessor()
        
        self.load_config()
        self.create_widgets()
        
    def create_widgets(self):
        # 预设格式框架
        preset_frame = ttk.LabelFrame(self.window, text="预设格式")
        preset_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # 预设格式选项
        self.format_var = tk.StringVar(value=self.current_format)
        formats = [
            "YYYY-MM-DD",
            "YYYY_MM_DD",
            "YYYYMMDD",
            "YYYYMMDD_hhmmss",  # 添加包含秒的格式
            "YYYY-MM-DD_hhmmss",  # 添加包含秒的格式
            "YYYY_MM_DD_hhmmss",  # 添加包含秒的格式
            "YYYY-MM-DD_hhmm",
            "YYYY_MM_DD_hhmm",
            "自定义格式"
        ]
        
        for fmt in formats:
            ttk.Radiobutton(
                preset_frame,
                text=fmt,
                value=fmt,
                variable=self.format_var,
                command=self.on_format_change
            ).pack(padx=10, pady=2, anchor=tk.W)
        
        # 自定义格式框架
        custom_frame = ttk.LabelFrame(self.window, text="自定义格式（回车生效）")
        custom_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.custom_format = ttk.Entry(custom_frame)
        self.custom_format.pack(padx=10, pady=5, fill=tk.X)
        self.custom_format.insert(0, self.current_custom_format)
        self.custom_format.bind('<Return>', lambda e: self.save_and_close())
        
        # 格式说明
        ttk.Label(custom_frame, text="支持的格式代码：").pack(padx=10, pady=2, anchor=tk.W)
        ttk.Label(custom_frame, text="YYYY: 四位年份").pack(padx=10, pady=2, anchor=tk.W)
        ttk.Label(custom_frame, text="MM: 两位月份").pack(padx=10, pady=2, anchor=tk.W)
        ttk.Label(custom_frame, text="DD: 两位日期").pack(padx=10, pady=2, anchor=tk.W)
        ttk.Label(custom_frame, text="hh: 两位小时").pack(padx=10, pady=2, anchor=tk.W)
        ttk.Label(custom_frame, text="mm: 两位分钟").pack(padx=10, pady=2, anchor=tk.W)
        ttk.Label(custom_frame, text="ss: 两位秒数").pack(padx=10, pady=2, anchor=tk.W)
        
        # 测试区域
        test_frame = ttk.LabelFrame(self.window, text="格式测试")
        test_frame.pack(padx=10, pady=5, fill=tk.X)
        
        test_input_frame = ttk.Frame(test_frame)
        test_input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(test_input_frame, text="测试文件名:").pack(side=tk.LEFT)
        self.test_filename = ttk.Entry(test_input_frame)
        self.test_filename.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        ttk.Button(
            test_frame,
            text="测试",
            command=self.test_format
        ).pack(pady=5)
        
        self.test_result = ttk.Label(test_frame, text="")
        self.test_result.pack(pady=5)
    
    def load_config(self):
        try:
            with open('date_format_config.json', 'r') as f:
                config = json.load(f)
                self.current_format = config.get('format', 'YYYY-MM-DD')
                self.current_custom_format = config.get('custom_format', '')
        except:
            self.current_format = 'YYYY-MM-DD'
            self.current_custom_format = ''
    
    def save_and_close(self):
        config = {
            'format': self.format_var.get(),
            'custom_format': self.custom_format.get()
        }
        with open('date_format_config.json', 'w') as f:
            json.dump(config, f)
        
        self.callback(self.get_current_format())
        self.window.destroy()
    
    def on_format_change(self):
        if self.format_var.get() == "自定义格式":
            self.custom_format.config(state='normal')
        else:
            self.custom_format.config(state='disabled')
            self.save_and_close()
    
    def get_current_format(self):
        if self.format_var.get() == "自定义格式":
            return self.custom_format.get()
        return self.format_var.get()
    
    def test_format(self):
        test_name = self.test_filename.get()
        if not test_name:
            self.test_result.config(text="请输入测试文件名")
            return
        
        try:
            date_str = self.format_processor.extract_date_from_filename(
                test_name, 
                self.get_current_format()
            )
            if date_str:
                self.test_result.config(
                    text=f"识别到的日期: {date_str}",
                    foreground="green"
                )
            else:
                self.test_result.config(
                    text="未能识别日期",
                    foreground="red"
                )
        except Exception as e:
            self.test_result.config(
                text=f"错误: {str(e)}",
                foreground="red"
            )
class PhotoDateModifier:
    def __init__(self, root):
        self.root = root
        self.root.title("照片日期修改器 V2.6.6_without_exif")
        self.root.geometry("1200x600")
        self.create_menu()

        self.date_format = "YYYY-MM-DD"
        self.format_processor = DateFormatProcessor()
        self.selected_files = []
        self.load_config()
        self.create_widgets()
        self.last_selected_item = None  # 添加这一行来跟踪上一次选择的项目
        self.create_context_menu() # 添加右键菜单
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="关于", menu=about_menu)
        about_menu.add_command(label="关于软件", command=self.show_about)

    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="打开文件所在位置", 
            command=self.open_file_location
        )

    def show_about(self):
        # 创建一个新的对话框窗口
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("关于")
        about_dialog.geometry("500x250")
        about_dialog.resizable(False, False)
        
        # 添加标题和作者信息
        tk.Label(about_dialog, text="照片日期修改器 V2.6.6_without_exif", font=('Arial', 12, 'bold')).pack(pady=10)
        tk.Label(about_dialog, text="by 类六怪都").pack(pady=5)
        
        # 创建可点击的链接
        link = tk.Label(about_dialog, 
                       text="https://github.com/wclwind/Photo-Date-Modifier", 
                       fg="blue", 
                       cursor="hand2")
        link.pack(pady=5)
        
        # 添加下划线
        link.bind("<Enter>", lambda e: link.configure(font=('Arial', 9, 'underline')))
        link.bind("<Leave>", lambda e: link.configure(font=('Arial', 9)))
        
        # 绑定点击事件
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/wclwind/Photo-Date-Modifier"))
    
    def create_widgets(self):
        # 左侧控制面板
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)   




        # 右侧文件列表
        list_frame = ttk.Frame(self.root)
        list_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        columns = ("选择", "文件名", "原始日期时间", "新日期时间", "状态")
        self.file_list = ttk.Treeview(
            list_frame, 
            columns=columns,
            show="headings",
            selectmode="extended"
        )
        

        # 绑定标题点击事件
        self.file_list.bind('<Button-1>', self.on_header_click)
        # 修改文件列表的绑定事件
        self.file_list.bind('<ButtonRelease-1>', self.handle_click)
        self.file_list.bind('<Shift-ButtonRelease-1>', self.handle_shift_click)
        # 在文件列表的绑定事件中添加右键菜单绑定
        self.file_list.bind('<Button-3>', self.show_context_menu)
        
        # 添加一个变量来跟踪全选状态
        self.all_selected = True  # 默认全选
        
        self.file_list.heading("选择", text="选择 ✔")  # 默认显示全选状态
        self.file_list.heading("文件名", text="文件名")
        self.file_list.heading("原始日期时间", text="原始日期时间")
        self.file_list.heading("新日期时间", text="新日期时间")
        self.file_list.heading("状态", text="状态")
        
        self.file_list.column("选择", width=10)
        self.file_list.column("文件名", width=200)
        self.file_list.column("原始日期时间", width=150)
        self.file_list.column("新日期时间", width=150)
        self.file_list.column("状态", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加复选框
        for item in self.selected_files:
            self.file_list.insert("", tk.END, values=("✔", item, "-", "-", "待处理"))
     
        # 选择文件按钮区域
        select_frame = ttk.Frame(control_frame)
        select_frame.pack(pady=10)
        
        self.select_folder_btn = ttk.Button(
            select_frame, 
            text="选择文件夹", 
            command=self.select_folder
        )
        self.select_folder_btn.pack(side=tk.LEFT, padx=5)
        
        self.select_files_btn = ttk.Button(
            select_frame, 
            text="选择文件", 
            command=self.select_files
        )
        self.select_files_btn.pack(side=tk.LEFT, padx=5)
        
        # 显示选中路径
        self.path_label = ttk.Label(control_frame, text="未选择文件夹")
        self.path_label.pack(pady=5)

        
        # 日期格式配置区域
        format_frame = ttk.LabelFrame(control_frame, text="日期格式配置")
        format_frame.pack(pady=10, fill=tk.X)
        
        # 当前格式显示
        self.current_format_label = ttk.Label(
            format_frame, 
            text=f"当前格式: {self.date_format}"
        )
        self.current_format_label.pack(pady=5)
        
        # 修改格式按钮
        self.format_btn = ttk.Button(
            format_frame,
            text="修改格式",
            command=self.show_format_config
        )
        self.format_btn.pack(pady=5)

        # 修改筛选区域的创建方式，将 filter_frame 设为实例变量
        self.filter_frame = ttk.LabelFrame(control_frame, text="文件筛选")
        self.filter_frame.pack(pady=10, fill=tk.X)
        
        # 筛选选项
        self.filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(
            self.filter_frame,
            text="全部照片",
            value="all",
            variable=self.filter_var,
            command=self.apply_filter
        ).pack(padx=10, pady=2, anchor=tk.W)

        ttk.Radiobutton(
            self.filter_frame,
            text="日期需要修改",
            value="different",
            variable=self.filter_var,
            command=self.apply_filter
        ).pack(padx=10, pady=2, anchor=tk.W)
        
        ttk.Radiobutton(
            self.filter_frame,
            text="无法识别日期",
            value="unrecognized",
            variable=self.filter_var,
            command=self.apply_filter
        ).pack(padx=10, pady=2, anchor=tk.W)
        
        ttk.Radiobutton(
            self.filter_frame,
            text="日期无需修改",
            value="same",
            variable=self.filter_var,
            command=self.apply_filter
        ).pack(padx=10, pady=2, anchor=tk.W)

      # 添加刷新按钮
        self.refresh_btn = ttk.Button(
            select_frame,
            text="刷新列表",
            command=self.refresh_list
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        
        # 进度条
        self.progress = ttk.Progressbar(
            control_frame,
            orient="horizontal",
            length=200,
            mode="determinate"
        )
        self.progress.pack(pady=10)
        
        # 处理按钮
        self.process_btn = ttk.Button(
            control_frame,
            text="开始处理",
            command=self.process_photos
        )
        self.process_btn.pack(pady=10)

    def show_context_menu(self, event):
        """显示右键菜单"""
        # 获取点击的项目
        item = self.file_list.identify_row(event.y)
        if item:
            # 选中被右键点击的项目
            self.file_list.selection_set(item)
            # 显示菜单
            self.context_menu.post(event.x_root, event.y_root)
    
    def open_file_location(self):
        """打开所选文件的位置"""
        # 获取选中的项目
        selected_item = self.file_list.selection()
        if selected_item:
            # 获取文件名
            filename = self.file_list.item(selected_item[0])["values"][1]
            # 构建完整路径
            file_path = os.path.join(self.folder_path, filename)
            # 确保文件存在
            if os.path.exists(file_path):
                # Windows 系统使用 explorer 命令，并使用 /select 参数选中具体文件
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])

    def handle_click(self, event):
        """处理普通点击事件"""
        region = self.file_list.identify_region(event.x, event.y)
        if region == "cell":
            column = self.file_list.identify_column(event.x)
            if column == "#1":  # 第一列（选择列）
                item = self.file_list.identify_row(event.y)
                if item:
                    values = list(self.file_list.item(item)["values"])
                    values[0] = "✔" if values[0] != "✔" else "□"
                    self.file_list.item(item, values=values)
                    self.last_selected_item = item
                    
                    # 检查是否所有项目都被选中，更新标题状态
                    all_checked = all(
                        self.file_list.item(item)["values"][0] == "✔" 
                        for item in self.file_list.get_children()
                    )
                    self.all_selected = all_checked
                    self.file_list.heading("选择", text=f"选择 {'✔' if self.all_selected else '□'}")

    def handle_shift_click(self, event):
        """处理 Shift 点击事件，实现连续选择"""
        region = self.file_list.identify_region(event.x, event.y)
        if region == "cell":
            column = self.file_list.identify_column(event.x)
            if column == "#1" and self.last_selected_item:  # 第一列（选择列）
                current_item = self.file_list.identify_row(event.y)
                if current_item:
                    # 获取所有可见项目
                    visible_items = self.file_list.get_children()
                    
                    # 获取起始和结束索引
                    start_idx = visible_items.index(self.last_selected_item)
                    end_idx = visible_items.index(current_item)
                    
                    # 确保正确的顺序
                    if start_idx > end_idx:
                        start_idx, end_idx = end_idx, start_idx
                    
                    # 获取最后选择项的状态
                    last_state = self.file_list.item(self.last_selected_item)["values"][0]
                    target_state = "✔" if last_state == "✔" else "□"
                    
                    # 更新范围内所有项目的状态
                    for idx in range(start_idx, end_idx + 1):
                        item = visible_items[idx]
                        values = list(self.file_list.item(item)["values"])
                        values[0] = target_state
                        self.file_list.item(item, values=values)
                    
                    # 更新标题状态
                    all_checked = all(
                        self.file_list.item(item)["values"][0] == "✔" 
                        for item in visible_items
                    )
                    self.all_selected = all_checked
                    self.file_list.heading("选择", text=f"选择 {'✔' if self.all_selected else '□'}")
                    
                    self.last_selected_item = current_item


    def refresh_list(self, skip_filter=False):
        # 保存当前的选择状态
        selection_states = {}
        for item in self.file_list.get_children():
            values = self.file_list.item(item)["values"]
            filename = values[1]
            selection_states[filename] = values[0]
        
        # 重新扫描文件
        if len(self.selected_files) > 0:
            if os.path.isfile(self.selected_files[0]):
                self.scan_selected_files(selection_states)
            else:
                self.scan_folder(selection_states)
                
        # 只有在不跳过筛选时才应用筛选
        if not skip_filter:
            self.apply_filter(skip_refresh=True)

    # 添加筛选方法
    def apply_filter(self, skip_refresh=False):
        # 只有在不跳过刷新时才执行刷新
        if not skip_refresh:
            self.refresh_list(skip_filter=True)
        
        filter_type = self.filter_var.get()
        
        # 获取所有项目
        all_items = self.file_list.get_children()
        
        # 先分离所有项目
        for item in all_items:
            self.file_list.detach(item)

        # 计数器
        count = 0
                
        # 然后根据筛选条件重新附加符合的项目
        for item in all_items:
            values = self.file_list.item(item)["values"]
            original_date = values[2]
            new_date = values[3]
            
            show_item = False
            if filter_type == "all":
                show_item = True
            elif filter_type == "unrecognized":
                show_item = (new_date == "-")
            elif filter_type == "different":
                show_item = (new_date != "-" and new_date != original_date)
            elif filter_type == "same":
                show_item = (new_date != "-" and new_date == original_date)
            
            if show_item:
                self.file_list.reattach(item, "", "end")
                count += 1

        # 更新单选按钮文本以显示文件数
        for child in self.filter_frame.winfo_children():
            if isinstance(child, ttk.Radiobutton):
                current_value = child.cget("value")
                if current_value == "all":
                    child.configure(text=f"全部照片 ({len(all_items)})")
                elif current_value == "unrecognized":
                    total = sum(1 for item in all_items if self.file_list.item(item)["values"][3] == "-")
                    child.configure(text=f"无法识别日期 ({total})")
                elif current_value == "different":
                    total = sum(1 for item in all_items 
                            if self.file_list.item(item)["values"][3] != "-" 
                            and self.file_list.item(item)["values"][3] != self.file_list.item(item)["values"][2])
                    child.configure(text=f"日期需要修改 ({total})")
                elif current_value == "same":
                    total = sum(1 for item in all_items 
                            if self.file_list.item(item)["values"][3] != "-" 
                            and self.file_list.item(item)["values"][3] == self.file_list.item(item)["values"][2])
                    child.configure(text=f"日期无需修改 ({total})")

    # 添加以下两个新方法
    def select_all_files(self):
        for item in self.file_list.get_children():
            values = list(self.file_list.item(item)["values"])
            values[0] = "✔"
            self.file_list.item(item, values=values)

    def deselect_all_files(self):
        for item in self.file_list.get_children():
            values = list(self.file_list.item(item)["values"])
            values[0] = "□"
            self.file_list.item(item, values=values)
    
    def show_format_config(self):
        DateFormatConfig(self.root, self.update_date_format)
    
    def update_date_format(self, new_format):
        self.date_format = new_format
        # 更新显示的当前格式
        self.current_format_label.config(text=f"当前格式: {self.date_format}")
        
        # 保存当前的选择状态和筛选状态
        selection_states = {}
        for item in self.file_list.get_children():
            values = self.file_list.item(item)["values"]
            filename = values[1]
            selection_states[filename] = values[0]
        
        # 如果是通过选择文件方式导入的，调用 scan_selected_files
        # 如果是通过选择文件夹导入的，调用 scan_folder
        if len(self.selected_files) > 0:
            if os.path.isfile(self.selected_files[0]):
                self.scan_selected_files(selection_states)
            else:
                self.scan_folder(selection_states)
        
        # 重新应用筛选
        self.apply_filter()
    
    def load_config(self):
        try:
            with open('date_format_config.json', 'r') as f:
                config = json.load(f)
                self.date_format = config.get('format', 'YYYY-MM-DD')
        except:
            pass
    
    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path = folder_path
            self.selected_files = []  # 清空之前选择的文件
            self.path_label.config(text=folder_path)
            self.scan_folder()
    
    def scan_folder(self, selection_states=None):
        # 清空列表
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        # 重置进度条
        self.progress["value"] = 0
        
        photo_files = [f for f in os.listdir(self.folder_path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))]
        
        self.selected_files = [os.path.join(self.folder_path, f) for f in photo_files]
        
        for filename in photo_files:
            full_path = os.path.join(self.folder_path, filename)
            original_date = datetime.fromtimestamp(
                os.path.getmtime(full_path)
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            date_str = self.format_processor.extract_date_from_filename(filename, self.date_format)
            # 状态判断逻辑
            if not date_str:
                status = "无法识别日期"
            elif date_str == original_date:
                status = "无需修改"
            else:
                status = "待处理"
            
            # 使用保存的选择状态或默认为选中
            selection_state = selection_states.get(filename, "✔") if selection_states else "✔"
            
            self.file_list.insert("", tk.END, values=(
                selection_state,
                filename,
                original_date,
                date_str if date_str else "-",
                status
            ))
        # 在方法末尾添加：
        self.apply_filter()
    
    def modify_photo_date(self, file_path, date_str):
        try:
                # 添加日志输出
                print(f"开始处理文件: {file_path}")
                print(f"目标日期时间: {date_str}")
                
                success = True
                
                # 修改文件的创建时间和修改时间
                # 更新时间格式以支持秒
                date_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                win_time = datetime(
                    date_time.year, date_time.month, date_time.day,
                    date_time.hour, date_time.minute, date_time.second
                )
                
                # 确保文件路径是绝对路径
                file_path = os.path.abspath(file_path)
                print(f"绝对路径: {file_path}")
                
                try:
                    handle = win32file.CreateFile(
                        file_path,
                        win32con.GENERIC_WRITE,
                        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                        None,
                        win32con.OPEN_EXISTING,
                        win32con.FILE_ATTRIBUTE_NORMAL,
                        None
                    )
                    
                    try:
                        print("正在设置文件时间...")
                        win32file.SetFileTime(handle, win_time, win_time, win_time)
                        print("文件时间设置成功")
                    except Exception as e:
                        print(f"设置文件时间时出错: {str(e)}")
                        success = False
                    finally:
                        handle.Close()
                        
                except Exception as e:
                    print(f"打开文件时出错: {str(e)}")
                    success = False
                
                return success
                    
        except Exception as e:
            print(f"修改文件日期时出错: {str(e)}")
            return False

    def select_files(self):
        files = filedialog.askopenfilenames(
            filetypes=[
                ('图片文件', '*.jpg;*.jpeg;*.png;*.heic'),
                ('所有文件', '*.*')
            ]
        )
        if files:
            self.selected_files = list(files)
            self.folder_path = os.path.dirname(self.selected_files[0])
            self.path_label.config(text=f"已选择 {len(self.selected_files)} 个文件")
            self.scan_selected_files()

    def scan_selected_files(self, selection_states=None):
        for item in self.file_list.get_children():
            self.file_list.delete(item)

        # 重置进度条
        self.progress["value"] = 0
        
        for filepath in self.selected_files:
            filename = os.path.basename(filepath)
            original_date = datetime.fromtimestamp(
                os.path.getmtime(filepath)
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            date_str = self.format_processor.extract_date_from_filename(filename, self.date_format)
           # 状态判断逻辑
            if not date_str:
                status = "无法识别日期"
            elif date_str == original_date:
                status = "无需修改"
            else:
                status = "待处理"
            
            # 使用保存的选择状态或默认为选中
            selection_state = selection_states.get(filename, "✔") if selection_states else "✔"
            
            self.file_list.insert("", tk.END, values=(
                selection_state,
                filename,
                original_date,
                date_str if date_str else "-",
                status
            ))
        # 在方法末尾添加：
        #self.apply_filter()


    def on_header_click(self, event):
        region = self.file_list.identify_region(event.x, event.y)
        if region == "heading":
            column = self.file_list.identify_column(event.x)
            if column == "#1":  # 选择列的标题
                self.all_selected = not self.all_selected
                # 更新标题显示
                self.file_list.heading("选择", text=f"选择 {'✔' if self.all_selected else '□'}")
                # 更新所有复选框
                for item in self.file_list.get_children():
                    values = list(self.file_list.item(item)["values"])
                    values[0] = "✔" if self.all_selected else "□"
                    self.file_list.item(item, values=values)

    def process_photos(self):
        if not self.selected_files:
            messagebox.showerror("错误", "请先选择文件或文件夹！")
            return
                    
        # 仅处理选中的文件
        selected_items = [item for item in self.file_list.get_children() 
                        if self.file_list.item(item)["values"][0] == "✔"]
        
        if not selected_items:
            messagebox.showerror("错误", "请至少选择一个文件进行处理！")
            return

        # 获取程序所在目录
        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(sys.executable)
        else:
            app_path = os.path.dirname(os.path.abspath(__file__))

        # 在程序目录中创建日志文件
        log_path = os.path.join(app_path, 'date_modifier.log')

        # 打开日志文件
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"\n=== 开始处理 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        
            try:
                self.progress["maximum"] = len(selected_items)
                self.progress["value"] = 0
                
                success_count = 0
                
                for i, item in enumerate(selected_items):
                    values = self.file_list.item(item)["values"]
                    filename = values[1]  # 文件名在第二列
                    new_date = values[3]  # 新日期在第四列
                    
                    if new_date and new_date != "-":
                        full_path = os.path.join(self.folder_path, filename)
                        log_message = f"\n处理文件 {i+1}/{len(selected_items)}: {filename}"
                        print(log_message)
                        log_file.write(log_message + '\n')
                        
                        if self.modify_photo_date(full_path, new_date):
                            success_count += 1
                            status = "处理成功"
                        else:
                            status = "处理失败"
                        
                        self.file_list.set(item, "状态", status)
                        log_file.write(f"状态: {status}\n")
                    
                    self.progress["value"] = i + 1
                    self.root.update()
                
                result_message = f"处理完成！\n成功处理: {success_count} 个文件\n总文件数: {len(selected_items)}"
                print(result_message)
                log_file.write(f"\n{result_message}\n")
                messagebox.showinfo("完成", result_message)
                
            except Exception as e:
                error_message = f"处理过程中出错：{str(e)}"
                print(error_message)
                log_file.write(f"\n错误: {error_message}\n")
                messagebox.showerror("错误", error_message)
            
            log_file.write("\n=== 处理结束 ===\n")

def main():
    root = tk.Tk()
    app = PhotoDateModifier(root)
    root.mainloop()

if __name__ == "__main__":
    main()