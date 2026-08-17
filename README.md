# quick-work-phraser
一个基于 PySide6 的 Windows 桌面工具，提供快捷短语粘贴发送，提高工作效率。

## 功能

- 短语列表点击即发送：自动粘贴到发送前的前台窗口输入框
- 支持自定义短语，本地保存
- 系统托盘常驻

## 环境要求

- Windows 10 / 11
- Python 3.10+

## 运行

### 1. 安装依赖

```bash
pip install PySide6 pyperclip pyautogui pywin32
```

### 2. 以 Python 文件运行

```bash
python quick_phraser.py
```

### 3. 以 exe 程序运行

```bash
python -m PyInstaller -F -w --clean \
  --exclude-module PyQt5 --exclude-module PyQt6 \
  quick_phraser.py
```

构建后的产物位于同目录下的 `dist` 文件夹

## 默认短语
项目提供一些默认短语，如下：

```json
[
  "好的",
  "收到",
  "明白",
  "谢谢",
  "稍等",
  "我马上处理",
  "请问有什么可以帮您？",
  "久等了",
  "确认无误",
  "已安排",
  "已完成",
  "请查收",
  "没问题",
  "不客气",
  "再见",
  "稍后再联系",
  "麻烦您了",
  "不辛苦",
  "祝好",
  "收到请回复",
  "1",
  "🌹",
  "对不起",
  "抱歉",
  "辛苦"
]
```
