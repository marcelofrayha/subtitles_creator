import os
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent, detect_silence
from faster_whisper import WhisperModel
import time
import random
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import re
import langid
import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt_tab', quiet=True)

# Initialize the translator
m2m_model = None
m2m_tokenizer = None

def initialize_translator():
    global m2m_model, m2m_tokenizer
    model_name = 'facebook/m2m100_418M'  # You can also use 'facebook/m2m100_1.2B' for better quality but slower performance
    m2m_model = M2M100ForConditionalGeneration.from_pretrained(model_name)
    m2m_tokenizer = M2M100Tokenizer.from_pretrained(model_name)

def translate_to_target(text, target_lang, source_lang):
    try:
        if source_lang == target_lang:
            return text
        
        global m2m_model, m2m_tokenizer
        if m2m_model is None or m2m_tokenizer is None:
            initialize_translator()
        
        m2m_tokenizer.src_lang = source_lang
        encoded = m2m_tokenizer(text, return_tensors="pt")
        generated_tokens = m2m_model.generate(**encoded, forced_bos_token_id=m2m_tokenizer.get_lang_id(target_lang))
        translated_text = m2m_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        
        print(f"Texto original ({source_lang}): {text}")
        print(f"Texto traduzido ({target_lang}): {translated_text}")
        
        return translated_text
    except Exception as e:
        print(f"Erro na tradução: {str(e)}")
        return text  # Retorna o texto original em caso de erro

# Configure the Whisper model
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

def normalize_lang_code(lang_code):
    """Normalize language codes to match the expected format."""
    lang_code = lang_code.lower()
    print(f"Normalizando idioma: {lang_code}")
    if lang_code == 'zh_cn':
        return 'zh'
    if lang_code == 'zh_tw':
        return 'zh'
    else:
        return lang_code

def process_translations(translations, source_lang, target_lang, max_phrase_duration=60000):
    processed_translations = []
    current_phrase = []
    current_phrase_duration = 0

    for i, (start, end, text) in enumerate(translations):
        current_phrase.append((start, end, text))
        current_phrase_duration += end - start

        if current_phrase_duration >= max_phrase_duration or i == len(translations) - 1:
            full_text = ' '.join(segment[2] for segment in current_phrase)
            sentences = sent_tokenize(full_text)
            translated_text = ' '.join([translate_to_target(sent, target_lang, source_lang) for sent in sentences])
            
            translated_words = translated_text.split()
            original_word_counts = [len(segment[2].split()) for segment in current_phrase]
            total_original_words = sum(original_word_counts)
            
            word_index = 0
            for (start, end, original_text), original_word_count in zip(current_phrase, original_word_counts):
                proportion = original_word_count / total_original_words
                segment_word_count = max(1, int(len(translated_words) * proportion))
                
                segment_translated = ' '.join(translated_words[word_index:word_index + segment_word_count])
                word_index += segment_word_count
                
                processed_translations.append((start, end, segment_translated))
            
            current_phrase = []
            current_phrase_duration = 0
    current_phrase = []
    current_phrase_duration = 0
    
    return processed_translations

def extract_audio(video_path):
    print(f"Extraindo áudio de: {video_path}")
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile("temp_audio.wav")
    return "temp_audio.wav"

