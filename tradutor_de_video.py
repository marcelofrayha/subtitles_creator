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

def segment_audio(audio_path, min_silence_len=1000, silence_thresh=-40, chunk_size=10*1000, update_progress=None):
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
        progress = (start / total_duration) * 25  # 0-25% progress for segmenting
        print(f"Progresso da segmentação: {progress:.2f}%")
        if update_progress:
            update_progress(int(progress))
        
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

def translate_text(text, target_lang, max_retries=3):
    if not text.strip():
        print("Texto vazio, pulando tradução.")
        return text

    source_lang = detect_language(text)
    print(f"Idioma detectado: {source_lang}")
    
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    for attempt in range(max_retries):
        try:
            print(f"Traduzindo: '{text[:50]}...'")  # Mostra apenas os primeiros 50 caracteres
            translation = translator.translate(text)
            print(f"Tradução: '{translation[:50]}...'")  # Mostra apenas os primeiros 50 caracteres
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

def create_srt(translations, output_file, max_duration=5000, max_chars=60, min_silence_len=500):
    print(f"Criando arquivo SRT: {output_file}")
    with open(output_file, "w", encoding="utf-8") as srt_file:
        subtitle_index = 1
        for i, (start, end, text) in enumerate(translations):
            duration = end - start
            
            # Verifica se há uma pausa significativa antes do próximo segmento
            next_start = translations[i+1][0] if i+1 < len(translations) else None
            if next_start and next_start - end > min_silence_len:
                end = min(end + min_silence_len, next_start)
            
            if duration <= max_duration:
                lines = split_long_text(text, max_chars)
                srt_file.write(f"{subtitle_index}\n")
                srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
                srt_file.write('\n'.join(lines) + "\n\n")
                subtitle_index += 1
            else:
                lines = split_long_text(text, max_chars)
                chunk_duration = duration / len(lines)
                for j, line in enumerate(lines):
                    chunk_start = start + j * chunk_duration
                    chunk_end = chunk_start + chunk_duration
                    
                    # Ajusta o final do último chunk para coincidir com o final do segmento
                    if j == len(lines) - 1:
                        chunk_end = end
                    
                    srt_file.write(f"{subtitle_index}\n")
                    srt_file.write(f"{format_time(int(chunk_start))} --> {format_time(int(chunk_end))}\n")
                    srt_file.write(f"{line}\n\n")
                    subtitle_index += 1

def get_context(chunks, current_index, context_size):
    start = max(0, current_index - context_size)
    end = min(len(chunks), current_index + context_size + 1)
    return chunks[start:end]

def translate_with_context(chunk, context, target_lang, max_retries=3):
    text_to_translate = chunk[2]
    print(f"Texto a ser traduzido: '{text_to_translate}'")

    source_lang = detect_language(text_to_translate)
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    for attempt in range(max_retries):
        try:
            print(f"Traduzindo: '{text_to_translate[:50]}...'")
            translation = translator.translate(text_to_translate)
            print(f"Tradução: '{translation[:100]}...'")
            return translation.strip()
        except Exception as e:
            print(f"Erro na tradução (tentativa {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                wait_time = random.uniform(2, 5)
                print(f"Aguardando {wait_time:.2f} segundos antes de tentar novamente...")
                time.sleep(wait_time)
            else:
                print("Todas as tentativas falharam. Retornando texto original.")
                return text_to_translate

    return text_to_translate  # Retorna o texto original se todas as tentativas falharem

def main(video_path, output_srt, context_size, update_progress=None, update_output=None, min_silence_len=500, target_lang='pt'):
    print(f"Vídeo Selecionado: {video_path}, Tamanho do Contexto da Tradução: {context_size}, Velocidade da fala: {min_silence_len}, Idioma alvo: {target_lang}")
    try:
        if context_size < 0 or context_size > 10:
            raise ValueError("O tamanho do contexto deve estar entre 0 e 10.")

        if update_output:
            update_output("Extraindo audio...")
        audio_path = extract_audio(video_path)
        
        if update_output:
            update_output("Segmentando audio...")
        audio_chunks = segment_audio(audio_path, update_progress=update_progress)
        
        transcriptions = []
        translations = []
        
        total_chunks = len(audio_chunks)
        
        # Primeira passagem: transcrição
        for i, (start_time, chunk) in enumerate(audio_chunks):
            if update_output:
                update_output(f"Transcrevendo segmento {i+1}/{total_chunks}")
            if update_progress:
                update_progress(25 + int((i / total_chunks) * 65))  # 25-90% progress for transcription
            
            transcription = transcribe_audio(chunk)
            end_time = start_time + len(chunk)
            transcriptions.append((start_time, end_time, transcription))
        
        # Segunda passagem: tradução com contexto
        for i, chunk in enumerate(transcriptions):
            if update_output:
                update_output(f"Traduzindo segmento {i+1}/{total_chunks}")
            if update_progress:
                update_progress(90 + int((i / total_chunks) * 10))  # 90-100% progress for translation
            
            context = get_context(transcriptions, i, context_size)
            translation = translate_with_context(chunk, context, target_lang)
            translations.append((chunk[0], chunk[1], translation))
        
        if not translations:
            print("Nenhuma tradução foi gerada!")
            return
        
        if update_output:
            update_output("Criando arquivo SRT...")
        create_srt(translations, output_srt, min_silence_len=min_silence_len)
        
        if update_output:
            update_output("Processo concluído!")
        if update_progress:
            update_progress(100)
        
        # Limpa arquivos temporários
        os.remove(audio_path)
        
        print(f"Legendas salvas em {output_srt}")
    except Exception as e:
        print(f"Erro: {str(e)}")
        if update_output:
            update_output(f"Erro: {str(e)}")

if __name__ == "__main__":
    video_path = "/Users/marcelofrayha/Downloads/Novas imagens： Câmera flagra queda de helicóptero em Pernambuco ｜ Primeiro Impacto (10⧸09⧸24).mp4"
    output_srt = "legendas_traduzidas.srt"
    context_size = int(input("Digite o tamanho do contexto (0-10): "))
    main(video_path, output_srt, context_size)