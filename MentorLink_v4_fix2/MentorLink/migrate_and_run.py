#!/usr/bin/env python
"""
Script de démarrage rapide MentorLink.
Lance : python migrate_and_run.py
"""
import os
import sys
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("=== MentorLink - Démarrage ===")
print("[1/2] Application des migrations...")
subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
print("[2/2] Lancement du serveur sur http://127.0.0.1:8000")
subprocess.run([sys.executable, 'manage.py', 'runserver'])
