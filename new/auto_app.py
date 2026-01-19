import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import time
import json
import os

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自動判断動作装置 (連打＆記憶版)")
        self.root.geometry("600x750")
        
        # 変数
        self.watch_x = None
        self.watch_y = None
        self.picked_color = None 
        self.rules = [] 
        self.is_running = False
        self.thread = None
        self.settings_file = "settings.json"

        # スタイル設定
        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Meiryo", 10, "bold"))

        # ============================================
        # エリア1：座標を特定
        # ============================================
        frame_pos = tk.LabelFrame(root, text="1. 監視する場所を決める", padx=10, pady=10)
        frame_pos.pack(fill="x", padx=10, pady=5)

        self.lbl_pos = ttk.Label(frame_pos, text="座標: 未設定", style="Bold.TLabel")
        self.lbl_pos.pack(side="left", padx=10)

        btn_set_pos = ttk.Button(frame_pos, text="座標を特定 (3秒タイマー)", command=self.start_pick_pos_timer)
        btn_set_pos.pack(side="right")

        # ============================================
        # エリア2：色とボタンを追加
        # ============================================
        frame_rule = tk.LabelFrame(root, text="2. ルールを追加する", padx=10, pady=10)
        frame_rule.pack(fill="x", padx=10, pady=5)

        # --- 色取得 ---
        frame_color_pick = tk.Frame(frame_rule)
        frame_color_pick.pack(fill="x", pady=5)
        
        self.canvas_color = tk.Canvas(frame_color_pick, width=30, height=30, bg="white", relief="solid", borderwidth=1)
        self.canvas_color.pack(side="left", padx=5)
        
        self.lbl_color_val = ttk.Label(frame_color_pick, text="未取得")
        self.lbl_color_val.pack(side="left", padx=5)

        btn_pick_color = ttk.Button(frame_color_pick, text="画面から色を取得 (3秒タイマー)", command=self.start_pick_color_timer)
        btn_pick_color.pack(side="right")

        # --- 動作設定 ---
        frame_action = tk.Frame(frame_rule)
        frame_action.pack(fill="x", pady=5)

        # キー入力
        ttk.Label(frame_action, text="押すキー:").pack(side="left")
        self.entry_key = tk.Entry(frame_action, width=15, font=("Meiryo", 10), justify="center", bg="#f0f0f0")
        self.entry_key.insert(0, "クリックして設定")
        self.entry_key.pack(side="left", padx=5)
        self.entry_key.bind("<Button-1>", self.enable_key_listen)
        self.entry_key.bind("<Key>", self.on_key_press)

        btn_set_click = ttk.Button(frame_action, text="クリック", width=8, command=self.set_mouse_click)
        btn_set_click.pack(side="left", padx=2)

        # ★連打速度設定（追加部分）
        ttk.Label(frame_action, text="待機(秒):").pack(side="left", padx=(10, 2))
        self.entry_interval = tk.Entry(frame_action, width=5, justify="center")
        self.entry_interval.insert(0, "0.1") # デフォルト0.1秒
        self.entry_interval.pack(side="left")

        btn_add_rule = ttk.Button(frame_rule, text="追加", command=self.add_rule)
        btn_add_rule.pack(side="right", pady=5)

        # ルール一覧
        self.tree = ttk.Treeview(frame_rule, columns=("Color", "Action", "Interval"), show="headings", height=6)
        self.tree.heading("Color", text="色 (RGB)")
        self.tree.heading("Action", text="動作")
        self.tree.heading("Interval", text="待機(秒)")
        self.tree.column("Color", width=120)
        self.tree.column("Action", width=100)
        self.tree.column("Interval", width=80)
        self.tree.pack(fill="x", pady=5)

        btn_del_rule = ttk.Button(frame_rule, text="選択削除", command=self.delete_rule)
        btn_del_rule.pack(anchor="e")

        # ============================================
        # エリア3：感度調整
        # ============================================
        frame_adjust = tk.LabelFrame(root, text="★ 感度(判定の甘さ)調整", padx=10, pady=10, fg="blue")
        frame_adjust.pack(fill="x", padx=10, pady=5)

        self.tolerance_var = tk.IntVar(value=30)
        self.scale_tolerance = tk.Scale(frame_adjust, from_=0, to=150, orient="horizontal", variable=self.tolerance_var, label="許容する色のズレ")
        self.scale_tolerance.pack(fill="x")

        # ============================================
        # エリア4：開始・停止
        # ============================================
        frame_ctrl = tk.Frame(root, pady=10)
        frame_ctrl.pack(fill="x", padx=10)

        self.btn_start = tk.Button(frame_ctrl, text="開始", bg="orange", fg="white", font=("Meiryo", 14, "bold"), width=10, command=self.start_automation)
        self.btn_start.pack(side="left", padx=20)

        self.btn_stop = tk.Button(frame_ctrl, text="停止", bg="gray", fg="white", font=("Meiryo", 14, "bold"), width=10, command=self.stop_automation, state="disabled")
        self.btn_stop.pack(side="right", padx=20)

        self.lbl_status = ttk.Label(root, text="待機中", font=("Meiryo", 10))
        self.lbl_status.pack(side="bottom", pady=5)

        # ★起動時に前回の設定を読み込む
        self.load_settings()

    # ----------------------------------------------------
    # キー入力取得ロジック
    # ----------------------------------------------------
    def enable_key_listen(self, event):
        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, "キーを押す...")
        self.entry_key.config(bg="#ffffcc")
    
    def on_key_press(self, event):
        key_name = event.keysym
        key_mapping = {
            "Return": "enter", "space": "space", "Escape": "esc",
            "Up": "up", "Down": "down", "Left": "left", "Right": "right",
            "BackSpace": "backspace", "Tab": "tab",
            "Shift_L": "shiftleft", "Shift_R": "shiftright",
            "Control_L": "ctrlleft", "Control_R": "ctrlright",
            "Alt_L": "altleft", "Alt_R": "altright"
        }
        final_key = key_mapping.get(key_name, key_name.lower())
        if len(key_name) > 1 and key_name.startswith("F") and key_name[1:].isdigit():
            final_key = key_name.lower()

        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, final_key)
        self.entry_key.config(bg="#f0f0f0")
        self.root.focus_set()
        return "break"

    def set_mouse_click(self):
        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, "click")
        self.entry_key.config(bg="#f0f0f0")

    # ----------------------------------------------------
    # 設定の保存・読込 (記憶機能)
    # ----------------------------------------------------
    def save_settings(self):
        """現在の設定をファイルに保存"""
        data = {
            "watch_x": self.watch_x,
            "watch_y": self.watch_y,
            "tolerance": self.tolerance_var.get(),
            "rules": self.rules
        }
        try:
            with open(self.settings_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"保存エラー: {e}")

    def load_settings(self):
        """起動時に設定を読み込む"""
        if not os.path.exists(self.settings_file):
            return # ファイルがなければ何もしない

        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
            
            # データを復元
            if data.get("watch_x") is not None:
                self.watch_x = data["watch_x"]
                self.watch_y = data["watch_y"]
                self.lbl_pos.config(text=f"座標: X={self.watch_x}, Y={self.watch_y}")
            
            if data.get("tolerance") is not None:
                self.tolerance_var.set(data["tolerance"])

            if data.get("rules"):
                self.rules = data["rules"]
                for r in self.rules:
                    # JSONから読み込むと色がリストになるのでタプルに戻す等の処理は自動で合う
                    # 待機時間が保存されていない古いデータ対策
                    interval = r.get("interval", 0.1)
                    r["interval"] = interval 
                    self.tree.insert("", "end", values=(str(r["color"]), r["action"], str(interval)))

        except Exception as e:
            print(f"読込エラー: {e}")

    # ----------------------------------------------------
    # その他の機能
    # ----------------------------------------------------
    def start_pick_pos_timer(self):
        self.lbl_status.config(text="3秒後に座標を取得します...", foreground="red")
        self.root.after(3000, self.get_position)

    def get_position(self):
        x, y = pyautogui.position()
        self.watch_x, self.watch_y = x, y
        self.lbl_pos.config(text=f"座標: X={x}, Y={y}")
        self.lbl_status.config(text=f"座標設定完了: {x}, {y}", foreground="black")
        self.save_settings() # 保存

    def start_pick_color_timer(self):
        self.lbl_status.config(text="3秒後に色を取得します...", foreground="red")
        self.root.after(3000, self.get_color)

    def get_color(self):
        x, y = pyautogui.position()
        try:
            pixel = pyautogui.screenshot().getpixel((x, y))
            self.picked_color = pixel
            hex_color = '#%02x%02x%02x' % pixel
            self.canvas_color.config(bg=hex_color)
            self.lbl_color_val.config(text=f"{pixel}")
            self.lbl_status.config(text="色を取得しました。", foreground="black")
        except Exception:
            self.lbl_status.config(text="色の取得に失敗しました", foreground="red")

    def add_rule(self):
        if self.picked_color is None:
            messagebox.showwarning("エラー", "色を取得してください")
            return
        action = self.entry_key.get()
        if "キーを押す" in action or "設定" in action:
            messagebox.showwarning("エラー", "キーを設定してください")
            return
        
        # 連打間隔の取得
        try:
            interval = float(self.entry_interval.get())
        except ValueError:
            messagebox.showwarning("エラー", "待機時間は数字で入力してください")
            return

        rule = {"color": self.picked_color, "action": action, "interval": interval}
        self.rules.append(rule)
        self.tree.insert("", "end", values=(str(self.picked_color), action, str(interval)))
        self.save_settings() # 保存

    def delete_rule(self):
        selected = self.tree.selection()
        if selected:
            idx = self.tree.index(selected)
            self.rules.pop(idx)
            self.tree.delete(selected)
            self.save_settings() # 保存

    def start_automation(self):
        if self.watch_x is None or not self.rules:
            messagebox.showerror("エラー", "座標またはルールが設定されていません")
            return
        self.is_running = True
        self.btn_start.config(state="disabled", bg="gray")
        self.btn_stop.config(state="normal", bg="red")
        self.lbl_status.config(text="監視中...", foreground="blue")
        
        self.thread = threading.Thread(target=self.loop_process)
        self.thread.daemon = True
        self.thread.start()

    def stop_automation(self):
        self.is_running = False
        self.btn_start.config(state="normal", bg="orange")
        self.btn_stop.config(state="disabled", bg="gray")
        self.lbl_status.config(text="停止しました", foreground="black")

    def loop_process(self):
        while self.is_running:
            try:
                pyautogui.FAILSAFE = False
                
                current_color = pyautogui.pixel(self.watch_x, self.watch_y)
                tolerance = self.tolerance_var.get()

                matched = False
                for rule in self.rules:
                    target = rule["color"]
                    if (abs(current_color[0] - target[0]) <= tolerance and
                        abs(current_color[1] - target[1]) <= tolerance and
                        abs(current_color[2] - target[2]) <= tolerance):
                        
                        action = rule["action"]
                        interval = rule.get("interval", 0.1) # 設定された連打間隔
                        
                        print(f"Hit! {current_color} matches {target} -> {action} (wait {interval}s)")
                        
                        if action == "click":
                            pyautogui.click()
                        else:
                            pyautogui.press(action)
                        
                        # ★ここが重要：設定した時間だけ待つ（高速化対応）
                        time.sleep(interval)
                        
                        matched = True
                        break 
                
                if not matched:
                    # 監視サイクル（超高速）
                    time.sleep(0.01)

            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()