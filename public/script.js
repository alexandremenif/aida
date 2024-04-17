$(document).ready(function() {
  const mainArea = $("#mainArea");
  const modal = $('.ui.basic.modal');
  const textInput = $("#textInput");
  const fabBtn = $("#fabBtn");
  const submitBtn = $("#submitBtn");

  // Show modal on FAB click
  fabBtn.click(function() {
    modal.modal('show');
  });

  // Submit logic
  function submitRequest() {
    const userText = textInput.val();
    modal.modal('hide');
    mainArea.html('<div class="ui huge active centered inline loader"></div>');

    $.ajax({
      type: "POST",
      url: "/query",
      data: userText,
      contentType: "text/plain",
      success: function(response) {
        mainArea.html(response);
      },
      error: function() {
        mainArea.html('<p>Error processing your request. Please try again.</p>');
      }
    });
  }

  // Handle submit button click
  submitBtn.click(function() {
    submitRequest();
  });

  // Handle enter key in text area
  textInput.keypress(function(e) {
    if (e.which === 13) {
      e.preventDefault(); // Prevent default enter behavior
      submitRequest();
    }
  });
});
