import sys
import os
import tkinter as tk
from tkinter import messagebox
import json
import schedule
import time
import threading
import pygame
from datetime import datetime, timedelta

if getattr(sys, "frozen", False):
    # pyinstaller로 생성된 exe 파일에서 실행 중인 경우
    base_path = sys._MEIPASS
else:
    # 개발 중일 때, 스크립트가 있는 디렉토리
    base_path = os.path.dirname(__file__)

# presets.json 경로 생성
presets_path = os.path.join(base_path, "presets.json")


# 프리셋 파일 로드
def load_presets():
    try:
        # JSON 파일 읽기
        with open(presets_path, "r", encoding="UTF-8") as f:
            return json.load(f)
    except FileNotFoundError:
        messagebox.showwarning("presets.json 파일을 찾을 수 없습니다.")
        return []


# 프리셋을 파일에 저장
def save_presets(presets):
    with open(presets_path, "w", encoding="UTF-8") as f:
        json.dump(presets, f, indent=4)


# GUI 로그 출력 함수
def log_message(message):
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)  # 스크롤을 아래로 자동 이동


# 프리셋을 GUI에 표시
def display_presets():
    presets_list.delete(0, tk.END)
    for preset in presets:
        presets_list.insert(tk.END, preset["name"])


# 프리셋 선택 이벤트
def select_preset(event):
    try:
        selected_index = event.widget.curselection()[0]
        selected_preset = presets[selected_index]

        name_entry.delete(0, tk.END)
        name_entry.insert(0, selected_preset["name"])

        time_entry.delete(0, tk.END)
        time_entry.insert(0, selected_preset["time"])

        log_message(f"프리셋 선택됨: {selected_preset['name']} - {selected_preset['time']}")

    except IndexError:
        pass


# 프리셋 수정 함수
def modify_preset():
    global presets

    try:
        selected_index = presets_list.curselection()[0]
        new_name = name_entry.get()
        new_time = time_entry.get()

        presets[selected_index]["name"] = new_name
        presets[selected_index]["time"] = new_time

        save_presets(presets)
        display_presets()
        schedule_presets()

        log_message(f"프리셋 수정됨: {new_name} - {new_time}")
        messagebox.showinfo("수정 완료", "프리셋이 수정되었습니다.")
    except IndexError:
        messagebox.showwarning("선택 오류", "수정할 프리셋을 선택해주세요.")


# 오디오 재생 함수
def play_audio(file_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)

        log_message(f"오디오 재생 중: {file_path}")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(1)
    except Exception as e:
        messagebox.showerror("오류", f"음원 재생 중 오류가 발생했습니다: {e}")
        log_message(f"오류 발생: {e}")


# 스케줄에 프리셋 등록
def schedule_presets():
    log_message("기존 스케줄 삭제 중...")
    schedule.clear()
    for preset in presets:
        file_path = os.path.join(base_path, "audio", preset["audio"])
        log_message(f"스케줄 등록: {preset['time']} - {file_path}")
        schedule.every().day.at(preset["time"]).do(start_audio_thread, file_path)


# 음원 재생을 위한 스레드 시작
def start_audio_thread(file_path):
    thread = threading.Thread(target=play_audio, args=(file_path,))
    thread.start()


# 남은 시간 계산
def get_time_left(target_time):
    current_time = datetime.now()
    target_time = datetime.strptime(target_time, "%H:%M")
    target_time = target_time.replace(year=current_time.year, month=current_time.month, day=current_time.day)
    time_left = target_time - current_time

    if time_left.total_seconds() < 0:
        target_time = target_time + timedelta(days=1)
        time_left = target_time - current_time

    return str(time_left).split(".")[0]


# 스케줄 실행
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


# GUI 시작
def start_gui():
    global presets, presets_list, name_entry, time_entry, log_text
    presets = load_presets()

    # 메인 윈도우 설정
    root = tk.Tk()
    root.title("오디오 타이머")
    root.geometry("850x550")

    # 스타일 설정
    root.configure(bg="#f5f5f5")  # 배경색
    title_font = ("맑은고딕", 16, "bold")
    label_font = ("맑은고딕", 12)

    # 좌측 프레임 (입력 및 리스트)
    left_frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # 타이틀 레이블
    label = tk.Label(left_frame, text="오디오 타이머", font=title_font, bg="#ffffff")
    label.pack(pady=10)

    # 프리셋 리스트 박스
    presets_list = tk.Listbox(left_frame, width=40, height=10, font=label_font)
    presets_list.pack(pady=10)
    display_presets()
    presets_list.bind("<<ListboxSelect>>", select_preset)

    # 프리셋 이름 입력 필드
    name_label = tk.Label(left_frame, text="프리셋 이름", font=label_font, bg="#ffffff")
    name_label.pack(pady=5)
    name_entry = tk.Entry(left_frame, width=30, font=label_font)
    name_entry.pack(pady=5)

    # 시간 입력 필드
    time_label = tk.Label(left_frame, text="시간 (HH:MM)", font=label_font, bg="#ffffff")
    time_label.pack(pady=5)
    time_entry = tk.Entry(left_frame, width=30, font=label_font)
    time_entry.pack(pady=5)

    # 수정 버튼
    modify_button = tk.Button(left_frame, text="수정", font=label_font, width=20, height=2, bg="#4CAF50", fg="white", command=modify_preset)
    modify_button.pack(pady=5)

    # 종료 버튼
    quit_button = tk.Button(left_frame, text="종료", font=label_font, width=20, height=2, bg="#f44336", fg="white", command=root.quit)
    quit_button.pack(pady=5)

    # 우측 프레임 (로그)
    right_frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)
    right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    # 로그 레이블
    log_label = tk.Label(right_frame, text="로그", font=title_font, bg="#ffffff")
    log_label.pack()

    # 로그 출력 창
    log_text = tk.Text(right_frame, height=20, width=50, font=("Courier", 10), bg="#f5f5f5", fg="black", wrap=tk.WORD)
    log_text.pack()
    log_text.insert(tk.END, "=== 로그 시작 ===\n")

    # 남은 시간 레이블 추가
    remaining_label = tk.Label(right_frame, text="남은 시간: 00:00", font=("Arial", 12), bg="#ffffff")
    remaining_label.pack(pady=10)

    # 스케줄 등록
    schedule_presets()

    def update_remaining_time():
        selected_index = presets_list.curselection()
        if selected_index:
            selected_index = selected_index[0]
            time_left = get_time_left(presets[selected_index]["time"])
            remaining_label.config(text=f"남은 시간: {time_left}")
        root.after(1000, update_remaining_time)

    update_remaining_time()

    threading.Thread(target=run_scheduler, daemon=True).start()

    root.mainloop()


# 프로그램 시작
if __name__ == "__main__":
    start_gui()
