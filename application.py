from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Plateforme de Mentorat",
    description="API pour la plateforme de mentorat",
    version="1.0"
)

# Modèle de données pour les profils des mentors
class Profil(BaseModel):
    id_utilisateur: int
    nom: str
    prenom: str
    email: str
    competences: List[str]

@app.get("/")
def home():
    return {"message": "Bienvenue sur la plateforme de mentorat !"}