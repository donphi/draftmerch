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
        const uploadInput = document.getElementById('image-upload');
        const uploadButton = document.getElementById('upload-btn');
        const fileChosen = document.getElementById('file-chosen');
        const uploadSection = document.getElementById('upload-section');

        // Hero dropdown listener
        document.getElementById('hero-dropdown').addEventListener('change', function() {
            var value = this.value; 
            
            if (value === 'Upload Image') {
                // Show the upload section if "Upload Image" is selected
                uploadSection.classList.remove('hidden');
                document.querySelector('.pillbutton').classList.remove('hidden');
                fileChosen.classList.remove('hidden');
            } else {
                // Hide the upload section for all other selections
                uploadSection.classList.add('hidden'); // Use classList.add for consistency
        
                // If the selection is not blank, update personality and actions
                if (value !== '' && value !== 'default') { // Assuming 'default' is the value for the blank option
                    updatePersonalityAndAction(value);
                }
            }
        });
        
        // Attach click event listener to the upload button
        uploadButton.addEventListener('click', function() {
        // Trigger the actual upload process
        });

        document.getElementById('image-upload').addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                var fileName = this.files[0].name;
                var fileExtension = fileName.split('.').pop();
                var truncatedName = fileName.length > 28 ? fileName.substring(0, 28) + '...' + fileExtension : fileName;

                //display black button
                document.querySelector('.pillbutton').classList.add('uploaded');
        
                document.getElementById('file-chosen').textContent = truncatedName;
                document.getElementById('upload-btn').classList.remove('hidden');
            }
        });

        // Attach click event listener to the upload button
        uploadButton.addEventListener('click', function() {
            // Ensure a file is selected
            if (uploadInput.files.length === 0) {
                alert('Please select a file to upload.');
                return;
            }

            // Prepare the file to be sent in a FormData object
            var formData = new FormData();
            formData.append('image-upload', uploadInput.files[0]);

            // Display loading or processing message
            imageContainer.innerHTML = '<p>Processing image, please wait...</p>';
            loading.classList.remove('hidden');
            waitingMessage.classList.remove('hidden');
            imageContainer.style.display = 'flex';

            //Hide other dropdowns
            team_spirit.classList.add('hidden');
            arenas.classList.add('hidden');
            team_colors.classList.add('hidden');
            winning_moves.classList.add('hidden');
            document.getElementById("submit-button").classList.add('hidden');

            //Hide Items
            explainerBox.classList.add('hidden');

            // AJAX request to the /analyze-image route
            fetch('/analyze-image', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if(data.error) {
                    // Handle the error case
                    console.error('Error:', data.error);
                    // Display error message to the user
                } else {
                    // Successful response from the server
                    // Hide upload section and buttons
                    uploadSection.classList.add('hidden');
                    uploadButton.classList.add('hidden');
                    document.querySelector('.pillbutton').classList.add('hidden');
                    fileChosen.classList.add('hidden');
            
                    //Bring back items
                    imageContainer.innerHTML = '<p>Processing complete, continue selection.</p>';
            
                    //Bring back dropdowns
                    team_spirit.classList.remove('hidden');
                    arenas.classList.remove('hidden');
                    team_colors.classList.remove('hidden');
                    winning_moves.classList.remove('hidden');
                    
                    // Show the submit button again
                    document.getElementById("submit-button").classList.remove('hidden');
            
                    // Update the hero dropdown
                    const heroDropdown = document.getElementById('hero-dropdown');
                    let fileName = uploadInput.files[0].name;
                    let fileExtension = fileName.split('.').pop();
                    let displayName = fileName.length > 23 ? fileName.substring(0, 23) + '...' + fileExtension : fileName;
                    
                    // Find and update the 'Upload File' option
                    for (let i = 0; i < heroDropdown.options.length; i++) {
                        if (heroDropdown.options[i].value === 'Upload Image') {
                            heroDropdown.options[i].textContent = 'Image: ' + displayName;
                            heroDropdown.options[i].value = 'Uploaded Image';
                            heroDropdown.selectedIndex = i; // Set this option as selected
                            break;
                        }
                    }

                    console.log('API Response:', data.api_response);
                    // Process the successful response
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Handle any additional errors
            })
            .finally(() => {
                // Hide loading or processing message
                loading.classList.add('hidden');
                waitingMessage.classList.add('hidden');
            });
        });

        // Set up the production API endpoint
        const apiEndpoint = 'https://api.draftmerch.com/gen'; // The production API endpoint
        const apiKey = 'x4ISPCpxA2ZXNqd7awV5a2SF7YlN5gu9OpVbIVA0'; // The API key for authorization

        console.log("API Endpoint: ", apiEndpoint);

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

            let bodyData = {
                'hero': getValueOrCustom('hero-dropdown', 'hero-custom-input'),
                'personality': getValueOrCustom('personality-dropdown', 'personality-custom-input'),
                'sport': getValueOrCustom('sport-dropdown', 'sport-custom-input'),
                'color': getValueOrCustom('color-dropdown', 'color-custom-input'),
                'action': getValueOrCustom('action-dropdown', 'action-custom-input')
            };

            // Log the submitted data to the console (For debugging purposes)
            console.log("Submitting data:", bodyData);

            fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': apiKey // Add the API key to the request headers for authorization
                },
                body: JSON.stringify(bodyData)
            })
            .then(response => {
                console.log("Response received: ", response);
                if (!response.ok) {
                    // Not a 2xx response. Log and throw an error.
                    console.error("Response status was not OK: ", response.status);
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json(); // Assuming the server always responds with JSON
            })
            .then(data => {
                console.log("Data received from Lambda:", data);
                if (data.watermarked_image_url && data.original_image_url && data.filename) {
                    console.log("Original image URL:", data.original_image_url);
                    console.log("Watermarked image URL:", data.watermarked_image_url);
                    console.log("Filename:", data.filename);

                    // Create a new .image-wrapper div to contain the image
                    const newImageWrapper = document.createElement('div');
                    newImageWrapper.className = 'image-wrapper checkered-background';
                    newImageWrapper.innerHTML = `<a href="${data.watermarked_image_url}" target="_blank">
                                                    <img src="${data.watermarked_image_url}" alt="Generated Image" id="resultImage" data-filename="${data.filename}">
                                                </a>`;

                    // Save Original Image
                    originalImageUrl = data.watermarked_image_url;
                    console.log("Original image URL:", originalImageUrl); // Check URL

                    // Clear the imageContainer and append the new .image-wrapper
                    imageContainer.innerHTML = "";
                    imageContainer.appendChild(newImageWrapper);

                    // Show and enable the vectorize switch
                    vectorizeSwitchContainer.classList.remove('hidden'); // Show the switch container
                    vectorizeSwitch.disabled = false; // Enable the switch
                    form.classList.remove('hidden'); // Show the form

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

    loadDropdownData('color','/static/text_data/dropdown_color.txt');
    loadDropdownData('hero', '/static/text_data/dropdown_hero.txt');
    loadDropdownData('personality', '/static/text_data/dropdown_personality.txt');
    loadDropdownData('sport', '/static/text_data/dropdown_sport.txt');
    loadDropdownData('action', '/static/text_data/dropdown_action.txt');

    document.getElementById('hero-dropdown').addEventListener('change', checkAllDropdowns);
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
    const hero = document.getElementById('hero-dropdown').value;
    const personality = document.getElementById('personality-dropdown').value;
    const sport = document.getElementById('sport-dropdown').value;
    const color = document.getElementById('color-dropdown').value;
    const submitButton = document.getElementById('submit-button'); // Get the submit button by its ID

    if (hero && personality && sport && color) {
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

function updatePersonalityAndAction(selectedHero) {
    if (selectedHero.trim() === 'custom') {
        // Reset the dropdowns if no hero is selected or if it's set back to empty
        loadDropdownData('personality', '/static/text_data/dropdown_personality.txt');
        loadDropdownData('action', '/static/text_data/dropdown_action.txt');
    } else {
        // Load personality and action for the chosen hero
        loadDropdownData('personality', `/static/text_data/personality_data/${selectedHero}_personality.txt`);
        // For action, combine options from the specific character and extra actions
        loadDropdownData('action', `/static/text_data/action_data/${selectedHero}_action.txt`, '/static/text_data/extra_action.txt');
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

    // Add a blank option as the first and default option
    dropdown.appendChild(new Option('', ''));

    // If this is the hero dropdown, add 'Upload Image' option
    if (dropdownId === 'hero') {
        dropdown.appendChild(new Option('Upload Image', 'Upload Image'));
    }

    // Add 'Custom' option
    dropdown.appendChild(new Option('Custom', 'custom'));

    // If this is the hero dropdown, add a separator
    if (dropdownId === 'hero') {
        const separator = new Option('──────────', '');
        separator.disabled = true;
        dropdown.appendChild(separator);
    }

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
updateOverlayMessageAfterDelay('I might as well draw this myself...', 45000);

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

fetch('/vectorize-image', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Server response:', data);
    if (data && data.url && data.svg_filename) {
        // URL-encode the filename to create a safe URL
        const encodedSvgFilename = encodeURIComponent(data.svg_filename);
        const svgUrl = `/static/image_vectorized/${encodedSvgFilename}`;
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

