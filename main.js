/**
 * main.js - Electron Main Process
 * 
 * This file is the entry point for the Electron application. It manages the 
 * application lifecycle, creates the native window, and handles the 
 * communication bridge between the renderer (UI) and the Python backend.
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { PythonShell } = require('python-shell');

let mainWindow;     // Reference to the main UI window
let pythonProcess;  // Reference to the background Python process

/**
 * Creates the main application window with premium styling and secure settings.
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        backgroundColor: '#0f172a', // Deep slate background to match the premium theme
        webPreferences: {
            // Securely expose native APIs via a preload script
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
        title: "Torrpeddo",
        // icon: path.join(__dirname, 'assets', 'icon.png') // Path to the app icon
    });

    // Load the frontend from the renderer directory
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

    // Optional: Open DevTools for debugging during development
    // mainWindow.webContents.openDevTools();
}

/**
 * Initializes the Python background process which handles libtorrent logic.
 * We use an IPC (Inter-Process Communication) bridge over standard I/O.
 */
function startPython() {
    // Launch the bridge script using PythonShell
    pythonProcess = new PythonShell('backend/bridge.py', {
        mode: 'json',
        pythonOptions: ['-u'], // -u ensures unbuffered output for real-time communication
    });

    // Listen for JSON messages from Python and forward them to the UI
    pythonProcess.on('message', (message) => {
        if (mainWindow) {
            mainWindow.webContents.send('python-data', message);
        }
    });

    // Log any Python errors to the system console for debugging
    pythonProcess.on('stderr', (stderr) => {
        console.error('Python Bridge Error:', stderr);
    });
}

/**
 * IPC Communication handler:
 * Receives commands from the renderer (UI) and forwards them to the Python process.
 */
ipcMain.on('to-python', (event, args) => {
    if (pythonProcess) {
        pythonProcess.send(args);
    }
});

/**
 * Application Lifecycle Management
 */

// Start Python and create window once Electron is ready
app.whenReady().then(() => {
    startPython();
    createWindow();

    app.on('activate', function () {
        // On macOS, re-create the window when the dock icon is clicked if no windows are open
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

// Clean up: Ensure Python process is closed when the application quits
app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        if (pythonProcess) pythonProcess.end();
        app.quit();
    }
});
