import os
import sys
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox
import pygame
import threading
import traceback
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import requests

# Load environment variables
load_dotenv()

# Output directory and preferences file
OUTPUT_DIR = "narrations"
os.makedirs(OUTPUT_DIR, exist_ok=True)
PREFS_FILE = "preferences.json"

# Debug function to help troubleshoot
def log_error(message, exception=None):
    """Log error to file for debugging"""
    with open("error_log.txt", "a") as f:
        f.write(f"{message}\n")
        if exception:
            f.write(f"{str(exception)}\n")
            f.write(traceback.format_exc())
            f.write("\n---\n")

# xAI API client setup
class xAIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, messages, model="grok-beta"):
        """Create a chat completion using the xAI API"""
        try:
            endpoint = f"{self.base_url}/chat/completions"
            payload = {
                "model": model,
                "messages": messages
            }
            
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            return response.json()
        except Exception as e:
            log_error(f"xAI API error: {str(e)}", e)
            raise

def load_preferences():
    default_prefs = {
        "voice_id": "",
        "narration_style": "classic_gothic",
        "output_format": "mp3_44100_128",
        "tone": "mysterious",
        "pitch": "low"
    }
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, 'r') as f:
                saved_prefs = json.load(f)
            default_prefs.update(saved_prefs)
        except Exception as e:
            log_error(f"Error loading preferences: {str(e)}", e)
    return default_prefs

def save_preferences(prefs):
    try:
        with open(PREFS_FILE, 'w') as f:
            json.dump(prefs, f)
    except Exception as e:
        log_error(f"Error saving preferences: {str(e)}", e)

def get_available_voices(api_key):
    try:
        client = ElevenLabs(api_key=api_key)
        voices = client.voices.get_all()
        return {voice.name: voice.voice_id for voice in voices.voices}
    except Exception as e:
        log_error(f"Error getting available voices: {str(e)}", e)
        # Return a default voice dictionary to allow the app to start
        return {"Default Voice": "default_voice_id"}

def transform_to_gothic(text, style, api_key):
    gothic_prompts = {
        "classic_gothic": "Transform this text into a classic gothic horror narrative with brooding atmosphere, dark romance, and supernatural elements.",
        "cosmic_horror": "Reimagine this text as a cosmic horror tale filled with unknowable entities and existential dread.",
        "southern_gothic": "Convert this text into a Southern gothic story with decayed settings, grotesque characters, and moral ambiguity.",
        "psychological_horror": "Rewrite this text as a psychological horror narrative, emphasizing inner torment and creeping madness.",
        "folk_horror": "Adapt this text into a folk horror story with ancient rituals, rural isolation, and pagan undertones."
    }
    style_prompt = gothic_prompts.get(style, gothic_prompts["classic_gothic"])
    
    try:
        # Create xAI client
        client = xAIClient(api_key=api_key)
        
        # Create the message payload for xAI
        messages = [
            {"role": "system", "content": f"You are a master of gothic horror literature. {style_prompt} Use vivid, atmospheric language and maintain a dark, mysterious tone throughout."},
            {"role": "user", "content": f"Transform this text into a gothic horror narrative:\n\n{text}"}
        ]
        
        # Call the xAI API
        response = client.chat(messages=messages)
        
        # Extract the response content from the Grok model
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            log_error(f"Empty response from xAI: {response}")
            return "The abyss remains silent. Try again, mortal."
            
        return content
    except Exception as e:
        log_error(f"Error transforming to gothic: {str(e)}", e)
        return f"The dark powers have failed. Error: {str(e)}"

def clean_narrative(text):
    cleaned = re.sub(r'\([^)]*\)', '', text)
    cleaned = re.sub(r'\[[^]]*\]', '', cleaned)
    return "\n".join(line.strip() for line in text.split('\n') if line.strip())

