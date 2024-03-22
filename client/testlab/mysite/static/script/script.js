let originalImageUrl = null;
let vectorizedImageUrl = null;
let websocket = null;
let expectedProgress = 0;
let currentProgress = 0;
let targetProgress = 0;
let intervalgenID = null;
let intervalvecID = null;

    document.addEventListener('DOMContentLoaded', function() {
        const form = document.querySelector('form');
        const loading = document.getElementById('loading');
        const imageContainer = document.getElementById('imageContainer');
        const waitingMessage = document.getElementById('waitingMessage');
        const vectorizeSwitch = document.getElementById('vectorizeSwitch');
        const imageWrapper = document.querySelector('.image-wrapper');
        const resultImage = document.getElementById('resultImage');
        //const uploadInput = document.getElementById('image-upload');
        //const uploadButton = document.getElementById('upload-btn');
        //const fileChosen = document.getElementById('file-chosen');
        //const uploadSection = document.getElementById('upload-section');
        const progressBarContainer = document.getElementById('progressBarContainer')
        const downloadContainer = document.getElementById('downloadContainer');
        const progressBar = document.getElementById('progressBar');

        // Define the WebSocket URL (replace with your own)
        const WEBSOCKET_URL = 'wss://web.draftmerch.com'; // Replace with your API Gateway WebSocket URL

        // Function to initialize or re-initialize the WebSocket connection
        function initializeWebSocketConnection() {
            websocket = new WebSocket(WEBSOCKET_URL);
    
            websocket.onopen = function(event) {
                console.log('WebSocket connection established:', event);
                // Optionally send a message to the server if needed
            };
    
            websocket.onmessage = function(event) {
                const message = JSON.parse(event.data);
                console.log(`Received message at ${new Date().toISOString()}:`, message);

                try {
                    const message = JSON.parse(event.data);
                    // Adjusted logic to check for renderId presence
                    if (message.status === "VectorComplete" && message.renderId) {
                        console.log('Websocket message received. Calling data function...');
                        localStorage.setItem('renderId', message.renderId);
                        fetchVectorData(message.renderId); // Pass renderId directly
                    } else if (message.status === "ProcessingComplete") {
                        console.log('Processing complete. Fetching results...');
                        if (message.renderId) {
                            localStorage.setItem('renderId', message.renderId);
                        }
                        fetchProcessedData();
                    } else if (message.connectionId) {
                        localStorage.setItem('connectionId', message.connectionId);
                        console.log('Stored connectionId in local storage:', message.connectionId);
                    // Handle progress updates specifically
                    } else if (message.type === "generateStatus" && message.renderId && message.renderStatus !== undefined) {
                        // Update the progress bar with the renderStatus value
                        updateProgressBar(message.renderStatus);
                        console.log("WebSocket message received:", event.data);
                    } else if (message.type === "vectorStatus" && message.renderId && message.renderStatus !== undefined) {
                        // Update the progress bar with the renderStatus value
                        updateProgressVectorBar(message.renderStatus);
                        console.log("WebSocket message received:", event.data);
                    } else {
                        console.log('Received message:', message);
                    }
                } catch (e) {
                    console.error('Error processing the WebSocket message:', e);
                }
            };
    
            websocket.onerror = function(event) {
                console.error('WebSocket error:', event);
            };
    
            websocket.onclose = function(event) {
                console.log('WebSocket connection closed:', event);
                setTimeout(initializeWebSocketConnection, 1000); // Attempt to reconnect after 1 second
            };
        }
    
        // Initialize WebSocket connection for the first time
        initializeWebSocketConnection();

        // Hero dropdown listener
        document.getElementById('hero-dropdown').addEventListener('change', function() {
            var value = this.value; 
            
            if (value === 'Upload Image') {
                // Show the upload section if "Upload Image" is selected
                //uploadSection.classList.remove('hidden');
                document.querySelector('.pillbutton').classList.remove('hidden');
                //fileChosen.classList.remove('hidden');
            } else {
                // Hide the upload section for all other selections
                //uploadSection.classList.add('hidden'); // Use classList.add for consistency
        
                // If the selection is not blank, update personality and actions
                if (value !== '' && value !== 'default') { // Assuming 'default' is the value for the blank option
                    updatePersonalityAndAction(value);
                }
            }
        });
        
        // Attach click event listener to the upload button
        //uploadButton.addEventListener('click', function() {
        // Trigger the actual upload process
        //});

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
        //uploadButton.addEventListener('click', function() {
            // Ensure a file is selected
        //    if (uploadInput.files.length === 0) {
        //        alert('Please select a file to upload.');
        //        return;
        //    }

            // Prepare the file to be sent in a FormData object
        //    var formData = new FormData();
        //    formData.append('image-upload', uploadInput.files[0]);

            // Display loading or processing message
        //    imageContainer.innerHTML = '<p>Processing image, please wait...</p>';
        //    loading.classList.remove('hidden');
        //    waitingMessage.classList.remove('hidden');
        //    imageContainer.style.display = 'flex';

            //Hide other dropdowns
        //    team_spirit.classList.add('hidden');
        //    arenas.classList.add('hidden');
        //    team_colors.classList.add('hidden');
        //    winning_moves.classList.add('hidden');
        //    document.getElementById("submit-button").classList.add('hidden');

            //Hide Items
        //    explainerBox.classList.add('hidden');

            // AJAX request to the /analyze-image route
        //    fetch('/analyze-image', {
        //        method: 'POST',
        //        body: formData
        //    })
        //    .then(response => response.json())
        //    .then(data => {
        //        if(data.error) {
                    // Handle the error case
        //            console.error('Error:', data.error);
        //            // Display error message to the user
        //        } else {
                    // Successful response from the server
                    // Hide upload section and buttons
        //            uploadSection.classList.add('hidden');
        //            uploadButton.classList.add('hidden');
        //            document.querySelector('.pillbutton').classList.add('hidden');
        //            fileChosen.classList.add('hidden');
            
                    //Bring back items
        //            imageContainer.innerHTML = '<p>Processing complete, continue selection.</p>';
            
                    //Bring back dropdowns
        //            team_spirit.classList.remove('hidden');
        //            arenas.classList.remove('hidden');
        //            team_colors.classList.remove('hidden');
        //            winning_moves.classList.remove('hidden');
                    
                    // Show the submit button again
        //            document.getElementById("submit-button").classList.remove('hidden');
            
                    // Update the hero dropdown
        //            const heroDropdown = document.getElementById('hero-dropdown');
        //            let fileName = uploadInput.files[0].name;
        //            let fileExtension = fileName.split('.').pop();
        //            let displayName = fileName.length > 23 ? fileName.substring(0, 23) + '...' + fileExtension : fileName;
                    
                    // Find and update the 'Upload File' option
        //            for (let i = 0; i < heroDropdown.options.length; i++) {
        //                if (heroDropdown.options[i].value === 'Upload Image') {
        //                    heroDropdown.options[i].textContent = 'Image: ' + displayName;
        //                    heroDropdown.options[i].value = 'Uploaded Image';
        //                    heroDropdown.selectedIndex = i; // Set this option as selected
        //                    break;
        //                }
        //            }

        //            console.log('API Response:', data.api_response);
                    // Process the successful response
        //        }
        //    })
        //    .catch(error => {
        //        console.error('Error:', error);
                // Handle any additional errors
        //    })
        //    .finally(() => {
                // Hide loading or processing message
        //        loading.classList.add('hidden');
        //        waitingMessage.classList.add('hidden');
        //    });
        //});

        // Set up the production API endpoint
        const apiEndpoint = 'https://api.draftmerch.com/gen'; // The production API endpoint
        const apiKey = 'x4ISPCpxA2ZXNqd7awV5a2SF7YlN5gu9OpVbIVA0'; // The API key for authorization

        console.log("API Endpoint: ", apiEndpoint);

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            resetProgressBar();
        
            // Reset and disable the toggle switch
            vectorizeSwitch.disabled = true;
            vectorizeSwitch.checked = false;

            // Hide UI elements indicating processing
            progressBarContainer.classList.remove('hidden');
            progressBarContainer.style.display = 'block';
            explainerBox.classList.add('hidden');
            vectorizeSwitchContainer.classList.add('hidden');
            downloadContainer.classList.add('hidden');
            form.classList.add('hidden');
            imageContainer.innerHTML = '<p>Generating image, please wait...</p>';
            loading.classList.remove('hidden');
            waitingMessage.classList.remove('hidden');
            imageContainer.style.display = 'flex';
            console.log('Attempting to show progressBarContainer', progressBarContainer.classList, progressBarContainer.style.display);

            // Temporarily remove the border for imageContainer
            imageContainer.style.boxShadow = 'none'; // Add this line to remove the border

            // Retrieve the connectionId from local storage
            const connectionId = localStorage.getItem('connectionId');

            if (!connectionId) {
                console.error('No connectionId available for the API call.');
                return;
            }
        
            let bodyData = {
                'connectionId': connectionId,
                'hero': getValueOrCustom('hero-dropdown', 'hero-custom-input'),
                'personality': getValueOrCustom('personality-dropdown', 'personality-custom-input'),
                'sport': getValueOrCustom('sport-dropdown', 'sport-custom-input'),
                'color': getValueOrCustom('color-dropdown', 'color-custom-input'),
                'action': getValueOrCustom('action-dropdown', 'action-custom-input')
            };
        
            console.log("Submitting data with connectionId:", bodyData);
        
            fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': apiKey
                },
                body: JSON.stringify(bodyData)
            })
            .then(response => {
                // Assuming you process the response here and possibly
                
                // Restore the original border style
                imageContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
            })
            .catch(error => {
                console.error('Error submitting initial request:', error);
                
                // Restore the original box-shadow style even in case of an error
                imageContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
            });
            // Note: No handling of the response here. Waiting for WebSocket notification.
        });

        function fetchProcessedData() {
            // Log to check if the function is being called
            console.log('fetchProcessedData called');
            const apiKey = 'x4ISPCpxA2ZXNqd7awV5a2SF7YlN5gu9OpVbIVA0';
            const renderId = localStorage.getItem('renderId');
        
            // Log the retrieved renderId to verify it's being correctly fetched from localStorage
            console.log('Retrieved renderId from localStorage:', renderId);
        
            if (!renderId) {
                console.error('No renderId found in localStorage.');
                // Optionally, handle this case by updating UI or notifying the user
                return; // Exit the function if no renderId is present
            }
        
            const fetchUrl = `https://api.draftmerch.com/rcv_ima?renderId=${renderId}`;
        
            // Log the fetch URL to verify it's correctly constructed
            console.log('Fetching processed data from URL:', fetchUrl);
            
            fetch(fetchUrl, {
                method: 'GET',
                headers: { 'x-api-key': apiKey }
            })
            .then(response => {
                // Log the HTTP response status to check if the request was successful
                console.log(`Received response from ${fetchUrl}:`, response.status);
        
                // Ensure response is OK before proceeding to parse it as JSON
                if (!response.ok) {
                    throw new Error(`HTTP error, status = ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Log the received data to inspect its structure and content
                console.log('Data received from API:', data);
        
                // Handle retrieved data - like displaying images and filenames
                updateUIWithRetrievedData(data);
            })
            .catch(error => {
                // Log any errors encountered during the fetch operation
                console.error('Error fetching processed data:', error);
            });
        }
        
        
        // Assume this function is declared in the scope where it can access your UI elements
        function updateUIWithRetrievedData(data) {
            imageContainer.innerHTML = ""; // Clear previous content
        
            // Assuming data receives both original (vector or non-watermarked) and watermarked URLs.
            originalImageUrl = data.original_image_url; 
            const watermarkedImageUrl = data.watermarked_image_url;
            const imageFilename = data.filename;

            const imageWrapper = document.createElement('div');
            imageWrapper.className = 'image-wrapper checkered-background';
        
            // Display the watermarked image but store the original image URL as well
            imageWrapper.innerHTML = `
                <a href="${watermarkedImageUrl}" target="_blank">
                    <img src="${watermarkedImageUrl}" id="resultImage" data-filename="${imageFilename}" data-original-url="${originalImageUrl}">
                </a>
            `;
        
            imageContainer.appendChild(imageWrapper);
            
            // UI reset actions
            vectorizeSwitch.disabled = false;
            vectorizeSwitchContainer.classList.remove('hidden');
            form.classList.remove('hidden');
            waitingMessage.classList.add('hidden');
            loading.classList.add('hidden');
            progressBarContainer.classList.add('hidden');
            resetProgressBar();
        }
        
        vectorizeSwitch.addEventListener('change', function() {
            const renderId = localStorage.getItem('renderId'); // Retrieve renderId from local storage
        
            if (this.checked) {
                if (renderId) {
                    console.log('Attempting to upscale/vectorize image with renderId:', renderId);
                    upscaleImage(renderId); // Call upscaleImage with only renderId
                } else {
                    console.error('Error: renderId not provided for upscaling/vectorization.');
                    this.checked = false;
                }
            } else {
                console.log('No action is taken. Showing the current image as per switch state:', this.checked);
            }
        });

        function upscaleImage(renderId) {
            console.log('Upscaling image with renderId:', renderId);
            resetProgressBar();
        
            // Assuming imageOverlay and overlayMessage handling remains the same
            let imageOverlay = document.getElementById('imageOverlay');
            let overlayMessage = document.getElementById('overlayMessage');
            let progressBarContainer = document.getElementById('progressBarContainer');
        
            if (!imageOverlay || !overlayMessage) {
                // Create overlay elements dynamically
                imageOverlay = document.createElement('div');
                imageOverlay.id = 'imageOverlay';
                imageOverlay.className = 'overlay';
                overlayMessage = document.createElement('p');
                overlayMessage.id = 'overlayMessage';
                overlayMessage.innerText = 'Vectorizing image, please wait...';
                imageOverlay.appendChild(overlayMessage);
                document.getElementById('imageContainer').appendChild(imageOverlay);
            
                // Append progressBarContainer below the overlayMessage
                if (!progressBarContainer) {
                    // If progressBarContainer does not exist, create it or fetch it from your existing DOM structure
                    progressBarContainer = document.createElement('div');
                    progressBarContainer.id = 'progressBarContainer';
                    // Add any additional properties or classes to progressBarContainer here
                }
                imageOverlay.appendChild(progressBarContainer);
                
                document.getElementById('imageContainer').style.display = 'flex'; // Adjust this line as necessary
            
            } else {
                // If they exist, simply update overlayMessage's text
                overlayMessage.innerText = 'Vectorizing image, please wait...';
                // Ensure progressBarContainer is positioned correctly
                if (progressBarContainer && progressBarContainer.parentNode !== imageOverlay) {
                    imageOverlay.appendChild(progressBarContainer);
                }
            }
            // Hide Buttons and Overlay
            imageOverlay.classList.remove('hidden');
            document.querySelector('form').classList.add('hidden');
            progressBarContainer.classList.remove('hidden');
            vectorizeSwitchContainer.classList.add('hidden');
        
            // URLs of the text files
            const textFilesUrls = [
                'https://draftmerch.com/text_data/messages/list.txt',
                'https://draftmerch.com/text_data/messages/list2.txt',
                'https://draftmerch.com/text_data/messages/list3.txt'
            ];
        
            // Function to fetch and return text file content as an array of lines
            async function fetchTextFile(url) {
                const response = await fetch(url);
                const text = await response.text();
                return text.split('\n'); // Assuming each message is on a new line
            }
        
            // Function to update the overlay message periodically
            async function updateMessage(messages) {
                let messageIndex = 0;
        
                function changeMessage() {
                    if (messageIndex >= messages.length) {
                        messageIndex = 0; // Loop back to the first message
                    }
                    overlayMessage.innerText = messages[messageIndex++];
                    setTimeout(changeMessage, 8000 + Math.random() * 2000); // Schedule next update
                }
        
                changeMessage();
            }
        
            // Select a random text file URL and start updating messages
            const selectedFileUrl = textFilesUrls[Math.floor(Math.random() * textFilesUrls.length)];
            fetchTextFile(selectedFileUrl)
                .then(messages => updateMessage(messages))
                .catch(error => console.error('Failed to fetch text file:', error));
        
            const apiUrl = 'https://api.draftmerch.com/fnl_ima';
            const apiKey = 'x4ISPCpxA2ZXNqd7awV5a2SF7YlN5gu9OpVbIVA0';
            const connectionId = localStorage.getItem('connectionId');
            
            // Prepare the request body with renderId
            let bodyData = { 'renderId': renderId, 'connectionId': connectionId }
            console.log('Sending request to API with body:', bodyData);
        
            fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': apiKey
                },
                body: JSON.stringify(bodyData)
            }).then(response => response.json())
            .then(data => {
                console.log('Initiated image processing, waiting for completion...');
                waitForProcessingComplete(renderId); // Wait for WebSocket message before proceeding
            })
            .catch(error => {
                console.error('Error during image processing initiation:', error);
                imageOverlay.classList.add('hidden'); // Hide the overlay on error
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
        
        // This function waits for a specific WebSocket message before proceeding
        function waitForProcessingComplete(renderId) {
            return new Promise((resolve, reject) => {
                // Attach a temporary event listener to the WebSocket
                const tempListener = (event) => {
                    console.log('WebSocket message received:', event.data);
                    const message = JSON.parse(event.data);
                    if (message.status === "VectorComplete" && message.renderId === renderId) {
                        console.log('Vector image processing complete. Fetching vector data...');
                        websocket.removeEventListener('message', tempListener); // Clean up listener
                        resolve(message.renderId); // Resolve the promise with the renderId
                    }
                };
                websocket.addEventListener('message', tempListener);
            });
        }
        
        function fetchVectorData(renderId) {
            console.log(`fetchVectorData called with renderId: ${renderId} at ${new Date().toISOString()}`);
            const apiKey = 'x4ISPCpxA2ZXNqd7awV5a2SF7YlN5gu9OpVbIVA0';
            const fetchUrl = `https://api.draftmerch.com/rcv_vec?renderId=${renderId}`; // Construct URL with renderId as query parameter
            console.log("Fetching vector data from URL:", fetchUrl);
            

            fetch(fetchUrl, {
                method: 'GET', // Using GET request
                headers: {
                    'x-api-key': apiKey
                }
            })
            .then(response => {
                // Check for a successful response
                if (!response.ok) {
                    throw new Error(`HTTP error, status = ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if(data.vectorImageUrl && data.watermarkedVectorImageUrl) {
                    // Assuming the data object includes vectorImageUrl and watermarkedVectorImageUrl
                    updateUIWithVectorData(data);
                } else {
                    console.error('Vector data did not contain expected URLs.');
                }
            })
            .catch(error => {
                console.error('Error fetching vector data:', error);
            });
        }

        function updateUIWithVectorData(data) {
            // First, check if the progressBarContainer is already detached or needs to be detached.
            const progressBarContainer = document.getElementById('progressBarContainer');
        
            // Clear the contents of the imageContainer to prepare for new content.
            imageContainer.innerHTML = ""; 
        
            // Process the data received to update the UI with the vectorized or watermarked images.
            const originalVectorImageUrl = data.vectorImageUrl; 
            const watermarkedVectorImageUrl = data.watermarkedVectorImageUrl;
            const imageFilename = data.filename; 
        
            // Logging the image URLs for debugging or informational purposes.
            console.log("Original Vector Image URL:", originalVectorImageUrl);
            console.log("Watermarked Vector Image URL:", watermarkedVectorImageUrl);
        
            // Create a new div element to wrap the image, applying a class for styling.
            const imageWrapper = document.createElement('div');
            imageWrapper.className = 'image-wrapper checkered-background';
        
            // Set the inner HTML of the wrapper to include the watermarked vector image.
            imageWrapper.innerHTML = `
                <a href="${watermarkedVectorImageUrl}" target="_blank">
                    <img src="${watermarkedVectorImageUrl}" id="vectorResultImage" class="checkered-background" data-filename="${imageFilename}" data-original-url="${originalVectorImageUrl}">
                </a>
            `;
        
            // If the progressBarContainer was successfully detached earlier, re-attach it to its original location.
            // This step is crucial if you had removed it to prevent deletion during content clearing.
            if (progressBarContainer) {
                document.body.insertBefore(progressBarContainer, imageContainer.nextSibling);
                progressBarContainer.classList.add('hidden'); // Hide the progressBarContainer after reinserting it.
            }
        
            // Append the new imageWrapper to the imageContainer.
            imageContainer.appendChild(imageWrapper);
        
            // Update actions for the download button, if applicable.
            const downloadButton = document.getElementById('downloadSvgButton');
            if (downloadButton) {
                downloadButton.onclick = function() { window.open(originalVectorImageUrl, '_blank'); };
            }
        
            // Reset UI elements to their default state or visibility.
            vectorizeSwitch.disabled = false;
            downloadContainer.classList.remove('hidden');
            waitingMessage.classList.add('hidden');
            loading.classList.add('hidden');
            resetProgressBar();
        }        
        
        // Function to handle WebSocket progress updates and initiate progress bar increase
        function updateProgressBar(percentage) {
            targetProgress = percentage; // Updated by WebSocket message
            processProgressUpdate(); // Call a function to act based on the new target
        }

        // Simplified interval configurations with just speeds
        const progressConfig = {
            intervals: [
                { range: [0, 3], speed: 20 },  // Fast updates
                { range: [3, 70], speed: 140 }, // Medium updates
                { range: [70, 93], speed: 30 }, // Slow updates
                { range: [93, 100], speed: 10 }  // Very slow updates
            ]
        };

        function processProgressUpdate() {
            let nextTarget;
            // Extract steps from the intervals configuration
            const steps = progressConfig.intervals.map(interval => interval.range[0]);
            steps.push(100); // Ensure the final step (100) is included for completeness

            for (let i = 0; i < steps.length; i++) {
                if (currentProgress < steps[i] && targetProgress >= steps[i]) {
                    nextTarget = steps[i];
                    break;
                }
            }

            if (!nextTarget || currentProgress >= steps[steps.length - 1]) {
                nextTarget = targetProgress;
            }

            if (currentProgress < nextTarget) {
                // Simplify step calculation without stepDivisor
                const step = Math.max(0.1, (nextTarget - currentProgress) / 100);
                increaseProgress(step, nextTarget); // No need to pass speed here, it's handled within increaseProgress
            }
        }

        function increaseProgress(step, nextTarget) {
            if (intervalgenID !== null) {
                clearInterval(intervalgenID);
                intervalgenID = null;
            }

            // Find the matching interval for the current progress to determine the interval speed
            const matchingInterval = progressConfig.intervals.find(interval =>
                currentProgress >= interval.range[0] && currentProgress < interval.range[1]
            );
            let intervalDuration = matchingInterval ? matchingInterval.speed : 100; // Default to 100 if no matching interval

            intervalgenID = setInterval(() => {
                if (currentProgress < nextTarget && currentProgress < targetProgress) {
                    currentProgress += step;
                    progressBar.style.width = currentProgress + '%';
                } else {
                    clearInterval(intervalgenID);
                    intervalgenID = null;

                    if (currentProgress > targetProgress) {
                        currentProgress = targetProgress;
                        progressBar.style.width = currentProgress + '%';
                    }

                    if (nextTarget < targetProgress) {
                        processProgressUpdate(); // Continue updates if needed
                    }
                }
            }, intervalDuration);
        }


        function resetProgressBar() {
            // Reset progress variables to initial state
            currentProgress = 0;
            targetProgress = 0;
            
            // Clear any running general progress bar interval to prevent overlapping intervals
            if (intervalgenID !== null) {
                clearInterval(intervalgenID);
                intervalgenID = null;
            }
        
            // Similarly, clear any running vector progress bar interval
            if (intervalvecID !== null) {
                clearInterval(intervalvecID);
                intervalvecID = null;
            }
            
            // Check if the progressBarContainer exists and is correctly displayed
            let progressBarContainer = document.getElementById('progressBarContainer');
            if (progressBarContainer) {
                progressBarContainer.style.display = 'block'; // Ensure it's visible
            } else {
                // If it doesn't exist, you could potentially recreate it or handle the absence appropriately
            }
            
            // Reset the general progress bar to 0%
            let progressBar = document.getElementById('progressBar'); // Assuming this ID is for the general progress bar
            if (progressBar) {
                progressBar.style.width = '0%';
            }
            
            // If the vector progress bar uses a different element, reset it as well
            // Assuming you have an ID assigned to the vector progress bar element, e.g., 'vectorProgressBar'
            let vectorProgressBar = document.getElementById('vectorProgressBar'); // Adjust the ID accordingly
            if (vectorProgressBar) {
                vectorProgressBar.style.width = '0%';
            }
        }
        
        // Define interval speeds for vector progress updates in a single structure
        const vectorProgressConfig = {
            intervals: [
                { range: [1, 19], speed: 100 },  // Interval 1: Fast updates (1-10)
                { range: [20, 59], speed: 120 }, // Interval 2: Slow updates (11-34)
                { range: [60, 79], speed: 200 }, // Interval 3: Medium updates (34-46)
                { range: [80, 100], speed: 30 } // Interval 4: Slow updates again (46-100)
            ]
        };

        function updateProgressVectorBar(percentage) {
            console.log(`Updating vector progress bar to ${percentage}%`); // Debug log
            targetProgress = percentage; // Updated by WebSocket message
            processVectorProgressUpdate(); // Call the function to act based on the new target
        }

        function processVectorProgressUpdate() {
            let nextTarget;
            // Extract steps from the intervals configuration for clarity and completeness
            const steps = vectorProgressConfig.intervals.map(interval => interval.range[0]);
            steps.push(100); // Include the final step explicitly

            for (let i = 0; i < steps.length; i++) {
                if (currentProgress < steps[i] && targetProgress >= steps[i]) {
                    nextTarget = steps[i];
                    break;
                }
            }

            if (!nextTarget || currentProgress >= steps[steps.length - 1]) {
                nextTarget = targetProgress;
            }

            if (currentProgress < nextTarget) {
                const step = Math.max(0.1, (nextTarget - currentProgress) / 100); // Keep step calculation consistent
                increaseVectorProgress(step, nextTarget);
            }
        }

        function increaseVectorProgress(step, nextTarget) {
            if (intervalvecID !== null) {
                clearInterval(intervalvecID);
                intervalvecID = null;
            }

            // Find the matching interval for the current progress to determine the interval speed
            const matchingInterval = vectorProgressConfig.intervals.find(interval =>
                currentProgress >= interval.range[0] && currentProgress < interval.range[1]
            );
            let intervalDuration = matchingInterval ? matchingInterval.speed : 100; // Default to 100 if no matching interval

            intervalvecID = setInterval(() => {
                if (currentProgress < nextTarget && currentProgress < targetProgress) {
                    currentProgress += step;
                    progressBar.style.width = currentProgress + '%';
                } else {
                    clearInterval(intervalvecID);
                    intervalvecID = null;

                    if (currentProgress > targetProgress) {
                        currentProgress = targetProgress;
                        progressBar.style.width = currentProgress + '%';
                    }

                    if (nextTarget < targetProgress) {
                        processVectorProgressUpdate(); // Continue updates if needed
                    }
                }
            }, intervalDuration);
        }
        document.getElementById('returnButton').addEventListener('click', function() {
            form.classList.remove('hidden');
            waitingMessage.classList.add('hidden');
            downloadContainer.classList.add('hidden');
            resetProgressBar();
        });
        
        // Call the function with the duration in milliseconds, e.g., 5000 milliseconds for 5 seconds

    loadDropdownData('color','https://draftmerch.com/text_data/dropdown_color.txt');
    loadDropdownData('hero', 'https://draftmerch.com/text_data/dropdown_hero.txt');
    loadDropdownData('personality', 'https://draftmerch.com/text_data/dropdown_personality.txt');
    loadDropdownData('sport', 'https://draftmerch.com/text_data/dropdown_sport.txt');
    loadDropdownData('action', 'https://draftmerch.com/text_data/dropdown_action.txt');

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
    const baseUrl = 'https://draftmerch.com/text_data';
    
    if (selectedHero.trim() === 'custom') {
        // Reset the dropdowns if no hero is selected or if it's set back to empty
        loadDropdownData('personality', `${baseUrl}/dropdown_personality.txt`);
        loadDropdownData('action', `${baseUrl}/dropdown_action.txt`);
    } else {
        // Load personality and action for the chosen hero
        loadDropdownData('personality', `${baseUrl}/personality_data/${selectedHero}_personality.txt`);
        // For action, combine options from the specific character and extra actions
        // Assuming loadDropdownData can accept multiple sources for a single dropdown as an array or additional arguments
        loadDropdownData('action', `${baseUrl}/action_data/${selectedHero}_action.txt`, `${baseUrl}/extra_action.txt`);
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
    //if (dropdownId === 'hero') {
    //    dropdown.appendChild(new Option('Upload Image', 'Upload Image'));
    //}

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

