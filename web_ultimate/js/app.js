// Ultimate AI Video System - Main JavaScript
// 小影AI終極版 - 主JavaScript邏輯

// 全局變量
let currentUser = 'admin';
let ws = null;
let uploadedFiles = {
    image: null,
    audio: null,
    referenceAudio: null
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    setupWebSocket();
    loadSystemStatus();
});

function initializeApp() {
    console.log('🚀 Initializing Ultimate AI Video System...');
    
    // 加載用戶選擇
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = savedUser;
        document.getElementById('userSelect').value = savedUser;
    }
}

function setupEventListeners() {
    // 用戶選擇
    document.getElementById('userSelect').addEventListener('change', (e) => {
        currentUser = e.target.value;
        localStorage.setItem('currentUser', currentUser);
        console.log('User changed to:', currentUser);
    });

    // Tab切換
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            switchTab(tabName);
        });
    });

    // 文件上傳 - 數字人圖片
    setupFileUpload('imageUpload', 'imageFile', 'image', 'imagePreview');
    
    // 文件上傳 - 數字人音頻
    setupFileUpload('audioUpload', 'audioFile', 'audio', 'audioPreview');
    
    // 文件上傳 - 聲音克隆參考音頻
    setupFileUpload('referenceAudioUpload', 'referenceAudioFile', 'referenceAudio', 'referenceAudioPreview');

    // 數字人生成按鈕
    document.getElementById('generateDigitalHuman').addEventListener('click', generateDigitalHuman);

    // 聲音克隆按鈕
    document.getElementById('generateVoice').addEventListener('click', generateVoice);

    // 聲音文本字數統計
    document.getElementById('voiceText').addEventListener('input', (e) => {
        const count = e.target.value.length;
        document.getElementById('charCount').textContent = count;
    });

    // 速度滑桿
    document.getElementById('voiceSpeed').addEventListener('input', (e) => {
        document.getElementById('speedValue').textContent = e.target.value + 'x';
    });
}

function setupFileUpload(areaId, inputId, type, previewId) {
    const area = document.getElementById(areaId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    // 點擊上傳
    area.addEventListener('click', () => {
        input.click();
    });

    // 拖拽上傳
    area.addEventListener('dragover', (e) => {
        e.preventDefault();
        area.classList.add('dragover');
    });

    area.addEventListener('dragleave', () => {
        area.classList.remove('dragover');
    });

    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file, type, preview);
        }
    });

    // 文件選擇
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file, type, preview);
        }
    });
}

function handleFileUpload(file, type, previewElement) {
    uploadedFiles[type] = file;
    console.log(`File uploaded for ${type}:`, file.name);

    const preview = document.getElementById(previewElement);
    
    if (type === 'image') {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = `<p>✅ ${file.name}</p>`;
    }
}

