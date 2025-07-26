#!/usr/bin/env python3
"""
Sunray Web Interface - Modularer Page Builder
Konvertiert bestehende HTML-Seiten zu modularen Komponenten
"""

import os
import re
from pathlib import Path

class PageBuilder:
    def __init__(self, static_dir):
        self.static_dir = Path(static_dir)
        self.templates_dir = self.static_dir / 'templates'
        self.components_dir = self.static_dir / 'components'
        self.output_dir = self.static_dir
        
        # Template laden
        self.base_template = self.load_base_template()
    
    def load_base_template(self):
        """Lädt das Basis-Template"""
        template_path = self.templates_dir / 'base.html'
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        else:
            raise FileNotFoundError(f"Basis-Template nicht gefunden: {template_path}")
    
    def extract_page_content(self, html_content, page_name):
        """Extrahiert den Hauptinhalt einer Seite"""
        # Verschiedene Content-Bereiche je nach Seite
        content_patterns = {
            'dashboard': r'<div class="dashboard-grid">(.*?)</div>\s*</div>\s*</main>',
            'advanced_planning': r'<div class="main-content-grid">(.*?)</div>\s*</div>\s*</main>',
            'default': r'<div class="page active">.*?<div class="page-content">(.*?)</div>\s*</div>'
        }
        
        pattern = content_patterns.get(page_name, content_patterns['default'])
        match = re.search(pattern, html_content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: Suche nach main-content
        fallback_pattern = r'<div class="main-content"[^>]*>(.*?)</div>\s*</div>\s*</body>'
        match = re.search(fallback_pattern, html_content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return "<!-- Inhalt konnte nicht extrahiert werden -->"
    
    def extract_additional_css(self, html_content):
        """Extrahiert zusätzliche CSS-Styles"""
        css_pattern = r'<style[^>]*>(.*?)</style>'
        matches = re.findall(css_pattern, html_content, re.DOTALL)
        
        if matches:
            return '<style>\n' + '\n'.join(matches) + '\n</style>'
        return ''
    
    def extract_additional_js(self, html_content):
        """Extrahiert zusätzliche JavaScript-Inhalte"""
        js_pattern = r'<script[^>]*>(.*?)</script>'
        matches = re.findall(js_pattern, html_content, re.DOTALL)
        
        if matches:
            scripts = []
            for match in matches:
                if match.strip() and 'components.js' not in match:
                    scripts.append(f'<script>\n{match}\n</script>')
            return '\n'.join(scripts)
        return ''
    
    def get_page_title(self, page_name):
        """Gibt den Seitentitel zurück"""
        titles = {
            'dashboard': 'Dashboard',
            'advanced_planning': 'Erweiterte Pfadplanung',
            'mapping': 'Kartierung',
            'tasks': 'Aufgaben',
            'settings': 'Einstellungen',
            'system': 'System',
            'updates': 'Updates',
            'info': 'Info'
        }
        return titles.get(page_name, page_name.title())
    
    def build_page(self, page_name, original_html_path):
        """Erstellt eine modulare Seite aus einer bestehenden HTML-Datei"""
        print(f"Konvertiere {page_name}...")
        
        # Original HTML laden
        if not original_html_path.exists():
            print(f"Warnung: {original_html_path} nicht gefunden")
            return
        
        original_content = original_html_path.read_text(encoding='utf-8')
        
        # Inhalte extrahieren
        main_content = self.extract_page_content(original_content, page_name)
        additional_css = self.extract_additional_css(original_content)
        additional_js = self.extract_additional_js(original_content)
        page_title = self.get_page_title(page_name)
        
        # Template-Variablen ersetzen
        page_html = self.base_template
        page_html = page_html.replace('{{TITLE}}', page_title)
        page_html = page_html.replace('{{PAGE_TITLE}}', page_title)
        page_html = page_html.replace('{{MAIN_CONTENT}}', main_content)
        page_html = page_html.replace('{{ADDITIONAL_CSS}}', additional_css)
        page_html = page_html.replace('{{ADDITIONAL_JS}}', additional_js)
        page_html = page_html.replace('{{PAGE_ACTIONS}}', '')  # Kann später erweitert werden
        
        # CSS-Import für Komponenten hinzufügen
        if additional_css:
            css_import = '<link rel="stylesheet" href="css/components.css">'
            page_html = page_html.replace('{{ADDITIONAL_CSS}}', css_import + '\n' + additional_css)
        else:
            page_html = page_html.replace('{{ADDITIONAL_CSS}}', '<link rel="stylesheet" href="css/components.css">')
        
        # Neue Datei speichern
        output_path = self.output_dir / f'{page_name}_modular.html'
        output_path.write_text(page_html, encoding='utf-8')
        print(f"✓ {output_path} erstellt")
    
    def build_all_pages(self):
        """Konvertiert alle bekannten Seiten"""
        pages = {
            'dashboard': 'dashboard.html',
            'advanced_planning': 'advanced_planning.html',
            'mapping': 'mapping.html',
            'tasks': 'tasks.html',
            'settings': 'settings.html',
            'system': 'system.html',
            'updates': 'updates.html',
            'info': 'info.html'
        }
        
        print("Starte Konvertierung zu modularen Seiten...")
        print(f"Basis-Verzeichnis: {self.static_dir}")
        
        for page_name, filename in pages.items():
            original_path = self.static_dir / filename
            self.build_page(page_name, original_path)
        
        print("\n✓ Konvertierung abgeschlossen!")
        print("\nNächste Schritte:")
        print("1. Testen Sie die neuen *_modular.html Dateien")
        print("2. Ersetzen Sie die originalen Dateien wenn alles funktioniert")
        print("3. Aktualisieren Sie Links in web_server.py falls nötig")
    
    def create_example_page(self, page_name, title, content):
        """Erstellt eine Beispielseite mit dem modularen System"""
        page_html = self.base_template
        page_html = page_html.replace('{{TITLE}}', title)
        page_html = page_html.replace('{{PAGE_TITLE}}', title)
        page_html = page_html.replace('{{MAIN_CONTENT}}', content)
        page_html = page_html.replace('{{ADDITIONAL_CSS}}', '<link rel="stylesheet" href="css/components.css">')
        page_html = page_html.replace('{{ADDITIONAL_JS}}', '')
        page_html = page_html.replace('{{PAGE_ACTIONS}}', '')
        
        output_path = self.output_dir / f'{page_name}.html'
        output_path.write_text(page_html, encoding='utf-8')
        print(f"✓ Beispielseite {output_path} erstellt")

def main():
    """Hauptfunktion"""
    # Aktuelles Verzeichnis ermitteln
    current_dir = Path(__file__).parent
    
    # PageBuilder initialisieren
    builder = PageBuilder(current_dir)
    
    # Alle Seiten konvertieren
    builder.build_all_pages()
    
    # Beispielseite erstellen
    example_content = '''
    <div class="dashboard-grid">
        <div class="card">
            <div class="card-header">
                <h3><i class="fas fa-info-circle"></i> Modulares System</h3>
            </div>
            <div class="card-content">
                <p>Diese Seite wurde mit dem modularen Komponenten-System erstellt!</p>
                <ul>
                    <li>✓ Automatisch geladene Sidebar</li>
                    <li>✓ Gemeinsame Header-Komponente</li>
                    <li>✓ Einheitlicher Footer</li>
                    <li>✓ Zentrale Navigation</li>
                </ul>
            </div>
        </div>
    </div>
    '''
    
    builder.create_example_page('example_modular', 'Modulares Beispiel', example_content)

if __name__ == '__main__':
    main()