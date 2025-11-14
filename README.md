# Draftmerch - The AI-Powered Logo Generator

**Project Status:** archived
**Learn More:** [**donphi.work/works/draftmerch**](https://www.donphi.work/works/draftmerch)

---

### The Story

Draftmerch was a magical tool for creating consistent, high-quality, AI-generated logos. It was a passion project and a fantastic learning experience, built with ChatGPT-3 acting as a co-writer.

Instead of a simple text prompt, Draftmerch used a unique pipeline. Users would pick from pre-defined lists of **characters, sports, fun actions, and environments**. This would generate a specific, repeatable prompt and a **seeding ID**, which was fed into the **DALL-E 2** API to render a consistent and fun logo.

Once a design was created, you could run a second pipeline. This serverless process would:
1.  Send the image to an **upscaling API** to double its size.
2.  Send the upscaled image to a **vectorization API** to create a perfect, print-ready vector file.

### The Hard Stop

Ultimately, the project had to be shut down. The operational costs for the **AWS** services (especially Lambda) and the **OpenAI API** tokens became too high to sustain for a personal project.

This was a tough decision, as many of my friends' children loved it. A special shout-out to my biggest fan, **Eli ❤️**, who was heartbroken when it went offline.

### What was it?

* **Consistent AI Design Pipeline:** Generated repeatable designs from fun, pre-set categories.
* **Print-Ready Vectorization:** A multi-step API pipeline to automatically upscale and vectorize images for print.
* **Fully Serverless Architecture:** The entire backend was built on **AWS Lambda** workers executing the API pipeline.

### 🤫 The Secret Sauce

The core of this project was the unique prompt and seeding technique used to get consistent results from DALL-E 2. This wasn't a simple, single-line prompt; it was a **five-paragraph, hyper-engineered prompt** that took months to perfect.

To this day, that prompt remains a secret. However, if you're a fellow developer or researcher, **feel free to reach out, and I'll be happy to share it with you.**

### Technology Stack

* **Framework:** **Next.js**
* **Language:** **TypeScript**
* **API:** **tRPC**
* **Styling:** **Tailwind CSS**
* **Backend:** **AWS Lambda** (Serverless Workers)
* **Database:** **Amazon DynamoDB** ("AWS tables")
* **AI Pipeline:** **OpenAI (DALL-E 2)**
* **Image Processing:** (External APIs for upscaling and vectorization)

### Running This Code (Archive)

As this project is archived, it is no longer maintained. To run it locally, you would need to:

1.  Clone the repository.
2.  Install dependencies with `npm install`.
3.  Create a `.env.local` file.
4.  Provide your own API keys for **OpenAI** and any image processing APIs.
5.  Set up **AWS IAM** credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) with permissions for **Lambda** and **DynamoDB**.
6.  Run the development server with `npm run dev`.
