/**
 * Sunray Web Interface - Component Loader
 * Lädt modulare HTML-Komponenten und verwaltet die Navigation
 */

class ComponentLoader {
    constructor() {
        this.currentPage = this.getCurrentPageName();
        this.init();
    }

    async init() {
        await this.loadComponents();
        this.setupNavigation();
        this.startSensorUpdates();
    }

    getCurrentPageName() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        return filename.replace('.html', '') || 'dashboard';
    }

    async loadComponents() {
        try {
            // Sidebar laden
            const sidebarResponse = await fetch('/static/components/sidebar.html');
            const sidebarHtml = await sidebarResponse.text();
            document.getElementById('sidebar-container').innerHTML = sidebarHtml;

            // Header laden
            const headerResponse = await fetch('/static/components/header.html');
            const headerHtml = await headerResponse.text();
            document.getElementById('header-container').innerHTML = headerHtml;

            // Footer laden
            const footerResponse = await fetch('/static/components/footer.html');
            const footerHtml = await footerResponse.text();
            document.getElementById('footer-container').innerHTML = footerHtml;

            console.log('Komponenten erfolgreich geladen');
        } catch (error) {
            console.error('Fehler beim Laden der Komponenten:', error);
        }
    }

    setupNavigation() {
        // Aktuelle Seite in der Navigation markieren
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            const page = link.getAttribute('data-page');
            if (page === this.currentPage) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Navigation Event Listener
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // Für normale Navigation keine Intervention
                console.log('Navigation zu:', link.href);
            });
        });
    }

    async startSensorUpdates() {
        // Sensor-Daten regelmäßig aktualisieren
        this.updateSensorData();
        setInterval(() => this.updateSensorData(), 5000); // Alle 5 Sekunden
    }

    async updateSensorData() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            // Batterie-Daten
            if (data.battery) {
                document.getElementById('global-battery-value').textContent = 
                    Math.round(data.battery.percentage || 0) + '%';
                document.getElementById('global-battery-voltage').textContent = 
                    (data.battery.voltage || 0).toFixed(1) + 'V';
                document.getElementById('global-battery-current').textContent = 
                    (data.battery.current || 0).toFixed(1) + 'A';
            }

            // GPS-Daten
            if (data.gps) {
                const quality = data.gps.quality || 'Kein Signal';
                document.getElementById('global-gps-value').textContent = quality;
                document.getElementById('global-gps-robot-sats').textContent = 
                    data.gps.robot_satellites || '--';
                document.getElementById('global-gps-base-sats').textContent = 
                    data.gps.base_satellites || '--';
            }

            // Temperatur
            if (data.sensors && data.sensors.temperature) {
                document.getElementById('global-temp').textContent = 
                    Math.round(data.sensors.temperature) + '°C';
            }

            // Status
            if (data.robot_status) {
                document.getElementById('global-status').textContent = data.robot_status;
            }

            // Laufzeit
            if (data.runtime) {
                document.getElementById('global-runtime').textContent = 
                    this.formatRuntime(data.runtime);
            }

            // Verbindungsstatus
            this.updateConnectionStatus(true);

        } catch (error) {
            console.error('Fehler beim Laden der Sensor-Daten:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        const footerStatus = document.querySelector('#footer-connection-status .status-dot');

        if (connected) {
            statusDot?.classList.add('online');
            statusDot?.classList.remove('offline');
            statusText && (statusText.textContent = 'Verbunden');
            footerStatus?.classList.add('online');
            footerStatus?.classList.remove('offline');
        } else {
            statusDot?.classList.add('offline');
            statusDot?.classList.remove('online');
            statusText && (statusText.textContent = 'Getrennt');
            footerStatus?.classList.add('offline');
            footerStatus?.classList.remove('online');
        }
    }

    formatRuntime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

// Komponenten laden, wenn DOM bereit ist
document.addEventListener('DOMContentLoaded', () => {
    new ComponentLoader();
});

// Globale Hilfsfunktionen
window.SunrayComponents = {
    // Notification System
    showNotification: function(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove nach duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    },

    // Loading Spinner
    showLoading: function(target) {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        target.appendChild(spinner);
        return spinner;
    },

    hideLoading: function(spinner) {
        if (spinner && spinner.parentElement) {
            spinner.remove();
        }
    }
};