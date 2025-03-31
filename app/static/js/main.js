document.addEventListener('DOMContentLoaded', function() {
    // Apply dark mode immediately when page loads
    applyDarkMode();
    
    // Set up dark mode toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            toggleDarkMode(this.checked);
        });
    }
    
    const searchForm = document.getElementById('searchForm');
    const designForm = document.getElementById('designForm');
    const quotesList = document.getElementById('quotesList');
    const quoteImage = document.getElementById('quoteImage');
    const designActions = document.getElementById('designActions');
    const downloadBtn = document.getElementById('downloadBtn');
    const shareBtn = document.getElementById('shareBtn');
    const showMoreBtn = document.createElement('button');
    
    showMoreBtn.className = 'btn btn-outline-primary mt-3';
    showMoreBtn.textContent = 'Show More Quotes';
    showMoreBtn.style.display = 'none';

    let currentDesignId = null;
    let currentMaxQuotes = 10;

    // Update the news ratio value display when the slider changes
    const newsRatio = document.getElementById('newsRatio');
    const newsRatioValue = document.getElementById('newsRatioValue');
    
    if (newsRatio && newsRatioValue) {
        newsRatio.addEventListener('input', function() {
            newsRatioValue.textContent = `${this.value}%`;
        });
    }

    // Handle quote search
    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const topic = document.getElementById('topic').value;
            const newsRatio = document.getElementById('newsRatio') ? 
                              document.getElementById('newsRatio').value : 40;
            
            console.log(`Submitting search with news ratio: ${newsRatio}%`);
            
            currentMaxQuotes = 10; // Reset to default when performing a new search
            
            // Show loading indicator
            quotesList.innerHTML = '<div class="text-center py-4"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Searching for quotes...</p></div>';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `topic=${encodeURIComponent(topic)}&max_quotes=${currentMaxQuotes}&news_ratio=${newsRatio}`
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Add source badges to quotes for debugging
                    data.forEach(quote => {
                        if (!quote.badge) {
                            if (quote.source === 'Recent News' || quote.source === 'Web Search') {
                                quote.badge = 'NEWS';
                            } else {
                                quote.badge = 'FAMOUS';
                            }
                        }
                    });
                    
                    displayQuotes(data);
                    
                    // Show "Show More" button if we received the full batch
                    if (data.length >= currentMaxQuotes) {
                        showMoreBtn.style.display = 'block';
                        if (!showMoreBtn.parentNode) {
                            quotesList.parentNode.appendChild(showMoreBtn);
                        }
                    } else {
                        showMoreBtn.style.display = 'none';
                    }
                } else {
                    showError(data.error || 'Failed to fetch quotes');
                    // Clear loading indicator if there's an error
                    quotesList.innerHTML = '';
                    showMoreBtn.style.display = 'none';
                }
            } catch (error) {
                showError('An error occurred while fetching quotes');
                // Clear loading indicator if there's an error
                quotesList.innerHTML = '';
                showMoreBtn.style.display = 'none';
            }
        });
    }
    
    // Handle "Show More" button click
    if (showMoreBtn) {
        showMoreBtn.addEventListener('click', async function() {
            const topic = document.getElementById('topic').value;
            const newsRatio = document.getElementById('newsRatio') ? 
                             document.getElementById('newsRatio').value : 40;
            
            // Increase the max quotes for the next request
            currentMaxQuotes += 10;
            if (currentMaxQuotes > 30) {
                showMoreBtn.style.display = 'none';
                return;
            }
            
            // Show loading state for the button
            showMoreBtn.disabled = true;
            showMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `topic=${encodeURIComponent(topic)}&max_quotes=${currentMaxQuotes}&news_ratio=${newsRatio}`
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    displayQuotes(data);
                    
                    // Hide button if we've reached the maximum
                    if (data.length < currentMaxQuotes || currentMaxQuotes >= 30) {
                        showMoreBtn.style.display = 'none';
                    }
                } else {
                    showError(data.error || 'Failed to fetch more quotes');
                }
                
                // Reset button state
                showMoreBtn.disabled = false;
                showMoreBtn.textContent = 'Show More Quotes';
                
            } catch (error) {
                showError('An error occurred while fetching more quotes');
                // Reset button state
                showMoreBtn.disabled = false;
                showMoreBtn.textContent = 'Show More Quotes';
            }
        });
    }

    // Handle design generation
    if (designForm) {
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
            const splitEnabled = document.getElementById('enableSplitDesign') && 
                                 document.getElementById('enableSplitDesign').checked;
            
            // Base background settings
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
            } else {
                // Default to white background if no valid option selected
                backgroundData = {
                    type: 'color',
                    color: '#ffffff'
                };
            }
            
            // Add split image if enabled
            if (splitEnabled && uploadedSplitImageUrl) {
                backgroundData.split_enabled = true;
                backgroundData.split_image = uploadedSplitImageUrl;
                backgroundData.split_position = document.getElementById('splitPosition').value;
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
    }

    // Handle download
    if (downloadBtn) {
        downloadBtn.addEventListener('click', async function() {
            if (!currentDesignId) return;
            
            try {
                window.location.href = `/download/${currentDesignId}`;
            } catch (error) {
                showError('Failed to download the design');
            }
        });
    }

    // Handle share
    if (shareBtn) {
        shareBtn.addEventListener('click', async function() {
            if (!currentDesignId) return;
            
            try {
                // Show a loading spinner or indication
                shareBtn.disabled = true;
                shareBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
                
                const response = await fetch(`/share/${currentDesignId}`);
                const data = await response.json();
                
                if (response.ok && data.success) {
                    // Show success toast notification
                    showToast(
                        data.saved_to_account 
                            ? 'Design saved to your Cloudinary account!' 
                            : 'Design shared successfully!',
                        data.saved_to_account 
                            ? 'Your design has been saved to your personal cloud library.'
                            : 'Your design has been shared to our cloud storage.',
                        'success'
                    );
                    
                    // If the design was saved to user's account, show an option to view their designs
                    if (data.saved_to_account) {
                        const viewDesignsBtn = document.createElement('a');
                        viewDesignsBtn.href = '/auth/designs';
                        viewDesignsBtn.className = 'btn btn-sm btn-outline-primary mt-2';
                        viewDesignsBtn.innerHTML = 'View My Designs';
                        
                        const actionsDiv = document.getElementById('designActions');
                        if (actionsDiv && !document.getElementById('viewDesignsBtn')) {
                            viewDesignsBtn.id = 'viewDesignsBtn';
                            actionsDiv.appendChild(viewDesignsBtn);
                        }
                    }
                } else {
                    showToast('Sharing failed', data.error || 'Failed to share the design', 'danger');
                }
            } catch (error) {
                console.error('Share error:', error);
                showToast('Error', 'An unexpected error occurred while sharing the design', 'danger');
            } finally {
                // Restore button state
                shareBtn.disabled = false;
                shareBtn.innerHTML = 'Share';
            }
        });
    }

    // Helper functions
    function displayQuotes(quotes) {
        quotesList.innerHTML = '';
        quotes.forEach(quote => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            
            // Add a source badge if available
            let sourceBadge = '';
            if (quote.source) {
                let badgeClass = 'bg-secondary';
                if (quote.source === 'Recent News') {
                    badgeClass = 'bg-info';
                } else if (quote.source === 'Web Search') {
                    badgeClass = 'bg-warning text-dark';
                }
                sourceBadge = `<span class="badge ${badgeClass} ms-2">${quote.source}</span>`;
            }
            
            // Create a debug badge to identify quote type
            let typeBadge = '';
            if (quote.source === 'Recent News' || quote.source === 'Web Search') {
                typeBadge = `<span class="badge bg-primary ms-1">NEWS</span>`;
            } else {
                typeBadge = `<span class="badge bg-dark ms-1">FAMOUS</span>`;
            }
            
            // Clean up the author display
            let author = quote.author || 'Unknown';
            if (author === 'Unknown Source') {
                author = 'Unknown';
            }
            
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${quote.text}</h6>
                    <small>${author} ${sourceBadge} ${typeBadge}</small>
                </div>
            `;
            item.dataset.quote = quote.text;
            item.dataset.author = author;
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
});

// Dark mode functions
function applyDarkMode() {
    const isDarkMode = localStorage.getItem('darkMode') === 'enabled';
    const darkModeToggle = document.getElementById('darkModeToggle');
    
    // Apply dark mode to the page if enabled in localStorage
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        if (darkModeToggle) {
            darkModeToggle.checked = true;
        }
    } else {
        document.body.classList.remove('dark-mode');
        if (darkModeToggle) {
            darkModeToggle.checked = false;
        }
    }
}

function toggleDarkMode(enable) {
    if (enable) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'enabled');
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Toast notification helper function
function showToast(title, message, type = 'primary') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Create toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>
                <span class="small">${message}</span>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, {
        animation: true,
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
} 