def create_output_folder(narrative):
    folder_name = re.sub(r'[^\w\-_\. ]', '_', narrative[:50].split('.')[0].strip())
    folder_path = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_narrative(text, folder_path):
    narrative_path = os.path.join(folder_path, "gothic_narrative.txt")
    with open(narrative_path, "w", encoding="utf-8") as f:
        f.write(text)
    return narrative_path

def text_to_speech_file(text, voice_id, output_format, folder_path, tone, pitch, api_key):
    try:
        # Create ElevenLabs client
        client = ElevenLabs(api_key=api_key)
        
        # Adjust stability and style based on tone (and pitch if needed)
        stability = 0.2 if tone == "mysterious" else 0.4
        style = 0.8 if tone == "somber" else 1.0
        
        response = client.text_to_speech.convert(
            voice_id=voice_id,
            optimize_streaming_latency="0",
            output_format=output_format,
            text=text,
            model_id="eleven_turbo_v2",
            voice_settings=VoiceSettings(
                stability=stability,
                similarity_boost=0.6,
                style=style,
                use_speaker_boost=True,
            ),
        )
        
        audio_path = os.path.join(folder_path, "gothic_audio.mp3")
        with open(audio_path, "wb") as f:
            for chunk in response:
                f.write(chunk)
        return audio_path
    except Exception as e:
        log_error(f"Error in text to speech: {str(e)}", e)
        raise

