    let originalImageUrl = null;
    let vectorizedImageUrl = null;

        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('form');
            const loading = document.getElementById('loading');
            const imageContainer = document.getElementById('imageContainer');
            const waitingMessage = document.getElementById('waitingMessage');
            const vectorizeSwitch = document.getElementById('vectorizeSwitch');
            const imageWrapper = document.querySelector('.image-wrapper');
            const resultImage = document.getElementById('resultImage');

            // Animal Dropdown listener
            document.getElementById('animal-dropdown').addEventListener('change', function() {
                updatePersonalityAndAction(this.value);
            });


            form.addEventListener('submit', function(event) {
                event.preventDefault();

                // Reset and disable the toggle switch
                vectorizeSwitch.disabled = true; // Disable the vectorize switch until background removal is done
                vectorizeSwitch.checked = false; // Uncheck the vectorize switch

                // Hide the explainerBox, vectorSwitch, Switching buttons & Download buttons when the form is submitted
                explainerBox.classList.add('hidden');
                vectorizeSwitchContainer.classList.add('hidden');
                downloadContainer.classList.add('hidden');
                form.classList.add('hidden');


                // Show loading state and message in the image container
                imageContainer.innerHTML = '<p>Generating image, please wait...</p>';
                loading.classList.remove('hidden');
                waitingMessage.classList.remove('hidden');
                imageContainer.style.display = 'flex';

                let formData = new FormData(form);
                formData.append('animal', getValueOrCustom('animal-dropdown', 'animal-custom-input'));
                formData.append('personality', getValueOrCustom('personality-dropdown', 'personality-custom-input'));
                formData.append('sport', getValueOrCustom('sport-dropdown', 'sport-custom-input'));
                formData.append('color', getValueOrCustom('color-dropdown', 'color-custom-input'));
                formData.append('action', getValueOrCustom('action-dropdown', 'action-custom-input'));

                fetch(window.location.href, { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.watermarked_url && data.filename) {
                        // Create a new .image-wrapper div to contain the image
                        const newImageWrapper = document.createElement('div');
                        newImageWrapper.className = 'image-wrapper checkered-background';
                        newImageWrapper.innerHTML = `<a href="${data.watermarked_url}" target="_blank">
                                                        <img src="${data.watermarked_url}" alt="Generated Image" id="resultImage" data-filename="${data.filename}">
                                                     </a>`;

                        // Save Original Image
                        originalImageUrl = data.watermarked_url;
                        console.log("Original image URL:", originalImageUrl); // Check URL

                        // Clear the imageContainer and append the new .image-wrapper
                        imageContainer.innerHTML = "";
                        imageContainer.appendChild(newImageWrapper);

                        // Show and enable the vectorize switch
                        const vectorizeSwitchContainer = document.getElementById('vectorizeSwitchContainer');
                        const vectorizeSwitch = document.getElementById('vectorizeSwitch');

                        vectorizeSwitchContainer.classList.remove('hidden'); // Show the switch container
                        vectorizeSwitch.disabled = false; // Enable the switch
                        form.classList.remove('hidden'); // Show the switch container

                        // Hide the waiting message as the image is now displayed
                        waitingMessage.classList.add('hidden');
                    } else {
                        // Error handling when data is incorrect
                        throw new Error(data.error || 'Unknown error occurred.');
                    }
                })
                                .catch(error => {
                    console.error('Error:', error);
                    imageContainer.innerHTML = `<p>Error occurred: ${error.message}. Please try again.</p>`;
                })
                .finally(() => {
                    loading.classList.add('hidden');
                    waitingMessage.classList.add('hidden');
                });
            });

            vectorizeSwitch.addEventListener('change', function() {
                const resultImage = document.getElementById('resultImage');

                if (vectorizedImageUrl && this.checked) {
            // If so, display the vectorized image and keep the switch enabled
                    resultImage.src = vectorizedImageUrl;
                    resultImage.alt = "Vectorized Image";
                    // No need to disable the switch
                } else if (!this.checked && originalImageUrl) {
                    // When the switch is turned off, display the original image
                    resultImage.src = originalImageUrl;
                    resultImage.alt = "Original Image";
                } else if (this.checked && !vectorizedImageUrl && originalImageUrl) {
                    // If the vectorized image is not yet set and the switch is turned on, go through the vectorization process
                    const filename = resultImage.getAttribute('data-filename');
                    if (filename) {
                        vectorizeImage(filename);
                    } else {
                        console.error('Error: No filename provided for vectorization.');
                        this.checked = false; // Reset the switch if there was an error
                    }
                }
            });

        loadDropdownData('color','/static/txt/color.txt');
        loadDropdownData('animal', '/static/txt/animal.txt');
        loadDropdownData('personality', '/static/txt/personality.txt');
        loadDropdownData('sport', '/static/txt/sport.txt');
        loadDropdownData('action', '/static/txt/action.txt');

        document.getElementById('animal-dropdown').addEventListener('change', checkAllDropdowns);
        document.getElementById('personality-dropdown').addEventListener('change', checkAllDropdowns);
        document.getElementById('sport-dropdown').addEventListener('change', checkAllDropdowns);
        document.getElementById('color-dropdown').addEventListener('change', checkAllDropdowns);

    });

    function getValueOrCustom(dropdownId, customInputId) {
        var dropdown = document.getElementById(dropdownId);
        var customInput = document.getElementById(customInputId);
        return dropdown.value === 'custom' ? customInput.value : dropdown.value;
    }

    function populateColorDropdown(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        dropdown.appendChild(new Option('', ''));
        dropdown.appendChild(new Option('Custom', 'custom'));

        Object.entries(colorMappings).forEach(([name, color]) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            option.style.backgroundColor = color;
            option.style.color = getContrastingColor(color);
            dropdown.appendChild(option);
        });
    }

    function getContrastingColor(color) {
        return (parseInt(color.substring(1), 16) > 0xffffff / 2) ? 'black' : 'white';
    }

    function checkAllDropdowns() {
        const animal = document.getElementById('animal-dropdown').value;
        const personality = document.getElementById('personality-dropdown').value;
        const sport = document.getElementById('sport-dropdown').value;
        const color = document.getElementById('color-dropdown').value;
        const submitButton = document.getElementById('submit-button'); // Get the submit button by its ID

        if (animal && personality && sport && color) {
            submitButton.classList.add('active');
            submitButton.disabled = false;
        } else {
            submitButton.classList.remove('active');
            submitButton.disabled = true;
        }
    }

    function checkCustom(selectElement, customInputId) {
        var customInput = document.getElementById(customInputId);
        customInput.style.display = selectElement.value === "custom" ? 'block' : 'none';
    }

    function updatePersonalityAndAction(selectedAnimal) {
        if (selectedAnimal.trim() === 'custom') {
            // Reset the dropdowns if no animal is selected or if it's set back to empty
            loadDropdownData('personality', '/static/txt/personality.txt');
            loadDropdownData('action', '/static/txt/action.txt');
        } else {
            // Load personality and action for the chosen animal
            loadDropdownData('personality', `/static/txt/personality/${selectedAnimal}_personality.txt`);
            // For action, combine options from the specific character and extra actions
            loadDropdownData('action', `/static/txt/action/${selectedAnimal}_action.txt`, '/static/txt/extra_action.txt');
        }
        // Remember to disable the form submit button since the options have changed
        checkAllDropdowns();
    }

    function loadDropdownData(dropdownId, filePath, extraFilePath = null) {
        const dropdown = document.getElementById(dropdownId + '-dropdown');
        if (!dropdown) {
            console.error('Dropdown with ID ' + dropdownId + '-dropdown' + ' does not exist in the DOM.');
            return;
        }

        // Clear dropdown before appending new options
        dropdown.innerHTML = '';
        dropdown.appendChild(new Option('', ''));
        dropdown.appendChild(new Option('Custom', 'custom'));

        fetch(filePath)
            .then(response => response.text())
            .then(text => {
                // Parse and add the main options
                let options = text.split('\n').filter(option => option.trim() !== '');
                // Sort options alphabetically
                options.sort();

                // Add the sorted options to the dropdown
                options.forEach(option => {
                    let opt = document.createElement('option');
                    opt.value = option.trim();
                    opt.innerHTML = option.trim();
                    dropdown.appendChild(opt);
                });

                // If an extra file path is provided, fetch and append those options as well
                if (extraFilePath) {
                    return fetch(extraFilePath).then(response => response.text());
                }
                return null; // No extra file to fetch
            })
            .then(extraText => {
                if (extraText) {
                    let extraOptions = extraText.split('\n').filter(option => option.trim() !== '');
                    // Sort extra options alphabetically
                    extraOptions.sort();

                    // Add the sorted options to the dropdown
                    extraOptions.forEach(option => {
                        let opt = document.createElement('option');
                        opt.value = option.trim();
                        opt.innerHTML = option.trim();
                        dropdown.appendChild(opt);
                    });
                }
            })
            .catch(error => console.error('Error loading ' + dropdownId + ':', error));
    }

