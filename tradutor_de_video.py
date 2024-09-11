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
from transformers import AutoTokenizer, AutoModelForMaskedLM, AutoModelForSeq2SeqLM
import torch

# Inicialize o tradutor
translator = GoogleTranslator(source='en', target='pt')

# Configura o modelo Whisper
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# Carregue o modelo e o tokenizador uma vez no início do script
tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
model = AutoModelForMaskedLM.from_pretrained("bert-base-multilingual-cased")

model_name = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Crie um pipeline para geração de texto
nlp = pipeline("text2text-generation", model=model, tokenizer=tokenizer)

def extract_audio(video_path):
    print(f"Extraindo áudio de: {video_path}")
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile("temp_audio.wav")
    return "temp_audio.wav"

def segment_audio(audio_path, min_silence_len=1000, silence_thresh=-40, max_chunk_duration=15000, update_progress=None):
    print(f"Segmentando áudio: {audio_path}")
    audio = AudioSegment.from_wav(audio_path)
    total_duration = len(audio)
    chunks = []
    
    nonsilent_ranges = detect_nonsilent(audio, 
                                        min_silence_len=min_silence_len, 
                                        silence_thresh=silence_thresh)
    
    current_chunk_start = 0
    for start, end in nonsilent_ranges:
        if end - current_chunk_start > max_chunk_duration:
            # If the current non-silent section exceeds max duration, split it
            while end - current_chunk_start > max_chunk_duration:
                chunk_end = current_chunk_start + max_chunk_duration
                chunks.append((current_chunk_start, audio[current_chunk_start:chunk_end]))
                current_chunk_start = chunk_end
        
        if end - current_chunk_start > 0:
            chunks.append((current_chunk_start, audio[current_chunk_start:end]))
        
        current_chunk_start = end
        
        # Progress reporting
        progress = (end / total_duration) * 20  # 0-20% progress for segmenting
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

def detect_language(text):
    try:
        return detect(text)
    except:
        print("Não foi possível detectar o idioma. Assumindo inglês.")
        return 'en'

def translate_to_english(text, source_lang):
    translator = GoogleTranslator(source=source_lang, target='en')
    return translator.translate(text)

def translate_to_target(text, target_lang):
    translator = GoogleTranslator(source='en', target=target_lang)
    return translator.translate(text)

def refine_translation(translation):
    prompt = f"Refine this translation, improving fluency and coherence: {translation}"
    refined = nlp(prompt, max_length=500, do_sample=False)[0]['generated_text']
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
            
            lines = split_long_text(text, max_chars)
            for j, line in enumerate(lines):
                chunk_duration = duration / len(lines)
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

def check_consistency(current_chunk, prev_chunk, next_chunk, target_lang):
    # Concatena os chunks com um separador especial
    full_text = f"{prev_chunk} [SEP] {current_chunk} [SEP] {next_chunk}"
    
    # Tokeniza o texto
    inputs = tokenizer(full_text, return_tensors="pt", truncation=True, max_length=512)
    
    # Gera as previsões do modelo
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Calcula a perplexidade do texto
    loss = outputs.loss
    perplexity = safe_exp(loss)
    
    # Define um limiar de perplexidade para considerar inconsistente
    threshold = 10  # Ajuste este valor conforme necessário
    
    if perplexity > threshold:
        print(f"Possível inconsistência detectada em {target_lang}. Perplexidade: {perplexity.item()}")
        return True
    return False

