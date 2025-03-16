import sys
import os
import tkinter as tk
from tkinter import messagebox, filedialog
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

    # 설정 값 초기화
    name_entry.delete(0, tk.END)
    time_entry.delete(0, tk.END)
    audio_file_label.config(text=f"선택된 파일: 없음")

    with open(presets_path, "w", encoding="UTF-8") as f:
        json.dump(presets, f, indent=4, ensure_ascii=False)


# GUI 로그 출력 함수
def log_message(message):
    log_text.config(state=tk.NORMAL)  # 수정 가능 상태로 변경
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)  # 스크롤을 아래로 자동 이동
    log_text.config(state=tk.DISABLED)  # 읽기 전용 상태로 되돌리기


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

        audio_file_label.config(text=f"선택된 파일: {selected_preset["audio"]}")

        log_message(f"프리셋 선택됨: {selected_preset["name"]} - {selected_preset["time"]}")

    except IndexError:
        name_entry.delete(0, tk.END)
        time_entry.delete(0, tk.END)
        audio_file_label.config(text=f"선택된 파일: 없음")
        pass


# 오디오 파일 선택
def select_audio_file():
    file_path = filedialog.askopenfilename(
        title="파일 선택",
        filetypes=[("MP3 파일", "*.mp3"), ("WAV 파일", "*.wav")],
    )
    if file_path:
        log_message(f"선택된 오디오 파일: {file_path}")
        audio_file_label.config(text=f"선택된 파일: {file_path}")
        return file_path
    else:
        audio_file_label.config(text="선택된 파일: 없음")

    return None


# 프리셋 추가 함수
def add_preset():
    global presets

    new_name = name_entry.get()
    new_time = time_entry.get()
    new_audio = audio_file_label.cget("text").replace("선택된 파일: ", "")

    if not new_name or not new_time or new_audio == "없음":
        messagebox.showwarning("입력 오류", "모든 항목을 입력하고 오디오 파일을 선택하세요.")
        return

    new_preset = {"name": new_name, "time": new_time, "audio": new_audio}
    presets.append(new_preset)
    save_presets(presets)
    display_presets()
    schedule_presets()

    log_message(f"프리셋 추가됨: {new_name} - {new_time}")
    messagebox.showinfo("추가 완료", "프리셋이 추가되었습니다.")


# 프리셋 수정 함수
def modify_preset():
    global presets

    try:
        selected_index = presets_list.curselection()[0]
        new_name = name_entry.get()
        new_time = time_entry.get()
        new_audio = audio_file_label.cget("text").replace("선택된 파일: ", "")

        if not new_name or not new_time or not new_audio:
            messagebox.showwarning("입력 오류", "모든 항목을 입력하고 오디오 파일을 선택하세요.")
            return

        presets[selected_index]["name"] = new_name
        presets[selected_index]["time"] = new_time
        presets[selected_index]["audio"] = new_audio

        save_presets(presets)
        display_presets()
        schedule_presets()

        log_message(f"프리셋 수정됨: {new_name} - {new_time}")
        messagebox.showinfo("수정 완료", "프리셋이 수정되었습니다.")
    except IndexError:
        messagebox.showwarning("선택 오류", "수정할 프리셋을 선택해주세요.")


# 프리셋 삭제 함수
def delete_preset():
    global presets

    try:
        selected_index = presets_list.curselection()[0]
        preset_to_delete = presets.pop(selected_index)
        save_presets(presets)
        display_presets()
        schedule_presets()

        log_message(f"프리셋 삭제됨: {preset_to_delete['name']}")
        messagebox.showinfo("삭제 완료", f"{preset_to_delete['name']} 프리셋이 삭제되었습니다.")
    except IndexError:
        messagebox.showwarning("선택 오류", "삭제할 프리셋을 선택해주세요.")


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


# 음원 재생을 위한 스레드 시작
def start_audio_thread(file_path):
    thread = threading.Thread(target=play_audio, args=(file_path,))
    thread.start()


# 스케줄에 프리셋 등록
def schedule_presets():
    log_message("기존 스케줄 삭제 중...")
    schedule.clear()

    log_message(f"스케줄 등록 중...: ")
    for preset in presets:
        log_message(f"{preset["name"]}: {preset["time"]} - {preset["audio"]}")
        schedule.every().day.at(preset["time"]).do(start_audio_thread, preset["audio"])


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


