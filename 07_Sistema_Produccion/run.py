"""
Script para ejecutar el sistema MVP
Uso: python run.py [api|dashboard|tests]
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("""
╔════════════════════════════════════════╗
║   PREDICAST v4.0 - Sistema Execution   ║
╚════════════════════════════════════════╝

Uso:
  python run.py api           → Ejecutar API Flask (puerto 5000)
  python run.py dashboard     → Ejecutar Dashboard v4 Profesional (puerto 8501)
  python run.py dashboard-v3  → Ejecutar Dashboard v3 Anterior
  python run.py tests         → Ejecutar tests
  python run.py both          → API + Dashboard (2 terminales)

Ejemplo:
  Terminal 1: python run.py api
  Terminal 2: python run.py dashboard
        """)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "api":
        print("🚀 Iniciando API Flask...")
        print("   → http://localhost:5000")
        os.system("python -m src.api.main")
    
    elif cmd == "dashboard":
        print("🎨 Iniciando Dashboard Streamlit v4 (PROFESIONAL REDISEÑADO)...")
        print("   → http://localhost:8501")
        os.system("python -m streamlit run src/ui/dashboard_v4.py")
    
    elif cmd == "dashboard-v3":
        print("🎨 Iniciando Dashboard v3 (Anterior)...")
        print("   → http://localhost:8501")
        os.system("python -m streamlit run src/ui/dashboard_v3.py")
    
    elif cmd == "dashboard-v1":
        print("🎨 Iniciando Dashboard v1 (PoC)...")
        print("   → http://localhost:8501")
        os.system("python -m streamlit run src/ui/dashboard.py")
    
    elif cmd == "tests":
        print("🧪 Ejecutando tests...")
        os.system("pytest tests/ -v --tb=short")
    
    elif cmd == "both":
        print("🚀 Iniciando AMBOS servicios...")
        print("   API: http://localhost:5000")
        print("   Dashboard: http://localhost:8501")
        print("\n   ⚠️  Abre DOS terminales:")
        print("   Terminal 1: python run.py api")
        print("   Terminal 2: python run.py dashboard")

if __name__ == "__main__":
    main()
