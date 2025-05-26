# backend/app/services/ai_service.py
from transformers import pipeline, WhisperProcessor, WhisperForConditionalGeneration, ElectraForSequenceClassification, ElectraTokenizer
import torch
import librosa # 음성 파일 로드 및 샘플링 레이트 변환

# --- 0. 모델 로드 (애플리케이션 시작 시 또는 첫 호출 시 로드) ---

# Whisper 모델 및 프로세서 로드 (STT)
whisper_model_name = "YongJaeLee/Whisper_FineTuning_Ko_Stagewise"
whisper_processor = None
whisper_model = None

# KoELECTRA 모델 및 토크나이저 로드 (위험도 예측)
koelectra_model_name = "seungb1027/koelectra-suicide-risk"
koelectra_tokenizer = None
koelectra_model = None

# 모델 로드 함수 (애플리케이션 시작 시 호출되도록 __init__.py 등에서 관리 가능)
def load_models():
    global whisper_processor, whisper_model, koelectra_tokenizer, koelectra_model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device} for AI models.")

    if whisper_processor is None or whisper_model is None:
        print(f"Loading Whisper model: {whisper_model_name}...")
        whisper_processor = WhisperProcessor.from_pretrained(whisper_model_name)
        whisper_model = WhisperForConditionalGeneration.from_pretrained(whisper_model_name).to(device)
        whisper_model.eval() # 추론 모드로 설정
        print("Whisper model loaded.")

    if koelectra_tokenizer is None or koelectra_model is None:
        print(f"Loading KoELECTRA model: {koelectra_model_name}...")
        koelectra_tokenizer = ElectraTokenizer.from_pretrained(koelectra_model_name)
        koelectra_model = ElectraForSequenceClassification.from_pretrained(koelectra_model_name).to(device)
        koelectra_model.eval() # 추론 모드로 설정
        print("KoELECTRA model loaded.")

# --- 1. 음성 파일을 텍스트로 변환 (STT) ---
def speech_to_text(audio_file_path):
    if whisper_model is None or whisper_processor is None:
        load_models() # 모델이 로드되지 않았다면 로드

    device = whisper_model.device

    try:
        # 음성 파일 로드 및 Whisper가 요구하는 형식으로 전처리
        # Whisper는 16kHz 샘플링 레이트의 모노 오디오를 기대합니다.
        speech_array, sampling_rate = librosa.load(audio_file_path, sr=16000, mono=True)

        input_features = whisper_processor(speech_array, sampling_rate=16000, return_tensors="pt").input_features.to(device)

        # 음성 인식 수행
        with torch.no_grad(): # 그래디언트 계산 비활성화 (추론 시)
            predicted_ids = whisper_model.generate(input_features)

        # 예측된 ID를 텍스트로 디코딩
        transcription = whisper_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        print(f"Transcription: {transcription}")
        return transcription
    except Exception as e:
        print(f"Error in speech_to_text: {e}")
        return None


# --- 2. 텍스트 기반 자살 위험도 예측 ---
def predict_suicide_risk(text):
    if koelectra_model is None or koelectra_tokenizer is None:
        load_models() # 모델이 로드되지 않았다면 로드

    device = koelectra_model.device

    try:
        inputs = koelectra_tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(device)

        with torch.no_grad():
            outputs = koelectra_model(**inputs)
            logits = outputs.logits

        # 로짓에서 확률 계산 (Softmax) 및 가장 높은 확률의 클래스 예측
        probabilities = torch.softmax(logits, dim=-1)
        risk_level = torch.argmax(probabilities, dim=-1).item()

        print(f"Predicted Class ID (Risk Level): {risk_level}")
        return risk_level
    except Exception as e:
        print(f"Error in predict_suicide_risk: {e}")
        return None # 또는 기본 위험도 레벨 반환


# --- 3. 전체 분석 파이프라인 함수 ---
def analyze_audio_risk(audio_file_path):
    """
    음성 파일을 입력받아 텍스트로 변환 후, 자살 위험도를 예측합니다.
    성공 시 위험도 레벨 (예: 0, 1, 2)을 반환하고, 실패 시 None을 반환합니다.
    """
    print(f"Starting risk analysis for: {audio_file_path}")
    transcribed_text = speech_to_text(audio_file_path)

    if transcribed_text:
        risk_level = predict_suicide_risk(transcribed_text)
        if risk_level is not None:
            print(f"Analysis complete. Risk level: {risk_level}")
            return risk_level
        else:
            print("Failed to predict risk from text.")
            return None # 또는 기본 위험도
    else:
        print("Failed to transcribe audio.")
        return None # 또는 기본 위험도

if __name__ == '__main__':
    # 간단한 테스트용 코드 (실제 실행은 Flask 앱을 통해)
    # load_models() # 테스트 시 모델 미리 로드

    # 테스트할 오디오 파일 경로 (실제 파일로 대체)
    # test_audio_path = "path_to_your_test_audio.wav"
    # if os.path.exists(test_audio_path):
    #     risk = analyze_audio_risk(test_audio_path)
    #     if risk is not None:
    #         print(f"Final determined risk level for {test_audio_path}: {risk}")
    #     else:
    #         print(f"Could not determine risk for {test_audio_path}")
    # else:
    #     print(f"Test audio file not found: {test_audio_path}")
    pass