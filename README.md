# Draftmerch - The AI-Powered Logo Generator

**Project Status:** archived
**Learn More:** [**donphi.work/works/draftmerch**](https://www.donphi.work/works/draftmerch)

---

### The Story

Draftmerch was a magical tool for creating consistent, high-quality, AI-generated logos, designed specifically for sports fantasy leagues. It was a passion project and a fantastic learning experience, built with ChatGPT-3 acting as a co-writer.

Instead of a simple text prompt, Draftmerch used a unique pipeline. Users would pick from pre-defined lists of **characters, sports, fun actions, and environments**. This would generate a specific, repeatable prompt and a **seeding ID**, which was fed into the **OpenAI** API to render a consistent and fun logo.

Once a design was created, a second serverless pipeline would run:
1.  Use **Python** and **OpenCV** for sophisticated image manipulation and upscaling.
2.  Send the image to a **vectorization API** to create a perfect, print-ready vector file.

### The Hard Stop

Ultimately, the project had to be shut down. The operational costs for the **AWS** services (especially Lambda) and the **OpenAI API** tokens became too high to sustain for a personal project.

This was a tough decision, as many of my friends' children loved it. A special shout-out to my biggest fan, **Eli ❤️**, who was heartbroken when it went offline.

### 🤫 The Secret Sauce

The core of this project was the unique prompt and seeding technique used to get consistent results from DALL-E 2. This wasn't a simple, single-line prompt; it was a **five-paragraph, hyper-engineered prompt** that took months to perfect.

To this day, that prompt remains a secret. However, if you're a fellow developer or researcher, **feel free to reach out, and I'll be happy to share it with you.**

### 💻 Technology Stack

This project was a full-stack, serverless application.

* **Frontend:** Hand-coded with love using **HTML, CSS, and vanilla JavaScript**.
* **Backend Logic:** **Python** & **AWS Lambda** (a 12-stage pipeline).
* **AI & Image Processing:** **OpenAI** & **OpenCV**.
* **Database:** **Amazon DynamoDB**.
* **API & Real-Time:** **AWS API Gateway** & **Websockets**.
* **CI/CD Pipeline:** A seamless **CI/CD** (Continuous Integration/Continuous Deployment) pipeline using **AWS CodeBuild** & **AWS CodePipeline**. This provided automated, seamless updates from **GitHub** directly to the 12-stage **AWS Lambda** servers.
* **Security:** **AWS Secret Manager**.

### Running This Code (Archive)

As this project is archived, it is no longer maintained. Running it would be a complex undertaking, requiring:

1.  Cloning the repository.
2.  Setting up the frontend (e.g., serving the static HTML/JS/CSS files).
3.  Configuring the entire AWS backend, including:
    * Deploying the **Python** code to **AWS Lambda**.
    * Setting up the **DynamoDB** tables.
    * Configuring **API Gateway** and **Websockets**.
    * Populating **AWS Secret Manager** with your **OpenAI** API keys and other credentials.
    * Rebuilding the **CodePipeline** and **CodeBuild** CI/CD process.
