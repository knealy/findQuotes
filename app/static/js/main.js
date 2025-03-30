document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const designForm = document.getElementById('designForm');
    const quotesList = document.getElementById('quotesList');
    const quoteImage = document.getElementById('quoteImage');
    const designActions = document.getElementById('designActions');
    const downloadBtn = document.getElementById('downloadBtn');
    const shareBtn = document.getElementById('shareBtn');

    let currentDesignId = null;

    // Handle quote search
    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const topic = document.getElementById('topic').value;
        
        // Show loading indicator
        quotesList.innerHTML = '<div class="text-center py-4"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Searching for quotes...</p></div>';
        
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `topic=${encodeURIComponent(topic)}`
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayQuotes(data);
            } else {
                showError(data.error || 'Failed to fetch quotes');
                // Clear loading indicator if there's an error
                quotesList.innerHTML = '';
            }
        } catch (error) {
            showError('An error occurred while fetching quotes');
            // Clear loading indicator if there's an error
            quotesList.innerHTML = '';
        }
    });

    // Handle design generation
    designForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const selectedQuote = document.querySelector('.list-group-item.active');
        
        if (!selectedQuote) {
            showError('Please select a quote first');
            return;
        }

        const quote = selectedQuote.dataset.quote;
        const author = selectedQuote.dataset.author;
        const fontStyle = document.getElementById('fontStyle').value;
        const fontSize = document.getElementById('fontSize').value;
        const fontColor = document.getElementById('fontColor').value;
        
        // Get background settings based on selected type
        let backgroundData = {};
        const bgType = document.getElementById('backgroundType').value;
        
        if (bgType === 'color') {
            backgroundData = {
                type: 'color',
                color: document.getElementById('backgroundColor').value
            };
        } else if (bgType === 'gradient') {
            backgroundData = {
                type: 'gradient',
                color1: document.getElementById('gradientColor1').value,
                color2: document.getElementById('gradientColor2').value,
                direction: document.getElementById('gradientDirection').value
            };
        } else if (bgType === 'image' && uploadedImageUrl) {
            backgroundData = {
                type: 'image',
                url: uploadedImageUrl
            };
        } else if (bgType === 'split' && uploadedSplitImageUrl) {
            backgroundData = {
                type: 'split',
                split_image: uploadedSplitImageUrl,
                position: document.getElementById('splitPosition').value,
                quote_background: document.getElementById('splitQuoteBackground').value
            };
        } else {
            // Default to white background if no valid option selected
            backgroundData = {
                type: 'color',
                color: '#ffffff'
            };
        }

        try {
            const response = await fetch('/design', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quote: quote,
                    author: author,
                    font_style: fontStyle,
                    font_size: fontSize,
                    font_color: fontColor,
                    background: backgroundData
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                displayDesign(data.image_url, data.design_id);
            } else {
                showError(data.error || 'Failed to generate design');
            }
        } catch (error) {
            showError('An error occurred while generating the design');
        }
    });

    // Handle download
    downloadBtn.addEventListener('click', async function() {
        if (!currentDesignId) return;
        
        try {
            window.location.href = `/download/${currentDesignId}`;
        } catch (error) {
            showError('Failed to download the design');
        }
    });

    // Handle share
    shareBtn.addEventListener('click', async function() {
        if (!currentDesignId) return;
        
        try {
            const response = await fetch(`/share/${currentDesignId}`);
            const data = await response.json();
            
            if (response.ok && data.success) {
                const shareDialog = document.createElement('div');
                shareDialog.className = 'modal fade';
                
                // Just open Twitter with no pre-filled text or URL
                const twitterShareUrl = 'https://twitter.com/intent/tweet';
                
                shareDialog.innerHTML = `
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Share Quote</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="text-center">
                                    <img src="${data.image_url}" class="img-fluid mb-3">
                                    <div class="d-grid gap-2">
                                        <a href="${data.image_url}" download="quote-design.png" class="btn btn-primary">Download Image</a>
                                        <p class="text-muted small mt-2">Download the image and share it directly on your social media!</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(shareDialog);
                const modal = new bootstrap.Modal(shareDialog);
                modal.show();
                
                shareDialog.addEventListener('hidden.bs.modal', function() {
                    document.body.removeChild(shareDialog);
                });
            } else {
                showError(data.error || 'Failed to share the design');
            }
        } catch (error) {
            console.error('Share error:', error);
            showError('An error occurred while sharing the design');
        }
    });

    // Helper functions
    function displayQuotes(quotes) {
        quotesList.innerHTML = '';
        quotes.forEach(quote => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${quote.text}</h6>
                    <small>${quote.author}</small>
                </div>
            `;
            item.dataset.quote = quote.text;
            item.dataset.author = quote.author;
            item.addEventListener('click', () => {
                document.querySelectorAll('.list-group-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            });
            quotesList.appendChild(item);
        });
    }

    function displayDesign(imageUrl, designId) {
        quoteImage.src = imageUrl;
        quoteImage.style.display = 'block';
        currentDesignId = designId;
        designActions.style.display = 'block';
        designActions.classList.add('visible');
    }

    function showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Find the container and the first row
        const container = document.querySelector('.container');
        const firstRow = container.querySelector('.row');
        
        // Check if elements exist before inserting
        if (container && firstRow) {
            container.insertBefore(alert, firstRow);
        } else {
            // Fallback: append to body if container/row not found
            document.body.appendChild(alert);
        }
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    // Background type selection
    const backgroundType = document.getElementById('backgroundType');
    const solidColorOption = document.getElementById('solidColorOption');
    const gradientOption = document.getElementById('gradientOption');
    const imageOption = document.getElementById('imageOption');

    backgroundType.addEventListener('change', function() {
        // Hide all options first
        solidColorOption.style.display = 'none';
        gradientOption.style.display = 'none';
        imageOption.style.display = 'none';
        document.getElementById('splitOption').style.display = 'none';
        
        // Show the selected option
        switch(this.value) {
            case 'color':
                solidColorOption.style.display = 'block';
                break;
            case 'gradient':
                gradientOption.style.display = 'block';
                break;
            case 'image':
                imageOption.style.display = 'block';
                break;
            case 'split':
                document.getElementById('splitOption').style.display = 'block';
                break;
        }
    });

    // Background image upload
    const backgroundImage = document.getElementById('backgroundImage');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = uploadProgress.querySelector('.progress-bar');
    const uploadedBackgroundPreview = document.getElementById('uploadedBackgroundPreview');
    const previewImage = document.getElementById('previewImage');
    let uploadedImageUrl = null;

    backgroundImage.addEventListener('change', async function(e) {
        if (!this.files || !this.files[0]) return;
        
        const file = this.files[0];
        const formData = new FormData();
        formData.append('background_image', file);
        
        // Show progress bar
        uploadProgress.style.display = 'block';
        progressBar.style.width = '0%';
        
        try {
            const xhr = new XMLHttpRequest();
            
            // Set up progress monitoring
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressBar.style.width = percentComplete + '%';
                }
            });
            
            // Set up completion handler
            xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    uploadedImageUrl = response.background_url;
                    
                    // Show preview
                    previewImage.src = uploadedImageUrl;
                    uploadedBackgroundPreview.style.display = 'block';
                } else {
                    showError('Failed to upload image');
                }
            });
            
            // Set up error handler
            xhr.addEventListener('error', function() {
                showError('Upload failed');
            });
            
            // Send the request
            xhr.open('POST', '/upload-background', true);
            xhr.send(formData);
        } catch (error) {
            showError('An error occurred during upload');
        }
    });

    // Add split image upload handler
    const splitImage = document.getElementById('splitImage');
    const splitUploadProgress = document.getElementById('splitUploadProgress');
    const splitPreviewImage = document.getElementById('splitPreviewImage');
    let uploadedSplitImageUrl = null;

    splitImage.addEventListener('change', async function(e) {
        if (!this.files || !this.files[0]) return;
        
        const file = this.files[0];
        const formData = new FormData();
        formData.append('split_image', file);
        
        splitUploadProgress.style.display = 'block';
        const progressBar = splitUploadProgress.querySelector('.progress-bar');
        progressBar.style.width = '0%';
        
        try {
            const response = await fetch('/upload-split-image', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                uploadedSplitImageUrl = data.image_url;
                splitPreviewImage.src = uploadedSplitImageUrl;
                document.getElementById('splitImagePreview').style.display = 'block';
            }
        } catch (error) {
            showError('Failed to upload split image');
        }
    });

    // Dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;

    // Check for saved preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        body.classList.add('dark-mode');
        darkModeToggle.checked = true;
    }

    darkModeToggle.addEventListener('change', function() {
        if (this.checked) {
            body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'disabled');
        }
    });
}); 