# TypeScript Setup für Sunray Web Interface

## 🚀 Übersicht

Dieses Projekt wurde mit TypeScript und modernen Code-Quality-Tools erweitert:

- **TypeScript**: Typsichere JavaScript-Entwicklung
- **ESLint**: Code-Qualitätsprüfung und Linting
- **Prettier**: Automatische Code-Formatierung
- **Modulare Architektur**: Bessere Wartbarkeit und Struktur

## 📁 Projektstruktur

```
static/js/
├── src/                    # TypeScript-Quelldateien
│   ├── components.ts       # Komponenten-Loader (TypeScript)
│   └── main.ts            # Haupt-Anwendungslogik
├── types/                  # TypeScript-Typdefinitionen
│   └── sunray.d.ts        # Sunray-spezifische Typen
├── dist/                   # Kompilierte JavaScript-Dateien (generiert)
└── components.js           # Legacy JavaScript (wird ersetzt)
```

## 🛠️ Installation & Setup

### Voraussetzungen
- Node.js (Version 16 oder höher)
- npm oder yarn

### Dependencies installieren

```bash
# Im sunray_py-Verzeichnis
npm install
```

**Hinweis**: Falls npm aufgrund von PowerShell-Richtlinien blockiert ist, können Sie die Dependencies manuell installieren oder die Ausführungsrichtlinien anpassen.

## 📝 Verfügbare Scripts

```bash
# TypeScript kompilieren
npm run build

# TypeScript im Watch-Modus (automatische Neukompilierung)
npm run watch

# Code-Linting
npm run lint

# Code-Linting mit automatischer Korrektur
npm run lint:fix

# Code-Formatierung
npm run format

# Typ-Überprüfung ohne Kompilierung
npm run type-check

# Development Server starten
npm run dev
```

## 🔧 Entwicklung

### TypeScript-Dateien bearbeiten

1. Bearbeiten Sie TypeScript-Dateien in `static/js/src/`
2. Kompilieren Sie mit `npm run build` oder `npm run watch`
3. Die kompilierten JavaScript-Dateien erscheinen in `static/js/dist/`

### Code-Qualität

- **ESLint** prüft automatisch auf Code-Qualitätsprobleme
- **Prettier** formatiert den Code einheitlich
- **TypeScript** bietet Typsicherheit und bessere IDE-Unterstützung

### Neue Komponenten hinzufügen

1. Erstellen Sie eine neue `.ts`-Datei in `static/js/src/`
2. Definieren Sie Typen in `static/js/types/sunray.d.ts`
3. Importieren Sie die Komponente in `main.ts`

## 📋 Konfigurationsdateien

- `tsconfig.json`: TypeScript-Konfiguration
- `.eslintrc.json`: ESLint-Regeln
- `.prettierrc.json`: Prettier-Formatierungsregeln
- `.prettierignore`: Dateien, die von Prettier ignoriert werden
- `package.json`: NPM-Konfiguration und Scripts

## 🎯 Typen und Interfaces

Alle Sunray-spezifischen Typen sind in `static/js/types/sunray.d.ts` definiert:

```typescript
// Beispiel: Status-API verwenden
import type { StatusResponse } from '../types/sunray';

const status: StatusResponse = await fetch('/api/status').then(r => r.json());
console.log(status.battery.percentage);
```

## 🔄 Migration von JavaScript zu TypeScript

### Schrittweise Migration

1. **Bestehende JS-Dateien**: Bleiben funktionsfähig
2. **Neue Features**: Werden in TypeScript entwickelt
3. **Schrittweise Konvertierung**: JS-Dateien können nach und nach zu TS konvertiert werden

### HTML-Templates aktualisieren

Ändern Sie Script-Referenzen von:
```html
<script src="/static/js/components.js"></script>
```

Zu:
```html
<script src="/static/js/dist/components.js"></script>
```

## 🚨 Troubleshooting

### PowerShell-Ausführungsrichtlinien

Falls npm-Befehle blockiert werden:

```powershell
# Temporär für aktuelle Session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Oder verwenden Sie npx direkt
npx tsc
npx eslint static/js/src/**/*.ts
```

### TypeScript-Kompilierungsfehler

- Überprüfen Sie `tsconfig.json` auf korrekte Pfade
- Stellen Sie sicher, dass alle Typen korrekt importiert sind
- Verwenden Sie `npm run type-check` für detaillierte Fehleranalyse

## 📈 Vorteile

✅ **Typsicherheit**: Weniger Laufzeitfehler durch Compile-Zeit-Checks
✅ **Bessere IDE-Unterstützung**: Autocompletion, Refactoring, Navigation
✅ **Code-Qualität**: Automatische Linting und Formatierung
✅ **Wartbarkeit**: Klarere Struktur und Dokumentation
✅ **Moderne Entwicklung**: ES2020+ Features mit Abwärtskompatibilität

## 🔗 Weiterführende Ressourcen

- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [ESLint Rules](https://eslint.org/docs/rules/)
- [Prettier Configuration](https://prettier.io/docs/en/configuration.html)