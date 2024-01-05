    const colorMappings = {
        "Red": "#FF5733",
        "Orange": "#FF7F50",
        "Yellow": "#FFD700",
        "Green": "#BFFF00",
        "LightGreen": "#98FF98",
        "Cyan": "#40E0D0",
        "LightBlue": "#87CEEB",
        "Blue": "#1E90FF",
        "DarkBlue": "#4B0082",
        "Purple": "#9400D3",
        "Violet": "#FF00FF",
        "DeepPink": "#FF1493",
        "Pink": "#FF69B4",
        "PalePink": "#FFB6C1",
        "DarkRed": "#DC143C"
    };

        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('form');
            const loading = document.getElementById('loading');
            const imageContainer = document.getElementById('imageContainer');
            const waitingMessage = document.getElementById('waitingMessage');
            const vectorizeSwitch = document.getElementById('vectorizeSwitch');
            const imageWrapper = document.querySelector('.image-wrapper');

            form.addEventListener('submit', function(event) {
                event.preventDefault();

                // Reset and disable the toggle switch
                vectorizeSwitch.disabled = true; // Disable the vectorize switch until background removal is done
                vectorizeSwitch.checked = false; // Uncheck the vectorize switc

                // Show loading state and message in the image container
                imageContainer.innerHTML = '<p>Generating image, please wait...</p>';
                waitingMessage.innerText = 'Generating image, please wait...';
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

                        // Clear the imageContainer and append the new .image-wrapper
                        imageContainer.innerHTML = "";
                        imageContainer.appendChild(newImageWrapper);

                        // Enable the vectorize switch
                        vectorizeSwitch.disabled = false;
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
                if (this.checked) {
                    // Immediately disable the switch as soon as it's clicked
                    this.disabled = true;

                    const resultImage = document.getElementById('resultImage');
                    const filename = resultImage.getAttribute('data-filename');
                    vectorizeImage(filename);  // Make sure filename is not 'null' or undefined here
                    waitingMessage.innerText = 'Vectorizing image, please wait...';
                    waitingMessage.classList.remove('hidden');
                    if (filename) { // Make sure filename is not 'null' or 'undefined'
                        vectorizeImage(filename);
                    } else {
                        console.error('Error: No filename provided for vectorization.');
                    }
                }
            });

        populateColorDropdown('color-dropdown');
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

    function loadDropdownData(dropdownId, filePath) {
    fetch(filePath)
        .then(response => response.text())
        .then(text => {
            let options = text.split('\n');
            let dropdown = document.getElementById(dropdownId + '-dropdown'); // Ensure this ID is correct

            if (!dropdown) {
                console.error('Dropdown with ID ' + dropdownId + '-dropdown' + ' does not exist in the DOM.');
                return;
            }

            // Clear dropdown before appending new options
            dropdown.innerHTML = '';
            dropdown.appendChild(new Option('', ''));
            dropdown.appendChild(new Option('Custom', 'custom'));

            options.forEach(option => {
                if (option.trim() !== '') {
                    let opt = document.createElement('option');
                    opt.value = option.trim();
                    opt.innerHTML = option.trim();
                    dropdown.appendChild(opt);
                }
            });
        })
        .catch(error => console.error('Error loading ' + dropdownId + ':', error));
}

function vectorizeImage(filename) {
    console.log('Filename:', filename);
    waitingMessage.innerText = 'Optimizing image, please wait...';
    waitingMessage.classList.remove('hidden');

    const formData = new FormData();
    formData.append('filename', filename);

    fetch('/vectorize_image', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
    if (data && data.url) {
        // Clear the imageContainer and create the new vectorized image with the updated URL
        imageContainer.innerHTML = `<div class="image-wrapper checkered-background">
                                        <a href="${data.url}" target="_blank">
                                            <img src="${data.url}" alt="Vectorized Image" class="checkered-background">
                                        </a>
                                    </div>`;
        // Ensure that the vectorizeSwitch is disabled after vectorization
        vectorizeSwitch.disabled = true;
        vectorizeSwitch.checked = true; // Uncheck the switch
        // Hide the waiting message as the vectorization is complete
        waitingMessage.classList.add('hidden');
    } else {
        // Error handling when data is incorrect
        throw new Error('Server response does not contain a URL for the vectorized image.');
    }
    })
    .catch(error => {
        // Handle errors appropriately
        console.error('Error during vectorization:', error);
    })
}

