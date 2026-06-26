const { app, BrowserWindow, shell, ipcMain, nativeTheme } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow = null;
let splashWindow = null;
let pythonProc = null;
const PORT = 8077;
const URL = `http://127.0.0.1:${PORT}`;

function startBackend() {
    return new Promise((resolve) => {
        const cwd = path.join(__dirname, '..');

        // 检测是否为打包环境（electron-builder 打包后 app.isPackaged 为 true）
        const isPackaged = app.isPackaged;

        if (isPackaged) {
            // 生产模式：启动打包后的 Python 后端可执行文件
            const serverPath = path.join(process.resourcesPath, 'server', 'AI Arena Server.exe');
            pythonProc = spawn(serverPath, [], {
                cwd: path.dirname(serverPath),
                stdio: ['pipe', 'pipe', 'pipe'],
                windowsHide: true,
            });
        } else {
            // 开发模式：使用系统 Python 启动 uvicorn
            const py = process.platform === 'win32' ? 'python' : 'python3';
            pythonProc = spawn(py, ['-m', 'uvicorn', 'src.main:app', '--host', '127.0.0.1', '--port', String(PORT)], {
                cwd,
                stdio: ['pipe', 'pipe', 'pipe'],
                shell: true,
                windowsHide: true,
            });
        }

        pythonProc.stdout.on('data', (d) => {
            if (d.toString().includes('Uvicorn running')) resolve();
        });
        pythonProc.stderr.on('data', (d) => {
            if (d.toString().includes('Uvicorn running')) resolve();
        });
        pythonProc.on('error', (err) => {
            console.error('后端启动失败:', err);
            resolve();
        });
        setTimeout(resolve, 8000);
    });
}

async function waitForBackend(max = 40, interval = 500) {
    for (let i = 0; i < max; i++) {
        try {
            const r = await fetch(URL);
            if (r.ok) return true;
        } catch (_) {}
        await new Promise(r => setTimeout(r, interval));
    }
    return false;
}

function createSplash() {
    splashWindow = new BrowserWindow({
        width: 420,
        height: 340,
        frame: false,
        transparent: true,
        resizable: false,
        skipTaskbar: true,
        alwaysOnTop: true,
        backgroundColor: '#09090b',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
    });
    splashWindow.loadFile(path.join(__dirname, 'splash.html'));
    splashWindow.center();
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 820,
        minWidth: 960,
        minHeight: 640,
        title: 'AI Arena',
        show: false,
        frame: false,
        transparent: true,
        titleBarStyle: 'hidden',
        titleBarOverlay: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
        },
    });

    mainWindow.loadURL(URL);

    mainWindow.once('ready-to-show', () => {
        if (splashWindow) {
            splashWindow.close();
            splashWindow = null;
        }
        mainWindow.show();
    });

    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    mainWindow.on('closed', () => { mainWindow = null; });
}

// 窗口控制 IPC
ipcMain.on('window-minimize', () => {
    mainWindow?.minimize();
});
ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
        mainWindow.unmaximize();
    } else {
        mainWindow?.maximize();
    }
});
ipcMain.on('window-close', () => {
    mainWindow?.close();
});

// 更新标题栏 overlay 颜色（亮色/暗色主题切换）
ipcMain.on('update-titlebar-color', (event, { color, symbolColor }) => {
    if (mainWindow) {
        mainWindow.setTitleBarOverlay({
            color: color,
            symbolColor: symbolColor,
            height: 36,
        });
    }
});

app.whenReady().then(async () => {
    createSplash();
    await startBackend();
    await waitForBackend();
    createWindow();
});

app.on('window-all-closed', () => {
    if (splashWindow) { splashWindow.close(); splashWindow = null; }
    if (pythonProc) pythonProc.kill();
    app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
