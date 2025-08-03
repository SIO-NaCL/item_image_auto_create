import sys
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import pandas as pd
import logging
from logging import getLogger


# df.iloc[行,列]
# 共通画像は png ファイルのみ対応 他の画像ファイルは jpg か png のみ対応

# グローバル変数
# カレントディレクトリ
if getattr(sys, 'frozen', False):
    # PyInstallerでバンドルされたexeとして実行されている場合
    BASE_DIR = Path(sys.executable).parent
else:
    # 通常の .py スクリプトとして実行されている場合
    BASE_DIR = Path(__file__).resolve().parent

# logger================================================
log_name = Path(__file__).parent / "商品画像生成.log"

logger = getLogger("LogTest")
logger.setLevel(logging.DEBUG)  # loggerとしてはDEBUGで
logger_formatter = logging.Formatter("%(asctime)s %(levelname)8s %(message)s")

# handler1を作成(コンソール出力)
handler1 = logging.StreamHandler()
handler1.setFormatter(logger_formatter)

# handler2を作成(ファイル出力)
handler2 = logging.FileHandler(
    filename=log_name, 
    encoding="utf-8-sig"
) 
handler2.setLevel(logging.INFO)  
handler2.setFormatter(logger_formatter)

# loggerに2つのハンドラを設定
logger.addHandler(handler1)
logger.addHandler(handler2)
# ================================================================================================



# jpgもしくはpngを張り付ける処理 ========================================
def paste_jpg_png(img:Image.Image, p_img:Image.Image, p_img_name:str):
    # 貼付座標の割り出し
    x, y = p_img.size

    x_p = round((600 - x) / 2)
    y_p = round((600 - y) / 2)

    # jpgファイルの場合の処理
    if ".jpg" in p_img_name[-4:]:
        img.paste(p_img, (x_p, y_p))

    # pngファイルの場合の処理
    elif ".png" in p_img_name[-4:]:
        # 透過情報を扱えるようRGBA化
        if p_img.mode != "RGBA":
            p_img = p_img.convert("RGBA")

        # アルファチャンネルをマスクに
        alpha = p_img.split()[-1]
        img.paste(p_img, (x_p, y_p), mask=alpha)

    return img


# 画像のリサイズ処理 ====================================================
def resize_img(img:Image.Image):
    x, y = img.size

    # 600px * 600pxの場合は何もしない
    if x == 600 and y == 600:
        return img

    # xの方が大きい場合かつxが600px以上の場合
    if x >= y and x > 600:
        size_ratio = 600 / x
        resize_y = round(y * size_ratio)
        resize_x = int(600)

    # yの方が大きい場合かつyが600px以上の場合
    elif y > x and y > 600:
        size_ratio = 600 / y
        resize_y = int(600)
        resize_x = round(x * size_ratio)

    # x,y共に600px以下の場合
    else:
        resize_y = y
        resize_x = x

    # 元画像の画像かつyが480より大きい場合はそれ以下のサイズにする
    if resize_y > 480:
        size_ratio = 480 / resize_y
        resize_y = 480
        resize_x = round(resize_x * size_ratio)

    # リサイズ処理
    if y != resize_y and x != resize_x:
        img = img.resize((resize_x, resize_y), resample=0)

    return img


# 文字入れ処理
def draw_text(text:str, img:Image.Image):
    max_font_size = 42 # 最大フォントサイズ
    min_font_size = 10 # 最小フォントサイズ
    padding = 5  # 右端と上端からの余白
    font_path = "C:/Windows/Fonts/meiryo.ttc"  # OS等で適宜フォントパスを変更(現在はwidows11日本語版を想定)

    draw = ImageDraw.Draw(img)

    # 文字の長さによってフォントサイズを調整
    font_size = max_font_size
    while font_size >= min_font_size:
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        if text_width <= img.width - padding * 2:
            break
        font_size -= 1

    # 最終描画位置（右上）
    x = img.width - text_width - padding
    y = padding
    # テキストを描画
    draw.text((x, y), text, fill="black", font=font)

    # 画像を保存
    return img


# =========================================================================
# dfを読み込んで各列に記載された名前の画像を挿入して出力する処理
def make_image(df:pd.DataFrame):
    cols = [t for t in df.columns if t not in ["完成画像"]]
    for ind in df.index:
        # 白画像、完成画像名が空欄のものはcontinue
        if pd.isna(df.loc[ind, f"元画像"]):
            continue
        if pd.isna(df.loc[ind, f"完成画像"]):
            continue

        # test用=========
        # if ind > 2:
        #     continue
        # ===============

        # 白背景画像の作成
        img = Image.new("RGB", (600, 600), (255, 255, 255))

        # 行ごとに各列を参照して素材画像の読込_貼付
        for col in cols:
            # 読込処理
            if pd.isna(df.loc[ind, f"{col}"]):
                continue

            value = df.loc[ind, f"{col}"]

            #文字入れ処理---------------------------------------------------
            if col == "_右上テキスト_":
                img = draw_text(value, img)

                continue

            # 画像貼り付け処理----------------------------------------------
            else:
                # ディレクトリを取得してファイルを取得
                coldir = col.split("_", 1)[0] if "_" in col else col
                img_p = BASE_DIR / coldir / value
                img_p = Image.open(img_p)

                # 貼付画像の長辺が600pxより大きかった場合、リサイズする処理
                if coldir == "元画像":
                    img_p = resize_img(img_p)

                # 貼付処理
                img = paste_jpg_png(img, img_p, value)

        # 出力処理
        fname = BASE_DIR/ "完成画像" / df.loc[ind, "完成画像"]
        img.save(fname, quality=95)

        # ログ出力
        logger.info(f"{ind+1}/{len(df.index)}【{fname}】生成完了")
    logger.info(f"作業完了")



# ==============================================================================
# メイン関数
def main():
    # 出力する画像リストのcsv名
    fname = BASE_DIR / "商品画像作成.csv"

    # 完成画像ディレクトリがなければ作成
    output_dir = BASE_DIR / "完成画像"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # 出力用のcsvの読込
    df = pd.read_csv(fname)

    # 画像出力処理
    make_image(df)


# ==============================================================================


# 実行処理
if __name__ == "__main__":
    main()
    # test_main()
