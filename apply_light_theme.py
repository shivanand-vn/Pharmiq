import os
import re

ui_dir = r"f:\Pharmiq\ui"
files = [r"f:\Pharmiq\main.py"] + [os.path.join(ui_dir, f) for f in os.listdir(ui_dir) if f.endswith(".py")]

light_mapping = {
    # Main Backgrounds (Deepest darks)
    "#0f0f1a": "#F8F9FA",   # Very light gray for main canvas
    "#12122a": "#F1F3F5",   # Alternating row bg
    
    # Headers & Cards
    "#1a1a2e": "#FFFFFF",   # Pure white for headers
    "#16213e": "#FFFFFF",   # Pure white for cards/panels
    
    # Borders
    "#2a2a4a": "#DEE2E6",   # Soft modern border gray
    
    # Typography
    "#ffffff": "#212529",   # White -> Near black
    "#aabbcc": "#495057",   # Muted -> Medium gray
    "#ccccdd": "#495057",
    "#888899": "#868E96",   # Very muted -> Lighter gray
    
    # Primary Accents (Bright Blues)
    "#00d4ff": "#4361EE",   # Modern vibrant primary blue
    "#00a8cc": "#3A0CA3",   # Hover state for primary
    
    # Secondary Accents (Purples)
    "#6c5ce7": "#7209B7",
    "#5a4bd1": "#560BAD",
    
    # Buttons (Utility)
    "#333355": "#E9ECEF",   # Resting state for utility buttons (light) 
    "#444466": "#CED4DA",   # Hover state for utility buttons
    
    # Success/Danger
    "#00b894": "#2DC653",
    "#009975": "#208B3A",
    "#e94560": "#EF233C",
    "#c83b51": "#D90429",
    "#ff4444": "#EF233C",
    "#cc3333": "#D90429",
}

for path in files:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content
    # Multi-pass regex replace using case-insensitive hex matching
    for old_hex, new_hex in light_mapping.items():
        pattern = re.compile(re.escape(old_hex), re.IGNORECASE)
        new_content = pattern.sub(new_hex, new_content)
        
    # We also need to fix utility button text.
    # Utility buttons now have bg #E9ECEF, so their text (which was replacing #ffffff to #212529) is perfectly readable!
    
    # The entry backgrounds were using ENTRY_BG = "#0f0f1a" -> became #F8F9FA
    # Let's explicitly ensure entries have a white border or slightly gray border to stand out against #FFFFFF cards
    # Actually DEE2E6 border on F8F9FA is perfect.
    
    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {path}")

print("Light Theme applied successfully.")