def find_optimal_silence_threshold(audio_path, min_silence_len=400):
    # Use only the first 5 chunks (or less if there are fewer chunks)
    audio = AudioSegment.from_wav(audio_path)

    audio_trimmed = audio[:50000]
  
    best_ratio_diff = float('inf')
    best_threshold = None
    best_ratio = 0

    last_valid_threshold = None  # To track the last valid threshold

    threshold = -15
    consecutive_no_improvement = 0
    max_no_improvement = 5  # Maximum number of consecutive iterations without improvement

    while threshold > -80:  # Adjust range as needed
        print(f"Threshold: {threshold} dB")
        silences = detect_silence(audio_trimmed, min_silence_len=min_silence_len, silence_thresh=threshold)
        nonsilent = detect_nonsilent(audio_trimmed, min_silence_len=min_silence_len, silence_thresh=threshold)
        
        total_silence = sum(end - start for start, end in silences)
        total_nonsilent = sum(end - start for start, end in nonsilent)
        
        # Skip if no nonsilent segments are detected
        if total_nonsilent == 0:
            threshold -= 1
            continue
        
        # Calculate the ratio only if total_silence is greater than zero
        if total_silence > 0:
            ratio = total_nonsilent / total_silence
            ratio_diff = abs(ratio - 18) 
                
            print(f"Threshold: {threshold} dB, Ratio (nonsilent/silent): {ratio:.2f}")
            if ratio_diff < best_ratio_diff:
                best_ratio_diff = ratio_diff
                best_threshold = threshold
                best_ratio = ratio
                last_valid_threshold = threshold  # Update last valid threshold
                consecutive_no_improvement = 0  # Reset the counter
                if ratio < 4:
                    threshold -= 6
                elif ratio < 8:
                    threshold -= 4
                elif ratio < 12:
                    threshold -= 3
                elif ratio < 15:
                    threshold -= 2
                elif ratio < 18:
                    threshold -= 1
                else:
                    threshold -= 0.5  # Smaller step when close to target
            else:
                consecutive_no_improvement += 1
                threshold -= 2  # Smaller step when no improvement
            
            if consecutive_no_improvement >= max_no_improvement:
                print(f"\nBest threshold: {best_threshold} dB with ratio: {best_ratio:.2f}")
                return best_threshold
        else:
            threshold -= 1

    # If we've exhausted the threshold range without finding an optimal value
    if best_threshold is not None:
        print(f"\nBest threshold found: {best_threshold} dB with ratio: {best_ratio:.2f}")
        return best_threshold
    else:
        print("\nNo suitable threshold found.")
        return -30  # Return a default value if no suitable threshold was found

def segment_audio(audio_path, min_silence_len=600, silence_thresh=None, max_chunk_duration=15000, update_progress=None):
    audio = AudioSegment.from_wav(audio_path)
    
    total_duration = len(audio)
    chunks = []
    print(f"Detectando silêncios...")
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len, silence_thresh)
    print(f"Debug: detect_nonsilent returned {len(nonsilent_ranges)} ranges")
    print(f"{(nonsilent_ranges)}")

    current_chunk_start = 0
    for start, end in nonsilent_ranges:
        if end - current_chunk_start > max_chunk_duration:
            while end - current_chunk_start > max_chunk_duration:
                chunk_end = current_chunk_start + max_chunk_duration
                chunks.append((current_chunk_start, audio[current_chunk_start:chunk_end]))
                current_chunk_start = chunk_end
        
        if end - current_chunk_start > 0:
            chunks.append((current_chunk_start, audio[current_chunk_start:end]))
        
        current_chunk_start = end
        
        progress = (end / total_duration) * 20
        print(f"Progresso da segmentação: {progress:.2f}%")
        if update_progress:
            update_progress(int(progress))
    
    print(f"Número de segmentos: {len(chunks)}")
    return chunks

def transcribe_audio(audio_chunk):
    audio_chunk.export("temp_chunk.wav", format="wav")
    print("Transcrevendo segmento de áudio...")
    segments, _ = whisper_model.transcribe("temp_chunk.wav")
    transcription = " ".join([segment.text for segment in segments])
    os.remove("temp_chunk.wav")
    return transcription

def detect_language(transcriptions):
    print(f"Detectando idioma...")
    sample_texts = [t[2] for t in transcriptions[:2500]]
    # Combine the texts, separating them with spaces
    combined_text = " ".join(sample_texts)
    print(f"Combined text: {combined_text}")
    # Detect the language of the combined text
    detected_lang, _ = langid.classify(combined_text)
    
    print(f"Detected language: {detected_lang}")
    return detected_lang

