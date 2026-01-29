/**
 * preload.js - Electron Preload Script
 * 
 * This script acts as a safe gated bridge between the Electron main process 
 * (which has full system access) and the renderer process (the UI window).
 * It uses contextBridge to expose only specific allowed IPC channels.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    /**
     * send: Forwards a command from the UI to the main process ('to-python' channel).
     */
    send: (channel, data) => {
        // Only allow strictly whitelisted channels for security
        let validChannels = ['to-python'];
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        }
    },

    /**
     * receive: Listens for data coming from the Python backend via the main process.
     */
    receive: (channel, func) => {
        let validChannels = ['python-data'];
        if (validChannels.includes(channel)) {
            // Strip the event object from the args list to prevent exposing the sender object
            ipcRenderer.on(channel, (event, ...args) => func(...args));
        }
    }
});
