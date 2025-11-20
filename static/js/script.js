// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
  // --- DOM nodes (robust selectors)
  const uploadBox = document.querySelector('.upload-box');
  const fileInput = document.getElementById('videoUpload');
  const uploadForm = document.getElementById('uploadForm');
  const previewContainer = document.getElementById('previewContainer');
  const previewVideo = document.getElementById('previewVideo');
  const previewName = document.getElementById('previewName');

  const analysisControls = document.getElementById('analysisControls');
  const analyzeHeatBtn = document.getElementById('analyzeHeatBtn');
  const analyzeTrajBtn = document.getElementById('analyzeTrajBtn');
  const analysisStatus = document.getElementById('analysisStatus');
  const analysisResults = document.getElementById('analysisResults');

  const body = document.body;
  const darkModeToggle = document.getElementById('dark-mode-toggle');

  // safety: bail if critical nodes missing and print diagnostics
  if (!fileInput || !uploadBox || !previewContainer || !analysisControls) {
    console.error('Missing one or more required DOM nodes. Check IDs/classes. Found:',
      { fileInput: !!fileInput, uploadBox: !!uploadBox, previewContainer: !!previewContainer, analysisControls: !!analysisControls });
    return;
  }

  // Helper: show/hide controls
  function showAnalysisControls() {
    analysisControls.style.display = 'flex';
    analysisControls.style.flexDirection = 'column';
    analysisControls.style.gap = '12px';
  }
  function hideAnalysisControls() {
    analysisControls.style.display = 'none';
  }

  // Initialize theme from localStorage on page load
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    body.classList.add('dark-mode');
    darkModeToggle.textContent = '☀️'; // Sun to switch to light
  } else {
    body.classList.remove('dark-mode'); // Ensure no dark class if light or unset
    darkModeToggle.textContent = '🌙'; // Moon to switch to dark
    if (savedTheme !== 'light') {
      localStorage.setItem('theme', 'light'); // Optional: Set default if nothing saved
    }
  }
  // Toggle event listener (your original code is fine here)
  darkModeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-mode');
    // Save the theme preference to localStorage
    if (body.classList.contains('dark-mode')) {
      localStorage.setItem('theme', 'dark');
      darkModeToggle.textContent = '☀️';
    } else {
      localStorage.setItem('theme', 'light');
      darkModeToggle.textContent = '🌙';
    }
  });
  function setAnalysisState(running, message) {
    if (running) {
      analyzeHeatBtn.disabled = true;
      analyzeTrajBtn.disabled = true;
      analysisStatus.textContent = message || 'Processing...';
    } else {
      analyzeHeatBtn.disabled = false;
      analyzeTrajBtn.disabled = false;
      analysisStatus.textContent = message || '';
    }
  }

  // Preview display
  function showPreviewFile(file) {
    try {
      const url = URL.createObjectURL(file);
      previewVideo.src = url;
      previewVideo.load();
      previewContainer.style.display = 'flex';
      previewName.textContent = file.name || 'Selected video';
      showAnalysisControls();
      console.log('Preview shown for file:', file.name);
      analysisControls.style.display = 'flex';
    } catch (err) {
      console.error('Error showing preview:', err);
    }
  }
  function showPreviewFromServer(url) {
    previewVideo.src = url;
    previewVideo.load();
    previewContainer.style.display = 'flex';
    previewName.textContent = 'sample.mp4 (server)';
    showAnalysisControls();
    console.log('Preview shown for server sample:', url);
  }
  function hidePreview() {
    try {
      previewVideo.pause();
      previewVideo.src = '';
      previewContainer.style.display = 'none';
      analysisControls.style.display = 'none';
      previewName.textContent = '';
      hideAnalysisControls();
    } catch (e) { }
  }

  // Drag & drop events
  uploadBox.addEventListener('dragover', (e) => { e.preventDefault(); uploadBox.classList.add('dragover'); });
  uploadBox.addEventListener('dragleave', (e) => { e.preventDefault(); uploadBox.classList.remove('dragover'); });
  uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      fileInput.files = files;               // attach to input so form submission includes it
      showPreviewFile(files[0]);
    }
  });

  // when user picks file via picker
  fileInput.addEventListener('change', (e) => {
    if (fileInput.files && fileInput.files[0]) {
      showPreviewFile(fileInput.files[0]);
    } else {
      hidePreview();
    }
  });

  // Optional: intercept form submit to upload via fetch (AJAX) so user doesn't lose preview
  // If you prefer to keep default full-form submit & reload, you may remove this block.
  if (uploadForm) {
    uploadForm.addEventListener('submit', async (ev) => {
      // If you want ajax upload and stay on page, uncomment below:
      ev.preventDefault();
      if (!fileInput.files || !fileInput.files[0]) {
        alert('Please select a video first.');
        return;
      }
      const formData = new FormData();
      formData.append('video', fileInput.files[0]);

      try {
        setAnalysisState(true, 'Uploading...');
        const resp = await fetch(uploadForm.action, { method: 'POST', body: formData });
        // after upload, server redirects normally; we handle both response types:
        if (resp.redirected) {
          // if server redirected (typical when using flash + redirect), follow the redirect
          window.location.href = resp.url;
          return;
        }
        const text = await resp.text();
        console.log('Upload response:', text);
        // run a check to load server sample if uploaded successfully
        await checkSampleExists();
      } catch (err) {
        console.error('Upload failed', err);
        alert('Upload failed: ' + err.message);
      } finally {
        setAnalysisState(false, '');
      }
    });
  }

  // Check if sample exists on server and show controls on load
  async function checkSampleExists() {
    try {
      const res = await fetch('/sample_exists', { cache: 'no-store' });
      if (!res.ok) {
        console.warn('/sample_exists returned', res.status);
        return;
      }
      const j = await res.json();
      if (j.exists && j.url) {
        showPreviewFromServer(j.url);
      } else {
        console.log('No server sample found');
      }
    } catch (err) {
      console.warn('checkSampleExists error', err);
    }
  }
  // Call once on load
  //checkSampleExists();

  // Analysis endpoints
  async function runAnalysis(endpoint, friendlyName) {
    setAnalysisState(true, `Starting ${friendlyName}...`);
    analysisResults.innerHTML = ''; // clear previous results
    try {
      const resp = await fetch(endpoint, { method: 'POST' });
      const json = await resp.json();
      if (resp.ok && json.status === 'ok') {
        setAnalysisState(false, `${friendlyName} complete — ${json.message || 'results ready'}.`);
        // show results inline
        const urls = json.result_urls || (json.result_url ? [json.result_url] : []);
        if (urls.length) {
          urls.forEach(url => {
            const wrapper = document.createElement('div');
            wrapper.className = 'result-wrap';
            const img = document.createElement('img');
            img.src = url;
            img.alt = friendlyName + ' result';
            img.loading = 'lazy';
            wrapper.appendChild(img);

            // add download button
            const a = document.createElement('a');
            a.href = url;
            a.download = url.split('/').pop();
            a.textContent = 'Download';
            a.className = 'result-download';
            wrapper.appendChild(a);

            analysisResults.appendChild(wrapper);
          });
        } else {
          // No result urls returned
          const msg = document.createElement('div');
          msg.textContent = 'No result images returned by server.';
          analysisResults.appendChild(msg);
        }
      } else {
        setAnalysisState(false, `Error: ${json.message || 'analysis failed'}`);
      }
    } catch (err) {
      console.error('Analysis request failed', err);
      setAnalysisState(false, `Request failed: ${err.message}`);
    }
  }

  // wire buttons
  analyzeHeatBtn.addEventListener('click', () => runAnalysis('/heatwagon', 'Heatmap & Wagon Wheel Analysis'));
  analyzeTrajBtn.addEventListener('click', () => runAnalysis('/analyze/trajectory', 'Trajectory & On-field Detection'));

  function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
  }

  function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
  }
  document.getElementById('loading_spinner').addEventListener('click', function (event) {
    showLoading();
  });

  //load
  const symbols = ["·", "✢", "✳", "✶", "✻", "✽"];
