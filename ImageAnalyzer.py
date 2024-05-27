import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
from utils.tagger import modelLoad, analysis
import glob
import json


# 実行ファイルのディレクトリパスを取得
dpath = os.path.dirname(sys.argv[0])

def create_default_settings_file(filename):
    """
    初期設定を含む設定ファイル(settings.ini)を作成する関数。
    もし既に ".old" ファイルが存在する場合は、その設定を読み込み、
    新しい設定があれば追加する。
    """
    # デフォルト設定値
    default_settings = {
        'prompt_save': 'False',
        'agree_terms': 'False'
    }

    config = configparser.ConfigParser()

    # ".old" ファイルが存在するかチェックし、存在すれば読み込む
    old_filename = filename + ".old"
    if os.path.exists(old_filename):
        config.read(old_filename)
        if 'Settings' in config:
            for key, value in default_settings.items():
                if key not in config['Settings']:
                    config['Settings'][key] = str(value)
    else:
        config['Settings'] = default_settings

    # 新しい設定ファイルを保存
    with open(filename, 'w') as configfile:
        config.write(configfile)

def save_settings(filename, new_settings):
    """
    新しい設定を指定された設定ファイルに保存する関数。
    """
    config = configparser.ConfigParser()
    config.read(filename)  # 既存の設定を読み込む

    if 'Settings' not in config:
        config['Settings'] = {}

    # 新しい設定を更新
    for key, value in new_settings.items():
        config['Settings'][key] = str(value)

    with open(filename, 'w') as configfile:
        config.write(configfile)

def save_terms_agreement(config_filename, agree_terms):
    """
    ユーザーが免責事項に同意したかどうかの情報を設定ファイルに保存する関数。
    """
    config = configparser.ConfigParser()
    config.read(config_filename)
    
    if 'Settings' not in config:
        config['Settings'] = {}

    config['Settings']['agree_terms'] = str(agree_terms)
    
    with open(config_filename, 'w') as configfile:
        config.write(configfile)

def check_and_display_terms(config_filename):
    """
    アプリケーションの初回起動時に免責事項を表示し、
    ユーザーからの同意を得る関数。ユーザーが同意した場合はTrueを返す。
    """
    config = configparser.ConfigParser()
    config.read(config_filename)

    if config.get('Settings', 'agree_terms', fallback='False') == 'True':
        return True

    # 免責事項を表示
    terms_text = (
        "責任の免除\n"
        "このソフトウェア使用に関連するすべての問題や損害について、ソフト開発者は責任を負いません。\n\n"
        "このソフトウェアはAIによってイラストが構成する要素を分析します。"
        "これはあくまで参照用であり確定ではありません。他人の絵を読み込ませて誹謗中傷する等の悪用はしないでください。\n\n"
        "この免責事項に同意するには「OK」をクリックしてください。OKをクリックすることにより、ユーザーは本免責事項に同意したものとみなされます。\n\n"
        "この免責事項は、ImageAnalyzerの使用に関するすべての問題やリスクに対するソフト開発者の責任を免除するものであり、"
        "ユーザーはこれを理解し、受け入れたものとみなされます。ImageAnalyzerを使用する前に、この免責事項をよく読んでください。"
        )
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示にする
    response = messagebox.showinfo("免責事項", terms_text)
    root.destroy()  # メインウィンドウを破棄する

    if response == "ok":
        save_terms_agreement(config_filename, True)
        return True
    else:
        return False

def find_images(directory):
    """
    指定されたディレクトリ内のすべての画像ファイルを再帰的に検索する関数。
    """
    image_extensions = ['*.jpg', '*.jpeg', '*.png']
    files = []
    for ext in image_extensions:
        files.extend(glob.glob(os.path.join(directory, '**', ext), recursive=True))
    return files

