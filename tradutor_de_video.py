import os
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from faster_whisper import WhisperModel
import time
import random
from deep_translator import GoogleTranslator
from langdetect import detect
import re
from transformers import pipeline

# Inicialize o tradutor
translator = GoogleTranslator(source='en', target='pt')

# Configura o modelo Whisper
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

def extract_audio(video_path):
    print(f"Extraindo áudio de: {video_path}")
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile("temp_audio.wav")
    return "temp_audio.wav"

def segment_audio(audio_path, min_silence_len=1000, silence_thresh=-40, chunk_size=10*1000):
    print(f"Segmentando áudio: {audio_path}")
    audio = AudioSegment.from_wav(audio_path)
    total_duration = len(audio)
    chunks = []
    start = 0
    
    while start < total_duration:
        end = min(start + chunk_size, total_duration)
        audio_chunk = audio[start:end]
        
        nonsilent_ranges = detect_nonsilent(audio_chunk, 
                                            min_silence_len=min_silence_len, 
                                            silence_thresh=silence_thresh)
        
        for chunk_start, chunk_end in nonsilent_ranges:
            absolute_start = start + chunk_start
            absolute_end = start + chunk_end
            chunks.append((absolute_start, audio[absolute_start:absolute_end]))
        
        start = end
        
        # Progress reporting
        progress = (start / total_duration) * 100
        print(f"Progresso da segmentação: {progress:.2f}%")
        
        # Add a small delay to allow for interrupt
        time.sleep(0.01)
    
    print(f"Número de segmentos: {len(chunks)}")
    return chunks

def transcribe_audio(audio_chunk):
    audio_chunk.export("temp_chunk.wav", format="wav")
    print("Transcrevendo segmento de áudio...")
    segments, _ = whisper_model.transcribe("temp_chunk.wav")
    transcription = " ".join([segment.text for segment in segments])
    os.remove("temp_chunk.wav")
    return transcription

def detect_language(text):
    try:
        return detect(text)
    except:
        print("Não foi possível detectar o idioma. Assumindo inglês.")
        return 'en'

def translate_text(text, max_retries=3):
    if not text.strip():
        print("Texto vazio, pulando tradução.")
        return text

    source_lang = detect_language(text)
    print(f"Idioma detectado: {source_lang}")
    
    translator = GoogleTranslator(source=source_lang, target='pt')
    
    for attempt in range(max_retries):
        try:
            print(f"Traduzindo: '{text}'")
            translation = translator.translate(text)
            print(f"Tradução: '{translation}'")
            return translation
        except Exception as e:
            print(f"Erro na tradução (tentativa {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                wait_time = random.uniform(2, 5)
                print(f"Aguardando {wait_time:.2f} segundos antes de tentar novamente...")
                time.sleep(wait_time)
            else:
                print("Todas as tentativas falharam. Retornando texto original.")
                return text

    return text  # Retorna o texto original se todas as tentativas falharem

def refine_translation(translation):
    nlp = pipeline("text2text-generation", model="facebook/bart-large-cnn")
    refined = nlp(f"Melhore esta tradução: {translation}", max_length=100, do_sample=False)[0]['generated_text']
    return refined

def format_time(milliseconds):
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def split_long_text(text, max_chars=50):
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 > max_chars and current_line:
            lines.append(' '.join(current_line))
            current_line = []
            current_length = 0
        current_line.append(word)
        current_length += len(word) + 1
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def create_srt(translations, output_file, max_duration=3000, max_chars=100):
    print(f"Criando arquivo SRT: {output_file}")
    with open(output_file, "w", encoding="utf-8") as srt_file:
        subtitle_index = 1
        for start, end, text in translations:
            duration = end - start
            if duration <= max_duration:
                # If the duration is short enough, write as is
                lines = split_long_text(text, max_chars)
                srt_file.write(f"{subtitle_index}\n")
                srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
                srt_file.write('\n'.join(lines) + "\n\n")
                subtitle_index += 1
            else:
                # If the duration is too long, split into smaller chunks
                lines = split_long_text(text, max_chars)
                chunk_duration = duration / len(lines)
                for i, line in enumerate(lines):
                    chunk_start = start + i * chunk_duration
                    chunk_end = chunk_start + chunk_duration
                    srt_file.write(f"{subtitle_index}\n")
                    srt_file.write(f"{format_time(int(chunk_start))} --> {format_time(int(chunk_end))}\n")
                    srt_file.write(f"{line}\n\n")
                    subtitle_index += 1

def main(video_path, output_srt, update_progress=None, update_output=None):
    if update_output:
        update_output("Extracting audio...")
    audio_path = extract_audio(video_path)
    
    if update_output:
        update_output("Segmenting audio...")
    audio_chunks = segment_audio(audio_path)
    
    translations = []
    
    for i, (start_time, chunk) in enumerate(audio_chunks):
        if update_output:
            update_output(f"Processing segment {i+1}/{len(audio_chunks)}")
        if update_progress:
            update_progress(int((i / len(audio_chunks)) * 100))
        
        # Transcreve o segmento de áudio
        transcription = transcribe_audio(chunk)
        print(f"Transcrição original: '{transcription}'")
        
        # Traduz a transcrição
        translation = translate_text(transcription)
        print(f"Tradução final: '{translation}'")
        
        end_time = start_time + len(chunk)
        translations.append((start_time, end_time, translation))
    
    print(f"Número total de traduções: {len(translations)}")
    
    if not translations:
        print("Nenhuma tradução foi gerada!")
        return
    
    if update_output:
        update_output("Creating SRT file...")
    create_srt(translations, output_srt)
    
    if update_output:
        update_output("Process completed!")
    if update_progress:
        update_progress(100)
    
    # Limpa arquivos temporários
    os.remove(audio_path)
    
    print(f"Legendas salvas em {output_srt}")

if __name__ == "__main__":
    video_path = "/Users/marcelofrayha/Documents/ai/VoiceAssistant/LLAMA3-Voice-Over-Text/Youtube videos/Deolane Bezerra sai da prisão em PE em meio à confusão e críticas às investigações.mp4"
    output_srt = "legendas_traduzidas.srt"
    main(video_path, output_srt)