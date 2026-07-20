# generate_sounds.py
import os
import math
import wave
import struct
import random

def ensure_dir(filename):
    """Создаёт папку для файла, если её нет"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)

def generate_sine_wave(frequency, duration, sample_rate=44100, volume=0.5, attack=0.01, decay=0.1):
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < attack:
            envelope = t / attack
        elif t > duration - decay:
            envelope = (duration - t) / decay
        
        value = math.sin(2 * math.pi * frequency * t) * volume * envelope
        value += math.sin(2 * math.pi * frequency * 2 * t) * volume * 0.3 * envelope
        value += math.sin(2 * math.pi * frequency * 3 * t) * volume * 0.1 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_water_sound():
    """Звук водяной башни — плеск воды"""
    sample_rate = 44100
    duration = 0.2
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.01:
            envelope = t / 0.01
        elif t > duration - 0.03:
            envelope = (duration - t) / 0.03
        
        # Сочетание случайных частот для эффекта воды
        freq1 = 300 + random.randint(-50, 50)
        freq2 = 500 + random.randint(-100, 100)
        value = math.sin(2 * math.pi * freq1 * t) * 0.3 * envelope
        value += math.sin(2 * math.pi * freq2 * t) * 0.2 * envelope
        value += (random.random() * 2 - 1) * 0.1 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_freeze_sound():
    """Звук замораживающей башни — хруст льда"""
    sample_rate = 44100
    duration = 0.15
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.005:
            envelope = t / 0.005
        elif t > duration - 0.02:
            envelope = (duration - t) / 0.02
        
        # Высокие частоты с шумом для эффекта льда
        freq = 800 + t * 200
        value = math.sin(2 * math.pi * freq * t) * 0.25 * envelope
        value += math.sin(2 * math.pi * freq * 1.5 * t) * 0.15 * envelope
        value += (random.random() * 2 - 1) * 0.15 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_acid_sound():
    """Звук кислотной башни — шипение"""
    sample_rate = 44100
    duration = 0.25
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.01:
            envelope = t / 0.01
        elif t > duration - 0.03:
            envelope = (duration - t) / 0.03
        
        # Шум с низкими частотами
        freq = 200 + random.randint(-30, 30)
        value = math.sin(2 * math.pi * freq * t) * 0.2 * envelope
        value += (random.random() * 2 - 1) * 0.3 * envelope
        value += math.sin(2 * math.pi * 100 * t) * 0.1 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_rocket_sound():
    """Звук ракетной башни — свист и взрыв"""
    sample_rate = 44100
    duration = 0.3
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.005:
            envelope = t / 0.005
        elif t > duration - 0.05:
            envelope = (duration - t) / 0.05
        
        # Свист с повышением частоты
        freq = 300 + t * 800
        value = math.sin(2 * math.pi * freq * t) * 0.3 * envelope
        value += math.sin(2 * math.pi * freq * 0.5 * t) * 0.15 * envelope
        
        # Взрыв в конце
        if t > duration - 0.05:
            value += (random.random() * 2 - 1) * 0.3
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_pvo_sound():
    """Звук ПВО — быстрая очередь"""
    sample_rate = 44100
    duration = 0.1
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.002:
            envelope = t / 0.002
        elif t > duration - 0.02:
            envelope = (duration - t) / 0.02
        
        # Короткие импульсы
        freq = 600 + math.sin(t * 200) * 100
        value = math.sin(2 * math.pi * freq * t) * 0.25 * envelope
        
        # Имитация очереди
        if t % 0.02 < 0.005:
            value += 0.2 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_water_hit_sound():
    """Звук попадания воды — брызги"""
    sample_rate = 44100
    duration = 0.15
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.005:
            envelope = t / 0.005
        elif t > duration - 0.03:
            envelope = (duration - t) / 0.03
        
        value = (random.random() * 2 - 1) * 0.2 * envelope
        value += math.sin(2 * math.pi * 400 * t) * 0.15 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_freeze_hit_sound():
    """Звук попадания заморозки — хруст"""
    sample_rate = 44100
    duration = 0.1
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.005:
            envelope = t / 0.005
        elif t > duration - 0.02:
            envelope = (duration - t) / 0.02
        
        freq = 1000 + t * 300
        value = math.sin(2 * math.pi * freq * t) * 0.2 * envelope
        value += (random.random() * 2 - 1) * 0.15 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_acid_hit_sound():
    """Звук попадания кислоты — шипение"""
    sample_rate = 44100
    duration = 0.2
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.005:
            envelope = t / 0.005
        elif t > duration - 0.03:
            envelope = (duration - t) / 0.03
        
        value = (random.random() * 2 - 1) * 0.25 * envelope
        value += math.sin(2 * math.pi * 150 * t) * 0.15 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def generate_rocket_hit_sound():
    """Звук попадания ракеты — взрыв"""
    sample_rate = 44100
    duration = 0.3
    samples = int(sample_rate * duration)
    wave_data = []
    
    for i in range(samples):
        t = i / sample_rate
        
        envelope = 1.0
        if t < 0.01:
            envelope = t / 0.01
        elif t > duration - 0.1:
            envelope = (duration - t) / 0.1
        
        # Низкий гул с шумом
        value = math.sin(2 * math.pi * 80 * t) * 0.3 * envelope
        value += math.sin(2 * math.pi * 150 * t) * 0.2 * envelope
        value += (random.random() * 2 - 1) * 0.2 * envelope
        
        wave_data.append(int(value * 32767))
    
    return wave_data

def save_wav(filename, wave_data):
    """Сохраняет звук в WAV файл"""
    ensure_dir(filename)
    try:
        with wave.open(filename, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            wav.writeframes(struct.pack('<' + 'h' * len(wave_data), *wave_data))
        print(f"✅ Generated: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error generating {filename}: {e}")
        return False

def generate_all_sounds():
    """Генерирует все звуки для игры"""
    print("🎵 Generating sounds...")
    
    sounds = {
        "assets/sounds/shoot.wav": generate_sine_wave(800, 0.15, volume=0.4),
        "assets/sounds/death.wav": generate_sine_wave(300, 0.3, volume=0.3),
        "assets/sounds/tower_build.wav": generate_sine_wave(600, 0.2, volume=0.3),
        "assets/sounds/game_over.wav": generate_sine_wave(200, 0.8, volume=0.3),
        "assets/sounds/wave_complete.wav": generate_sine_wave(800, 0.3, volume=0.3),
        "assets/sounds/button_click.wav": generate_sine_wave(1200, 0.05, volume=0.2),
        "assets/sounds/enemy_spawn.wav": generate_sine_wave(400, 0.15, volume=0.2),
        "assets/sounds/background.wav": generate_sine_wave(220, 30, volume=0.05),
        # ✅ Новые звуки башен
        "assets/sounds/water_shoot.wav": generate_water_sound(),
        "assets/sounds/freeze_shoot.wav": generate_freeze_sound(),
        "assets/sounds/acid_shoot.wav": generate_acid_sound(),
        "assets/sounds/rocket_shoot.wav": generate_rocket_sound(),
        "assets/sounds/pvo_shoot.wav": generate_pvo_sound(),
        # ✅ Звуки попаданий
        "assets/sounds/water_hit.wav": generate_water_hit_sound(),
        "assets/sounds/freeze_hit.wav": generate_freeze_hit_sound(),
        "assets/sounds/acid_hit.wav": generate_acid_hit_sound(),
        "assets/sounds/rocket_hit.wav": generate_rocket_hit_sound(),
    }
    
    success_count = 0
    for filename, wave_data in sounds.items():
        if save_wav(filename, wave_data):
            success_count += 1
    
    print(f"\n✅ {success_count}/{len(sounds)} sounds generated successfully!")
    print("🎮 You can now run the game: python main.py")

if __name__ == "__main__":
    generate_all_sounds()