# 設定ウィンドウのクラス定義
class ConfigWindow:
    def __init__(self, root, config_filename, main_app):
        self.root = root  # Tkinterのルートウィンドウ
        self.main_app = main_app  # メインアプリケーションへの参照
        root.title("Config")  # ウィンドウタイトルの設定
        self.root.geometry("600x150")  # ウィンドウサイズの設定
        self.model = None
        
        # ウィンドウの第2列を拡張可能に設定
        root.columnconfigure(1, weight=1)

        # 設定値を保持するための辞書
        self.settings = {}

        # ウィジェットの配置
        ttk.Label(root, text="Image_path").grid(row=1, column=0)
        self.image_path_entry = ttk.Entry(root)
        self.image_path_entry.grid(row=1, column=1, sticky=tk.EW)
        
        ttk.Label(root, text="Additional tags").grid(row=2, column=0)
        self.additional_tags_entry = ttk.Entry(root)
        self.additional_tags_entry.grid(row=2, column=1, sticky=tk.EW)

        ttk.Label(root, text="Exclude tag").grid(row=3, column=0)
        self.exclude_tags_entry = ttk.Entry(root)
        self.exclude_tags_entry.grid(row=3, column=1, sticky=tk.EW)

        # チェックボックスの状態を格納する変数
        self.save_text_var = tk.BooleanVar()
        # チェックボックスの作成と配置
        self.save_text_checkbutton = ttk.Checkbutton(root, text="Prompt Save", variable=self.save_text_var, onvalue=True, offvalue=False)
        self.save_text_checkbutton.grid(row=4, column=0, columnspan=2, sticky=tk.W)

        self.prompt_analysis_button = ttk.Button(root, text="Prompt Analysis", command=self.prompt_analysis)
        self.prompt_analysis_button.grid(row=5, column=0, columnspan=2, sticky=tk.EW)

        ttk.Label(root, text="Prompt").grid(row=6, column=0)
        self.prompt_entry = tk.Text(root, height=1)
        self.prompt_entry.grid(row=6, column=1, sticky=tk.EW)

        # 設定ファイルが存在しない場合は、デフォルト設定ファイルを作成
        if not os.path.exists(config_filename):
            create_default_settings_file(config_filename)

        # 設定を読み込み、各ウィジェットに反映
        self.settings = self.load_settings(config_filename)
        self.save_text_var.set(self.settings.get('prompt_save', False) )        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """ウィンドウが閉じられる時の処理"""
        self.main_app.cleanup()

    def load_settings(self, config_filename):
        """設定ファイルから設定を読み込む"""
        config = configparser.ConfigParser()
        try:
            if not os.path.exists(config_filename):
                create_default_settings_file(config_filename)
            config.read(config_filename)
            return dict(config.items('Settings'))  # 'Settings' セクションの項目を辞書として取得
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}

    def get_user_settings(self):
        """ユーザーの設定を取得する"""
        return {
            'prompt': self.prompt_entry.get("1.0", "end-1c"),  # Textウィジェットからテキストを取得する正しい方法
            'prompt_save': self.save_text_var.get(),  # チェックボックスの状態を取得して辞書に追加
        }


    def get_current_settings(self):
        """現在のUIから設定を取得する"""
        return {
            'prompt_save': self.save_text_var.get(),  # チェックボックスの状態を取得して辞書に追加           
        }

    def adjust_text_widget_height(self):
        content = self.prompt_entry.get("1.0", tk.END)
        # 一行あたりの最大文字数（ウィジェットの幅やフォントサイズに応じて調整）
        max_chars_per_line = 73

        # 改行を考慮して必要な行数を計算
        lines = sum((len(line) // max_chars_per_line + (1 if len(line) % max_chars_per_line > 0 else 0)) for line in content.split('\n'))

        # Textウィジェットの高さを更新
        self.prompt_entry.config(height=lines)

        # ウィンドウの基本高さ（Textウィジェット以外の部分）
        base_height = 120
        # Textウィジェット内の1行あたりの高さ（おおよその値）
        per_line_height = 15
        # ウィンドウの新しい高さを計算
        window_height = base_height + (lines * per_line_height)

        # ウィンドウのサイズを更新
        self.root.geometry(f"600x{window_height}")


    def prompt_analysis(self):
        model_dir = os.path.join(dpath, 'Models/')
        if not os.path.exists(model_dir):
            print("管理者権限で『model_DL.cmd』を実行して下さい")
        if self.model is None:
            self.model = modelLoad(model_dir)

        path_input = self.image_path_entry.get().replace("\\", "/").replace("\"", "")
        additional_tags_input = self.additional_tags_entry.get().strip()
        additional_tags = [tag.strip() for tag in additional_tags_input.split(",") if tag.strip()]
        exclude_tags_input = self.exclude_tags_entry.get().strip()
        exclude_tags = set(tag.strip() for tag in exclude_tags_input.split(",") if tag.strip())

        dump_file_path = os.path.join(dpath, 'dump.json')
        image_files = []
        all_tags_list = []
        try:
            with open(dump_file_path, 'r') as f:
                data = json.load(f)
            if data['path_input'] == path_input:
                print("以前の解析結果を使用します。")
                image_files = data['image_files']
                # ここで all_tags_list の再構成は不要
            else:
                raise FileNotFoundError  # path_input が変更された場合は再検索を行う
        except (FileNotFoundError, json.JSONDecodeError):
            if os.path.isdir(path_input):
                image_files = find_images(path_input)
            elif os.path.isfile(path_input):
                image_files = [path_input]
            else:
                messagebox.showerror("Error", "Invalid path.")
                return

        if not image_files:  # image_files が空の場合、再検索を試みる
            image_files = find_images(path_input) if os.path.isdir(path_input) else ([path_input] if os.path.isfile(path_input) else [])
            if not image_files:
                messagebox.showerror("Error", "No images found.")
                return

        total_images = len(image_files)
        for index, image_path in enumerate(image_files, start=1):
            print(f"処理中: {index}/{total_images}")  # 進捗状況を表示

            tag = analysis(image_path, model_dir, self.model)
            result_tags_list = tag.split(", ")

            filtered_tags_list = [t for t in result_tags_list if t not in exclude_tags and t not in additional_tags]
            final_tags_list = additional_tags + filtered_tags_list

            if self.save_text_var.get():
                tags_text = ', '.join(final_tags_list)
                txt_path = f"{os.path.splitext(image_path)[0]}.txt"
                with open(txt_path, 'w') as file:
                    file.write(tags_text)

            all_tags_list.extend(final_tags_list)

        unique_tags_ordered = list(dict.fromkeys(all_tags_list))

        # 新しい解析結果を dump.json に保存
        data = {
            'path_input': path_input,
            'image_files': image_files,
            'all_tags_list': all_tags_list
        }
        with open(dump_file_path, 'w') as f:
            json.dump(data, f)

        self.prompt_entry.delete("1.0", tk.END)
        self.prompt_entry.insert("1.0", ', '.join(unique_tags_ordered))
        self.adjust_text_widget_height()

# MainAppクラスは、アプリケーションのメインウィンドウを管理し、アプリケーションの起動と終了処理を担当します。
class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.config_filename = "settings.ini"
        self.config_window = ConfigWindow(self.root, self.config_filename, self)
        self.settings = self.config_window.load_settings(self.config_filename)

        self.setup_callbacks()
        if not os.path.exists(self.config_filename):
            create_default_settings_file(self.config_filename)  # デフォルトの設定ファイルを作成します。

        # 免責事項に対するユーザーの同意を確認します。
        if not check_and_display_terms(self.config_filename):
            print("ユーザーが免責事項に同意しなかったため、アプリケーションを終了します。")
            sys.exit()

    def setup_callbacks(self):
        # ウィンドウが閉じられる際のコールバックを設定します。
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

    def cleanup(self):
        # アプリケーション終了時に設定を保存し、メインウィンドウを閉じます。
        current_settings = self.config_window.get_current_settings()
        save_settings(self.config_filename, current_settings)
        self.root.destroy()

    def run(self):
        # アプリケーションのメインループを実行します。
        self.root.mainloop()

def main():
    app = MainApp()
    app.run()

if __name__ == "__main__":
    main()