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

// --- Auth Tab Switcher ---
function switchTab(tab) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    if (tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        tabLogin.classList.remove('active');
        tabRegister.classList.add('active');
    }
    // Clear alerts
    setAlert('login-alert', '', '');
    setAlert('register-alert', '', '');
}

function setAlert(id, message, type) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!message) { el.style.display = 'none'; el.textContent = ''; return; }
    el.textContent = message;
    el.className = `auth-alert ${type}`;
    el.style.display = 'block';
}

async function login() {
    const user = document.getElementById('login-username').value.trim();
    const pass = document.getElementById('login-password').value;
    if (!user || !pass) { setAlert('login-alert', 'Please fill in all fields.', 'error'); return; }

    const btn = document.getElementById('btn-login');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';
    
    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Incorrect username or password');
        }
        
        const data = await res.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        showDashboard();
    } catch (e) {
        setAlert('login-alert', e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Access Cluster';
    }
}

async function register() {
    const username = document.getElementById('reg-username').value.trim();
    const fullname = document.getElementById('reg-fullname').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm  = document.getElementById('reg-password-confirm').value;

    if (!username || !password) { setAlert('register-alert', 'Username and password are required.', 'error'); return; }
    if (password !== confirm)   { setAlert('register-alert', 'Passwords do not match.', 'error'); return; }
    if (password.length < 4)    { setAlert('register-alert', 'Password must be at least 4 characters.', 'error'); return; }

    const btn = document.getElementById('btn-register');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';

    try {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, full_name: fullname || null })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Registration failed');
        }

        // Auto-fill login and switch tab
        document.getElementById('login-username').value = username;
        document.getElementById('login-password').value = '';
        switchTab('login');
        setAlert('login-alert', `Account "${username}" created! Please sign in.`, 'success');

        // Clear register fields
        ['reg-username','reg-fullname','reg-password','reg-password-confirm'].forEach(id => {
            document.getElementById(id).value = '';
        });
    } catch (e) {
        setAlert('register-alert', e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
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

        // Fetch node topology to know where to send each chunk
        // Works for 1-node, 3-node, or any N-node setup
        uploadStatus.innerText = "Fetching cluster topology...";
        const topoRes = await fetch(`${API_BASE}/api/nodes/topology`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const topology = topoRes.ok ? await topoRes.json() : {};
        
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
            
            // Route chunk to the correct node using topology from API
            // Fallback to current host (same node) if topology not available
            let targetUrl;
            if (topology[placement.primary_node]) {
                let { host, port } = topology[placement.primary_node];
                
                // Smart rewrite for local docker-compose testing vs Real LAN deployment
                // If the backend returns "node1", "node2" AND the browser is running on localhost,
                // we rewrite it to 8001, 8002 so the browser can reach it outside the docker network.
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    if (host.startsWith('node')) {
                        const nMatch = host.replace('node', '');
                        if (!isNaN(nMatch)) {
                            host = 'localhost';
                            port = 8000 + parseInt(nMatch);
                        }
                    }
                }
                
                targetUrl = `http://${host}:${port}/api/chunks/upload`;
            } else {
                // Fallback: send to current gateway (works for 1-node setup)
                targetUrl = `${API_BASE}/api/chunks/upload`;
            }
            
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
