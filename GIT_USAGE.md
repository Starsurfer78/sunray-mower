# Git Versionskontrolle - Anleitung

## Repository-Status

✅ **Git-Repository erfolgreich eingerichtet!**

- Repository initialisiert in: `E:\VibeCoding`
- Erster Commit erstellt mit allen Projektdateien
- `.gitignore` konfiguriert für Python/Arduino-Projekte
- Benutzer konfiguriert als "Sunray Developer"

## Grundlegende Git-Befehle

### Status prüfen
```bash
git status
```

### Änderungen anzeigen
```bash
git diff
```

### Dateien hinzufügen
```bash
# Einzelne Datei
git add dateiname.py

# Alle Änderungen
git add .

# Bestimmte Dateitypen
git add *.py
```

### Commit erstellen
```bash
# Mit Nachricht
git commit -m "Beschreibung der Änderungen"

# Mit detaillierter Nachricht
git commit -m "Kurze Zusammenfassung" -m "Detaillierte Beschreibung"
```

### Commit-Historie anzeigen
```bash
# Kompakte Ansicht
git log --oneline

# Detaillierte Ansicht
git log

# Grafische Darstellung
git log --graph --oneline
```

## Branching-Workflow

### Neuen Branch erstellen
```bash
# Branch erstellen und wechseln
git checkout -b feature/neue-funktion

# Oder mit neuerer Syntax
git switch -c feature/neue-funktion
```

### Zwischen Branches wechseln
```bash
git checkout master
git switch feature/neue-funktion
```

### Branches anzeigen
```bash
# Lokale Branches
git branch

# Alle Branches
git branch -a
```

### Branch mergen
```bash
# Zu master wechseln
git checkout master

# Feature-Branch mergen
git merge feature/neue-funktion
```

## Remote Repository (GitHub/GitLab)

### Remote hinzufügen
```bash
git remote add origin https://github.com/username/sunray-mower.git
```

### Zum Remote pushen
```bash
# Erster Push
git push -u origin master

# Weitere Pushes
git push
```

### Vom Remote pullen
```bash
git pull origin master
```

## Empfohlener Workflow

### 1. Feature-Entwicklung
```bash
# Neuen Feature-Branch erstellen
git checkout -b feature/motor-verbesserung

# Änderungen vornehmen
# ...

# Änderungen committen
git add .
git commit -m "Motor PID-Parameter optimiert"

# Zu master wechseln
git checkout master

# Feature mergen
git merge feature/motor-verbesserung

# Feature-Branch löschen
git branch -d feature/motor-verbesserung
```

### 2. Bugfix-Workflow
```bash
# Bugfix-Branch erstellen
git checkout -b bugfix/sensor-kalibrierung

# Bug beheben
# ...

# Committen
git add .
git commit -m "Fix: IMU-Sensor Kalibrierung korrigiert"

# Mergen
git checkout master
git merge bugfix/sensor-kalibrierung
git branch -d bugfix/sensor-kalibrierung
```

## Nützliche Aliase

Füge diese zu deiner Git-Konfiguration hinzu:

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'
```

## Wichtige Dateien in .gitignore

Folgende Dateien werden automatisch ignoriert:

- `__pycache__/` - Python-Cache
- `*.pyc` - Kompilierte Python-Dateien
- `.pytest_cache/` - Test-Cache
- `config.json` - Lokale Konfiguration
- `*.log` - Log-Dateien
- `.vscode/`, `.idea/` - IDE-Einstellungen
- `venv/`, `env/` - Virtual Environments

## Backup und Sicherheit

### Lokales Backup
```bash
# Repository klonen
git clone E:\VibeCoding E:\VibeCoding-Backup
```

### Remote-Backup
```bash
# Zu GitHub/GitLab pushen
git remote add backup https://github.com/username/sunray-backup.git
git push backup master
```

## Troubleshooting

### Änderungen rückgängig machen
```bash
# Unstaged Änderungen verwerfen
git checkout -- dateiname.py

# Letzten Commit rückgängig (behält Änderungen)
git reset --soft HEAD~1

# Letzten Commit komplett rückgängig
git reset --hard HEAD~1
```

### Merge-Konflikte lösen
```bash
# Status prüfen
git status

# Konflikte manuell in Dateien lösen
# Dann:
git add .
git commit -m "Merge-Konflikt gelöst"
```

## Nächste Schritte

1. **Remote Repository einrichten**: Erstelle ein Repository auf GitHub/GitLab
2. **Collaborators hinzufügen**: Lade Teammitglieder ein
3. **CI/CD einrichten**: Automatische Tests und Deployment
4. **Issues und Pull Requests**: Nutze GitHub/GitLab Features
5. **Releases**: Erstelle Tagged Releases für Versionen

## Hilfreiche Ressourcen

- [Git Dokumentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Atlassian Git Tutorials](https://www.atlassian.com/git/tutorials)
- [Interactive Git Tutorial](https://learngitbranching.js.org/)