# Frontend Setup Guide

## Quick Start

### 1. Install Node.js (if not already installed)

Download and install Node.js 18+ from [nodejs.org](https://nodejs.org/)

### 2. Navigate to Frontend Directory

```bash
cd c:\xampp\htdocs\NOVARAai\frontend
```

### 3. Install Dependencies

```bash
npm install
```

This will install all required packages including:
- Next.js 14
- React 18
- TypeScript
- TailwindCSS
- Axios
- shadcn/ui components
- Lucide icons

### 4. Start Development Server

```bash
npm run dev
```

The frontend will start at: **http://localhost:3000**

### 5. Access the Application

Open your browser and navigate to:
- **Home**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs (backend Swagger UI)

## Running with Backend

The frontend requires the backend services to be running. Start the backend first:

```bash
# From NOVARAai root directory
cd c:\xampp\htdocs\NOVARAai
docker-compose up -d
```

Then start the frontend:

```bash
cd frontend
npm run dev
```

## Environment Configuration

The frontend uses environment variables to connect to the backend. Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Port 3000 Already in Use

If port 3000 is busy, Next.js will automatically try 3001, 3002, etc.

### Module Not Found Errors

If you see "Cannot find module" errors, run:

```bash
npm install
```

### TypeScript Errors

TypeScript errors are expected before `npm install` is run. They will resolve after installing dependencies.

### Backend Connection Failed

Ensure the backend services are running:

```bash
# Check backend status
curl http://localhost:8000/health
```

## Production Build

To build for production:

```bash
npm run build
npm start
```

The production server will run at http://localhost:3000

## Next Steps

After the frontend is running:

1. Navigate to http://localhost:3000
2. Explore the home page
3. Check the backend API at http://localhost:8000/docs
4. Submit a test application (when implemented)

## Development Tips

- Hot reload is enabled - changes appear automatically
- TypeScript provides type checking in real-time
- TailwindCSS classes are auto-completed in VS Code
- API calls are logged to the browser console

## Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
