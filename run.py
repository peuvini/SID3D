#!/usr/bin/env python3
"""
Script para executar o projeto SID3D
"""

import uvicorn
from config import settings


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 