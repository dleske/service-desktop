function initializeInfoModal(initialText) {

  console.log("initializing info modal");
  var infoModalEl = document.getElementById('infoModal');

  // create Bootstrap object around it
  var infoModal = new bootstrap.Modal(infoModalEl);
}

function showInfo(title, body) {

  // set title
  var modalTitleEl = document.getElementById('infoModalTitle');
  modalTitleEl.innerHTML = title;

  // set content
  var modalBodyEl = document.getElementById('infoModalBody');
  modalBodyEl.innerHTML = body;

  // show modal
  var modalEl = document.getElementById('infoModal');
  var modal = bootstrap.Modal.getInstance(modalEl);
  modal.show();
}
