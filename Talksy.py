import tkinter as tk
from tkinter import filedialog
import threading
import random
import time
import re
from datetime import datetime
import math
import speech_recognition as sr
import google.generativeai as genai
import requests

# 🤖 Configure Gemini
genai.configure(api_key="AIzaSyAL9XtlU6DQMHDiyI_zcMclJBzZ0VT8AUs")  # Replace with your real key
model = genai.GenerativeModel("gemini-2.0-flash")

user_name = None

# 🌤 Weather API setup
WEATHER_API_KEY = "6a7cbed363b4f4dde4e70263ab8376c5"  # Replace with your key

def get_weather(city=None):
    if not city:
        city = "Delhi"
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()
        if data.get("cod") != 200:
            return f"Sorry, I couldn't find weather info for '{city}'."
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        return f"🌤 Weather in {city.capitalize()}: {weather}, {temp} °C"
    except:
        return "Weather data is not available right now."

def ask_gemini(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip().replace("*", "")
    except Exception as e:
        return f"⚠ Gemini error: {e}"

def maybe_extract_name(text):
    match = re.search(r"(?:my name is|i am|i'm|this is)\s+([A-Za-z]+)", text, re.I)
    if match:
        name_candidate = match.group(1).capitalize()
        if name_candidate.lower() in ["fine", "good", "okay", "ok", "great", "well"]:
            return None
        return name_candidate
    return None

def get_reply(user_input):
    global user_name
    query = user_input.strip().lower()

    if name := maybe_extract_name(user_input):
        user_name = name
        return f"Nice to meet you, {name}! 😊"

    greetings_pattern = r"\b(?:hi|hello|hey|namaste)\b"
    if re.search(greetings_pattern, query):
        hour = datetime.now().hour
        greet_msg = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening" if hour < 21 else "Good night"
        return f"{greet_msg}, {user_name or 'friend'}! 😊"

    if "how are you" in query:
        return "I'm doing great! How about you? 😊"

    if "your name" in query or "who are you" in query:
        return "I'm Talksy 🤖 — your smart assistant!"

    if "what can you do" in query:
        return "I can chat, calculate, tell weather, and more using Gemini AI!"

    if "who made you" in query:
        return "I'm Talksy created by Sushmita."

    if "date" in query:
        return "📅 Today is " + datetime.now().strftime("%A, %d %B %Y")

    if "time" in query:
        return "⏰ Current time is " + datetime.now().strftime("%I:%M %p")

    if re.search(r"weather(?: in ([a-zA-Z ]+))?", query):
        match = re.search(r"weather in ([a-zA-Z ]+)", query)
        city = match.group(1) if match else "Delhi"
        return get_weather(city.strip())

    if "bye" in query or "exit" in query:
        return "👋 Goodbye! Take care!"

    if query.startswith("calculate"):
        expr = query.replace("calculate", "", 1).strip().replace("^", "**")
        try:
            result = eval(expr, {"__builtins__": {}}, {"sqrt": math.sqrt, "pi": math.pi})
            return f"The answer is {result} 🧮"
        except:
            return "Sorry, I couldn't calculate that."

    if "joke" in query:
        return random.choice([
            "😂 Why don’t scientists trust atoms? Because they make up everything!",
            "😆 Why did the math book look sad? Too many problems!",
            "🤖 I told my computer I needed a break — it said 'No problem, going to sleep!'"
        ])

    return ask_gemini(user_input)

# 🎨 GUI
class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Talksy - Gemini Assistant")
        self.geometry("720x750")
        self.configure(bg="black")

        self.chat_frame = tk.Frame(self, bg="black")
        self.chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.chat_frame, bg="black", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="black")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bottom = tk.Frame(self, bg="#1a1a1a")
        self.bottom.pack(fill=tk.X)

        self.entry = tk.Entry(self.bottom, font=("Segoe UI", 14), bg="white")
        self.entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_message)

        tk.Button(self.bottom, text="📨", command=self.send_message).pack(side=tk.LEFT, padx=5)
        tk.Button(self.bottom, text="🎤", command=self.listen_voice).pack(side=tk.LEFT)
        tk.Button(self.bottom, text="💾", command=self.save_chat).pack(side=tk.LEFT, padx=5)

        self.after(500, lambda: self.add_message("🤖 Talksy", "Hi, I'm Talksy powered by Gemini!\nHow may I help you today?", animated=True))

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input: return
        self.entry.delete(0, tk.END)
        self.add_message("🧑 You", user_input)
        threading.Thread(target=self.generate_reply, args=(user_input,), daemon=True).start()

    def generate_reply(self, user_input):
        bubble = self.add_message("🤖 Talksy", "Processing", animate_dots=True)
        reply = get_reply(user_input)
        for widget in bubble.winfo_children():
            if isinstance(widget, tk.Label):
                setattr(widget, "_stop", True)
        bubble.destroy()
        self.add_message("🤖 Talksy", reply, animated=True)

    def add_message(self, sender, message, animated=False, animate_dots=False):
        bubble = tk.Frame(self.scrollable_frame, bg="#2b2b2b", padx=10, pady=6)
        bubble.pack(anchor="e" if sender.startswith("🧑") else "w", pady=5, padx=10, fill="x")

        tk.Label(bubble, text=sender, font=("Segoe UI", 9, "bold"), fg="white", bg="#2b2b2b").pack(anchor="w")

        msg = tk.Label(bubble, text="", font=("Segoe UI", 12), fg="white", bg="#2b2b2b", wraplength=550, justify="left")
        msg.pack(anchor="w")

        def copy_text():
            self.clipboard_clear()
            self.clipboard_append(msg.cget("text"))
            self.update()

        tk.Button(bubble, text="📋", command=copy_text, font=("Segoe UI", 10), bg="#1a1a1a", fg="white").pack(anchor="e")

        def animate(index=0):
            if index < len(message):
                msg.config(text=message[:index + 1])
                self.after(10, lambda: animate(index + 1))

        def dot_animation(i=0):
            if not hasattr(msg, "_stop"):
                msg._stop = False
            if msg._stop:
                return
            msg.config(text="Processing" + "." * (i % 4))
            msg.after(500, lambda: dot_animation(i + 1))

        if animate_dots:
            dot_animation()
        elif animated:
            animate()
        else:
            msg.config(text=message)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        return bubble

    def listen_voice(self):
        self.listening_bubble = self.add_message("🎤 Voice", "Listening...", animated=False)
        threading.Thread(target=self._record_voice, daemon=True).start()

    def _record_voice(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                query = recognizer.recognize_google(audio)
                if hasattr(self, 'listening_bubble'):
                    self.listening_bubble.destroy()
                self.add_message("🧑 You (voice)", query)
                self.generate_reply(query)
            except:
                if hasattr(self, 'listening_bubble'):
                    self.listening_bubble.destroy()
                self.add_message("🤖 Talksy", "Sorry, I couldn't understand. 😅")

    def save_chat(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if filename:
            text = ""
            for widget in self.scrollable_frame.winfo_children():
                for label in widget.winfo_children():
                    if isinstance(label, tk.Label):
                        text += label.cget("text") + "\n"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)

if __name__ == "__main__":
    ChatApp().mainloop()
