document.getElementById('send-btn').addEventListener('click', function() {
  const inputText = document.getElementById('input-text').value;
  const contentWrapper = document.getElementById('content-wrapper');
  contentWrapper.innerHTML = '<div class="spinner"></div>'; // Show spinner

  fetch('/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'text/plain',
    },
    body: inputText,
  })
    .then(response => response.text())
    .then(htmlContent => {
      contentWrapper.innerHTML = htmlContent; // Replace spinner with HTML content
    })
    .catch(error => {
      contentWrapper.innerHTML = 'Error: ' + error; // Replace spinner with error message
      console.error('Error:', error)
    });
});
