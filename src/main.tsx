import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import AppWeb from './App-web.tsx'
import './index.css'

const queryClient = new QueryClient()

// Choose the right App component based on environment
const AppComponent = import.meta.env.VITE_MODE === 'web' ? AppWeb : App;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
        <AppComponent />
    </QueryClientProvider>
  </React.StrictMode>,
)