class GothicNarratorApp(tk.Tk):
    def __init__(self):
        try:
            super().__init__()
            
            # Get API keys - this is deferred until needed
            self.xai_api_key = os.getenv("XAI_API_KEY")
            self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            
            # Check API keys and warn if missing
            if not self.xai_api_key or not self.elevenlabs_api_key:
                messagebox.showwarning(
                    "Missing API Keys", 
                    "One or more API keys are missing. Some features may not work.\n"
                    "Please check your .env file."
                )
            
            self.title("Deep Narrator")
            self.geometry("900x600")
            self.configure(bg="black")
            self.user_prefs = load_preferences()
            
            # Get available voices
            if self.elevenlabs_api_key:
                self.available_voices = get_available_voices(self.elevenlabs_api_key)
            else:
                self.available_voices = {"API Key Missing": "missing_key"}
            
            # Audio player state
            self.current_audio_path = None
            self.is_playing = False
            self.audio_length = 0
            self.current_position = 0
            self.audio_thread = None
            self.audio_paths = {}
            
            # Create UI elements
            self.create_custom_titlebar()
            self.create_main_frames()
            self.create_left_sidebar()
            self.create_center_input()
            self.create_right_sidebar()
            self.update_audio_list()
            
            # Fix for text input focus issues
            self.after(100, self.set_initial_focus)
            
            # Bind application-wide events for better focus management
            self.bind_all("<Button-1>", self.check_focus)
            
            # Bind special key events to the text widget
            self.bind_text_commands()
            
            # Create a periodic audio status update
            self.after(500, self.update_player_status)
        except Exception as e:
            log_error(f"Error initializing app: {str(e)}", e)
            messagebox.showerror("Initialization Error", f"Error starting the application: {str(e)}")
            self.destroy()

    def set_initial_focus(self):
        """Set initial focus to the text input area and ensure it's ready to receive text."""
        self.input_text.focus_force()  # Force focus
        self.input_text.config(state=tk.NORMAL)  # Ensure it's enabled
        
    def check_focus(self, event=None):
        """Check where the focus is and refocus text if appropriate."""
        # If the click is inside the text frame, ensure text has focus
        widget = event.widget
        if widget == self.center_frame or widget == self.input_text:
            self.input_text.focus_set()
            
    def bind_text_commands(self):
        """Bind common text editing keyboard shortcuts."""
        # Allow standard text operations with keyboard
        self.input_text.bind("<Control-a>", self.select_all)
        self.input_text.bind("<Control-v>", lambda e: self.after(10, self.check_paste))
        
    def select_all(self, event=None):
        """Select all text in the input text area."""
        self.input_text.tag_add(tk.SEL, "1.0", tk.END)
        self.input_text.mark_set(tk.INSERT, "1.0")
        self.input_text.see(tk.INSERT)
        return 'break'  # Prevent default handling
        
    def check_paste(self):
        """Ensure pasted content is properly displayed."""
        self.input_text.update_idletasks()

    def create_custom_titlebar(self):
        # Custom titlebar with drag functionality
        self.overrideredirect(True)
        self.titlebar = tk.Frame(self, bg="black", relief="raised", bd=2)
        self.titlebar.pack(fill=tk.X)
        self.title_label = tk.Label(self.titlebar, text="Deep Narrator", bg="black", fg="white",
                                    font=("Courier New", 12, "bold"))
        self.title_label.pack(side=tk.LEFT, padx=10)
        self.btn_min = tk.Button(self.titlebar, text="–", bg="black", fg="black", command=self.iconify,
                                  font=("Courier New", 10, "bold"), bd=1, relief="solid", width=3)
        self.btn_min.config(highlightbackground="black", activebackground="black")
        self.btn_min.pack(side=tk.RIGHT, padx=2, pady=2)
        self.btn_max = tk.Button(self.titlebar, text="□", bg="black", fg="black", command=self.toggle_maximize,
                                  font=("Courier New", 10, "bold"), bd=1, relief="solid", width=3)
        self.btn_max.pack(side=tk.RIGHT, padx=2, pady=2)
        self.btn_close = tk.Button(self.titlebar, text="X", bg="black", fg="black", command=self.quit,
                                   font=("Courier New", 10, "bold"), bd=1, relief="solid", width=3)
        self.btn_close.pack(side=tk.RIGHT, padx=2, pady=2)
        self.titlebar.bind("<Button-1>", self.start_drag)
        self.titlebar.bind("<B1-Motion>", self.on_drag)
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.on_drag)

    def start_drag(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def on_drag(self, event):
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.geometry(f"+{x}+{y}")

    def toggle_maximize(self):
        if self.state() == "normal":
            self.state("zoomed")
        else:
            self.state("normal")
        # Ensure text input has focus after window state changes
        self.after(10, self.input_text.focus_set)

    def create_main_frames(self):
        # Main container frame divided into left sidebar, center input, right sidebar.
        self.main_frame = tk.Frame(self, bg="black")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

    def create_left_sidebar(self):
        # Create left sidebar with white outline
        self.left_frame = tk.Frame(self.main_frame, bg="black", bd=0, 
                               highlightbackground="white", highlightcolor="white", 
                               highlightthickness=1, width=200)
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=(5, 2), pady=5)
        
        # Voice selection (Listbox without visible scrollbar)
        tk.Label(self.left_frame, text="Select Voice", bg="black", fg="white",
                 font=("Courier New", 10, "bold")).pack(pady=(10, 2))
        
        voice_container = tk.Frame(self.left_frame, bg="black")
        voice_container.pack(fill=tk.X, padx=10, pady=0)
        
        self.voice_listbox = tk.Listbox(voice_container, bg="black", fg="white", 
                                      font=("Courier New", 10), height=6,
                                      selectbackground="#2a2a2a", selectforeground="white",
                                      borderwidth=0, highlightthickness=0)
        
        # Create scrollbar but don't show it visually (we'll keep the functionality)
        self.voice_scroll = tk.Scrollbar(voice_container, orient=tk.VERTICAL, 
                                       command=self.voice_listbox.yview, width=0)
        self.voice_listbox.config(yscrollcommand=self.voice_scroll.set)
        
        self.voice_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Pack but hide the scrollbar
        self.voice_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.voice_scroll.pack_forget()
        
        # Bind mousewheel for scrolling without visible scrollbar
        self.voice_listbox.bind("<MouseWheel>", self.on_voice_mousewheel)
        
        # Add voices to the list
        for name in self.available_voices.keys():
            self.voice_listbox.insert(tk.END, name)
            
        # Set default selection
        default_voice = self.user_prefs.get("voice_id")
        default_voice_name = next((name for name, vid in self.available_voices.items() if vid == default_voice), None)
        if default_voice_name:
            index = list(self.available_voices.keys()).index(default_voice_name)
            self.voice_listbox.select_set(index)
            self.voice_listbox.activate(index)
        else:
            self.voice_listbox.select_set(0)

        # Narration style (Radiobuttons)
        tk.Label(self.left_frame, text="Narration Style", bg="black", fg="white",
                 font=("Courier New", 10, "bold")).pack(pady=(15, 2))
        self.style_var = tk.StringVar(value=self.user_prefs.get("narration_style"))
        styles = ["classic_gothic", "cosmic_horror", "southern_gothic",
                  "psychological_horror", "folk_horror"]
        
        # Fix the radiobutton styling to ensure visibility
        for style in styles:
            radio = tk.Radiobutton(self.left_frame, text=style.replace("_", " ").title(), 
                                  variable=self.style_var, value=style, 
                                  bg="black", fg="white", selectcolor="black",
                                  activebackground="black", activeforeground="white",
                                  font=("Courier New", 10))
            radio.pack(anchor="w", padx=10)

        # Tone (Radiobuttons)
        tk.Label(self.left_frame, text="Tone", bg="black", fg="white",
                 font=("Courier New", 10, "bold")).pack(pady=(15, 2))
        self.tone_var = tk.StringVar(value=self.user_prefs.get("tone"))
        tones = ["mysterious", "somber", "menacing"]
        
        # Fix the tone radiobutton styling
        for tone in tones:
            radio = tk.Radiobutton(self.left_frame, text=tone.title(), 
                                  variable=self.tone_var, value=tone, 
                                  bg="black", fg="white", selectcolor="black",
                                  activebackground="black", activeforeground="white",
                                  font=("Courier New", 10))
            radio.pack(anchor="w", padx=10)

        # Generate button with better contrast
        self.generate_button = tk.Button(self.left_frame, text="Awaken the Abyss",
                                         command=self.generate_narration,
                                         bg="black", fg="black", 
                                         font=("Courier New", 10, "bold"),
                                         bd=1, relief="solid",
                                         activebackground="#333333",
                                         activeforeground="black")
        self.generate_button.pack(pady=(20, 10), padx=10, fill=tk.X)
        
    def on_voice_mousewheel(self, event):
        # Handle mousewheel scrolling for voice listbox
        if event.delta > 0:
            self.voice_listbox.yview_scroll(-2, "units")
        else:
            self.voice_listbox.yview_scroll(2, "units")

    def create_center_input(self):
        self.center_frame = tk.Frame(self.main_frame, bg="black", bd=0, 
                                highlightbackground="white", highlightcolor="white", 
                                highlightthickness=1)
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=5)
        
        # Create a label that doesn't capture focus
        tk.Label(self.center_frame, text="Enter What You Will....", bg="black", fg="white",
                font=("Courier New", 10, "bold")).pack(pady=(10, 2))
        
        # Create a frame to hold the text widget
        text_container = tk.Frame(self.center_frame, bg="black")
        text_container.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Add text widget with scrollbar
        self.input_text = tk.Text(text_container, bg="black", fg="white",
                                insertbackground="white", font=("Courier New", 10),
                                borderwidth=0, highlightthickness=0)
        
        # Create scrollbar but don't show it visually (keep the functionality)
        self.text_scroll = tk.Scrollbar(text_container, command=self.input_text.yview,
                                    bg="black", troughcolor="black", 
                                    activebackground="#333333")
        self.input_text.configure(yscrollcommand=self.text_scroll.set)
        
        # Pack text only, don't pack the scrollbar
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # The following line is commented out to hide the scrollbar
        # self.text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add mousewheel binding to enable scrolling without scrollbar
        self.input_text.bind("<MouseWheel>", self.on_text_mousewheel)
        
        # Make sure clicks in the text area keep focus there
        self.input_text.bind("<Button-1>", lambda event: "break" if self.input_text.focus_set() else None)
        self.center_frame.bind("<Button-1>", lambda event: self.input_text.focus_set())

    def on_text_mousewheel(self, event):
        # Handle mousewheel scrolling for text widget
        if event.delta > 0:
            self.input_text.yview_scroll(-2, "units")
        else:
            self.input_text.yview_scroll(2, "units")

    def create_right_sidebar(self):
        # Create right frame with white outline
        self.right_frame = tk.Frame(self.main_frame, bg="black", bd=0, 
                                 highlightbackground="white", highlightcolor="white", 
                                 highlightthickness=1, width=250)
        self.right_frame.grid(row=0, column=2, sticky="ns", padx=(2, 5), pady=5)
        
        # Title label
        tk.Label(self.right_frame, text="Generated Audio Tracks", bg="black", fg="white",
                 font=("Courier New", 10, "bold")).pack(pady=(10, 2))
        
        # Audio list without visible scrollbar
        list_frame = tk.Frame(self.right_frame, bg="black")
        list_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.audio_listbox = tk.Listbox(list_frame, bg="black", fg="white", 
                                      font=("Courier New", 10),
                                      selectbackground="#2a2a2a", selectforeground="white",
                                      borderwidth=0, highlightthickness=0)
        
        # Create scrollbar but don't show it visually
        list_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.audio_listbox.yview, width=0)
        self.audio_listbox.config(yscrollcommand=list_scroll.set)
        
        # Pack audio listbox but not the scrollbar
        self.audio_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        list_scroll.pack_forget()
        
        # Bind mousewheel for scrolling without visible scrollbar
        self.audio_listbox.bind("<MouseWheel>", self.on_audio_mousewheel)
        
        # Double-click to play audio
        self.audio_listbox.bind("<Double-1>", self.play_selected_audio)
        
        # Player controls frame
        player_frame = tk.Frame(self.right_frame, bg="black")
        player_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Now playing label
        self.now_playing_var = tk.StringVar(value="No file selected")
        self.now_playing_label = tk.Label(player_frame, textvariable=self.now_playing_var, 
                                         bg="black", fg="white", font=("Courier New", 8),
                                         wraplength=230, justify=tk.LEFT)
        self.now_playing_label.pack(fill=tk.X, pady=(0, 5))
        
        # Control buttons frame
        controls_frame = tk.Frame(player_frame, bg="black")
        controls_frame.pack(fill=tk.X)
        
        # Play button - improved contrast
        self.play_btn = tk.Button(controls_frame, text="▶", 
                                 bg="black", fg="#00FF00",  # Bright green for better visibility
                                 font=("Courier New", 12, "bold"), 
                                 bd=1, relief="solid",
                                 activebackground="#333333", activeforeground="#00FF00",
                                 command=self.play_audio)
        self.play_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Pause button - improved contrast
        self.pause_btn = tk.Button(controls_frame, text="⏸", 
                                  bg="black", fg="#FFFF00",  # Yellow for better visibility
                                  font=("Courier New", 12, "bold"), 
                                  bd=1, relief="solid",
                                  activebackground="#333333", activeforeground="#FFFF00",
                                  command=self.pause_audio)
        self.pause_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Stop button - improved contrast
        self.stop_btn = tk.Button(controls_frame, text="⏹", 
                                 bg="black", fg="#FF3333",  # Red for better visibility
                                 font=("Courier New", 12, "bold"), 
                                 bd=1, relief="solid",
                                 activebackground="#333333", activeforeground="#FF3333",
                                 command=self.stop_audio)
        self.stop_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Refresh button - improved contrast
        refresh_btn = tk.Button(self.right_frame, text="Refresh", 
                               bg="black", fg="black", 
                               font=("Courier New", 10, "bold"), 
                               bd=1, relief="solid",
                               activebackground="#333333", activeforeground="white",
                               command=self.update_audio_list)
        refresh_btn.pack(pady=(5, 10), padx=10, fill=tk.X)
        
        # Initialize audio player state
        self.current_audio = None
        self.is_playing = False
        
    def on_audio_mousewheel(self, event):
        # Handle mousewheel scrolling for audio listbox
        if event.delta > 0:
            self.audio_listbox.yview_scroll(-2, "units")
        else:
            self.audio_listbox.yview_scroll(2, "units")

    def update_audio_list(self):
        """Clear and repopulate the audio list from the OUTPUT_DIR"""
        self.audio_listbox.delete(0, tk.END)
        
        # We'll store paths in a separate dictionary since we can't use itemconfig to store custom data
        self.audio_paths = {}
        
        # Get all MP3 files
        audio_files = []
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                if file.endswith(".mp3"):
                    full_path = os.path.join(root, file)
                    parent_folder = os.path.basename(os.path.dirname(full_path))
                    display_name = f"{parent_folder} - {file}"
                    audio_files.append((display_name, full_path))
        
        # Sort by most recently created
        audio_files.sort(key=lambda x: os.path.getctime(x[1]), reverse=True)
        
        # Add to listbox and store paths in the dictionary
        for i, (display_name, full_path) in enumerate(audio_files):
            self.audio_listbox.insert(tk.END, display_name)
            self.audio_paths[i] = full_path
            
        # Select the first item if available
        if self.audio_listbox.size() > 0:
            self.audio_listbox.select_set(0)
            
    def get_selected_audio_path(self):
        """Get the full path of the selected audio file"""
        selected_indices = self.audio_listbox.curselection()
        if not selected_indices:
            return None
            
        index = selected_indices[0]
        # Get the path from our dictionary
        if index in self.audio_paths:
            return self.audio_paths[index]
            
        # Fallback method if path isn't in the dictionary
        filename = self.audio_listbox.get(index)
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                if file.endswith(".mp3") and (file in filename or os.path.basename(root) in filename):
                    return os.path.join(root, file)
        return None
        
    def play_selected_audio(self, event=None):
        """Play the audio file selected in the listbox"""
        path = self.get_selected_audio_path()
        if path:
            self.load_audio(path)
            self.play_audio()
            
    def load_audio(self, path):
        """Load an audio file for playback"""
        # Stop any currently playing audio
        self.stop_audio()
        
        # Set the current audio path
        self.current_audio_path = path
        
        # Update the now playing label
        folder_name = os.path.basename(os.path.dirname(path))
        file_name = os.path.basename(path)
        self.now_playing_var.set(f"Playing: {folder_name}/{file_name}")
        
    def play_audio(self):
        """Play the current audio file"""
        if not self.current_audio_path or not os.path.exists(self.current_audio_path):
            path = self.get_selected_audio_path()
            if not path:
                messagebox.showinfo("No Selection", "Please select an audio file to play.")
                return
            self.load_audio(path)
            
        if self.is_playing:
            # If already playing, just continue (unpause)
            pygame.mixer.music.unpause()
        else:
            # Start new playback
            try:
                pygame.mixer.music.load(self.current_audio_path)
                pygame.mixer.music.play()
                self.is_playing = True
                
                # Visually indicate the playing track
                self.highlight_playing_track()
            except Exception as e:
                log_error(f"Playback Error: {str(e)}", e)
                messagebox.showerror("Playback Error", f"Could not play the audio file:\n{str(e)}")
                
    def pause_audio(self):
        """Pause the currently playing audio"""
        if self.is_playing:
            pygame.mixer.music.pause()
            
    def stop_audio(self):
        """Stop the currently playing audio"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.current_position = 0
        
    def highlight_playing_track(self):
        """Highlight the currently playing track in the listbox"""
        # Reset all items to default color
        for i in range(self.audio_listbox.size()):
            self.audio_listbox.itemconfig(i, {'background': 'black'})
            
        # Find and highlight the playing track
        if self.current_audio_path:
            for i in range(self.audio_listbox.size()):
                if i in self.audio_paths and self.audio_paths[i] == self.current_audio_path:
                    self.audio_listbox.itemconfig(i, {'background': '#2a2a2a'})
                    break
                    
    def update_player_status(self):
        """Update player status and UI elements periodically"""
        # Check if music is still playing
        if self.is_playing and not pygame.mixer.music.get_busy():
            # Music finished playing
            self.is_playing = False
            self.now_playing_var.set("Playback finished")
            
        # Schedule the next update
        self.after(500, self.update_player_status)
        
    def generate_narration(self):
        """Generate a gothic narration from the input text"""
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("The Void Screams", "The abyss demands a tale. Scribe thy words.")
            self.input_text.focus_set()  # Refocus to text area
            return

        # Check API keys
        if not self.xai_api_key:
            messagebox.showerror("API Key Missing", 
                               "The xAI API key is missing. Please check your .env file.")
            return
            
        if not self.elevenlabs_api_key:
            messagebox.showerror("API Key Missing", 
                               "The ElevenLabs API key is missing. Please check your .env file.")
            return

        selected_indices = self.voice_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("No Voice Selected", "Please select a voice from the list.")
            return
        voice_name = self.voice_listbox.get(selected_indices[0])
        voice_id = self.available_voices.get(voice_name, list(self.available_voices.values())[0])

        narration_style = self.style_var.get()
        tone = self.tone_var.get()

        self.user_prefs.update({
            "voice_id": voice_id,
            "narration_style": narration_style,
            "tone": tone
        })
        save_preferences(self.user_prefs)

        try:
            # Show a processing indicator
            self.generate_button.config(text="Summoning...", state=tk.DISABLED)
            self.update_idletasks()
            
            # Transform text to gothic style using xAI
            narrative = transform_to_gothic(text, narration_style, self.xai_api_key)
            narrative = clean_narrative(narrative)
            
            # Create output files
            output_folder = create_output_folder(narrative)
            narrative_file = save_narrative(narrative, output_folder)
            
            # Generate audio using ElevenLabs
            audio_file = text_to_speech_file(
                narrative, voice_id, self.user_prefs["output_format"],
                output_folder, tone, self.user_prefs["pitch"],
                self.elevenlabs_api_key
            )
            
            # Reset button state
            self.generate_button.config(text="Awaken the Abyss", state=tk.NORMAL)
            
            # Ask if they want to play the new audio immediately
            play_now = messagebox.askyesno(
                "The Abyss Hath Spoken",
                f"Thy gothic curse hath risen!\n\nAudio saved to:\n{audio_file}\n\n"
                f"Do you wish to hear the darkness speak?"
            )
            
            # Update the audio list
            self.update_audio_list()
            
            # Auto-play the new file if requested
            if play_now:
                self.load_audio(audio_file)
                self.play_audio()
                
            self.input_text.focus_set()  # Refocus to text area after generation
        except Exception as e:
            log_error(f"Error in generate_narration: {str(e)}", e)
            # Reset button state
            self.generate_button.config(text="Awaken the Abyss", state=tk.NORMAL)
            messagebox.showerror("The Abyss Weeps", f"An error hath plagued the darkness:\n{str(e)}")
            self.input_text.focus_set()  # Refocus to text area


if __name__ == "__main__":
    try:
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Create log file
        open("error_log.txt", "w").close()
        
        # Start the app
        app = GothicNarratorApp()
        app.mainloop()
    except Exception as e:
        with open("error_log.txt", "a") as f:
            f.write(f"Critical app error: {str(e)}\n")
            f.write(traceback.format_exc())
        
        # Try to show an error dialog if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Critical Error", 
                               f"Critical error starting the application:\n{str(e)}\n\n"
                               f"Check error_log.txt for details.")
            root.destroy()
        except:
            print(f"Critical error: {str(e)}")
            print("See error_log.txt for details.")
    finally:
        # Clean up pygame
        pygame.mixer.quit()