#!/usr/bin/env node
/**
 * Build-Skript für Sunray TypeScript-Projekt
 * Kompiliert TypeScript-Dateien und führt Code-Quality-Checks durch
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Farben für Console-Output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logStep(step, message) {
  log(`[${step}] ${message}`, 'cyan');
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logError(message) {
  log(`❌ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

// Hauptfunktion
function build() {
  log('🚀 Sunray TypeScript Build gestartet', 'bright');
  
  try {
    // 1. Verzeichnisse erstellen
    logStep('1/5', 'Erstelle Build-Verzeichnisse...');
    const distDir = path.join(__dirname, 'static', 'js', 'dist');
    if (!fs.existsSync(distDir)) {
      fs.mkdirSync(distDir, { recursive: true });
      logSuccess('dist-Verzeichnis erstellt');
    } else {
      logSuccess('dist-Verzeichnis bereits vorhanden');
    }

    // 2. TypeScript-Kompilierung prüfen
    logStep('2/5', 'Prüfe TypeScript-Installation...');
    try {
      execSync('npx tsc --version', { stdio: 'pipe' });
      logSuccess('TypeScript verfügbar');
    } catch (error) {
      logWarning('TypeScript nicht über npm verfügbar - verwende manuelle Kompilierung');
      return manualBuild();
    }

    // 3. Typ-Überprüfung
    logStep('3/5', 'Führe Typ-Überprüfung durch...');
    try {
      execSync('npx tsc --noEmit', { stdio: 'pipe' });
      logSuccess('Typ-Überprüfung erfolgreich');
    } catch (error) {
      logWarning('Typ-Überprüfung mit Warnungen - Build wird fortgesetzt');
    }

    // 4. TypeScript kompilieren
    logStep('4/5', 'Kompiliere TypeScript...');
    try {
      execSync('npx tsc', { stdio: 'pipe' });
      logSuccess('TypeScript-Kompilierung erfolgreich');
    } catch (error) {
      logError('TypeScript-Kompilierung fehlgeschlagen');
      console.error(error.toString());
      return false;
    }

    // 5. Code-Quality-Checks (optional)
    logStep('5/5', 'Führe Code-Quality-Checks durch...');
    try {
      execSync('npx eslint static/js/src/**/*.ts --quiet', { stdio: 'pipe' });
      logSuccess('ESLint-Checks erfolgreich');
    } catch (error) {
      logWarning('ESLint-Warnungen gefunden - siehe Details mit "npm run lint"');
    }

    logSuccess('🎉 Build erfolgreich abgeschlossen!');
    
    // Build-Info ausgeben
    const buildInfo = {
      timestamp: new Date().toISOString(),
      files: getCompiledFiles(distDir)
    };
    
    log('\n📋 Build-Zusammenfassung:', 'bright');
    log(`   Zeitstempel: ${buildInfo.timestamp}`);
    log(`   Kompilierte Dateien: ${buildInfo.files.length}`);
    buildInfo.files.forEach(file => {
      log(`   - ${file}`, 'blue');
    });
    
    return true;
    
  } catch (error) {
    logError(`Build fehlgeschlagen: ${error.message}`);
    return false;
  }
}

// Manuelle Build-Funktion für Fallback
function manualBuild() {
  logStep('FALLBACK', 'Führe manuellen Build durch...');
  
  try {
    // Einfache Kopie der TypeScript-Dateien als JavaScript
    const srcDir = path.join(__dirname, 'static', 'js', 'src');
    const distDir = path.join(__dirname, 'static', 'js', 'dist');
    
    if (!fs.existsSync(srcDir)) {
      logError('src-Verzeichnis nicht gefunden');
      return false;
    }
    
    const files = fs.readdirSync(srcDir).filter(file => file.endsWith('.ts'));
    
    files.forEach(file => {
      const srcPath = path.join(srcDir, file);
      const distPath = path.join(distDir, file.replace('.ts', '.js'));
      
      let content = fs.readFileSync(srcPath, 'utf8');
      
      // Einfache TypeScript-zu-JavaScript-Konvertierung
      content = content
        .replace(/import\s+type\s+\{[^}]+\}\s+from\s+['"][^'"]+['"];?/g, '') // Typ-Imports entfernen
        .replace(/:\s*[A-Za-z<>\[\]|\s]+(?=\s*[=,)}])/g, '') // Typ-Annotationen entfernen
        .replace(/as\s+[A-Za-z<>\[\]|\s]+/g, '') // Type-Assertions entfernen
        .replace(/export\s+default\s+/g, '') // Default-Exports vereinfachen
        .replace(/export\s+\{[^}]+\};?/g, ''); // Named-Exports entfernen
      
      fs.writeFileSync(distPath, content);
      log(`   Konvertiert: ${file} -> ${path.basename(distPath)}`, 'blue');
    });
    
    logSuccess('Manueller Build abgeschlossen');
    return true;
    
  } catch (error) {
    logError(`Manueller Build fehlgeschlagen: ${error.message}`);
    return false;
  }
}

// Hilfsfunktion: Kompilierte Dateien auflisten
function getCompiledFiles(distDir) {
  try {
    return fs.readdirSync(distDir)
      .filter(file => file.endsWith('.js'))
      .map(file => path.join('static/js/dist', file));
  } catch (error) {
    return [];
  }
}

// Script direkt ausführen, wenn es als Hauptmodul aufgerufen wird
if (require.main === module) {
  const success = build();
  process.exit(success ? 0 : 1);
}

module.exports = { build, manualBuild };