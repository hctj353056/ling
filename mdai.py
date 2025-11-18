#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-mdai：把 /storage/emulated/0/聆灵/文件库/ 里的所有文件
一键转换成 mdai 格式的数字矩阵。
运行方式：
    python auto_mdai.py
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime

# ---------- 依赖库 ----------
# pip install pillow pydub opencv-python python-docx PyPDF2 markitdown

from PIL import Image
import cv2
import numpy as np
from pydub import AudioSegment
from docx import Document
import PyPDF2
from markitdown import MarkItDown   # 用于兜底文本提取

# ---------- 配置 ----------
INPUT_DIR   = "/storage/emulated/0/聆灵/文件库"
OUTPUT_DIR  = "/storage/emulated/0/聆灵/mdai_out"
AUDIO_SLICE = 0.1   # 秒
IMG_GRID    = (10, 10)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- 通用矩阵化 ----------
def matrixize_txt(path):
    """纯文本 -> 字符编码矩阵"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return [[ord(ch) for ch in line] for line in text.splitlines()]

def matrixize_docx(path):
    """Word -> 段落+样式矩阵"""
    doc = Document(path)
    return [[p.text, p.style.name] for p in doc.paragraphs]

def matrixize_pdf(path):
    """PDF -> 页文本矩阵"""
    reader = PyPDF2.PdfReader(path)
    return [page.extract_text() or "" for page in reader.pages]

def matrixize_image(path):
    """图片 -> RGB 网格矩阵"""
    img = Image.open(path).convert("RGB")
    img = img.resize(IMG_GRID)
    pixels = list(img.getdata())
    return [list(pixel) for pixel in pixels]

def matrixize_audio(path):
    """音频 -> 每 0.1s 的响度矩阵"""
    audio = AudioSegment.from_file(path)
    step = int(AUDIO_SLICE * 1000)
    loudness = [chunk.dBFS for chunk in audio[::step]]
    return loudness

def matrixize_video(path):
    """视频 -> 帧矩阵 + 音频矩阵"""
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        small = cv2.resize(frame, IMG_GRID)
        frames.append(small.tolist())
    cap.release()
    audio_matrix = matrixize_audio(path) if path.lower().endswith((".mp4", ".avi")) else []
    return {"video": frames, "audio": audio_matrix}

# ---------- 路由 ----------
PARSERS = {
    ".txt":  matrixize_txt,
    ".md":   matrixize_txt,
    ".docx": matrixize_docx,
    ".pdf":  matrixize_pdf,
    ".jpg":  matrixize_image,
    ".jpeg": matrixize_image,
    ".png":  matrixize_image,
    ".gif":  matrixize_image,
    ".mp3":  matrixize_audio,
    ".wav":  matrixize_audio,
    ".mp4":  matrixize_video,
    ".avi":  matrixize_video,
}

# ---------- 主流程 ----------
def convert_one(file_path: Path):
    ext = file_path.suffix.lower()
    if ext not in PARSERS:
        # 兜底：用 markitdown 转 Markdown 再矩阵化
        md = MarkItDown()
        result = md.convert(str(file_path))
        matrix = result.text_content.splitlines()
    else:
        matrix = PARSERS[ext](str(file_path))

    meta = {
        "original": str(file_path),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "matrix": matrix
    }

    out_file = Path(OUTPUT_DIR) / f"{file_path.stem}_{int(time.time())}.mdai"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成 {out_file.name}")

def main():
    for file in Path(INPUT_DIR).rglob("*"):
        if file.is_file():
            try:
                convert_one(file)
            except Exception as e:
                print(f"❌ 跳过 {file.name}：{e}")

if __name__ == "__main__":
    main()