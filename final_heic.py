import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timezone
import os
from PIL import Image
import piexif
import json
import re
import win32file
import win32con
from pillow_heif import register_heif_opener
import webbrowser
import sys

# 注册 HEIF 支持
register_heif_opener()

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
                'ss': '00'
            }
            
            for part, value in zip(format_parts, date_parts):
                date_dict[part] = value
            
            return f"{date_dict['YYYY']}-{date_dict['MM']}-{date_dict['DD']} {date_dict['hh']}:{date_dict['mm']}"
        return None

class DateFormatConfig:
    def __init__(self, parent, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("日期格式配置")
        self.window.geometry("400x400")
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
            "YYYYMMDD_hhmmss",
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
        custom_frame = ttk.LabelFrame(self.window, text="自定义格式")
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
        self.root.title("照片日期修改器")
        self.root.geometry("800x600")
        self.create_menu()

        self.date_format = "YYYY-MM-DD"
        self.format_processor = DateFormatProcessor()
        
        self.load_config()
        self.create_widgets()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="关于", menu=about_menu)
        about_menu.add_command(label="关于软件", command=self.show_about)

    def show_about(self):
        # 创建一个新的对话框窗口
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("关于")
        about_dialog.geometry("300x150")
        about_dialog.resizable(False, False)
        
        # 添加标题和作者信息
        tk.Label(about_dialog, text="照片日期修改器 V1.6", font=('Arial', 12, 'bold')).pack(pady=10)
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
        
        # 选择文件按钮
        self.select_btn = ttk.Button(
            control_frame, 
            text="选择照片文件夹", 
            command=self.select_folder
        )
        self.select_btn.pack(pady=10)
        
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
        
        # 右侧文件列表
        list_frame = ttk.Frame(self.root)
        list_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        columns = ("文件名", "原始日期时间", "新日期时间", "状态")
        self.file_list = ttk.Treeview(
            list_frame, 
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        for col in columns:
            self.file_list.heading(col, text=col)
        
        self.file_list.column("文件名", width=200)
        self.file_list.column("原始日期时间", width=150)
        self.file_list.column("新日期时间", width=150)
        self.file_list.column("状态", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_format_config(self):
        DateFormatConfig(self.root, self.update_date_format)
    
    def update_date_format(self, new_format):
        self.date_format = new_format
        # 更新显示的当前格式
        self.current_format_label.config(text=f"当前格式: {self.date_format}")
        if hasattr(self, 'folder_path'):
            self.scan_folder()
    
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
            self.path_label.config(text=folder_path)
            self.scan_folder()
    
    def scan_folder(self):
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        
        photo_files = [f for f in os.listdir(self.folder_path) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))]
        
        for filename in photo_files:
            full_path = os.path.join(self.folder_path, filename)
            original_date = datetime.fromtimestamp(
                os.path.getmtime(full_path)
            ).strftime('%Y-%m-%d %H:%M')
            
            date_str = self.format_processor.extract_date_from_filename(filename, self.date_format)
            status = "待处理" if date_str else "无法识别日期"
            
            self.file_list.insert("", tk.END, values=(
                filename,
                original_date,
                date_str if date_str else "-",
                status
            ))
    
    def modify_photo_date(self, file_path, date_str):
        try:
            # 添加日志输出
            print(f"开始处理文件: {file_path}")
            print(f"目标日期时间: {date_str}")
            
            success = True
            
            # 1. 修改文件的创建时间和修改时间
            date_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            win_time = datetime(
                date_time.year, date_time.month, date_time.day,
                date_time.hour, date_time.minute, 0
            )
            
            # 确保文件路径是绝对路径
            file_path = os.path.abspath(file_path)
            print(f"绝对路径: {file_path}")
            
            try:
                handle = win32file.CreateFile(
                    file_path,
                    win32con.GENERIC_WRITE,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,  # 添加共享模式
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
            
            # 2. 修改EXIF时间信息
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.jpg' or file_ext == '.jpeg':
                try:
                    # JPEG 文件使用 piexif
                    exif_date = date_time.strftime('%Y:%m:%d %H:%M:00')
                    exif_dict = piexif.load(file_path)
                    
                    exif_dict['0th'][piexif.ImageIFD.DateTime] = exif_date.encode('ascii')
                    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date.encode('ascii')
                    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = exif_date.encode('ascii')
                    
                    exif_bytes = piexif.dump(exif_dict)
                    im = Image.open(file_path)
                    im.save(file_path, exif=exif_bytes)
                except Exception as e:
                    print(f"EXIF修改失败，但文件时间已更新: {str(e)}")
                    return True
                    
            elif file_ext == '.heic':
                # HEIC 文件只修改文件时间，不处理 EXIF
                pass
            
            elif file_ext == '.png':
                # PNG 文件只修改文件时间，不处理 EXIF
                pass
            
            return success
                
        except Exception as e:
            print(f"修改文件日期时出错: {str(e)}")
            return False
    
    def process_photos(self):
        if not hasattr(self, 'folder_path'):
            messagebox.showerror("错误", "请先选择文件夹！")
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
                items = self.file_list.get_children()
                self.progress["maximum"] = len(items)
                self.progress["value"] = 0
                
                success_count = 0
                
                for i, item in enumerate(items):
                    values = self.file_list.item(item)['values']
                    filename = values[0]
                    date_str = values[2]
                    
                    if date_str and date_str != "-":
                        full_path = os.path.join(self.folder_path, filename)
                        log_message = f"\n处理文件 {i+1}/{len(items)}: {filename}"
                        print(log_message)
                        log_file.write(log_message + '\n')
                        
                        if self.modify_photo_date(full_path, date_str):
                            success_count += 1
                            status = "处理成功"
                        else:
                            status = "处理失败"
                        
                        self.file_list.set(item, "状态", status)
                        log_file.write(f"状态: {status}\n")
                    
                    self.progress["value"] = i + 1
                    self.root.update()
                
                result_message = f"处理完成！\n成功处理: {success_count} 个文件\n总文件数: {len(items)}"
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