import os
import time
import spacy
import json
import src.telegram_bot as telegram_bot
import psutil
from fastapi import FastAPI, UploadFile, File, HTTPException, status,Depends, Request
from fastapi.responses import JSONResponse, Response, FileResponse
from functools import cache
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware
from src.db.db_manage import DatabaseManager
from src.sentiment import SentimentAnalysisService
from src.config import get_settings
from typing import List
from src.response_models import (
    CombinedReportResponse,
    SentimentAnalysisResponse,
    TextAnalysisResponse,
    StatusResponse,
)


_SETTINGS = get_settings()

app = FastAPI(
    title=_SETTINGS.service_name,
    version=_SETTINGS.k_revision
)

db_manager = DatabaseManager(_SETTINGS.db_host, _SETTINGS.db_port, _SETTINGS.db_user, _SETTINGS.db_pass, _SETTINGS.db_name)

nlp = spacy.load("es_core_news_sm")

def get_sentiment_service():
    return SentimentAnalysisService()

@app.get("/status", response_model=StatusResponse, summary="Obtiene estado del servicio", description="Obtiene el estado actual del servicio, incluyendo información sobre los modelos utilizados.")
def get_status():
    status = db_manager.get_status()
    if not status:
        status_data = {
            "service_name": _SETTINGS.service_name,
            "version": _SETTINGS.k_revision,
            "log_level": _SETTINGS.log_level,
            "status": "Running",
            "models_info": json.dumps({
                "sentiment_model": _SETTINGS.sentiment_model_id,
                "nlp_model": "Spacy es_core_news_sm",
                "gpt_model": _SETTINGS.model 
            })
        }
        db_manager.insert_status(status_data)
        status = db_manager.get_status()

    return {
        "service_name": status['service_name'],
        "version": status['version'],
        "log_level": status['log_level'],
        "status": status['status'],
        "models_info": json.loads(status['models_info'])
    }

@app.post("/sentiment", response_model=SentimentAnalysisResponse, summary="Analiza sentimiento", description="Realiza un análisis de sentimiento en el texto proporcionado.")
def analyze_sentiment(text: str, user_id: int, sentiment_service: SentimentAnalysisService = Depends(get_sentiment_service)):
    start_time = time.time()
    result = sentiment_service.analyze_sentiment(text)
    end_time = time.time()
    execution_time = end_time - start_time

    prediction_datetime = datetime.now().isoformat()
    text_length = len(text)
    model_version = _SETTINGS.sentiment_model_id 
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info().rss 
    cpu_usage = process.cpu_percent(interval=1)

    adjusted_score = (result[0]['score'] * 2) - 1

    db_data = {
        "user_id": user_id,
        "Nombre del Archivo": "Sentiment Analysis",
        "Texto Analizado": text,
        "Label": result[0]['label'],
        "Score": adjusted_score,
        "Fecha y Hora": prediction_datetime,
        "Tiempo de Ejecución": execution_time,
        "Modelos": model_version,
        "Longitud del Texto": text_length,
        "Uso de Memoria": memory_info,
        "Uso de CPU": cpu_usage
    }

    db_manager.insert_sentiment(db_data)

    return {
        "prediction": {
            "label": result[0]['label'],
            "score": adjusted_score
        },
        "execution_info": {
            "execution_time": execution_time,
            "prediction_datetime": prediction_datetime,
            "text_length": text_length,
            "model_version": model_version,
            "memory_usage": memory_info,
            "cpu_usage": cpu_usage
        }
    }

@app.post("/analysis", response_model=TextAnalysisResponse, summary="Analiza texto", description="Realiza un análisis de texto, incluyendo etiquetas POS y entidades NER, y también realiza un análisis de sentimiento.")
def analyze_text(text: str, user_id: int, sentiment_service: SentimentAnalysisService = Depends(get_sentiment_service)):
    start_time = time.time()

    doc = nlp(text)
    pos_tags = [(token.text, token.pos_) for token in doc]
    ner_entities = [(ent.text, ent.label_) for ent in doc.ents]

    pos_tags_summary = {tag: [] for _, tag in pos_tags}
    for word, tag in pos_tags:
        pos_tags_summary[tag].append(word)
    pos_tag_count = {tag: len(words) for tag, words in pos_tags_summary.items()}

    ner_summary = {label: [] for _, label in ner_entities}
    for text, label in ner_entities:
        ner_summary[label].append(text)
    ner_count = {label: len(texts) for label, texts in ner_summary.items()}

    sentiment_result = sentiment_service.analyze_sentiment(text)
    adjusted_score = (sentiment_result[0]['score'] * 2) - 1

    end_time = time.time()
    execution_time = end_time - start_time

    prediction_datetime = datetime.now().isoformat()
    text_length = len(text)
    model_version = "Spacy & Sentiment Model"
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info().rss
    cpu_usage = process.cpu_percent(interval=1)

    db_data = {
        "user_id": user_id,
        "Texto Analizado": text,
        "POS Tags Resumen": str(pos_tags_summary),
        "POS Tags Conteo": str(pos_tag_count),
        "NER Resumen": str(ner_summary),
        "NER Conteo": str(ner_count),
        "Sentimiento Label": sentiment_result[0]['label'],
        "Sentimiento Score": adjusted_score,
        "Fecha y Hora": prediction_datetime,
        "Tiempo de Ejecución": execution_time,
        "Modelos": model_version,
        "Longitud del Texto": text_length,
        "Uso de Memoria": memory_info,
        "Uso de CPU": cpu_usage
    }

    db_manager.insert_analysis(db_data)
    
    return {
        "nlp_analysis": {
            "pos_tags_summary": pos_tags_summary,
            "pos_tag_count": pos_tag_count,
            "ner_summary": ner_summary,
            "ner_count": ner_count,
            "embeddings": [token.vector.tolist() for token in doc]
        },
        "sentiment_analysis": {
            "label": sentiment_result[0]['label'],
            "score": adjusted_score
        },
        "execution_info": {
            "execution_time": execution_time,
            "prediction_datetime": prediction_datetime,
            "text_length": text_length,
            "model_version": model_version,
            "memory_usage": memory_info,
            "cpu_usage": cpu_usage
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", reload=True)