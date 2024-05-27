@echo off
setlocal enabledelayedexpansion

REM モデルディレクトリの基本パスを実行ディレクトリのmodelsサブディレクトリに設定
set "dpath=%~dp0Models"

REM Taggerモデルダウンロード

REM Taggerモデルダウンロード
set "MODEL_DIR=%dpath%"
set "MODEL_ID=SmilingWolf/wd-swinv2-tagger-v3"
set "FILES=config.json model.onnx selected_tags.csv sw_jax_cv_config.json"

if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"

for %%f in (%FILES%) do (
    set "FILE_PATH=%MODEL_DIR%\%%f"
    if not exist "!FILE_PATH!" (
        curl -L "https://huggingface.co/%MODEL_ID%/resolve/main/%%f" -o "!FILE_PATH!"
        echo Downloaded %%f
    ) else (
        echo %%f already exists.
    )
)

endlocal

pause