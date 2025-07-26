// Sunray Mähroboter Web Interface
class SunrayApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.isConnected = false;
        this.sensorData = {};
        this.mapData = null;
        this.robotPosition = { x: 0, y: 0, heading: 0 };
        this.updateInterval = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.startDataUpdates();
        this.initializeMap();
        this.checkConnection();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.currentTarget.dataset.page;
                this.navigateToPage(page);
            });
        });

        // Window resize for responsive map
        window.addEventListener('resize', () => {
            this.resizeMap();
        });
    }

    setupNavigation() {
        // Set initial active page
        this.navigateToPage('dashboard');
    }

    navigateToPage(pageName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

        // Update page content
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(`${pageName}-page`).classList.add('active');

        this.currentPage = pageName;
        this.loadPageContent(pageName);
    }

    async loadPageContent(pageName) {
        switch(pageName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'mapping':
                this.loadMapping();
                break;
            case 'tasks':
                this.loadTasks();
                break;
            case 'settings':
                this.loadSettings();
                break;
            case 'system':
                this.loadSystemInfo();
                break;
            case 'updates':
                this.loadUpdates();
                break;
            case 'info':
                this.loadInfo();
                break;
        }
    }

    // API Communication
    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            if (data && method !== 'GET') {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(`/api${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showToast('API-Fehler: ' + error.message, 'error');
            throw error;
        }
    }

    // Connection Management
    async checkConnection() {
        try {
            await this.apiCall('/status');
            this.setConnectionStatus(true);
        } catch (error) {
            this.setConnectionStatus(false);
        }
    }

    setConnectionStatus(connected) {
        this.isConnected = connected;
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        
        if (connected) {
            statusDot.style.background = '#4CAF50';
            statusText.textContent = 'Verbunden';
        } else {
            statusDot.style.background = '#f44336';
            statusText.textContent = 'Getrennt';
        }
    }

    // Data Updates
    startDataUpdates() {
        this.updateInterval = setInterval(() => {
            if (this.isConnected) {
                this.updateSensorData();
                this.updateRobotStatus();
                this.updateMap();
            }
            this.checkConnection();
        }, 2000);
    }

    async updateSensorData() {
        try {
            const data = await this.apiCall('/sensors');
            this.sensorData = data;
            this.updateSensorDisplay();
        } catch (error) {
            console.error('Failed to update sensor data:', error);
        }
    }

    updateSensorDisplay() {
        // Update battery level
        const batteryElement = document.getElementById('battery-level');
        if (this.sensorData.battery) {
            batteryElement.textContent = `${this.sensorData.battery.level}%`;
        }

        // Update GPS signal
        const gpsElement = document.getElementById('gps-signal');
        if (this.sensorData.gps) {
            const quality = this.sensorData.gps.quality || 0;
            gpsElement.textContent = quality > 3 ? 'Stark' : quality > 1 ? 'Mittel' : 'Schwach';
        }

        // Update temperature
        const tempElement = document.getElementById('temperature');
        if (this.sensorData.imu && this.sensorData.imu.temperature) {
            tempElement.textContent = `${this.sensorData.imu.temperature.toFixed(1)}°C`;
        }

        // Update orientation
        const orientationElement = document.getElementById('orientation');
        if (this.sensorData.imu && this.sensorData.imu.heading) {
            orientationElement.textContent = `${this.sensorData.imu.heading.toFixed(0)}°`;
            this.robotPosition.heading = this.sensorData.imu.heading;
        }
    }

    async updateRobotStatus() {
        try {
            const status = await this.apiCall('/navigation/status');
            document.getElementById('robot-status').textContent = status.state || 'Unbekannt';
            document.getElementById('robot-mode').textContent = status.mode || 'Manuell';
        } catch (error) {
            console.error('Failed to update robot status:', error);
        }
    }

    // Map Management
    initializeMap() {
        const canvas = document.getElementById('map-canvas');
        this.mapCanvas = canvas;
        this.mapContext = canvas.getContext('2d');
        this.resizeMap();
        this.drawMap();
    }

    resizeMap() {
        const canvas = this.mapCanvas;
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = 300;
        this.drawMap();
    }

    async updateMap() {
        try {
            const mapData = await this.apiCall('/map/current');
            this.mapData = mapData;
            this.drawMap();
        } catch (error) {
            // Map data might not be available yet
        }
    }

    drawMap() {
        const ctx = this.mapContext;
        const canvas = this.mapCanvas;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw background
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw grid
        this.drawGrid(ctx, canvas);
        
        // Draw zones if available
        if (this.mapData && this.mapData.zones) {
            this.drawZones(ctx, this.mapData.zones);
        }
        
        // Draw path if available
        if (this.mapData && this.mapData.path) {
            this.drawPath(ctx, this.mapData.path);
        }
        
        // Draw robot
        this.drawRobot(ctx, canvas);
    }

    drawGrid(ctx, canvas) {
        ctx.strokeStyle = '#ddd';
        ctx.lineWidth = 1;
        
        const gridSize = 20;
        for (let x = 0; x < canvas.width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        
        for (let y = 0; y < canvas.height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }

    drawZones(ctx, zones) {
        ctx.fillStyle = 'rgba(76, 175, 80, 0.3)';
        ctx.strokeStyle = '#4CAF50';
        ctx.lineWidth = 2;
        
        zones.forEach(zone => {
            if (zone.points && zone.points.length > 0) {
                ctx.beginPath();
                ctx.moveTo(zone.points[0].x, zone.points[0].y);
                zone.points.forEach(point => {
                    ctx.lineTo(point.x, point.y);
                });
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            }
        });
    }

    drawPath(ctx, path) {
        if (path.length < 2) return;
        
        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(path[0].x, path[0].y);
        path.forEach(point => {
            ctx.lineTo(point.x, point.y);
        });
        ctx.stroke();
    }

    drawRobot(ctx, canvas) {
        const centerX = canvas.width / 2 + this.robotPosition.x;
        const centerY = canvas.height / 2 + this.robotPosition.y;
        const size = 15;
        
        // Robot body
        ctx.fillStyle = '#FF5722';
        ctx.beginPath();
        ctx.arc(centerX, centerY, size, 0, 2 * Math.PI);
        ctx.fill();
        
        // Robot direction indicator
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 3;
        ctx.beginPath();
        const headingRad = (this.robotPosition.heading * Math.PI) / 180;
        const endX = centerX + Math.cos(headingRad) * size * 0.8;
        const endY = centerY + Math.sin(headingRad) * size * 0.8;
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(endX, endY);
        ctx.stroke();
    }

    // Control Functions
    async startMowing() {
        this.showLoading(true);
        try {
            await this.apiCall('/navigation/start', 'POST');
            this.showToast('Mähen gestartet', 'success');
        } catch (error) {
            this.showToast('Fehler beim Starten', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async stopMowing() {
        this.showLoading(true);
        try {
            await this.apiCall('/navigation/stop', 'POST');
            this.showToast('Mähen gestoppt', 'success');
        } catch (error) {
            this.showToast('Fehler beim Stoppen', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async pauseMowing() {
        this.showLoading(true);
        try {
            await this.apiCall('/navigation/pause', 'POST');
            this.showToast('Mähen pausiert', 'success');
        } catch (error) {
            this.showToast('Fehler beim Pausieren', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async returnHome() {
        this.showLoading(true);
        try {
            await this.apiCall('/navigation/home', 'POST');
            this.showToast('Rückkehr zur Basis', 'success');
        } catch (error) {
            this.showToast('Fehler bei Rückkehr', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Page Loading Functions
    loadDashboard() {
        // Dashboard is already loaded in HTML
        this.updateSensorData();
        this.updateRobotStatus();
        this.updateMap();
    }

    loadMapping() {
        const content = `
            <div class="mapping-content">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-map"></i> Kartenverwaltung</h3>
                    </div>
                    <div class="card-content">
                        <div class="mapping-tools">
                            <button class="btn btn-primary" onclick="app.startMapping()">
                                <i class="fas fa-play"></i> Kartierung starten
                            </button>
                            <button class="btn btn-secondary" onclick="app.loadMap()">
                                <i class="fas fa-upload"></i> Karte laden
                            </button>
                            <button class="btn btn-success" onclick="app.saveMap()">
                                <i class="fas fa-save"></i> Karte speichern
                            </button>
                        </div>
                        <div class="map-list" id="map-list">
                            <!-- Map list will be populated here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('mapping-page').innerHTML = content;
    }

    loadTasks() {
        const content = `
            <div class="tasks-content">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-tasks"></i> Aufgaben & Zonen</h3>
                    </div>
                    <div class="card-content">
                        <div class="task-tools">
                            <button class="btn btn-primary" onclick="app.createZone()">
                                <i class="fas fa-plus"></i> Zone erstellen
                            </button>
                            <button class="btn btn-success" onclick="app.scheduleTask()">
                                <i class="fas fa-clock"></i> Aufgabe planen
                            </button>
                        </div>
                        <div class="zone-list" id="zone-list">
                            <!-- Zone list will be populated here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('tasks-page').innerHTML = content;
    }

    loadSettings() {
        const content = `
            <div class="settings-content">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-cog"></i> Konfiguration</h3>
                    </div>
                    <div class="card-content">
                        <form id="settings-form">
                            <div class="form-group">
                                <label>Mähgeschwindigkeit</label>
                                <input type="range" min="0.1" max="2.0" step="0.1" value="1.0" id="mow-speed">
                                <span id="mow-speed-value">1.0 m/s</span>
                            </div>
                            <div class="form-group">
                                <label>Linienabstand</label>
                                <input type="range" min="0.1" max="1.0" step="0.05" value="0.3" id="line-spacing">
                                <span id="line-spacing-value">0.3 m</span>
                            </div>
                            <div class="form-group">
                                <label>Mähmuster</label>
                                <select id="mow-pattern">
                                    <option value="LINES">Linien</option>
                                    <option value="SQUARES">Quadrate</option>
                                    <option value="SPIRAL">Spirale</option>
                                </select>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('settings-page').innerHTML = content;
    }

    loadSystemInfo() {
        const content = `
            <div class="system-content">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-server"></i> Hardware Information</h3>
                    </div>
                    <div class="card-content">
                        <div class="system-stats" id="system-stats">
                            <!-- System stats will be populated here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('system-page').innerHTML = content;
        this.loadSystemStats();
    }

    loadUpdates() {
        const content = `
            <div class="updates-content">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-download"></i> Software Updates</h3>
                    </div>
                    <div class="card-content">
                        <div class="update-tools">
                            <button class="btn btn-primary" onclick="app.checkUpdates()">
                                <i class="fas fa-search"></i> Nach Updates suchen
                            </button>
                            <button class="btn btn-warning" onclick="app.flashPico()">
                                <i class="fas fa-microchip"></i> Pico flashen
                            </button>
                        </div>
                        <div class="update-status" id="update-status">
                            <!-- Update status will be populated here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('updates-page').innerHTML = content;
    }

    loadInfo() {
        const content = `
            <div class="info-content">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-info-circle"></i> System Information</h3>
                    </div>
                    <div class="card-content">
                        <div class="info-grid">
                            <div class="info-item">
                                <strong>Software Version:</strong>
                                <span>1.0.0</span>
                            </div>
                            <div class="info-item">
                                <strong>Hardware Version:</strong>
                                <span>Raspberry Pi 4</span>
                            </div>
                            <div class="info-item">
                                <strong>Letzte Aktualisierung:</strong>
                                <span id="last-update">-</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('info-page').innerHTML = content;
    }

    async loadSystemStats() {
        try {
            const stats = await this.apiCall('/system/stats');
            const container = document.getElementById('system-stats');
            container.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-icon"><i class="fas fa-microchip"></i></div>
                        <div class="stat-data">
                            <span class="stat-label">CPU Auslastung</span>
                            <span class="stat-value">${stats.cpu_usage || 0}%</span>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-icon"><i class="fas fa-memory"></i></div>
                        <div class="stat-data">
                            <span class="stat-label">RAM Nutzung</span>
                            <span class="stat-value">${stats.memory_usage || 0}%</span>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-icon"><i class="fas fa-thermometer-half"></i></div>
                        <div class="stat-data">
                            <span class="stat-label">CPU Temperatur</span>
                            <span class="stat-value">${stats.cpu_temp || 0}°C</span>
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-icon"><i class="fas fa-hdd"></i></div>
                        <div class="stat-data">
                            <span class="stat-label">Speicher</span>
                            <span class="stat-value">${stats.disk_usage || 0}%</span>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Failed to load system stats:', error);
        }
    }

    // Utility Functions
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span>${message}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    // Camera Functions
    toggleCamera() {
        const icon = document.getElementById('camera-toggle-icon');
        if (icon.classList.contains('fa-play')) {
            icon.classList.remove('fa-play');
            icon.classList.add('fa-pause');
            this.showToast('Kamera gestartet', 'success');
        } else {
            icon.classList.remove('fa-pause');
            icon.classList.add('fa-play');
            this.showToast('Kamera gestoppt', 'info');
        }
    }

    centerMap() {
        this.robotPosition = { x: 0, y: 0, heading: this.robotPosition.heading };
        this.drawMap();
        this.showToast('Karte zentriert', 'info');
    }

    // Placeholder functions for future implementation
    async startMapping() {
        this.showToast('Kartierung gestartet', 'success');
    }

    async createZone() {
        this.showToast('Zone-Editor wird geöffnet', 'info');
    }

    async saveSettings() {
        this.showToast('Einstellungen gespeichert', 'success');
    }

    async refreshSystemInfo() {
        this.loadSystemStats();
        this.showToast('System-Info aktualisiert', 'success');
    }

    async checkUpdates() {
        this.showToast('Suche nach Updates...', 'info');
    }

    async flashPico() {
        this.showToast('Pico Flash-Prozess gestartet', 'warning');
    }
}

// Global functions for HTML onclick handlers
function toggleCamera() { app.toggleCamera(); }
function centerMap() { app.centerMap(); }
function startMowing() { app.startMowing(); }
function stopMowing() { app.stopMowing(); }
function pauseMowing() { app.pauseMowing(); }
function returnHome() { app.returnHome(); }
function startMapping() { app.startMapping(); }
function createTask() { app.createZone(); }
function saveSettings() { app.saveSettings(); }
function refreshSystemInfo() { app.refreshSystemInfo(); }
function checkUpdates() { app.checkUpdates(); }
function createZone() { app.createZone(); }
function scheduleTask() { app.createZone(); }
function loadMap() { app.startMapping(); }
function saveMap() { app.startMapping(); }
function flashPico() { app.flashPico(); }

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SunrayApp();
});