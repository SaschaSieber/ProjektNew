// static/js/scripts.js
document.getElementById("similarity-threshold").addEventListener("input", function () {
    const value = this.value;
    document.getElementById("threshold-value").innerText = `${(value * 1).toFixed(1)}`;
});
document.getElementById('shutdown-button').addEventListener('click', function() {
    fetch('/shutdown').then(() => window.close()); // Call to the shutdown function
        });

