import tkinter as tk
from tkinter import ttk, messagebox
import screeninfo
from pynput import keyboard
import threading
import ctypes
import sys

# 全局变量定义
selected_monitors = []  # 选中的显示器列表
mask_windows = []  # 遮罩窗口列表
current_alpha = None  # 不透明度(0-100)
monitor_check_vars = []  # 显示器复选框变量
listener = None  # 快捷键监听器
root = None  # 主窗口（全局化，用于子线程UI更新）

# 线程安全的按键集合（记录当前按下的键）
pressed_keys = set()
key_lock = threading.Lock()

# Windows API 常量
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
LWA_ALPHA = 0x2
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010


# 设置窗口属性（Windows）
def set_window_attributes(hwnd, alpha):
    try:
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, int(alpha * 2.55), LWA_ALPHA)
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
    except Exception as e:
        print(f"设置窗口属性失败: {e}")


# 获取所有显示器信息
def get_monitors():
    try:
        return screeninfo.get_monitors()
    except Exception as e:
        messagebox.showerror("错误", f"获取显示器信息失败: {e}")
        sys.exit(1)


# 生成遮罩窗口
def create_mask_windows():
    close_mask_windows()

    selected_monitors.clear()
    monitors = get_monitors()
    for idx, var in enumerate(monitor_check_vars):
        if var.get() == 1:
            selected_monitors.append(monitors[idx])

    if not selected_monitors:
        messagebox.showwarning("提示", "请至少选择一个显示器！")
        return

    alpha = current_alpha.get()
    for monitor in selected_monitors:
        mask = tk.Toplevel()
        mask.title("")
        mask.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        mask.overrideredirect(True)
        mask.attributes("-topmost", True)
        mask.resizable(False, False)
        mask.configure(bg="black")

        mask.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(mask.winfo_id())
        set_window_attributes(hwnd, alpha)

        mask_windows.append(mask)

    messagebox.showinfo("成功", f"已为 {len(selected_monitors)} 个显示器生成遮罩！")


# 关闭所有遮罩窗口
def close_mask_windows():
    for win in mask_windows:
        try:
            win.destroy()
        except:
            pass
    mask_windows.clear()
    selected_monitors.clear()


# 进度条更新输入框
def scale_update_entry(event=None):
    alpha = current_alpha.get()
    entry_alpha.delete(0, tk.END)
    entry_alpha.insert(0, f"{int(alpha)}")


# 输入框更新进度条
def entry_update_scale(event=None):
    try:
        val = int(entry_alpha.get().strip())
        if 0 <= val <= 100:
            current_alpha.set(val)
            for win in mask_windows:
                hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
                set_window_attributes(hwnd, val)
        else:
            messagebox.showwarning("提示", "请输入0-100之间的数字！")
            entry_alpha.delete(0, tk.END)
            entry_alpha.insert(0, f"{int(current_alpha.get())}")
    except ValueError:
        messagebox.showwarning("提示", "请输入有效的数字！")
        entry_alpha.delete(0, tk.END)
        entry_alpha.insert(0, f"{int(current_alpha.get())}")


# 快捷键监听 - 按键按下
def on_key_press(key):
    # 线程安全地记录按下的键
    with key_lock:
        pressed_keys.add(key)

    try:
        # 判断是否按下Ctrl（左/右Ctrl均可）
        has_ctrl = keyboard.Key.ctrl_l in pressed_keys or keyboard.Key.ctrl_r in pressed_keys
        if not has_ctrl:
            return

        # Ctrl+Up 增加5%不透明度
        if key == keyboard.Key.up:
            new_alpha = min(current_alpha.get() + 5, 100)
            current_alpha.set(new_alpha)
            # 主线程更新UI（TKinter仅允许主线程操作UI）
            root.after(0, scale_update_entry)
            # 更新遮罩不透明度
            for win in mask_windows:
                hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
                set_window_attributes(hwnd, new_alpha)

        # Ctrl+Down 减少5%不透明度
        elif key == keyboard.Key.down:
            new_alpha = max(current_alpha.get() - 5, 0)
            current_alpha.set(new_alpha)
            root.after(0, scale_update_entry)
            # 更新遮罩不透明度
            for win in mask_windows:
                hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
                set_window_attributes(hwnd, new_alpha)

    except Exception as e:
        print(f"快捷键处理错误: {e}")