# GUI 함수
def start_gui():
    global presets, presets_list, name_entry, time_entry, log_text, audio_file_label
    presets = load_presets()

    # 메인 윈도우 설정
    root = tk.Tk()
    root.title("오디오 타이머")
    root.geometry("860x600")

    # 스타일 설정
    root.configure(bg="#f5f5f5")  # 배경색
    title_font = ("맑은고딕", 16, "bold")
    label_font = ("맑은고딕", 12)

    # 좌측 프레임 (입력 및 리스트)
    left_frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # 타이틀 레이블
    label = tk.Label(left_frame, text="오디오 타이머", font=title_font, bg="#ffffff")
    label.grid(row=0, column=0, pady=10)

    # 프리셋 리스트 박스
    presets_list = tk.Listbox(left_frame, width=40, height=10, font=label_font)
    presets_list.grid(row=1, column=0, pady=10)
    display_presets()
    presets_list.bind("<<ListboxSelect>>", select_preset)

    # 프리셋 이름 입력 필드
    name_label = tk.Label(left_frame, text="프리셋 이름", font=label_font, bg="#ffffff")
    name_label.grid(row=2, column=0, pady=5)
    name_entry = tk.Entry(left_frame, width=30, font=label_font)
    name_entry.grid(row=3, column=0, pady=5)

    # 시간 입력 필드
    time_label = tk.Label(left_frame, text="시간 (HH:MM)", font=label_font, bg="#ffffff")
    time_label.grid(row=4, column=0, pady=5)
    time_entry = tk.Entry(left_frame, width=30, font=label_font)
    time_entry.grid(row=5, column=0, pady=5)

    # 오디오 설정을 가로로 배치할 프레임 추가
    audio_frame = tk.Frame(left_frame, bg="#ffffff")
    audio_frame.grid(row=6, column=0, pady=10)

    # 오디오 파일 선택 레이블
    audio_file_label = tk.Label(audio_frame, text="선택된 파일: 없음", font=label_font, bg="#ffffff", wraplength=250)
    audio_file_label.grid(row=0, column=0, pady=5, sticky="w")

    # 오디오 파일 선택 버튼
    audio_file_button = tk.Button(
        audio_frame,
        text="파일 선택",
        font=label_font,
        width=8,
        height=1,
        bg="#2196F3",
        fg="white",
        command=select_audio_file,
    )
    audio_file_button.grid(row=0, column=1, pady=5, padx=10)

    # 버튼들을 가로로 배치할 프레임 추가
    button_frame = tk.Frame(left_frame, bg="#ffffff")
    button_frame.grid(row=7, column=0, pady=10)

    # 추가 버튼
    add_button = tk.Button(
        button_frame,
        text="추가",
        font=label_font,
        width=5,
        height=1,
        bg="#4CAF50",
        fg="white",
        command=add_preset,
    )
    add_button.grid(row=0, column=0, padx=5)

    # 수정 버튼
    modify_button = tk.Button(
        button_frame,
        text="수정",
        font=label_font,
        width=5,
        height=1,
        bg="#4CAF50",
        fg="white",
        command=modify_preset,
    )
    modify_button.grid(row=0, column=1, padx=5)

    # 삭제 버튼
    delete_button = tk.Button(
        button_frame,
        text="삭제",
        font=label_font,
        width=5,
        height=1,
        bg="#f44336",
        fg="white",
        command=delete_preset,
    )
    delete_button.grid(row=0, column=2, padx=5)

    # 종료 버튼
    quit_button = tk.Button(
        left_frame,
        text="종료",
        font=label_font,
        width=20,
        height=1,
        bg="#f44336",
        fg="white",
        command=root.quit,
    )
    quit_button.grid(row=9, column=0, pady=5)

    # 우측 프레임 (로그)
    right_frame = tk.Frame(root, bg="#ffffff", padx=20, pady=20)
    right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    # 로그 레이블
    log_label = tk.Label(right_frame, text="로그", font=title_font, bg="#ffffff")
    log_label.pack()

    # 로그 출력 창
    log_text = tk.Text(right_frame, height=20, width=60, font=("Courier", 8), bg="#f5f5f5", fg="black", wrap=tk.WORD)
    log_text.pack()
    log_text.insert(tk.END, "=== 로그 시작 ===\n")
    log_text.config(state=tk.DISABLED)

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
