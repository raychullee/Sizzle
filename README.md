# Sizzle - Animated Recipe Assistant

An AI-powered recipe assistant with animated step-by-step cooking instructions.

## Features

- Get detailed recipes with ingredients and instructions
- Ask follow-up questions about cooking techniques
- Get suggestions for ingredient substitutions
- Animated recipe steps with 2D visualizations
- Animated ingredients and equipment displays

## Project Structure

The project is split into two main parts:

- `backend/`: Python FastAPI backend with LangChain integration
- `frontend/`: Next.js frontend with animations via Framer Motion

## Tech Stack

Frontend:
- Next.js (React-based) with Framer Motion for animations
- TypeScript for type safety
- Tailwind CSS for styling

Backend:
- Python with LangChain and OpenAI
- FastAPI to create an API layer 
- Support for AI-generated animations (planned)

Database (planned):
- PostgreSQL with Supabase for user authentication and profile management
- Redis for caching frequent recipe requests

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

4. Start the backend server:
   ```
   uvicorn app:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Features

- Chat interface for asking about recipes
- Animated recipe steps for visualizing cooking processes
- Visual representations of ingredients and cooking equipment
- Step-by-step animated cooking instructions

## Roadmap for Animation Enhancement

1. **Phase 1: Foundation**
   - Basic animations using Framer Motion
   - Ingredient and equipment visualization
   - Cooking action animations

2. **Phase 2: AI Integration**
   - Connect to Stability AI or similar APIs
   - Generate custom animations for specific recipe steps
   - Build animation library for common cooking actions

3. **Phase 3: Advanced Animations**
   - Real-time animation generation
   - User-customizable animations
   - Mobile-optimized animations

## Deployment

For production deployment, consider:

- Frontend: Vercel, Netlify, or AWS Amplify
- Backend: AWS Lambda, Google Cloud Run, or Oracle Cloud
- Database: PostgreSQL with Supabase for user authentication

## TODO 

1. Expand the Animation Library:
   - Add more cooking actions (bake, grill, simmer, blend)
   - Create more ingredient-specific animations
   - Implement more complex multi-step animations
2. Integrate with AI Image Generation:
   - Use Stability AI API or DALL-E to generate custom cooking visuals
   - Build a preprocessing pipeline to convert AI images to animation frames
   - Implement a caching system for frequently requested animations
3. Enhance Existing Animations:
   - Add more physics-based motion (liquid flowing, dough rising)
   - Improve transitions between animation states
   - Add optional sound effects for immersion
4. Technical Improvements:
   - Use Lottie for vector-based animations (smaller file size)
   - Implement lazy loading for better performance
   - Create adaptive animations that respond to screen size
5. User Experience:
   - Add playback controls (pause, rewind, slow down)
   - Create hover states with additional information
   - Allow users to toggle between simplified/detailed animations
