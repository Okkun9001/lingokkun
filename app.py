
import tkinter as tk
from tkinter import scrolledtext
import threading
import pexpect
import re

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def clean_ansi(text):
    return ansi_escape.sub('', text)


sdcv_process = None
waiting_for_choice = False


def log(msg):
    """Helper to print debug/debug-like messages in the output box."""
    output_text.config(state='normal')
    output_text.insert(tk.END, f"[DEBUG] {msg}\n")
    output_text.see(tk.END)
    output_text.config(state='disabled')


def append_output(msg, prefix=""):

    msg = clean_ansi(msg)
    output_text.config(state='normal')
    output_text.insert(tk.END, f"{prefix}{msg}")
    output_text.see(tk.END)
    output_text.config(state='disabled')


def query_sdcv():
    global sdcv_process, waiting_for_choice
    word = entry.get().strip()
    if not word:
        return

    append_output(f"{word}\n", prefix="You: ")  # append user input
    entry.delete(0, tk.END)

    def worker():
        global sdcv_process, waiting_for_choice
        log(f"Spawning sdcv for word: {word}")
        try:
            sdcv_process = pexpect.spawn(f'sdcv {word}', encoding='utf-8')
        except Exception as e:
            log(f"Failed to spawn sdcv: {e}")
            return
        patterns = ["Your choice", pexpect.EOF]
        while True:
            try:
                i = sdcv_process.expect(patterns, timeout=0.1)
                output = sdcv_process.before
                if output:
                    append_output(output)
                if i == 0:  # "Your choice" detected
                    append_output(sdcv_process.after)
                    waiting_for_choice = True
                    append_output("\n")
                    log("Waiting for user choice now...")
                elif i == 1:  # EOF
                    log("sdcv process finished")
                    break
            except pexpect.TIMEOUT:
                continue
            except pexpect.EOF:
                log("sdcv process finished")
                break

    threading.Thread(target=worker, daemon=True).start()


def send_choice():
    global sdcv_process, waiting_for_choice
    if not sdcv_process or not waiting_for_choice:
        log("No choice expected, ignoring input")
        return
    choice = entry.get().strip()
    if not choice:
        log("Empty choice, ignoring")
        return
    append_output(f"{choice}\n", prefix="You: ")  # append user choice
    log(f"Sending choice: {choice}")
    sdcv_process.sendline(choice)
    entry.delete(0, tk.END)
    waiting_for_choice = False


# --- Tkinter UI ---
root = tk.Tk()
root.title("Lingokkun")
root.geometry("800x600")

output_text = scrolledtext.ScrolledText(root, font=("Consolas", 12))
output_text.pack(fill='both', expand=True, padx=10, pady=10)
output_text.config(state='disabled')

input_frame = tk.Frame(root)
input_frame.pack(fill='x', padx=10, pady=10)

entry = tk.Entry(input_frame, font=("Arial", 14))
entry.pack(side='left', fill='x', expand=True)
entry.bind("<Return>", lambda event: send_choice()
           if waiting_for_choice else query_sdcv())

search_btn = tk.Button(input_frame, text="Search", command=lambda: send_choice(
) if waiting_for_choice else query_sdcv())
search_btn.pack(side='left', padx=5)

root.mainloop()
