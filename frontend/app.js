'use strict';

// ─── DOM references ────────────────────────────────────────────────────────────
const recordBtn            = document.getElementById('recordBtn');
const recordBtnText        = document.getElementById('recordBtnText');
const recordingStatus      = document.getElementById('recordingStatus');
const recordedAudioPlayer  = document.getElementById('recordedAudioPlayer');
const uploadArea           = document.getElementById('uploadArea');
const imageInput           = document.getElementById('imageInput');
const imagePreview         = document.getElementById('imagePreview');
const uploadHintText       = document.querySelector('.upload-hint-text');
const clearImageBtn        = document.getElementById('clearImageBtn');
const analyzeBtn           = document.getElementById('analyzeBtn');
const errorBanner          = document.getElementById('errorBanner');
const loadingSection       = document.getElementById('loadingSection');
const resultsContent       = document.getElementById('resultsContent');
const emptyState           = document.getElementById('emptyState');
const transcriptionOutput  = document.getElementById('transcriptionOutput');
const doctorResponseOutput = document.getElementById('doctorResponseOutput');
const responseAudioPlayer  = document.getElementById('responseAudioPlayer');

// ─── State ─────────────────────────────────────────────────────────────────────
let mediaRecorder    = null;
let audioChunks      = [];
let audioBlob        = null;
let droppedImageFile = null;
let isRecording      = false;

// ─── Audio recording ───────────────────────────────────────────────────────────
recordBtn.addEventListener('click', async () => {
  if (isRecording) {
    stopRecording();
  } else {
    await startRecording();
  }
});

async function startRecording() {
  try {
    const stream  = await navigator.mediaDevices.getUserMedia({ audio: true });
    const options = chooseMimeType();
    mediaRecorder  = options ? new MediaRecorder(stream, options) : new MediaRecorder(stream);
    audioChunks    = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      const mimeType = mediaRecorder.mimeType || 'audio/webm';
      audioBlob = new Blob(audioChunks, { type: mimeType });
      recordedAudioPlayer.src = URL.createObjectURL(audioBlob);
      recordedAudioPlayer.classList.remove('hidden');
      analyzeBtn.disabled = false;
      stream.getTracks().forEach((t) => t.stop());
    };

    // Collect chunks every 250 ms so we always get data on short recordings.
    mediaRecorder.start(250);
    isRecording = true;
    setRecordingUI(true);
  } catch (err) {
    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
      showError('Microphone access denied. Please allow microphone permissions in your browser and try again.');
    } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
      showError('No microphone found. Please connect a microphone and try again.');
    } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
      showError('Microphone is already in use by another application. Please close it and try again.');
    } else {
      showError(`Could not access microphone: ${err.message}`);
    }
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  isRecording = false;
  setRecordingUI(false);
}

function chooseMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
    'audio/mp4',
  ];
  for (const type of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(type)) {
      return { mimeType: type };
    }
  }
  return null;
}

function setRecordingUI(recording) {
  if (recording) {
    recordBtnText.textContent = 'Stop Recording';
    recordBtn.querySelector('.btn-icon').textContent = '⏹';
    recordBtn.classList.add('recording');
    recordingStatus.classList.remove('hidden');
  } else {
    recordBtnText.textContent = 'Start Recording';
    recordBtn.querySelector('.btn-icon').textContent = '⏺';
    recordBtn.classList.remove('recording');
    recordingStatus.classList.add('hidden');
  }
}

// ─── Image upload ──────────────────────────────────────────────────────────────
imageInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) setImageFile(file);
});

clearImageBtn.addEventListener('click', () => {
  droppedImageFile     = null;
  imageInput.value     = '';
  imagePreview.src     = '';
  imagePreview.classList.add('hidden');
  clearImageBtn.classList.add('hidden');
  if (uploadHintText) uploadHintText.classList.remove('hidden');
});

// Drag-and-drop
uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadArea.classList.add('drag-over');
});
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadArea.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) setImageFile(file);
});

// Allow keyboard activation of the upload area
uploadArea.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    imageInput.click();
  }
});

function setImageFile(file) {
  droppedImageFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreview.src = e.target.result;
    imagePreview.classList.remove('hidden');
    clearImageBtn.classList.remove('hidden');
    if (uploadHintText) uploadHintText.classList.add('hidden');
  };
  reader.readAsDataURL(file);
}

// ─── Analyze ───────────────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', async () => {
  if (!audioBlob) {
    showError('Please record your voice first.');
    return;
  }

  hideError();
  setAnalyzingState(true);

  const formData  = new FormData();
  const ext       = audioExtension(audioBlob.type);
  formData.append('audio', audioBlob, `recording.${ext}`);

  const imageFile = droppedImageFile || imageInput.files[0] || null;
  if (imageFile) formData.append('image', imageFile);

  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    displayResults(data);
  } catch (err) {
    showError(`Analysis failed: ${err.message}`);
    showEmptyState();
  } finally {
    setAnalyzingState(false);
  }
});

function audioExtension(mimeType) {
  const base = (mimeType || '').split(';')[0].trim();
  const map  = {
    'audio/webm': 'webm',
    'audio/ogg':  'ogg',
    'audio/mp4':  'mp4',
    'audio/mpeg': 'mp3',
    'audio/wav':  'wav',
  };
  return map[base] || 'webm';
}

// ─── UI helpers ────────────────────────────────────────────────────────────────
function displayResults(data) {
  transcriptionOutput.textContent  = data.transcription  || '(no transcription returned)';
  doctorResponseOutput.textContent = data.doctor_response || '(no response returned)';

  if (data.audio_base64) {
    responseAudioPlayer.src = `data:audio/mp3;base64,${data.audio_base64}`;
  }

  loadingSection.classList.add('hidden');
  emptyState.classList.add('hidden');
  resultsContent.classList.remove('hidden');
}

function setAnalyzingState(loading) {
  analyzeBtn.disabled = loading;
  if (loading) {
    loadingSection.classList.remove('hidden');
    resultsContent.classList.add('hidden');
    emptyState.classList.add('hidden');
  }
}

function showEmptyState() {
  loadingSection.classList.add('hidden');
  resultsContent.classList.add('hidden');
  emptyState.classList.remove('hidden');
}

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove('hidden');
}

function hideError() {
  errorBanner.classList.add('hidden');
}
