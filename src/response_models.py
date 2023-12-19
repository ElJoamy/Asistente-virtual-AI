from pydantic import BaseModel
from typing import List, Dict

class CombinedReportResponse(BaseModel):
    nombre_archivo: str
    label: str
    score: float
    fecha_hora: str
    tiempo_ejecucion: float
    modelos: str
    longitud_texto: int
    uso_memoria: int
    uso_cpu: float

class SentimentAnalysisResponse(BaseModel):
    prediction: Dict[str, float]
    execution_info: Dict[str, float]

class TextAnalysisResponse(BaseModel):
    nlp_analysis: Dict[str, List[str]]
    sentiment_analysis: Dict[str, float]
    execution_info: Dict[str, float]

class StatusResponse(BaseModel):
    service_name: str
    version: str
    log_level: str
    status: str
    models_info: Dict[str, str]