/**
 * PolyGlot Translator - Frontend Controller
 * Robust client-side interaction with Flask backend API
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const sourceText = document.getElementById('sourceText');
    const targetText = document.getElementById('targetText');
    const sourceLanguage = document.getElementById('sourceLanguage');
    const targetLanguage = document.getElementById('targetLanguage');
    const swapLanguagesBtn = document.getElementById('swapLanguagesBtn');
    const translateBtn = document.getElementById('translateBtn');
    const translateBtnText = document.getElementById('translateBtnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const clearInputBtn = document.getElementById('clearInputBtn');
    const copyTargetBtn = document.getElementById('copyTargetBtn');
    const copyBtnText = document.getElementById('copyBtnText');
    const listenSourceBtn = document.getElementById('listenSourceBtn');
    const listenTargetBtn = document.getElementById('listenTargetBtn');
    const charCount = document.getElementById('charCount');
    const outputLoading = document.getElementById('outputLoading');
    const detectedLangBadge = document.getElementById('detectedLangBadge');
    const detectedLangText = document.getElementById('detectedLangText');
    const providerBadge = document.getElementById('providerBadge');
    const providerName = document.getElementById('providerName');
    const toastContainer = document.getElementById('toastContainer');
    const sampleChips = document.querySelectorAll('.sample-chip');

    let currentTranslation = {
        sourceText: '',
        translatedText: '',
        detectedLang: null,
        provider: ''
    };

    // Initialize character counter
    updateCharCounter();

    // Event Listeners
    sourceText.addEventListener('input', () => {
        updateCharCounter();
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl + Enter or Cmd + Enter to translate
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleTranslate();
        }
        // Alt + S to swap languages
        if (e.altKey && (e.key === 's' || e.key === 'S')) {
            e.preventDefault();
            handleSwapLanguages();
        }
    });

    translateBtn.addEventListener('click', handleTranslate);
    swapLanguagesBtn.addEventListener('click', handleSwapLanguages);
    clearInputBtn.addEventListener('click', handleClear);
    copyTargetBtn.addEventListener('click', handleCopy);
    listenSourceBtn.addEventListener('click', () => handleListen(sourceText.value, sourceLanguage.value));
    listenTargetBtn.addEventListener('click', () => handleListen(currentTranslation.translatedText, targetLanguage.value));

    // Sample chips click handler
    sampleChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const text = chip.getAttribute('data-text');
            if (text) {
                sourceText.value = text;
                updateCharCounter();
                sourceText.focus();
                handleTranslate();
            }
        });
    });

    /**
     * Updates character counter display
     */
    function updateCharCounter() {
        const count = sourceText.value.length;
        charCount.textContent = `${count.toLocaleString()} / 5,000`;
        if (count > 4800) {
            charCount.style.color = 'var(--status-error)';
        } else if (count > 4000) {
            charCount.style.color = 'var(--status-warning)';
        } else {
            charCount.style.color = 'var(--text-dim)';
        }
    }

    /**
     * Handles translation request to the Flask backend
     */
    async function handleTranslate() {
        const text = sourceText.value.trim();
        if (!text) {
            showToast('Please enter text to translate.', 'warning');
            sourceText.focus();
            return;
        }

        const source = sourceLanguage.value;
        const target = targetLanguage.value;

        // Set loading state
        setLoading(true);

        try {
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    source: source,
                    target: target
                })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                const errorMessage = result.error || `Translation request failed (HTTP ${response.status})`;
                showToast(errorMessage, 'error');
                renderErrorState(errorMessage);
                return;
            }

            const data = result.data;
            currentTranslation = {
                sourceText: text,
                translatedText: data.translatedText,
                detectedLang: data.detectedLanguage,
                provider: data.provider
            };

            // Display translation
            renderTranslation(data);

        } catch (error) {
            console.error('Translation network error:', error);
            const msg = 'Network error: Unable to reach translation server.';
            showToast(msg, 'error');
            renderErrorState(msg);
        } finally {
            setLoading(false);
        }
    }

    /**
     * Render translated text and badges
     */
    function renderTranslation(data) {
        targetText.classList.remove('empty-state');
        targetText.textContent = data.translatedText;

        // Enable copy and listen buttons
        copyTargetBtn.removeAttribute('disabled');
        listenTargetBtn.removeAttribute('disabled');

        // Detected language badge
        if (data.detectedLanguageName) {
            detectedLangText.textContent = `Detected: ${data.detectedLanguageName}`;
            detectedLangBadge.style.display = 'inline-flex';
        } else if (data.detectedLanguage && data.detectedLanguage !== 'auto') {
            detectedLangText.textContent = `Detected: ${data.detectedLanguage.toUpperCase()}`;
            detectedLangBadge.style.display = 'inline-flex';
        } else {
            detectedLangBadge.style.display = 'none';
        }

        // Provider badge
        if (data.provider) {
            providerName.textContent = `Engine: ${data.provider}`;
            providerBadge.style.display = 'inline-flex';
        }
    }

    /**
     * Render error state in output box
     */
    function renderErrorState(message) {
        targetText.classList.remove('empty-state');
        targetText.innerHTML = `<span style="color: var(--status-error);"><i class="fa-solid fa-triangle-exclamation"></i> ${escapeHtml(message)}</span>`;
        copyTargetBtn.setAttribute('disabled', 'true');
        listenTargetBtn.setAttribute('disabled', 'true');
    }

    /**
     * Set loading UI state
     */
    function setLoading(isLoading) {
        if (isLoading) {
            translateBtn.setAttribute('disabled', 'true');
            translateBtnText.textContent = 'Translating...';
            btnSpinner.style.display = 'inline-block';
            outputLoading.style.display = 'flex';
        } else {
            translateBtn.removeAttribute('disabled');
            translateBtnText.textContent = 'Translate Now';
            btnSpinner.style.display = 'none';
            outputLoading.style.display = 'none';
        }
    }

    /**
     * Swaps source and target languages and text
     */
    function handleSwapLanguages() {
        const sourceVal = sourceLanguage.value;
        const targetVal = targetLanguage.value;

        // If source is auto, check if we have a detected language
        let newSourceVal = targetVal;
        let newTargetVal = sourceVal;

        if (sourceVal === 'auto') {
            if (currentTranslation.detectedLang && currentTranslation.detectedLang !== targetVal) {
                newTargetVal = currentTranslation.detectedLang;
            } else {
                // Default target language if previous was auto
                newTargetVal = 'en';
            }
        }

        // Set select values
        sourceLanguage.value = newSourceVal;
        targetLanguage.value = newTargetVal;

        // If there is translated text available, swap texts too!
        if (currentTranslation.translatedText && currentTranslation.translatedText.trim()) {
            const previousOutput = currentTranslation.translatedText;
            const previousInput = sourceText.value;

            sourceText.value = previousOutput;
            targetText.classList.remove('empty-state');
            targetText.textContent = previousInput;
            updateCharCounter();

            currentTranslation.sourceText = previousOutput;
            currentTranslation.translatedText = previousInput;

            showToast('Languages and text swapped', 'info');
        } else {
            showToast('Languages swapped', 'info');
        }
    }

    /**
     * Clears input and output fields
     */
    function handleClear() {
        sourceText.value = '';
        updateCharCounter();
        
        targetText.classList.add('empty-state');
        targetText.innerHTML = `
            <div class="empty-placeholder">
                <i class="fa-solid fa-language placeholder-icon"></i>
                <p>Translation will appear here instantly</p>
            </div>
        `;

        copyTargetBtn.setAttribute('disabled', 'true');
        listenTargetBtn.setAttribute('disabled', 'true');
        detectedLangBadge.style.display = 'none';
        providerBadge.style.display = 'none';

        currentTranslation = {
            sourceText: '',
            translatedText: '',
            detectedLang: null,
            provider: ''
        };

        sourceText.focus();
        showToast('Cleared', 'info');
    }

    /**
     * Copies translated text to clipboard
     */
    async function handleCopy() {
        const text = currentTranslation.translatedText;
        if (!text) return;

        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
            } else {
                // Fallback for older browsers
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
            }

            // Visual feedback
            copyBtnText.textContent = 'Copied!';
            copyTargetBtn.classList.add('copied');
            const icon = copyTargetBtn.querySelector('i');
            icon.className = 'fa-solid fa-check';

            showToast('Copied to clipboard!', 'success');

            setTimeout(() => {
                copyBtnText.textContent = 'Copy';
                copyTargetBtn.classList.remove('copied');
                icon.className = 'fa-regular fa-copy';
            }, 2000);

        } catch (err) {
            console.error('Clipboard copy error:', err);
            showToast('Failed to copy to clipboard.', 'error');
        }
    }

    /**
     * Pronounces text using Web Speech Synthesis API
     */
    function handleListen(text, langCode) {
        if (!text || !text.trim()) {
            showToast('No text to speak.', 'warning');
            return;
        }

        if (!('speechSynthesis' in window)) {
            showToast('Text-to-speech is not supported in this browser.', 'warning');
            return;
        }

        window.speechSynthesis.cancel(); // Stop any active speech

        const utterance = new SpeechSynthesisUtterance(text);
        if (langCode && langCode !== 'auto') {
            utterance.lang = langCode;
        }

        utterance.rate = 0.95;
        utterance.pitch = 1.0;

        utterance.onerror = (e) => {
            console.warn('Speech synthesis error:', e);
            showToast('Audio playback could not be completed.', 'warning');
        };

        window.speechSynthesis.speak(utterance);
    }

    /**
     * Shows a toast notification
     */
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        let iconClass = 'fa-circle-info';
        if (type === 'success') iconClass = 'fa-circle-check';
        if (type === 'error') iconClass = 'fa-circle-exclamation';
        if (type === 'warning') iconClass = 'fa-triangle-exclamation';

        toast.innerHTML = `
            <i class="fa-solid ${iconClass}"></i>
            <span>${escapeHtml(message)}</span>
        `;

        toastContainer.appendChild(toast);

        // Auto remove after 3.5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px) scale(0.95)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3500);
    }

    /**
     * Safe HTML escape
     */
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
