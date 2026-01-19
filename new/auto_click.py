import pyautogui
import keyboard
import time

# ================= 設定エリア =================

# 1. 監視したい場所の座標
WATCH_X = 100
WATCH_Y = 200

# 2. パターンA：もしこの色（赤）なら...
COLOR_A = (255, 0, 0) # 調べたRGB値 (例: 真っ赤)
# その時に押すボタンの座標
BUTTON_A_X = 500
BUTTON_A_Y = 500

# 3. パターンB：もしこの色（青）なら...
COLOR_B = (0, 0, 255) # 調べたRGB値 (例: 真っ青)
# その時に押すボタンの座標
BUTTON_B_X = 600
BUTTON_B_Y = 600

# ============================================

print("自動化を開始します。")
print("終了するにはキーボードの 'q' を押してください。")

while True:
    # 緊急停止用
    if keyboard.is_pressed('q'):
        print("終了します。")
        break

    try:
        # 指定した座標の色を取得
        # pixelMatchesColorは、指定座標が指定色と一致するか判定します
        # tolerance=10 は「多少の色のズレ(誤差10)を許容する」という意味です
        
        # パターンAのチェック
        if pyautogui.pixelMatchesColor(WATCH_X, WATCH_Y, COLOR_A, tolerance=10):
            print(f"色A({COLOR_A})を検知！ -> ボタンAをクリック")
            pyautogui.click(BUTTON_A_X, BUTTON_A_Y)
            time.sleep(0.5) # 連打防止のための待機時間

        # パターンBのチェック
        elif pyautogui.pixelMatchesColor(WATCH_X, WATCH_Y, COLOR_B, tolerance=10):
            print(f"色B({COLOR_B})を検知！ -> ボタンBをクリック")
            pyautogui.click(BUTTON_B_X, BUTTON_B_Y)
            time.sleep(0.5) # 連打防止のための待機時間
        
        # 負荷を下げるために少し待つ
        time.sleep(0.1)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        break