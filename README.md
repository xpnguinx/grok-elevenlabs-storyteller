# Grok Elevenlabs Storyteller

![Screenshot 2025-03-04 at 11 48 38 AM](https://github.com/user-attachments/assets/f7ac2c29-4bd3-4616-9b61-7766ef82c068)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

A dark, atmospheric text-to-speech application that transforms ordinary text into haunting narratives and brings them to life with professional voice narration.


 

## 🔮 Features

- Transform ordinary text into rich gothic horror narratives
- Choose from multiple gothic styles: classic, cosmic horror, southern gothic, psychological horror, folk horror
- Professional text-to-speech narration through ElevenLabs
- Customizable voice settings and tone controls
- Built-in audio player for instant playback
- Sleek hacker-inspired dark interface
- Save both text narratives and audio files for later use

## 🧠 How It Works

The Gothic Hacker Narrator app uses the power of xAI's Grok LLM to transform your input text into richly detailed gothic narratives. The app then leverages ElevenLabs' voice synthesis to narrate your gothic tale with the perfect atmospheric tone.

1. **Input your text** - Start with any text you want to transform
2. **Select a gothic style** - Choose the gothic horror subgenre that fits your vision
3. **Customize voice and tone** - Select from available ElevenLabs voices and adjust tone settings
4. **Generate** - Click "Awaken the Abyss" to transform and narrate your text
5. **Listen and save** - The app automatically saves both the gothic narrative text and audio file

## ⚙️ Installation

### Prerequisites

- Python 3.10 or higher
- xAI API key (Grok)
- ElevenLabs API key

### Setting Up

1. Clone the repository:
```bash
git clone https://github.com/xpnguinx/grok-elevenlabs-storyteller.git
cd grok-elevenlabs-storyteller
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory with your API keys:
```
XAI_API_KEY=your_xai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

4. Run the application:
```bash
python app.py
```

## 📦 Dependencies

- tkinter - GUI framework
- pygame - Audio playback
- requests - API communication
- python-dotenv - Environment variable management
- elevenlabs - Voice synthesis

## 🎭 Gothic Style Options

- **Classic Gothic**: Brooding atmosphere, dark romance, and supernatural elements
- **Cosmic Horror**: Unknowable entities and existential dread (Lovecraftian)
- **Southern Gothic**: Decayed settings, grotesque characters, and moral ambiguity
- **Psychological Horror**: Inner torment and creeping madness
- **Folk Horror**: Ancient rituals, rural isolation, and pagan undertones

## 🏗️ Project Structure

```
grok-elevenlabs-storyteller/
├── app.py                  # Main application file
├── .env                    # API keys (create this file)
├── requirements.txt        # Project dependencies
├── narrations/             # Output directory for generated content
├── preferences.json        # Saved user preferences
└── error_log.txt           # Application error logs
```

## 🚀 Roadmap

- [ ] Add batch processing for multiple texts
- [ ] Implement additional voice customization options
- [ ] Create preset gothic templates for different scenarios
- [ ] Add export options for sharing content
- [ ] Develop a theme system for interface customization

## 💡 Troubleshooting

If you encounter issues:

1. Check the `error_log.txt` file for detailed error information
2. Verify your API keys are correctly set in the `.env` file
3. Ensure all dependencies are properly installed
4. For voice-related issues, verify your ElevenLabs account has available character credits

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.


---

<p align="center">
  Created by <a href="https://github.com/xpnguinx">xpnguinx</a> | Powered by Grok and ElevenLabs
</p>
