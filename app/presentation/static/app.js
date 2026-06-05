document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-message');
    
    try {
        const response = await fetch('/api/v1/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            errorMsg.style.color = 'green';
            errorMsg.textContent = '登入成功！正在導向...';
            
            // 儲存 JWT Token
            localStorage.setItem('admin_token', data.token);
            // 導向未來可能擴充的管理後台 Dashboard
            // window.location.href = '/admin/dashboard';
        } else {
            errorMsg.style.color = '#f44336';
            errorMsg.textContent = data.detail || '帳號或密碼錯誤';
        }
    } catch (error) {
        errorMsg.style.color = '#f44336';
        errorMsg.textContent = '伺服器連線錯誤';
    }
});