# 快捷键监听 - 按键释放
def on_key_release(key):
    # 线程安全地移除释放的键
    with key_lock:
        if key in pressed_keys:
            pressed_keys.remove(key)


# 启动快捷键监听线程
def start_hotkey_listener():
    global listener
    # 同时监听按键按下和释放事件
    listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    listener.start()


# 构建主界面
def build_ui(main_root):
    global current_alpha, entry_alpha, root
    root = main_root  # 全局化主窗口

    current_alpha = tk.DoubleVar(value=50)

    root.title("显示器遮罩工具")
    root.geometry("450x400")
    root.resizable(False, False)

    # 居中窗口
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # 样式美化
    style = ttk.Style(root)
    style.configure("TLabel", font=("微软雅黑", 10))
    style.configure("TButton", font=("微软雅黑", 10), padding=5)
    style.configure("TScale", font=("微软雅黑", 9))

    # 1. 显示器选择区域
    frame_monitor = ttk.LabelFrame(root, text="选择显示器", padding=(10, 5))
    frame_monitor.pack(fill=tk.X, padx=20, pady=10)

    monitors = get_monitors()
    monitor_check_vars.clear()
    for idx, monitor in enumerate(monitors):
        var = tk.IntVar(value=0)
        monitor_check_vars.append(var)
        monitor_info = f"显示器 {idx + 1}: {monitor.width}x{monitor.height} (位置: {monitor.x},{monitor.y})"
        chk = ttk.Checkbutton(frame_monitor, text=monitor_info, variable=var)
        chk.pack(anchor=tk.W, pady=2)

    # 2. 不透明度调节区域
    frame_alpha = ttk.LabelFrame(root, text="遮罩不透明度 (0-100)", padding=(10, 5))
    frame_alpha.pack(fill=tk.X, padx=20, pady=10)

    scale_alpha = ttk.Scale(frame_alpha, from_=0, to=100, variable=current_alpha,
                            orient=tk.HORIZONTAL, command=scale_update_entry)
    scale_alpha.pack(fill=tk.X, padx=5, pady=5)

    frame_entry = ttk.Frame(frame_alpha)
    frame_entry.pack(fill=tk.X, padx=5, pady=5)

    entry_alpha = ttk.Entry(frame_entry, font=("微软雅黑", 10), width=10)
    entry_alpha.insert(0, "50")
    entry_alpha.pack(side=tk.LEFT, padx=5)
    entry_alpha.bind("<Return>", entry_update_scale)

    btn_confirm = ttk.Button(frame_entry, text="确认", command=entry_update_scale)
    btn_confirm.pack(side=tk.LEFT)

    lbl_hotkey = ttk.Label(frame_alpha, text="快捷键：Ctrl+↑ 增加不透明度 | Ctrl+↓ 减少不透明度",
                           font=("微软雅黑", 9), foreground="#666666")
    lbl_hotkey.pack(anchor=tk.W, padx=5, pady=2)

    # 3. 功能按钮区域
    frame_btn = ttk.Frame(root, padding=(10, 5))
    frame_btn.pack(fill=tk.X, padx=20, pady=10)

    btn_create = ttk.Button(frame_btn, text="生成遮罩", command=create_mask_windows)
    btn_create.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    btn_close = ttk.Button(frame_btn, text="关闭遮罩", command=close_mask_windows)
    btn_close.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    # 窗口关闭事件
    def on_closing():
        close_mask_windows()
        if listener:
            listener.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)


# 主函数
if __name__ == "__main__":
    if sys.platform != "win32":
        messagebox.showerror("不支持的系统", "该脚本仅支持Windows系统！")
        sys.exit(1)

    root = tk.Tk()
    build_ui(root)

    # 启动快捷键监听（守护线程）
    hotkey_thread = threading.Thread(target=start_hotkey_listener, daemon=True)
    hotkey_thread.start()

    root.mainloop()