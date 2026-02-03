#!/usr/bin/env python
"""
Script para iniciar el servidor en modo desarrollo
"""
import os
import sys

def main():
    """Iniciar servidor de desarrollo"""
    print("🚀 Iniciando servidor de desarrollo...")
    print("📍 URL: http://localhost:3000")
    print("⏹️  Presiona CTRL+C para detener el servidor")
    print("-" * 50)
    
    os.system("python app.py")

if __name__ == "__main__":
    main()
