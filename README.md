# HomePilot

HomePilot is a full-stack home-services booking platform presented under the HomeFix Pro brand. Customers can browse services, make bookings, upload reference images, pay online or in cash, and track job progress. Administrators and technicians have dedicated dashboards for managing the service workflow.

## Tech stack

- React, React Router, Tailwind CSS, and Radix UI
- FastAPI and MongoDB
- Local filesystem storage for uploads
- Optional Resend email delivery
- Optional Stripe Checkout payments

## Run locally

Requirements: Node.js 18+, Python 3.10+, and MongoDB.

1. Copy `backend/.env.example` to `backend/.env` and update the values.
2. Copy `frontend/.env.example` to `frontend/.env` and update the backend URL if needed.
3. Install and start the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m uvicorn server:app --reload
   ```

4. In another terminal, install and start the frontend:

   ```powershell
   cd frontend
   npm install
   npm start
   ```

The frontend runs at `http://localhost:3000` and the API at `http://localhost:8000/api`.

## Optional services

Emails fall back to application logs until `RESEND_API_KEY` and `EMAIL_FROM` are set. Cash bookings work without payment configuration. To accept online payments, configure `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`, then point your Stripe webhook to `/api/webhook/stripe`.

Uploaded images are stored under `backend/data/uploads` by default. Set `UPLOAD_DIR` if your deployment uses a persistent mounted volume.

## Tests and builds

```powershell
cd backend
pytest

cd ..\frontend
npm test -- --watchAll=false
npm run build
```

## Production notes

- Replace `JWT_SECRET` and the initial admin password.
- Use a managed MongoDB database and a persistent upload volume.
- Set `CORS_ORIGINS` to your deployed frontend domain.
- Serve the FastAPI app behind HTTPS and a production process manager.