const words = [
  "Accomplishing",
  "Actioning",
  "Actualizing",
  "Baking",
  "Booping",
  "Brewing",
  "Calculating",
  "Cerebrating",
  "Channelling",
  "Churning",
  "Clauding",
  "Coalescing",
  "Cogitating",
  "Computing",
  "Combobulating",
  "Concocting",
  "Considering",
  "Contemplating",
  "Cooking",
  "Crafting",
  "Creating",
  "Crunching",
  "Deciphering",
  "Deliberating",
  "Determining",
  "Discombobulating",
  "Doing",
  "Effecting",
  "Elucidating",
  "Enchanting",
  "Envisioning",
  "Finagling",
  "Flibbertigibbeting",
  "Forging",
  "Forming",
  "Frolicking",
  "Generating",
  "Germinating",
  "Hatching",
  "Herding",
  "Honking",
  "Ideating",
  "Imagining",
  "Incubating",
  "Inferring",
  "Manifesting",
  "Marinating",
  "Meandering",
  "Moseying",
  "Mulling",
  "Mustering",
  "Musing",
  "Noodling",
  "Percolating",
  "Perusing",
  "Philosophising",
  "Pontificating",
  "Pondering",
  "Processing",
  "Puttering",
  "Puzzling",
  "Reticulating",
  "Ruminating",
  "Scheming",
  "Schlepping",
  "Shimmying",
  "Simmering",
  "Smooshing",
  "Spelunking",
  "Spinning",
  "Stewing",
  "Sussing",
  "Synthesizing",
  "Thinking",
  "Tinkering",
  "Transmuting",
  "Unfurling",
  "Unravelling",
  "Vibing",
  "Wandering",
  "Whirring",
  "Wibbling",
  "Working",
  "Wrangling"
];

document.addEventListener("DOMContentLoaded", function () {
  const wordElement = document.getElementById("word");

  function updateWord() {
    let randomIndex = Math.floor(Math.random() * words.length);
    wordElement.textContent = words[randomIndex] + "…";
  }
  updateWord();
  setInterval(function () {
    updateWord();
  }, 10000); // Update the symbol and word every 10 seconds
});

document.addEventListener("DOMContentLoaded", function () {
  const symbolElement = document.getElementById("symbol");
  let symbolIndex = 0;
  let directionUp = true;

  function updateSymbol() {
    symbolElement.textContent = symbols[symbolIndex];

    if (symbolIndex >= symbols.length - 1) {
      directionUp = false;
    } else if (symbolIndex <= 0) {
      directionUp = true;
    }

    if (directionUp) {
      symbolIndex++;
    } else {
      symbolIndex = symbolIndex - 1;
    }
  }
  updateSymbol();
  setInterval(updateSymbol, 250); // Update the symbol every quarter-second (250 milliseconds)
});


});
