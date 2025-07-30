from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

PROFESSOR = [
    {
        "id": 1,
        "nome": "Hyder Aragao",
        "email": "hyder@academico.ufs.br",
        "senha": 1234
    },
    {
        "id": 2,
        "nome": "pedro",
        "email": "hyder@academico.ufs.br",
        "senha": 1234
    }
]

class Professor(BaseModel):
    """Classe Professor"""

    nome: str
    email: str
    senha: int

@app.get("/professor", tags=["Professor"])
def getProfessor() -> list:
    """Retorna todos os professores presentes no sistema."""
    return PROFESSOR

@app.get("/professor/{professor_id}", tags=["Professor"])
def getProfessorByID(professor_id: int) -> dict:
    """Retornar Professor passando como parâmetro o ID"""
    for professor in PROFESSOR:
        if professor["id"] == professor_id:
            return professor
    return {}

@app.post("/professor", tags=["Professor"])
def createProfessor(professor: Professor) -> dict:
    """Criar professor"""
    professor = professor.model_dump()
    professor["id"] = len(PROFESSOR) + 1
    PROFESSOR.append(professor)
    return professor

@app.put("/professor/{professor_id}", tags=["Professor"])
def updateProfessor(professor_id: int, professor: Professor) -> dict:
    """Atualiza informação de professor com base no seu ID"""
    for index, prof in enumerate(PROFESSOR):
        if prof["id"] == professor_id:
            PROFESSOR[index] = professor
            return prof
    return {}

@app.delete("/professor/{professor_id}", tags=["Professor"])
def deleteProfessor(professor_id: int) -> dict:
    """Deleta um professor"""
    for index, prof in enumerate(PROFESSOR):
        if prof["id"] == professor_id:
            PROFESSOR.pop(index)
            return {"message": "Professor removido com sucesso"}
    return {}