function switchTab(tabName) {
    // 移除所有active類
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // 添加active類到選中的tab
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/status`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('✅ WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'status_update') {
            updateSystemStatus(data);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 5s...');
        setTimeout(setupWebSocket, 5000);
    };
}

function updateSystemStatus(data) {
    // 更新GPU狀態
    if (data.gpus && data.gpus.length > 0) {
        const avgUtilization = data.gpus.reduce((sum, gpu) => sum + gpu.utilization, 0) / data.gpus.length;
        document.getElementById('gpuStatus').textContent = `${avgUtilization.toFixed(1)}%`;
    }

    // 更新記憶體狀態
    if (data.memory) {
        document.getElementById('memoryStatus').textContent = 
            `${data.memory.used_gb} / ${(data.memory.used_gb + data.memory.available_gb).toFixed(0)} GB (${data.memory.percent}%)`;
    }
}

async function loadSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        document.getElementById('modelStatus').textContent = `${data.cached_models} 個模型`;
        
        console.log('System status loaded:', data);
    } catch (error) {
        console.error('Failed to load system status:', error);
    }
}

async function generateDigitalHuman() {
    if (!uploadedFiles.image || !uploadedFiles.audio) {
        alert('請先上傳照片和語音文件！');
        return;
    }

    const button = document.getElementById('generateDigitalHuman');
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const resultPreview = document.getElementById('resultPreview');

    // 禁用按鈕
    button.disabled = true;
    button.textContent = '處理中...';

    // 顯示進度條
    progressBar.style.display = 'block';
    resultPreview.style.display = 'none';

    // 準備FormData
    const formData = new FormData();
    formData.append('image', uploadedFiles.image);
    formData.append('audio', uploadedFiles.audio);

    // 準備請求數據
    const requestData = {
        user_id: currentUser,
        resolution: document.getElementById('resolution').value,
        fps: parseInt(document.getElementById('fps').value),
        quality: document.getElementById('quality').value,
        enable_blink: document.getElementById('enableBlink').checked,
        enable_micro_expressions: document.getElementById('enableMicro').checked,
        enable_breathing: document.getElementById('enableBreathing').checked
    };

    // 將請求數據添加為JSON字符串
    for (const [key, value] of Object.entries(requestData)) {
        formData.append(key, value);
    }

    try {
        // 模擬進度
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
            progressText.textContent = `處理中... ${progress.toFixed(0)}%`;
        }, 500);

        const response = await fetch('/api/digital-human/generate', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);

        if (!response.ok) {
            throw new Error('生成失敗');
        }

        const result = await response.json();

        // 完成進度
        progressFill.style.width = '100%';
        progressText.textContent = '處理完成！';

        // 顯示結果
        setTimeout(() => {
            progressBar.style.display = 'none';
            resultPreview.style.display = 'block';
            
            document.getElementById('resultVideo').src = result.video_url;
            document.getElementById('processingTime').textContent = result.processing_time.toFixed(2) + '秒';
            document.getElementById('resultResolution').textContent = result.resolution.join('x');
            document.getElementById('resultFPS').textContent = result.fps + ' FPS';
        }, 1000);

    } catch (error) {
        alert('生成失敗：' + error.message);
        progressBar.style.display = 'none';
    } finally {
        button.disabled = false;
        button.textContent = '🎬 開始生成';
    }
}

async function generateVoice() {
    if (!uploadedFiles.referenceAudio) {
        alert('請先上傳參考音頻！');
        return;
    }

    const text = document.getElementById('voiceText').value;
    if (!text) {
        alert('請輸入要合成的文本！');
        return;
    }

    const button = document.getElementById('generateVoice');
    const progressBar = document.getElementById('voiceProgressBar');
    const progressFill = document.getElementById('voiceProgressFill');
    const progressText = document.getElementById('voiceProgressText');
    const resultPreview = document.getElementById('voiceResultPreview');

    button.disabled = true;
    button.textContent = '處理中...';
    progressBar.style.display = 'block';
    resultPreview.style.display = 'none';

    const formData = new FormData();
    formData.append('reference_audio', uploadedFiles.referenceAudio);

    const requestData = {
        user_id: currentUser,
        text: text,
        model: document.getElementById('voiceModel').value,
        language: document.getElementById('voiceLanguage').value,
        emotion: document.getElementById('voiceEmotion').value,
        speed: parseFloat(document.getElementById('voiceSpeed').value)
    };

    for (const [key, value] of Object.entries(requestData)) {
        formData.append(key, value);
    }

    try {
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
            progressText.textContent = `處理中... ${progress.toFixed(0)}%`;
        }, 300);

        const response = await fetch('/api/voice-clone/generate', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);

        if (!response.ok) {
            throw new Error('克隆失敗');
        }

        const result = await response.json();

        progressFill.style.width = '100%';
        progressText.textContent = '處理完成！';

        setTimeout(() => {
            progressBar.style.display = 'none';
            resultPreview.style.display = 'block';
            
            document.getElementById('resultAudio').src = result.audio_url;
            document.getElementById('voiceProcessingTime').textContent = result.processing_time.toFixed(2) + '秒';
            document.getElementById('resultDuration').textContent = result.duration.toFixed(2) + '秒';
        }, 1000);

    } catch (error) {
        alert('克隆失敗：' + error.message);
        progressBar.style.display = 'none';
    } finally {
        button.disabled = false;
        button.textContent = '🎤 克隆聲音';
    }
}

function quickGenerate(mode) {
    alert(`快速模式：${mode} 即將推出！`);
    console.log('Quick generate:', mode);
}

// 導出函數供HTML使用
window.quickGenerate = quickGenerate;