def process_translations(translations, source_lang, target_lang):
    processed_translations = []
    for i, (start, end, text) in enumerate(translations):
        prev_chunk = translations[i-1][2] if i > 0 else ""
        next_chunk = translations[i+1][2] if i < len(translations) - 1 else ""
        
        # Traduzir para inglês
        text_en = translate_to_english(text, source_lang)
        prev_chunk_en = translate_to_english(prev_chunk, source_lang) if prev_chunk else ""
        next_chunk_en = translate_to_english(next_chunk, source_lang) if next_chunk else ""
        
        if check_consistency(text_en, prev_chunk_en, next_chunk_en, 'en'):
            print(f"Inconsistência detectada no trecho: {text}")
            
            # Refinar a tradução em inglês usando o modelo de linguagem
            refined_text_en = refine_translation(text_en)
            
            print(f"Texto original em inglês: {text_en}")
            print(f"Texto refinado em inglês: {refined_text_en}")
            
            # Verificar se o texto refinado em inglês é mais consistente
            if check_consistency(refined_text_en, prev_chunk_en, next_chunk_en, 'en'):
                print("O texto refinado ainda apresenta inconsistências. Mantendo o original.")
                final_text = text  # Manter o texto original no idioma alvo
            else:
                # Traduzir o texto refinado de volta para o idioma alvo
                final_text = translate_to_target(refined_text_en, target_lang)
                print(f"Texto refinado traduzido para {target_lang}: {final_text}")
                print("Texto refinado aceito.")
        else:
            final_text = text  # Se não houver inconsistência, manter o texto original
        
        processed_translations.append((start, end, final_text))
    
    return processed_translations

def safe_exp(input_tensor):
    if input_tensor is None:
        return torch.tensor(0.0)  # ou outro valor padrão apropriado
    return torch.exp(input_tensor)

def main(video_path, output_srt, context_size, target_lang, min_silence_len, update_progress=None, update_output=None):
    print(f"Vídeo Selecionado: {video_path}, Tamanho do Contexto da Tradução: {context_size}, Velocidade da fala: {min_silence_len}, Idioma alvo: {target_lang}")
    try:
        if context_size < 0 or context_size > 10:
            raise ValueError("O tamanho do contexto deve estar entre 0 e 10.")

        if update_output:
            update_output("Extraindo audio...")
        audio_path = extract_audio(video_path)
        
        if update_output:
            update_output("Segmentando audio...")
        audio_chunks = segment_audio(audio_path, min_silence_len=min_silence_len, max_chunk_duration=15000, update_progress=update_progress)
        
        transcriptions = []
        translations = []
        
        total_chunks = len(audio_chunks)
        
        # Primeira passagem: transcrição
        for i, (start_time, chunk) in enumerate(audio_chunks):
            if update_output:
                update_output(f"Transcrevendo segmento {i+1}/{total_chunks}")
            if update_progress:
                update_progress(30 + int((i / total_chunks) * 35))  # 30-65% progress for transcription
            
            transcription = transcribe_audio(chunk)
            end_time = start_time + len(chunk)
            transcriptions.append((start_time, end_time, transcription))
        
        # Segunda passagem: tradução com contexto
        for i, (start_time, end_time, current_chunk) in enumerate(transcriptions):
            if update_output:
                update_output(f"Traduzindo segmento {i+1}/{total_chunks}")
            if update_progress:
                # Adjust progress calculation: 65% (previous steps) + 35% (translation)
                progress = 65 + int((i / total_chunks) * 35)
                update_progress(progress)

            context_chunks = get_context(transcriptions, i, context_size)
            context_window = " ".join([c[2] for c in context_chunks])

            source_lang = detect_language(context_window)

            if source_lang != 'en':
                translated_window = translate_to_english(context_window, source_lang)
            else:
                translated_window = context_window

            # Translate only the current chunk to the target language
            current_chunk_translation = translate_to_target(
                translate_to_english(current_chunk, source_lang) if source_lang != 'en' else current_chunk, 
                target_lang
            )

            translations.append((start_time, end_time, current_chunk_translation))
        
        if not translations:
            print("Nenhuma tradução foi gerada!")
            return
        
        # Adicione a etapa de verificação de consistência e refinamento
        processed_translations = process_translations(translations, source_lang, target_lang)
        
        if update_output:
            update_output("Criando arquivo SRT...")
        create_srt(processed_translations, output_srt, min_silence_len=min_silence_len)
        
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
    target_lang = input("Digite o idioma alvo (ex: pt, es, fr): ")
    main(video_path, output_srt, target_lang, context_size)