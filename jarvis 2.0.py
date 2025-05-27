import sys
import os
import json
import time
import threading
import asyncio
from datetime import datetime, timedelta
import calendar
import random
import webbrowser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import psutil
import requests
from typing import Dict, List, Optional, Any
import logging

# Third-party imports
try:
    import speech_recognition as sr
    import pyttsx3
    import wikipedia
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    import geocoder
    import wolframalpha
    import openai
    from googletrans import Translator
    import schedule
    import sqlite3
    from cryptography.fernet import Fernet
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install speechrecognition pyttsx3 wikipedia pyautogui opencv-python pillow geocoder wolframalpha openai googletrans schedule cryptography")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)

class AdvancedVoiceAssistant:
    def __init__(self):
        self.name = "JARVIS Pro"
        self.version = "2.0"
        self.user_name = "Sir"
        self.listening = False
        self.conversation_history = []
        self.tasks = []
        self.reminders = []
        self.user_preferences = self.load_preferences()
        
        # Initialize components
        self.init_speech_engine()
        self.init_recognizer()
        self.init_database()
        self.init_apis()
        
        # Feature flags
        self.features = {
            'weather': True,
            'news': True,
            'email': True,
            'calendar': True,
            'smart_home': True,
            'learning': True,
            'security': True
        }
        
        print(f"🤖 {self.name} v{self.version} initialized successfully!")
        logging.info(f"{self.name} v{self.version} started")

    def init_speech_engine(self):
        """Initialize text-to-speech engine with advanced settings"""
        try:
            self.engine = pyttsx3.init('sapi5')
            voices = self.engine.getProperty('voices')
            
            # Set voice preference
            voice_id = self.user_preferences.get('voice_id', 1)
            if voices and len(voices) > voice_id:
                self.engine.setProperty('voice', voices[voice_id].id)
            
            # Set speech properties
            self.engine.setProperty('rate', self.user_preferences.get('speech_rate', 180))
            self.engine.setProperty('volume', self.user_preferences.get('volume', 0.9))
            
            logging.info("Speech engine initialized")
        except Exception as e:
            logging.error(f"Speech engine initialization failed: {e}")
            self.engine = None

    def init_recognizer(self):
        """Initialize speech recognition with advanced settings"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Set recognition parameters
        self.recognizer.energy_threshold = self.user_preferences.get('energy_threshold', 300)
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        logging.info("Speech recognizer initialized")

    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            self.db_path = 'jarvis_data.db'
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # Create tables
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    user_input TEXT,
                    assistant_response TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT,
                    priority INTEGER,
                    due_date TEXT,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reminder TEXT,
                    reminder_time TEXT,
                    created_at TEXT,
                    triggered BOOLEAN DEFAULT FALSE
                )
            ''')
            
            self.conn.commit()
            logging.info("Database initialized")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")

    def init_apis(self):
        """Initialize external APIs"""
        self.api_keys = {
            'weather': 'your_openweather_api_key',
            'news': 'your_news_api_key',
            'wolfram': 'your_wolfram_api_key',
            'openai': 'your_openai_api_key'
        }
        
        self.translator = Translator()
        
        # Initialize Wolfram Alpha client
        try:
            if self.api_keys['wolfram'] != 'your_wolfram_api_key':
                self.wolfram_client = wolframalpha.Client(self.api_keys['wolfram'])
            else:
                self.wolfram_client = None
        except:
            self.wolfram_client = None

    def load_preferences(self) -> Dict:
        """Load user preferences from file"""
        try:
            if os.path.exists('preferences.json'):
                with open('preferences.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load preferences: {e}")
        
        return {
            'voice_id': 1,
            'speech_rate': 180,
            'volume': 0.9,
            'energy_threshold': 300,
            'wake_word': 'jarvis',
            'language': 'en-US'
        }

    def save_preferences(self):
        """Save user preferences to file"""
        try:
            with open('preferences.json', 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save preferences: {e}")

    def speak(self, text: str, interrupt: bool = False):
        """Advanced text-to-speech with emotion and context"""
        if not self.engine:
            print(f"🤖 {text}")
            return
        
        try:
            # Add personality to responses
            if "error" in text.lower() or "sorry" in text.lower():
                self.engine.setProperty('rate', 160)
            elif "!" in text or "exciting" in text.lower():
                self.engine.setProperty('rate', 200)
            else:
                self.engine.setProperty('rate', self.user_preferences.get('speech_rate', 180))
            
            print(f"🤖 {text}")
            self.engine.say(text)
            self.engine.runAndWait()
            
            # Log conversation
            self.log_conversation("JARVIS", text)
            
        except Exception as e:
            logging.error(f"Speech synthesis error: {e}")
            print(f"🤖 {text}")

    def listen(self, timeout: int = 5) -> Optional[str]:
        """Advanced speech recognition with noise filtering"""
        try:
            with self.microphone as source:
                print("🎤 Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            print("🔍 Processing speech...")
            
            # Try multiple recognition services
            try:
                query = self.recognizer.recognize_google(
                    audio, 
                    language=self.user_preferences.get('language', 'en-US')
                )
                print(f"👤 User: {query}")
                self.log_conversation("User", query)
                return query.lower()
            except sr.UnknownValueError:
                # Try with different language if primary fails
                try:
                    query = self.recognizer.recognize_google(audio, language='en-US')
                    print(f"👤 User: {query}")
                    self.log_conversation("User", query)
                    return query.lower()
                except:
                    pass
        
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            logging.error(f"Speech recognition error: {e}")
        
        return None

    def log_conversation(self, speaker: str, message: str):
        """Log conversation to database and memory"""
        timestamp = datetime.now().isoformat()
        
        try:
            if speaker == "User":
                self.cursor.execute(
                    "INSERT INTO conversations (timestamp, user_input, assistant_response) VALUES (?, ?, ?)",
                    (timestamp, message, "")
                )
            else:
                # Update the last entry with assistant response
                self.cursor.execute(
                    "UPDATE conversations SET assistant_response = ? WHERE id = (SELECT MAX(id) FROM conversations)",
                    (message,)
                )
            self.conn.commit()
        except Exception as e:
            logging.error(f"Database logging error: {e}")
        
        # Keep in-memory history
        self.conversation_history.append({
            'timestamp': timestamp,
            'speaker': speaker,
            'message': message
        })
        
        # Limit memory usage
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-50:]

    def wish_user(self):
        """Personalized greeting based on time and context"""
        hour = datetime.now().hour
        
        greetings = {
            (5, 12): ["Good morning", "Morning", "Rise and shine"],
            (12, 17): ["Good afternoon", "Afternoon", "Hope you're having a great day"],
            (17, 21): ["Good evening", "Evening", "Hope your day went well"],
            (21, 24): ["Good night", "It's getting late", "Evening"],
            (0, 5): ["You're up late", "Burning the midnight oil", "Late night session"]
        }
        
        greeting = "Hello"
        for time_range, greet_list in greetings.items():
            if time_range[0] <= hour < time_range[1]:
                greeting = random.choice(greet_list)
                break
        
        # Get user's name if available
        user_name = self.user_preferences.get('user_name', 'Sir')
        
        welcome_msg = f"{greeting}, {user_name}! I'm {self.name}, your advanced AI assistant. How can I help you today?"
        self.speak(welcome_msg)

    def get_weather(self, city: str = None) -> str:
        """Get weather information"""
        try:
            if not city:
                # Get location automatically
                g = geocoder.ip('me')
                city = g.city or "London"
            
            api_key = self.api_keys.get('weather')
            if api_key == 'your_openweather_api_key':
                return "Weather service not configured. Please add your OpenWeather API key."
            
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                humidity = data['main']['humidity']
                
                return f"Weather in {city}: {temp}°C, {desc}. Humidity: {humidity}%"
            else:
                return f"Couldn't get weather for {city}"
                
        except Exception as e:
            logging.error(f"Weather error: {e}")
            return "Weather service temporarily unavailable"

    def get_news(self, category: str = "general") -> str:
        """Get latest news"""
        try:
            api_key = self.api_keys.get('news')
            if api_key == 'your_news_api_key':
                return "News service not configured. Please add your News API key."
            
            url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200 and data['articles']:
                headlines = []
                for article in data['articles'][:5]:
                    headlines.append(article['title'])
                
                return "Here are the top headlines: " + ". ".join(headlines)
            else:
                return "Couldn't fetch news at the moment"
                
        except Exception as e:
            logging.error(f"News error: {e}")
            return "News service temporarily unavailable"

    def calculate_advanced(self, query: str) -> str:
        """Advanced calculations using Wolfram Alpha"""
        try:
            if not self.wolfram_client:
                # Fallback to basic eval for simple math
                try:
                    # Extract mathematical expression
                    import re
                    math_expr = re.search(r'[\d+\-*/().\s]+', query)
                    if math_expr:
                        result = eval(math_expr.group())
                        return f"The result is {result}"
                except:
                    pass
                return "Advanced calculation service not available"
            
            res = self.wolfram_client.query(query)
            answer = next(res.results).text
            return f"According to Wolfram Alpha: {answer}"
            
        except Exception as e:
            logging.error(f"Calculation error: {e}")
            return "I couldn't calculate that"

    def manage_tasks(self, action: str, task: str = "", priority: int = 1) -> str:
        """Advanced task management"""
        try:
            if action == "add":
                due_date = (datetime.now() + timedelta(days=1)).isoformat()
                self.cursor.execute(
                    "INSERT INTO tasks (task, priority, due_date, created_at) VALUES (?, ?, ?, ?)",
                    (task, priority, due_date, datetime.now().isoformat())
                )
                self.conn.commit()
                return f"Task added: {task}"
            
            elif action == "list":
                self.cursor.execute("SELECT task, priority FROM tasks WHERE completed = FALSE ORDER BY priority DESC")
                tasks = self.cursor.fetchall()
                if tasks:
                    task_list = ", ".join([f"{task[0]} (Priority: {task[1]})" for task in tasks])
                    return f"Your pending tasks: {task_list}"
                else:
                    return "No pending tasks"
            
            elif action == "complete":
                self.cursor.execute("UPDATE tasks SET completed = TRUE WHERE task LIKE ? AND completed = FALSE", (f"%{task}%",))
                if self.cursor.rowcount > 0:
                    self.conn.commit()
                    return f"Task completed: {task}"
                else:
                    return "Task not found"
        
        except Exception as e:
            logging.error(f"Task management error: {e}")
            return "Task management error occurred"

    def set_reminder(self, reminder_text: str, reminder_time: str) -> str:
        """Set reminders with natural language processing"""
        try:
            # Simple time parsing - can be enhanced with NLP libraries
            now = datetime.now()
            
            if "in" in reminder_time and "minutes" in reminder_time:
                minutes = int(reminder_time.split()[1])
                reminder_datetime = now + timedelta(minutes=minutes)
            elif "in" in reminder_time and "hours" in reminder_time:
                hours = int(reminder_time.split()[1])
                reminder_datetime = now + timedelta(hours=hours)
            else:
                # Default to 1 hour
                reminder_datetime = now + timedelta(hours=1)
            
            self.cursor.execute(
                "INSERT INTO reminders (reminder, reminder_time, created_at) VALUES (?, ?, ?)",
                (reminder_text, reminder_datetime.isoformat(), now.isoformat())
            )
            self.conn.commit()
            
            return f"Reminder set: {reminder_text} at {reminder_datetime.strftime('%Y-%m-%d %H:%M')}"
        
        except Exception as e:
            logging.error(f"Reminder error: {e}")
            return "Couldn't set reminder"

    def check_reminders(self):
        """Check and trigger due reminders"""
        try:
            now = datetime.now().isoformat()
            self.cursor.execute(
                "SELECT id, reminder FROM reminders WHERE reminder_time <= ? AND triggered = FALSE",
                (now,)
            )
            due_reminders = self.cursor.fetchall()
            
            for reminder_id, reminder_text in due_reminders:
                self.speak(f"Reminder: {reminder_text}")
                self.cursor.execute("UPDATE reminders SET triggered = TRUE WHERE id = ?", (reminder_id,))
            
            if due_reminders:
                self.conn.commit()
        
        except Exception as e:
            logging.error(f"Reminder check error: {e}")

    def smart_home_control(self, device: str, action: str) -> str:
        """Smart home device control simulation"""
        devices = {
            'lights': ['on', 'off', 'dim', 'brighten'],
            'thermostat': ['increase', 'decrease', 'set'],
            'music': ['play', 'pause', 'stop', 'next', 'previous'],
            'security': ['arm', 'disarm', 'status']
        }
        
        if device in devices and action in devices[device]:
            return f"Smart home: {device} {action} command executed"
        else:
            return f"Smart home device '{device}' not found or action '{action}' not supported"

    def take_screenshot(self) -> str:
        """Take and save screenshot"""
        try:
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(filename)
            return f"Screenshot saved as {filename}"
        except Exception as e:
            logging.error(f"Screenshot error: {e}")
            return "Couldn't take screenshot"

    def translate_text(self, text: str, target_lang: str = 'es') -> str:
        """Translate text to different languages"""
        try:
            translation = self.translator.translate(text, dest=target_lang)
            return f"Translation ({target_lang}): {translation.text}"
        except Exception as e:
            logging.error(f"Translation error: {e}")
            return "Translation service unavailable"

    def system_info(self) -> str:
        """Get system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return f"System Status - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%"
        except Exception as e:
            logging.error(f"System info error: {e}")
            return "Couldn't get system information"

    def process_command(self, query: str) -> str:
        """Advanced command processing with AI-like understanding"""
        query = query.lower().strip()
        
        # Check reminders first
        self.check_reminders()
        
        # Wikipedia search
        if 'wikipedia' in query:
            try:
                topic = query.replace('wikipedia', '').replace('search', '').strip()
                if topic:
                    self.speak('Searching Wikipedia...')
                    result = wikipedia.summary(topic, sentences=2)
                    return f"According to Wikipedia: {result}"
                else:
                    return "What would you like me to search on Wikipedia?"
            except wikipedia.exceptions.DisambiguationError as e:
                return f"Multiple results found. Please be more specific. Options: {', '.join(e.options[:3])}"
            except Exception as e:
                return "Wikipedia search failed"
        
        # Weather
        elif any(word in query for word in ['weather', 'temperature', 'forecast']):
            city = None
            if ' in ' in query:
                city = query.split(' in ')[-1].strip()
            return self.get_weather(city)
        
        # News
        elif 'news' in query:
            category = "general"
            if 'tech' in query: category = "technology"
            elif 'sport' in query: category = "sports"
            elif 'business' in query: category = "business"
            return self.get_news(category)
        
        # Calculations
        elif any(word in query for word in ['calculate', 'compute', 'math', '+', '-', '*', '/', '=']):
            return self.calculate_advanced(query)
        
        # Time
        elif 'time' in query:
            current_time = datetime.now().strftime("%I:%M %p")
            return f"The current time is {current_time}"
        
        # Date
        elif 'date' in query:
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {current_date}"
        
        # Task management
        elif 'task' in query or 'todo' in query:
            if 'add' in query or 'create' in query:
                task_text = query.replace('add task', '').replace('create task', '').strip()
                return self.manage_tasks("add", task_text)
            elif 'list' in query or 'show' in query:
                return self.manage_tasks("list")
            elif 'complete' in query or 'done' in query:
                task_text = query.replace('complete task', '').replace('mark done', '').strip()
                return self.manage_tasks("complete", task_text)
        
        # Reminders
        elif 'remind' in query:
            if 'in' in query:
                parts = query.split(' in ')
                reminder_text = parts[0].replace('remind me to', '').replace('remind me', '').strip()
                time_part = parts[1]
                return self.set_reminder(reminder_text, f"in {time_part}")
            else:
                return "Please specify when you'd like to be reminded"
        
        # Web browsing
        elif 'open' in query:
            sites = {
                'youtube': 'https://youtube.com',
                'google': 'https://google.com',
                'github': 'https://github.com',
                'stackoverflow': 'https://stackoverflow.com',
                'reddit': 'https://reddit.com',
                'twitter': 'https://twitter.com',
                'facebook': 'https://facebook.com',
                'instagram': 'https://instagram.com',
                'whatsapp': 'https://web.whatsapp.com'
            }
            
            for site, url in sites.items():
                if site in query:
                    webbrowser.open(url)
                    return f"Opening {site}"
            
            # Try to extract URL or site name
            words = query.split()
            if 'open' in words:
                idx = words.index('open')
                if idx + 1 < len(words):
                    site = words[idx + 1]
                    webbrowser.open(f"https://{site}.com")
                    return f"Opening {site}"
        
        # Applications
        elif 'open code' in query or 'visual studio' in query:
            try:
                subprocess.Popen(['code'])
                return "Opening Visual Studio Code"
            except:
                return "Visual Studio Code not found"
        
        elif 'open notepad' in query:
            try:
                subprocess.Popen(['notepad.exe'])
                return "Opening Notepad"
            except:
                return "Notepad not found"
        
        # Smart home
        elif any(word in query for word in ['lights', 'thermostat', 'music', 'security']):
            for device in ['lights', 'thermostat', 'music', 'security']:
                if device in query:
                    actions = ['on', 'off', 'play', 'pause', 'arm', 'disarm', 'increase', 'decrease']
                    for action in actions:
                        if action in query:
                            return self.smart_home_control(device, action)
                    return f"What would you like me to do with the {device}?"
        
        # Screenshot
        elif 'screenshot' in query or 'capture screen' in query:
            return self.take_screenshot()
        
        # Translation
        elif 'translate' in query:
            if ' to ' in query:
                parts = query.split(' to ')
                text_to_translate = parts[0].replace('translate', '').strip()
                target_lang = parts[1].strip()
                
                lang_codes = {'spanish': 'es', 'french': 'fr', 'german': 'de', 'italian': 'it'}
                target_code = lang_codes.get(target_lang, target_lang)
                
                return self.translate_text(text_to_translate, target_code)
            else:
                return "Please specify what to translate and to which language"
        
        # System information
        elif 'system' in query and 'info' in query:
            return self.system_info()
        
        # Email
        elif 'email' in query or 'send mail' in query:
            return "Email functionality requires configuration. Please set up your email credentials."
        
        # Jokes
        elif 'joke' in query:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                "Why don't programmers like nature? It has too many bugs!",
                "I'm reading a book about anti-gravity. It's impossible to put down!"
            ]
            return random.choice(jokes)
        
        # Exit commands
        elif any(word in query for word in ['exit', 'quit', 'goodbye', 'bye', 'stop']):
            return "QUIT"
        
        # Default response with learning capability
        else:
            responses = [
                "I'm not sure I understand. Could you rephrase that?",
                "That's interesting! I'm still learning about that topic.",
                "I didn't catch that. Could you try asking differently?",
                "I'm working on understanding more commands like that.",
                "Could you be more specific about what you'd like me to do?"
            ]
            
            # Add to learning database for future improvements
            try:
                timestamp = datetime.now().isoformat()
                self.cursor.execute(
                    "INSERT INTO conversations (timestamp, user_input, assistant_response) VALUES (?, ?, ?)",
                    (timestamp, query, "UNKNOWN_COMMAND")
                )
                self.conn.commit()
            except:
                pass
            
            return random.choice(responses)

    def run(self):
        """Main execution loop with advanced features"""
        print(f"\n🚀 Starting {self.name} v{self.version}")
        print("=" * 50)
        
        self.wish_user()
        
        # Background reminder checker
        def reminder_thread():
            while True:
                self.check_reminders()
                time.sleep(60)  # Check every minute
        
        threading.Thread(target=reminder_thread, daemon=True).start()
        
        consecutive_failures = 0
        max_failures = 3
        
        while True:
            try:
                query = self.listen(timeout=10)
                
                if query is None:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        self.speak("I haven't heard anything for a while. Say 'hello' to wake me up.")
                        consecutive_failures = 0
                    continue
                
                consecutive_failures = 0
                
                # Process wake word
                wake_word = self.user_preferences.get('wake_word', 'jarvis')
                if wake_word in query:
                    query = query.replace(wake_word, '').strip()
                    if not query:
                        self.speak("Yes, how can I help you?")
                        continue
                
                # Process command
                response = self.process_command(query)
                
                if response == "QUIT":
                    self.speak("Goodbye! Have a great day!")
                    break
                
                self.speak(response)
                
            except KeyboardInterrupt:
                self.speak("Shutting down gracefully. Goodbye!")
                break
            except Exception as e:
                logging.error(f"Main loop error: {e}")
                self.speak("I encountered an error, but I'm still here to help.")
        
        # Cleanup
        try:
            self.conn.close()
            self.save_preferences()
        except:
            pass
        
        print(f"\n{self.name} shutdown complete.")

def main():
    """Main entry point"""
    try:
        assistant = AdvancedVoiceAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()