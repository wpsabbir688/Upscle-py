// ===== Image Zoom Overlay =====
const overlay = document.getElementById('overlay');
const overlayImg = overlay.querySelector('img');

function zoomImage(img) {
  overlayImg.src = img.src;
  overlay.style.display = 'flex';
}

function closeZoom() {
  overlay.style.display = 'none';
  overlayImg.src = '';
}

document.addEventListener('keydown', (e) => {
  if (e.key === "Escape") closeZoom();
});

// ===== Toggle Upload Option (Single vs Folder) =====
function toggleUploadOption() {
  const selectedType = document.querySelector('input[name="uploadType"]:checked').value;
  document.getElementById('singleUpload').style.display = selectedType === 'single' ? 'block' : 'none';
  document.getElementById('folderUpload').style.display = selectedType === 'folder' ? 'block' : 'none';
}

// ===== Real Upload Progress with AJAX =====
document.getElementById('uploadForm').addEventListener('submit', function(e) {
  e.preventDefault();  // Prevent traditional form submit

  const form = e.target;
  const formData = new FormData(form);
  const xhr = new XMLHttpRequest();

  const progressWrapper = document.getElementById('progressWrapper');
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');

  progressWrapper.style.display = 'block';
  progressBar.value = 0;
  progressText.textContent = '0%';

  xhr.upload.addEventListener("progress", function(e) {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      progressBar.value = percent;
      progressText.textContent = percent + "%";
    }
  });

  xhr.onload = function () {
    if (xhr.status === 200) {
      // Replace page content with new HTML from response
      document.open();
      document.write(xhr.responseText);
      document.close();
    } else {
      alert("❌ Upload failed. Please try again.");
    }
  };

  xhr.onerror = function () {
    alert("❌ Error occurred during upload.");
  };

  xhr.open("POST", form.action, true);
  xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");  // For Flask to detect AJAX
  xhr.send(formData);
});
