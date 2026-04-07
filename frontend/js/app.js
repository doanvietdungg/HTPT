const API_BASE = ""; // Relative if served from same origin

// State
let token = localStorage.getItem('token');
let placementNodesCache = {}; // Cache node allocations

// DOM Elements
const authView = document.getElementById('auth-view');
const dashboardView = document.getElementById('dashboard-view');
const fileList = document.getElementById('file-list');
const dropZone = document.getElementById('drop-zone');
const uploadProgressContainer = document.getElementById('upload-progress-container');
const uploadProgress = document.getElementById('upload-progress');
const uploadStatus = document.getElementById('upload-status');
const placementMap = document.getElementById('placement-map');
const uploadFilename = document.getElementById('upload-filename');

// Initialize
function init() {
    if (token) {
        showDashboard();
    } else {
        showAuth();
    }
}

function showAuth() {
    authView.classList.add('active');
    dashboardView.classList.remove('active');
}

function showDashboard() {
    authView.classList.remove('active');
    dashboardView.classList.add('active');
    fetchFileList();
}

async function login() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    
    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        
        if (!res.ok) throw new Error('Login failed');
        
        const data = await res.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        showDashboard();
    } catch (e) {
        alert(e.message);
    }
}

function logout() {
    token = null;
    localStorage.removeItem('token');
    showAuth();
}

async function fetchFileList() {
    try {
        const res = await fetch(`${API_BASE}/api/files/list`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch files');
        
        const files = await res.json();
        renderFiles(files);
    } catch (e) {
        if(e.message.includes('401')) logout();
        console.error(e);
    }
}

function renderFiles(files) {
    fileList.innerHTML = '';
    if(files.length === 0) {
        fileList.innerHTML = '<p style="color: #94a3b8; text-align:center;">No files found in Vault.</p>';
        return;
    }
    
    files.forEach(f => {
        const sizeMB = (f.size_bytes / (1024*1024)).toFixed(2);
        const icon = getFileIcon(f.file_name);
        
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <div class="file-info">
                <i class="fas ${icon} file-icon"></i>
                <div>
                    <div class="file-name">${f.file_name}</div>
                    <div class="file-meta">${sizeMB} MB • Origin: ${f.created_at ? f.created_at.substring(0,10) : 'Now'}</div>
                </div>
            </div>
            <div class="file-actions">
                <a href="${API_BASE}/api/files/s3/${f.file_id}" target="_blank" title="View Stream (S3)">
                    <i class="fas fa-external-link-alt action-icon"></i>
                </a>
            </div>
        `;
        fileList.appendChild(div);
    });
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    if(['mp4','avi','mkv'].includes(ext)) return 'fa-file-video';
    if(['jpg','png','jpeg','gif'].includes(ext)) return 'fa-file-image';
    if(['pdf'].includes(ext)) return 'fa-file-pdf';
    return 'fa-file-alt';
}

// ----------------------------------------------------
// PIPELINE UPLOAD IMPLEMENTATION
// ----------------------------------------------------
async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // UI Reset
    dropZone.style.display = 'none';
    uploadProgressContainer.style.display = 'block';
    uploadFilename.innerText = `Uploading: ${file.name}`;
    uploadProgress.style.width = '0%';
    placementMap.innerHTML = '';
    
    try {
        // Step 1: Init Upload (Get Block Map)
        uploadStatus.innerText = "Requesting Placement Plan from NameNode...";
        const initRes = await fetch(`${API_BASE}/api/files/upload/init`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                file_name: file.name,
                size_bytes: file.size,
                logical_path: "/"
            })
        });
        
        if (!initRes.ok) throw new Error("Initialization failed");
        const plan = await initRes.json();
        
        // Render initial map UI
        plan.placement_plan.forEach(p => {
            const el = document.createElement('div');
            el.id = `chunk-badge-${p.chunk_index}`;
            el.className = 'map-badge';
            el.innerHTML = `CK_${p.chunk_index} ➔ ${p.primary_node}`;
            placementMap.appendChild(el);
        });
        
        // Step 2: Slice and Upload Chunks sequentially 
        // (In reality could be parallel, but sequential here to show precise pipeline progress safely)
        for (let i = 0; i < plan.total_chunks; i++) {
            const placement = plan.placement_plan.find(x => x.chunk_index === i);
            const startByte = i * plan.chunk_size;
            const endByte = Math.min(startByte + plan.chunk_size, file.size);
            const blob = file.slice(startByte, endByte);
            
            uploadStatus.innerText = `Pipelining Chunk ${i+1}/${plan.total_chunks} to ${placement.primary_node}...`;
            
            const formData = new FormData();
            formData.append('file_id', plan.file_id);
            formData.append('chunk_index', i);
            if(placement.secondary_nodes.length > 0) {
                formData.append('secondary_nodes', placement.secondary_nodes.join(','));
            }
            formData.append('file', blob, file.name);
            
            // Map node1 -> 8001, node2 -> 8002, node3 -> 8003
            const nodeNum = placement.primary_node.replace('node', '');
            const targetPort = 8000 + parseInt(nodeNum);
            const targetUrl = `http://localhost:${targetPort}/api/chunks/upload`;
            
            const chunkRes = await fetch(targetUrl, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            
            if(!chunkRes.ok) throw new Error(`Chunk ${i} upload failed`);
            
            // Update UI
            const percent = Math.round(((i + 1) / plan.total_chunks) * 100);
            uploadProgress.style.width = `${percent}%`;
            document.getElementById(`chunk-badge-${i}`).classList.add('done');
        }
        
        uploadStatus.innerText = "Replication Complete! S3 Ready.";
        uploadProgress.style.width = '100%';
        
        setTimeout(() => {
            dropZone.style.display = 'block';
            uploadProgressContainer.style.display = 'none';
            fetchFileList();
        }, 2000);
        
    } catch (e) {
        uploadStatus.innerText = "Error: " + e.message;
        uploadStatus.style.color = "red";
        setTimeout(() => {
            dropZone.style.display = 'block';
            uploadProgressContainer.style.display = 'none';
        }, 3000);
    }
}

async function triggerElection() {
    try {
        const res = await fetch(`${API_BASE}/api/election/start`, { method: 'POST' });
        if(res.ok) alert("Election triggered! Check docker logs.");
    } catch(e) {
        console.error(e);
    }
}

// Boot
init();
