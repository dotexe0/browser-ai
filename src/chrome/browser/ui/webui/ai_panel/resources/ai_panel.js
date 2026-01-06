document.getElementById('ping').onclick = function() {
    chrome.send('ping');
};

document.addEventListener('pong', function(event) {
    document.getElementById('output').textContent = event.detail;
});