def format_time(milliseconds):
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def split_long_text(text, max_chars=60):
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) - 1 > max_chars and current_line:
            lines.append(' '.join(current_line))
            current_line = []
            current_length = 0
        current_line.append(word)
        current_length += len(word) + 1
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def create_srt(translations, output_file, max_chars=60, min_silence_len=500):
    print(f"Criando arquivo SRT: {output_file}")
    with open(output_file, "w", encoding="utf-8") as srt_file:
        subtitle_index = 1
        for i, (start, end, text) in enumerate(translations):
            duration = end - start
            
            next_start = translations[i+1][0] if i+1 < len(translations) else None
            if next_start and next_start - end > min_silence_len:
                end = min(end + min_silence_len, next_start)
            
            lines = split_long_text(text, max_chars)
            for j, line in enumerate(lines):
                chunk_duration = duration / len(lines)
                chunk_start = start + j * chunk_duration
                chunk_end = chunk_start + chunk_duration
                
                if j == len(lines) - 1:
                    chunk_end = end
                
                srt_file.write(f"{subtitle_index}\n")
                srt_file.write(f"{format_time(int(chunk_start))} --> {format_time(int(chunk_end))}\n")
                srt_file.write(f"{line}\n\n")
                subtitle_index += 1

def main(video_path, output_srt, target_lang, min_silence_len=400, silence_thresh=None, update_progress=None, update_output=None):
    print("Iniciando a função main...")
    print(f"Vídeo Selecionado: {video_path}, Velocidade da fala: {min_silence_len}, Idioma alvo: {target_lang}")
    try:
        if update_output:
            update_output("Extraindo audio...")
        audio_path = extract_audio(video_path)
    
        if silence_thresh is None:
            if update_output:
                update_output("Determinando o melhor limiar de silêncio...")
            silence_thresh = find_optimal_silence_threshold(
                audio_path,  
                min_silence_len=min_silence_len,
            )
        audio_chunks = segment_audio(audio_path, min_silence_len=min_silence_len, silence_thresh=silence_thresh, max_chunk_duration=15000, update_progress=update_progress)
        if update_output:
            update_output(f"Segmentando audio com limiar de {silence_thresh} dB...")
        
        transcriptions = []
        
        total_chunks = len(audio_chunks)
        
        for i, (start_time, chunk) in enumerate(audio_chunks):
            if update_output:
                update_output(f"Transcrevendo segmento {i+1}/{total_chunks}")
            if update_progress:
                update_progress(30 + int((i / total_chunks) * 35))
            
            transcription = transcribe_audio(chunk)
            end_time = start_time + len(chunk)
            transcriptions.append((start_time, end_time, transcription))
        source_lang = detect_language(transcriptions)
        target_lang = normalize_lang_code(target_lang)
        source_lang = normalize_lang_code(source_lang)

        print(f"Idioma detectado: {source_lang}")
        for i, (start_time, end_time, transcription) in enumerate(transcriptions):
            if update_output:
                update_output(f"Traduzindo segmento {i+1}/{total_chunks}")
            if update_progress:
                progress = 65 + int((i / total_chunks) * 35)
                update_progress(progress)
        processed_translations = process_translations(transcriptions, source_lang, target_lang)

        if not processed_translations:
            print("Nenhuma tradução foi gerada!")
            return
        
        if update_output:
            update_output("Criando arquivo SRT...")
        create_srt(processed_translations, output_srt, min_silence_len=min_silence_len)
        
        if update_output:
            update_output("Processo concluído!")
        if update_progress:
            update_progress(100)
        
        os.remove(audio_path)
        
        print(f"Legendas salvas em {output_srt}")
    except Exception as e:
        print(f"Erro: {str(e)}")
        if update_output:
            update_output(f"Erro: {str(e)}")

if __name__ == "__main__":
    print("Iniciando a execução principal...")
    video_path = "/Users/marcelofrayha/Downloads/(PHASE 1) - Anonymous Testimony Of An American Physician PART 14.mp4"
    output_srt = "legendas_traduzidas.srt"
    target_lang = input("Digite o idioma alvo (ex: pt, es, fr): ")
    silence_thresh = input("Digite o limiar de silêncio em dB (ou pressione Enter para detectar automaticamente): ")
    silence_thresh = float(silence_thresh) if silence_thresh else None
    main(video_path, output_srt, target_lang, min_silence_len=400, silence_thresh=silence_thresh)
