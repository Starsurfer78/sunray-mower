/*
Sunray Mähroboter - Web Interface Scripts
Based on the Ardumower Sunray project

Original Sunray project:
- Forum: https://forum.ardumower.de/
- GitHub: https://github.com/Ardumower/Sunray
- Copyright (c) 2021-2024 by Alexander Grau, Grau GmbH

License: GPL-3.0 (same as original Sunray project)
Author: [Ihr Name]
Project: https://github.com/Starsurfer78/sunray-mower
*/

// Sunray Mähroboter Web Interface
class SunrayApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.isConnected = false;
        this.sensorData = {};
        this.mapData = null;
        this.robotPosition = { x: 0, y: 0, heading: 0 };
        this.updateInterval = null;
        
        // Mapping variables
        this.isMappingActive = false;
        this.mappingStartTime = null;
        this.mappingTimer = null;
        
        this.init();
        
        // Load available maps when mapping page is loaded
        this.loadAvailableMaps();
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

            const response = await fetch(`http://localhost:5000/api${endpoint}`, options);
            
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
        const globalConnectionElement = document.getElementById('global-connection-value');
        
        if (connected) {
            if (statusDot) statusDot.style.background = '#4CAF50';
            if (statusText) statusText.textContent = 'Verbunden';
            if (globalConnectionElement) globalConnectionElement.textContent = 'Verbunden';
        } else {
            if (statusDot) statusDot.style.background = '#f44336';
            if (statusText) statusText.textContent = 'Getrennt';
            if (globalConnectionElement) globalConnectionElement.textContent = 'Getrennt';
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
        const globalBatteryElement = document.getElementById('global-battery-value');
        const globalBatteryVoltage = document.getElementById('global-battery-voltage');
        const globalBatteryCurrent = document.getElementById('global-battery-current');
        
        if (this.sensorData.battery) {
            const batteryLevel = `${this.sensorData.battery.level}%`;
            if (batteryElement) batteryElement.textContent = batteryLevel;
            if (globalBatteryElement) globalBatteryElement.textContent = batteryLevel;
            
            if (globalBatteryVoltage && this.sensorData.battery.voltage) {
                globalBatteryVoltage.textContent = `${this.sensorData.battery.voltage.toFixed(1)}V`;
            }
            
            if (globalBatteryCurrent && this.sensorData.battery.current) {
                globalBatteryCurrent.textContent = `${this.sensorData.battery.current.toFixed(1)}A`;
            }
        }

        // Update GPS signal
        const gpsElement = document.getElementById('gps-signal');
        const globalGpsElement = document.getElementById('global-gps-value');
        const globalGpsRobotSats = document.getElementById('global-gps-robot-sats');
        const globalGpsBaseSats = document.getElementById('global-gps-base-sats');
        
        if (this.sensorData.gps) {
            const quality = this.sensorData.gps.quality || 0;
            const gpsText = quality > 3 ? 'Stark' : quality > 1 ? 'Mittel' : 'Schwach';
            if (gpsElement) gpsElement.textContent = gpsText;
            if (globalGpsElement) globalGpsElement.textContent = gpsText;
            
            if (globalGpsRobotSats && this.sensorData.gps.satellites_robot !== undefined) {
                globalGpsRobotSats.textContent = this.sensorData.gps.satellites_robot;
            }
            
            if (globalGpsBaseSats && this.sensorData.gps.satellites_base !== undefined) {
                globalGpsBaseSats.textContent = this.sensorData.gps.satellites_base;
            }
        }

        // Update temperature
        const tempElement = document.getElementById('temperature');
        const globalTempElement = document.getElementById('global-temp-value');
        if (this.sensorData.imu && this.sensorData.imu.temperature) {
            const tempText = `${this.sensorData.imu.temperature.toFixed(1)}°C`;
            if (tempElement) tempElement.textContent = tempText;
            if (globalTempElement) globalTempElement.textContent = tempText;
        }

        // Update orientation
        const orientationElement = document.getElementById('orientation');
        if (this.sensorData.imu && this.sensorData.imu.heading) {
            if (orientationElement) orientationElement.textContent = `${this.sensorData.imu.heading.toFixed(0)}°`;
            this.robotPosition.heading = this.sensorData.imu.heading;
        }
        
        // Update global sensor bar elements
        this.updateGlobalSensorBar();
    }

    async updateRobotStatus() {
        try {
            const status = await this.apiCall('/navigation/status');
            const statusElement = document.getElementById('robot-status');
            const modeElement = document.getElementById('robot-mode');
            const globalStatusElement = document.getElementById('global-status-value');
            
            if (statusElement) statusElement.textContent = status.state || 'Unbekannt';
            if (modeElement) modeElement.textContent = status.mode || 'Manuell';
            if (globalStatusElement) globalStatusElement.textContent = status.state || 'Unbekannt';
        } catch (error) {
            console.error('Failed to update robot status:', error);
        }
    }
    
    updateGlobalSensorBar() {
        // Update runtime
        const globalRuntimeElement = document.getElementById('global-runtime-value');
        if (globalRuntimeElement && this.sensorData.runtime) {
            const hours = Math.floor(this.sensorData.runtime / 3600);
            const minutes = Math.floor((this.sensorData.runtime % 3600) / 60);
            globalRuntimeElement.textContent = `${hours}:${minutes.toString().padStart(2, '0')}`;
        }
        
        // Update connection status in global bar
        const globalConnectionElement = document.getElementById('global-connection-value');
        if (globalConnectionElement) {
            globalConnectionElement.textContent = this.isConnected ? 'Verbunden' : 'Getrennt';
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

    // Mapping Functions
    async startMapping() {
        try {
            await this.apiCall('/mapping/start', 'POST');
            this.isMappingActive = true;
            this.updateMappingUI();
            this.showToast('Kartierung gestartet', 'success');
            this.startMappingTimer();
        } catch (error) {
            this.showToast('Fehler beim Starten der Kartierung', 'error');
        }
    }
    
    async stopMapping() {
        try {
            await this.apiCall('/mapping/stop', 'POST');
            this.isMappingActive = false;
            this.updateMappingUI();
            this.showToast('Kartierung beendet', 'info');
            this.stopMappingTimer();
        } catch (error) {
            this.showToast('Fehler beim Beenden der Kartierung', 'error');
        }
    }
    
    async loadMap() {
        const mapSelect = document.getElementById('map-select');
        const selectedMap = mapSelect.value;
        
        if (!selectedMap) {
            this.showToast('Bitte wählen Sie eine Karte aus', 'warning');
            return;
        }
        
        try {
            const mapData = await this.apiCall(`/mapping/load/${selectedMap}`);
            this.mapData = mapData;
            this.drawMap();
            this.showToast(`Karte '${selectedMap}' geladen`, 'success');
        } catch (error) {
            this.showToast('Fehler beim Laden der Karte', 'error');
        }
    }
    
    async saveMap() {
        const saveForm = document.getElementById('save-map-form');
        saveForm.style.display = 'block';
    }
    
    async confirmSaveMap() {
        const mapNameInput = document.getElementById('map-name-input');
        const mapName = mapNameInput.value.trim();
        
        if (!mapName) {
            this.showToast('Bitte geben Sie einen Kartennamen ein', 'warning');
            return;
        }
        
        try {
            await this.apiCall('/mapping/save', 'POST', {
                name: mapName,
                data: this.mapData
            });
            this.showToast(`Karte '${mapName}' gespeichert`, 'success');
            this.cancelSaveMap();
            this.loadAvailableMaps();
        } catch (error) {
            this.showToast('Fehler beim Speichern der Karte', 'error');
        }
    }
    
    cancelSaveMap() {
        const saveForm = document.getElementById('save-map-form');
        const mapNameInput = document.getElementById('map-name-input');
        saveForm.style.display = 'none';
        mapNameInput.value = '';
    }
    
    async deleteMap() {
        const mapSelect = document.getElementById('map-select');
        const selectedMap = mapSelect.value;
        
        if (!selectedMap) {
            this.showToast('Bitte wählen Sie eine Karte aus', 'warning');
            return;
        }
        
        if (!confirm(`Möchten Sie die Karte '${selectedMap}' wirklich löschen?`)) {
            return;
        }
        
        try {
            await this.apiCall(`/mapping/delete/${selectedMap}`, 'DELETE');
            this.showToast(`Karte '${selectedMap}' gelöscht`, 'success');
            this.loadAvailableMaps();
        } catch (error) {
            this.showToast('Fehler beim Löschen der Karte', 'error');
        }
    }
    
    async loadAvailableMaps() {
        try {
            const maps = await this.apiCall('/mapping/list');
            const mapSelect = document.getElementById('map-select');
            
            mapSelect.innerHTML = '<option value="">-- Karte auswählen --</option>';
            maps.forEach(map => {
                const option = document.createElement('option');
                option.value = map.name;
                option.textContent = `${map.name} (${map.date})`;
                mapSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load available maps:', error);
        }
    }
    
    updateMappingUI() {
        const startBtn = document.getElementById('start-mapping-btn');
        const stopBtn = document.getElementById('stop-mapping-btn');
        const statusText = document.getElementById('mapping-status-text');
        const statusDot = document.querySelector('#mapping-status .status-dot');
        
        if (this.isMappingActive) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusText.textContent = 'Kartierung läuft';
            statusDot.style.background = '#4CAF50';
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusText.textContent = 'Bereit';
            statusDot.style.background = '#666';
        }
    }
    
    startMappingTimer() {
        this.mappingStartTime = Date.now();
        this.mappingTimer = setInterval(() => {
            this.updateMappingTime();
        }, 1000);
    }
    
    stopMappingTimer() {
        if (this.mappingTimer) {
            clearInterval(this.mappingTimer);
            this.mappingTimer = null;
        }
    }
    
    updateMappingTime() {
        if (!this.mappingStartTime) return;
        
        const elapsed = Date.now() - this.mappingStartTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        const timeElement = document.getElementById('mapping-time');
         if (timeElement) {
             timeElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
         }
     }
     
     drawMap() {
         const canvas = document.getElementById('mapping-canvas');
         if (!canvas || !this.mapData) return;
         
         const ctx = canvas.getContext('2d');
         const rect = canvas.getBoundingClientRect();
         canvas.width = rect.width;
         canvas.height = rect.height;
         
         // Clear canvas
         ctx.clearRect(0, 0, canvas.width, canvas.height);
         
         // Draw grid
         this.drawGrid(ctx, canvas.width, canvas.height);
         
         // Draw map data if available
         if (this.mapData && this.mapData.points) {
             this.drawMapPoints(ctx, this.mapData.points, canvas.width, canvas.height);
         }
         
         // Update mapping info
         this.updateMappingInfo();
     }
     
     drawGrid(ctx, width, height) {
         ctx.strokeStyle = '#333';
         ctx.lineWidth = 1;
         
         const gridSize = 20;
         
         for (let x = 0; x <= width; x += gridSize) {
             ctx.beginPath();
             ctx.moveTo(x, 0);
             ctx.lineTo(x, height);
             ctx.stroke();
         }
         
         for (let y = 0; y <= height; y += gridSize) {
             ctx.beginPath();
             ctx.moveTo(0, y);
             ctx.lineTo(width, y);
             ctx.stroke();
         }
     }
     
     drawMapPoints(ctx, points, width, height) {
         if (!points || points.length === 0) return;
         
         // Find bounds
         let minX = Math.min(...points.map(p => p.x));
         let maxX = Math.max(...points.map(p => p.x));
         let minY = Math.min(...points.map(p => p.y));
         let maxY = Math.max(...points.map(p => p.y));
         
         // Add padding
         const padding = 20;
         const scaleX = (width - 2 * padding) / (maxX - minX || 1);
         const scaleY = (height - 2 * padding) / (maxY - minY || 1);
         const scale = Math.min(scaleX, scaleY);
         
         // Draw path
         ctx.strokeStyle = '#4CAF50';
         ctx.lineWidth = 2;
         ctx.beginPath();
         
         points.forEach((point, index) => {
             const x = padding + (point.x - minX) * scale;
             const y = padding + (point.y - minY) * scale;
             
             if (index === 0) {
                 ctx.moveTo(x, y);
             } else {
                 ctx.lineTo(x, y);
             }
         });
         
         ctx.stroke();
         
         // Draw start point
         if (points.length > 0) {
             const startPoint = points[0];
             const x = padding + (startPoint.x - minX) * scale;
             const y = padding + (startPoint.y - minY) * scale;
             
             ctx.fillStyle = '#2196F3';
             ctx.beginPath();
             ctx.arc(x, y, 5, 0, 2 * Math.PI);
             ctx.fill();
         }
         
         // Draw current position (last point)
         if (points.length > 1) {
             const currentPoint = points[points.length - 1];
             const x = padding + (currentPoint.x - minX) * scale;
             const y = padding + (currentPoint.y - minY) * scale;
             
             ctx.fillStyle = '#FF5722';
             ctx.beginPath();
             ctx.arc(x, y, 4, 0, 2 * Math.PI);
             ctx.fill();
         }
     }
     
     updateMappingInfo() {
         // Update mapped area
         const areaElement = document.getElementById('mapped-area');
         if (areaElement && this.mapData) {
             const area = this.calculateMappedArea();
             areaElement.textContent = `${area.toFixed(1)} m²`;
         }
         
         // Update waypoints
         const waypointsElement = document.getElementById('waypoints-count');
         if (waypointsElement && this.mapData && this.mapData.points) {
             waypointsElement.textContent = this.mapData.points.length.toString();
         }
     }
     
     calculateMappedArea() {
         if (!this.mapData || !this.mapData.points || this.mapData.points.length < 3) {
             return 0;
         }
         
         // Simple polygon area calculation using shoelace formula
         const points = this.mapData.points;
         let area = 0;
         
         for (let i = 0; i < points.length; i++) {
             const j = (i + 1) % points.length;
             area += points[i].x * points[j].y;
             area -= points[j].x * points[i].y;
         }
         
         return Math.abs(area) / 2;
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
function stopMapping() { app.stopMapping(); }
function loadMap() { app.loadMap(); }
function saveMap() { app.saveMap(); }
function confirmSaveMap() { app.confirmSaveMap(); }
function cancelSaveMap() { app.cancelSaveMap(); }
function deleteMap() { app.deleteMap(); }
function createTask() { app.createZone(); }
function saveSettings() { app.saveSettings(); }
function refreshSystemInfo() { app.refreshSystemInfo(); }
function checkUpdates() { app.checkUpdates(); }
function createZone() { app.createZone(); }
function scheduleTask() { app.createZone(); }
function flashPico() { app.flashPico(); }

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SunrayApp();
});