function updateOverlayMessageAfterDelay(message, delay) {
    setTimeout(() => {
        let overlayMessage = document.getElementById('overlayMessage');
        if (overlayMessage) {
            overlayMessage.innerText = message;
        }
    }, delay);
}

function vectorizeImage(filename) {
    console.log('Filename:', filename);
    updateOverlayMessageAfterDelay('Removing background...', 8000); // 8000 milliseconds = 8 seconds
    updateOverlayMessageAfterDelay('Optimizing image...', 16000);
    updateOverlayMessageAfterDelay('Still...optimizing image...', 25000);
    updateOverlayMessageAfterDelay('Still...optimizing...🙄', 33000);
    updateOverlayMessageAfterDelay('Still...opitmizing...WTF', 39000);
    updateOverlayMessageAfterDelay('I might aswell draw this myself...', 45000);

    // If the overlay is removed with the imageContainer's innerHTML reset, create it dynamically
    let imageOverlay = document.getElementById('imageOverlay');
    let overlayMessage = document.getElementById('overlayMessage');

    if (!imageOverlay || !overlayMessage) {
        // Create overlay elements dynamically
        imageOverlay = document.createElement('div');
        imageOverlay.id = 'imageOverlay';
        imageOverlay.className = 'overlay';

        overlayMessage = document.createElement('p');
        overlayMessage.id = 'overlayMessage';
        overlayMessage.innerText = 'Upscaling image, please wait...';

        imageOverlay.appendChild(overlayMessage);
        imageContainer.appendChild(imageOverlay); // Assume imageContainer itself is never removed
    } else {
        // If they exist, simply update overlayMessage's text
        overlayMessage.innerText = 'Vectorizing image, please wait...';
    }

    // Hide Buttons and Overlay
    imageOverlay.classList.remove('hidden');
    form.classList.add('hidden');
    const vectorizeSwitchContainer = document.getElementById('vectorizeSwitchContainer');
    //vectorizeSwitchContainer.classList.add('hidden');

    const formData = new FormData();
    formData.append('filename', filename);

    fetch('/vectorize_image', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Server response:', data);
        if (data && data.url && data.svg_filename) {
            // URL-encode the filename to create a safe URL
            const encodedSvgFilename = encodeURIComponent(data.svg_filename);
            const svgUrl = `/static/vector/${encodedSvgFilename}`;
            console.log('Encoded SVG URL:', svgUrl);
            // Clear the imageContainer and create the new vectorized image with the updated URL
            imageContainer.innerHTML = `<div class="image-wrapper checkered-background">
                                            <a href="${data.url}" target="_blank">
                                                <img src="${data.url}" alt="Vectorized Image" id="resultImage" class="checkered-background">
                                            </a>
                                        </div>`;

            // Save Vectorized Link
            vectorizedImageUrl = data.url;
            console.log("Vectorized image URL:", vectorizedImageUrl);

            // Ensure that the vectorizeSwitch is disabled after vectorization
            const vectorizeSwitch = document.getElementById('vectorizeSwitch');
            vectorizeSwitch.disabled = false; // Re-enable the switch for toggling
            vectorizeSwitch.checked = true; // Keep the switch on

            // Get the download button container and button
            const downloadContainer = document.getElementById('downloadContainer');
            const downloadSvgButton = document.getElementById('downloadSvgButton');
            const returnButton = document.getElementById('returnButton'); // The return button

            // Update the href to the SVG file location
            //downloadSvgButton.href = svgUrl;
            //downloadSvgButton.setAttribute('download', data.svg_filename);

            downloadSvgButton.onclick = function() {
            const link = document.createElement('a');
            link.href = svgUrl;
            link.download = data.svg_filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            };

            // Handler for the return button
            returnButton.onclick = function() {
                // Logic to return, for example, navigate to a different page or view
                window.location.href = 'https://chonkie.pythonanywhere.com'; // Change to your root site URL
            };

            // Show the download button by removing the "hidden" class
            downloadContainer.classList.remove('hidden');
        } else {
            throw new Error('Server response does not contain a valid SVG file.');
        }
    })
    .catch(error => {
        console.error('Error during vectorization:', error);
    })
    .finally(() => {
        imageOverlay.classList.add('hidden'); // Hide the overlay
    });
}

// Helper function to manage the active state of the buttons
function setActiveButton(activeButton) {
    const showOriginalImageBtn = document.getElementById('showOriginalImage');
    const showVectorizedImageBtn = document.getElementById('showVectorizedImage');
    showOriginalImageBtn.classList.remove('active');
    showVectorizedImageBtn.classList.remove('active');
    activeButton.classList.add('active');
}

