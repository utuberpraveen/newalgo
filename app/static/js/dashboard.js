// app/static/js/dashboard.js

function loadSection(section) {
    const contentArea = document.getElementById('content-area');

    switch (section) {
        case 'dashboard':
            contentArea.innerHTML = '<h2>Dashboard Overview</h2><p>Display account summary here.</p>';
            break;
        case 'excel_upload':
            window.location.href = uploadStockDataUrl;
            break;
        case 'view_stock_data':
            window.location.href = viewStockDataUrl;
            break;
        case 'bot_control':
            contentArea.innerHTML = '<h2>Bot Control</h2><p>Start or stop the bot here.</p>';
            break;
        case 'trade_history':
            contentArea.innerHTML = '<h2>Trade History</h2><p>Display trade history here.</p>';
            break;
        default:
            contentArea.innerHTML = '<h2>Welcome</h2><p>Select an option from the sidebar.</p>';
    }
}
