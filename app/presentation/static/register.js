document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const tenant_name = document.getElementById('tenant_name').value;
    const admin_name = document.getElementById('admin_name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const msgElement = document.getElementById('register-message');
    
    try {
        const response = await fetch('/api/v1/admin/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tenant_name: tenant_name,
                admin_name: admin_name,
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            msgElement.style.color = 'green';
            msgElement.textContent = '註冊成功！3秒後導向登入頁面...';
            setTimeout(() => {
                window.location.href = '/admin/login';
            }, 3000);
        } else {
            msgElement.style.color = '#f44336';
            msgElement.textContent = data.detail || '註冊失敗';
        }
    } catch (error) {
        msgElement.style.color = '#f44336';
        msgElement.textContent = '伺服器錯誤，請稍後再試';
    }
});
