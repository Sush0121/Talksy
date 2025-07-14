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

# Configure Gemini
genai.configure(api_key="AIzaSyAL9XtlU6DQMHDiyI_zcMclJBzZ0VT8AUs")
model = genai.GenerativeModel("gemini-2.0-flash")

user_name = None
WEATHER_API_KEY = "6a7cbed363b4f4dde4e70263ab8376c5"  # Replace with your key

def get_weather(city=None):
    if not city:
        city = "Delhi"
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        print(f"Requesting weather for: {city}")  # ✅ DEBUG
        print(f"API URL: {url}")  # ✅ DEBUG
        response = requests.get(url)
        data = response.json()
        print(f"Response JSON: {data}")  # ✅ DEBUG

        if data.get("cod") != 200:
            return f"❌ Sorry, I couldn't find weather info for '{city}'."
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        return f"🌤 Weather in {city.capitalize()}: {weather}, {temp} °C"
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # 🔍 Full error trace in terminal
        return f"⚠ Error fetching weather: {e}"


def ask_gemini(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip().replace("**", "")
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
    if re.fullmatch(greetings_pattern, query, re.IGNORECASE):
        hour = datetime.now().hour
        greet_msg = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening" if hour < 21 else "Good night"
        return random.choice([
            f"{greet_msg}, {user_name or 'friend'}! 😊 How can I help you?",
            f"hey {user_name or 'mate'}, How are you its been a while since last time!",
            f"{greet_msg}, How would you like me to assist you today?",
            f"Hey, how are you?"
        ])
    weather_match = re.search(r"weather in ([a-zA-Z ]+)", query)
    if "weather" in query:
        if weather_match:
           city = weather_match.group(1).strip()
           return get_weather(city)
        else:
            return get_weather()  # default to Delhi



    if re.search(r"\b(?:bye|exit|quit|see you)\b", query):
        return "🌙 Good night! Take care and sleep well! 🛌" if datetime.now().hour >= 21 or datetime.now().hour < 5 else "👋 Goodbye! Have a great day!"

    if "how are you" in query:
        return "I'm doing great! How about you? 😊"
    if "i'm fine" in query or "i am fine" in query:
        return "Glad to hear that! 💖"
    if "your name" in query or "who are you" in query:
        return "I'm Talksy 🤖 — your smart assistant!"
    if "what can you do" in query or "what do you do" in query:
        return "I can chat, answer questions, tell jokes, motivate, and more using Gemini AI! ✨"
    if "who made you" in query or "who created you" in query:
        return "I'm Talksy created by Sushmita"
    if "date" in query:
        return "📅 Today is " + datetime.now().strftime("%A, %d %B %Y")
    if "time" in query:
        return "⏰ Current time is " + datetime.now().strftime("%I:%M %p")

    if query.startswith("calculate"):
        expr = query.replace("calculate", "", 1).strip().replace("^", "**")
        try:
            result = eval(expr, {"__builtins__": {}}, {"sqrt": math.sqrt, "pi": math.pi, "e": math.e})
            return f"The answer is {result} 🧒"
        except:
            return "Sorry, I couldn't calculate that. ❌"

    if "joke" in query:
        return random.choice([
            "😂 Why don’t scientists trust atoms? Because they make up everything!",
            "😆 Why did the math book look sad? Too many problems!",
            "🤖 I told my computer I needed a break — it said 'No problem, going to sleep!'"
        ])

    if "fact" in user_input:
        return random.choice([
            "Honey never spoils. Archaeologists have found 3,000 year old pots of honey that are still edible!",
            "Octopuses have three hearts ❤️❤️❤️.",
            "Bananas are berries, but strawberries aren’t!",
            "A day on Venus is longer than a year on Venus."
        ])

    if "motivate" in query or "motivation" in query:
        return random.choice([
            "💪 You’ve got this!", "🌟 Every day is a fresh start.", "🔥 Believe in yourself!"
        ])

    if "prime minister of india" in query:
        return "🇮🇳 The current Prime Minister of India is Narendra Modi (since 2014)."
    if "president of india" in query:
        return "🇮🇳 The current President of India is Droupadi Murmu (since 2022)."
    if "president of usa" in query:
        return "🇺🇸 The current President of the USA is Joe Biden (since 2021)."

    return ask_gemini(user_input)

class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🤖 Talksy - Gemini Powered")
        self.geometry("700x770")
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

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.bottom = tk.Frame(self, bg="#1a1a1a")
        self.bottom.pack(fill=tk.X, padx=5, pady=5)

        self.entry = tk.Entry(self.bottom, font=("Segoe UI", 14), bg="white")
        self.entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(self.bottom, text="📨", font=("Segoe UI", 12), command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5)

        self.voice_btn = tk.Button(self.bottom, text="🎤", font=("Segoe UI", 14), command=self.listen_voice)
        self.voice_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = tk.Button(self.bottom, text="💾", font=("Segoe UI", 12), command=self.save_chat)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.after(500, lambda: self.add_message("🤖 Talksy", "Hi, I am Talksy powered by Gemini! ✨\nHow may I assist you today?", animated=True))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, tk.END)
        display_name = f"🧑 {user_name}" if user_name else "🧑 You"
        self.add_message(display_name, user_input)
        threading.Thread(target=self.generate_reply, args=(user_input,), daemon=True).start()

    def generate_reply(self, user_input):
        typing_bubble = self.add_message("🤖 Talksy", "Processing", animate_dots=True)
        reply = get_reply(user_input)
        for widget in typing_bubble.winfo_children():
            if isinstance(widget, tk.Label):
                setattr(widget, "_stop", True)
        typing_bubble.destroy()
        self.add_message("🤖 Talksy", reply, animated=True)

    def add_message(self, sender, message, animated=False, animate_dots=False):
        bubble = tk.Frame(self.scrollable_frame, bg="#2b2b2b", padx=10, pady=6, bd=1, relief="solid")
        bubble.pack(anchor="e" if sender.startswith("🧑") else "w", pady=5, padx=10, fill="x")

        label = tk.Label(bubble, text=sender, font=("Segoe UI", 9, "bold"), fg="white", bg="#2b2b2b")
        label.pack(anchor="w")

        msg = tk.Label(bubble, text="", font=("Segoe UI", 12), fg="white", bg="#2b2b2b", wraplength=550, justify="left")
        msg.pack(anchor="w")

        def copy_text():
            self.clipboard_clear()
            self.clipboard_append(msg.cget("text"))
            self.update()

        copy_btn = tk.Button(bubble, text="📋", font=("Segoe UI", 10), command=copy_text, bg="#1a1a1a", fg="white", relief="flat")
        copy_btn.pack(anchor="e", pady=(2, 0))

        def dot_animation(i=0):
            if not hasattr(msg, "_stop"):
                msg._stop = False
            if msg._stop:
                return
            dots = '.' * (i % 4)
            msg.config(text=f"Processing{dots}")
            msg.after(500, lambda: dot_animation(i + 1))

        def animate(index=0):
            if index < len(message):
                msg.config(text=message[:index + 1])
                self.after(10, lambda: animate(index + 1))

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
                self.add_message(f"🧑 {user_name or 'You (voice)'}", query)
                self.generate_reply(query)
            except Exception:
                if hasattr(self, 'listening_bubble'):
                    self.listening_bubble.destroy()
                self.add_message("🤖 Talksy", "Sorry, I couldn't understand. 😅")

    def save_chat(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
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