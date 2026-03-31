import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import screeninfo
import threading
import ctypes
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

# 全局变量
selected_monitors = []
mask_windows = []
current_alpha = 50
current_color = "#000000"

# Windows API 常量
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
LWA_ALPHA = 0x2
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

def set_window_attributes(hwnd, alpha):
    try:
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, int(alpha * 2.55), LWA_ALPHA)
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
    except Exception as e:
        print(f"设置窗口属性失败: {e}")

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/monitors':
            try:
                monitors = screeninfo.get_monitors()
                data = [{
                    'id': idx,
                    'name': f"Display {idx + 1}",
                    'width': m.width,
                    'height': m.height,
                    'x': m.x,
                    'y': m.y
                } for idx, m in enumerate(monitors)]
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'alpha': current_alpha,
                'color': current_color,
                'mask_count': len(mask_windows)
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global selected_monitors, mask_windows, current_alpha, current_color

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()

        if self.path == '/api/mask/create':
            try:
                data = json.loads(body) if body else {}
                selected_ids = data.get('monitor_ids', [])

                for win in mask_windows:
                    try:
                        win.destroy()
                    except:
                        pass
                mask_windows.clear()
                selected_monitors.clear()

                monitors = screeninfo.get_monitors()
                selected_monitors = [monitors[i] for i in selected_ids if i < len(monitors)]

                if not selected_monitors:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': '请至少选择一个显示器'}).encode())
                    return

                def create_masks_thread():
                    for monitor in selected_monitors:
                        try:
                            mask = tk.Toplevel()
                            mask.title("")
                            mask.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
                            mask.overrideredirect(True)
                            mask.attributes("-topmost", True)
                            mask.resizable(False, False)
                            mask.configure(bg=current_color)

                            mask.update_idletasks()
                            hwnd = ctypes.windll.user32.GetParent(mask.winfo_id())
                            set_window_attributes(hwnd, current_alpha)

                            mask_windows.append(mask)
                        except Exception as e:
                            print(f"创建遮罩失败: {e}")

                thread = threading.Thread(target=create_masks_thread, daemon=True)
                thread.start()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'count': len(selected_monitors)}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        elif self.path == '/api/mask/close':
            try:
                for win in mask_windows:
                    try:
                        win.destroy()
                    except:
                        pass
                mask_windows.clear()
                selected_monitors.clear()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        elif self.path == '/api/mask/update':
            try:
                data = json.loads(body) if body else {}
                current_alpha = data.get('alpha', 50)
                current_color = data.get('color', '#000000')

                for win in mask_windows:
                    try:
                        win.configure(bg=current_color)
                        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
                        set_window_attributes(hwnd, current_alpha)
                    except:
                        pass

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    if sys.platform != "win32":
        print("仅支持 Windows 系统")
        sys.exit(1)

    root = tk.Tk()
    root.withdraw()

    server = HTTPServer(('127.0.0.1', 5000), APIHandler)
    print("Backend running on http://127.0.0.1:5000")

    def run_server():
        server.serve_forever()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    root.mainloop()


