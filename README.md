# Keystroke & Mouse Dynamics Auth Project

## Running the React Frontend

1. Go to the `frontend` folder:
   ```sh
   cd frontend
   ```
2. Install dependencies:
   ```sh
   npm install
   ```
3. Start the development server:
   ```sh
   npm run dev
   ```
4. Open [http://localhost:5173](http://localhost:5173) in your browser.

The React app will communicate with your backend (FastAPI, etc.) on the default ports. Make sure your backend is running as well.

---

# DeepPavlov GPT-like Chatbot

## Local Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the API:
   ```bash
   python api.py
   ```
3. Send POST requests to `http://localhost:8000/chat` with JSON `{ "message": "your text" }`

## Deploying to Vercel

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```
2. Add a `vercel.json` config (see Vercel docs for Python serverless functions).
3. Deploy:
   ```bash
   vercel
   ```

---

**Note:** DeepPavlov models can be large and may have cold start times on serverless platforms. For best results, use Vercel's Python support and test locally first. 