document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-message');
    
    // 這裡通常會呼叫您的 API 端點，例如 /api/v1/admin/login
    // 目前我們先寫一個簡單的模擬邏輯
    if (username === 'admin' && password === 'admin123') {
        errorMsg.textContent = '';
        errorMsg.style.color = 'green';
        errorMsg.textContent = '登入成功！正在導向...';
        
        // 模擬儲存 token 並導向管理後台
        // localStorage.setItem('token', 'fake-jwt-token');
        // window.location.href = '/admin/dashboard';
    } else {
        errorMsg.textContent = '帳號或密碼錯誤';
    }
});
