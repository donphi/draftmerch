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
            const generateActionButton = document.getElementById('generateActionButton');
            const removeBackgroundButton = document.getElementById('removeBackgroundButton');
            const backgroundRemovalSwitch = document.getElementById('backgroundRemovalSwitch');

            form.addEventListener('submit', function(event) {
                event.preventDefault();

                // Reset and disable the toggle switch
                backgroundRemovalSwitch.checked = false;
                backgroundRemovalSwitch.disabled = true;

                // Show loading state and message in the image container
                imageContainer.innerHTML = '<p>Generating image, please wait...</p>';
                waitingMessage.innerText = 'Generating image, please wait...';
                loading.classList.remove('hidden');
                waitingMessage.classList.remove('hidden');

                let formData = new FormData(form);
                formData.append('animal', getValueOrCustom('animal-dropdown', 'animal-custom-input'));
                formData.append('personality', getValueOrCustom('personality-dropdown', 'personality-custom-input'));
                formData.append('sport', getValueOrCustom('sport-dropdown', 'sport-custom-input'));
                formData.append('color', getValueOrCustom('color-dropdown', 'color-custom-input'));
                formData.append('action', getValueOrCustom('action-dropdown', 'action-custom-input'));

                fetch(window.location.href, { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.url && data.filename) {
                        imageContainer.innerHTML = `<img src="${data.url}" alt="Generated Image" id="resultImage" data-filename="${data.filename}">`;
                        backgroundRemovalSwitch.disabled = false;
                    } else {
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

            backgroundRemovalSwitch.addEventListener('change', function() {
                const resultImage = document.getElementById('resultImage');
                const filename = resultImage.dataset.filename;

                if (filename && this.checked) {
                    removeBackground(filename);
                    this.disabled = true;
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

        generateActionButton.addEventListener('click', generateCustomAction);
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
        const button = document.getElementById('generateActionButton');

        if (animal && personality && sport && color) {
            button.classList.add('active');
            button.disabled = false;
        } else {
            button.classList.remove('active');
            button.disabled = true;
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
                let dropdown = document.getElementById(dropdownId + '-dropdown');

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

    function generateCustomAction() {
        document.getElementById('waitingMessage').innerText = 'Generating action, please wait...';
        loading.classList.remove('hidden');

        var animal = document.getElementById('animal-dropdown').value;
        var personality = document.getElementById('personality-dropdown').value;
        var sport = document.getElementById('sport-dropdown').value;
        var color = document.getElementById('color-dropdown').value;

        var data = { 'animal': animal, 'personality': personality, 'sport': sport, 'color': color };

        fetch('/generate_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text();
        })
        .then(data => {
            document.getElementById('action-dropdown').value = 'custom';
            let customInput = document.getElementById('action-custom-input');
            customInput.value = data;
            customInput.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('waitingMessage').innerText = 'Error generating action, please try again.';
        })
        .finally(() => {
            loading.classList.add('hidden');
        });
    }

function removeBackground(filename) {
    console.log('removeBackground called with filename:', filename); // Debug log
    const resultImage = document.getElementById('resultImage');
    const imageContainer = document.getElementById('imageContainer'); // Make sure this is the correct ID

    if (!resultImage || !filename) {
        console.error('No image to remove background from or filename is missing.');
        console.log('Filename received:', filename);  // Log for debugging purposes
        return;
    }

    // Show waiting message
    waitingMessage.innerText = 'Removing background, please wait...';
    waitingMessage.classList.remove('hidden');

    const formData = new FormData();
    formData.append('filename', filename);

    fetch('/remove_background', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Data received from Flask:', data);  // Add for debugging
        if (data.url) {  // Use 'url' key here
            resultImage.onload = function() {
                // Once the image is loaded, apply the checkered background
                imageContainer.classList.add('checkered-background');
            };

            resultImage.src = data.url; // Set 'src' to 'url' value from the server
            resultImage.dataset.filename = filename;

            // Clear current content and append the image to the container
            imageContainer.innerHTML = '';
            imageContainer.appendChild(resultImage);

            // Update any UI/UX to show the image removal was successful
            waitingMessage.innerText = ''; // Clear any waiting messages
        } else {
            throw new Error('The image URL was not provided in the response.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        waitingMessage.innerText = `Error: ${error.message}`;
    })
    .finally(() => {
        // Optionally hide any loading indicators
        waitingMessage.classList.add('hidden');
    });
}

