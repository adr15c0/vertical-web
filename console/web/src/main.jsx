import React from 'react';
import { createRoot } from 'react-dom/client';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import App from './App.jsx';

// Brand green primary (matches the site's Global Color #15c586).
const theme = createTheme({
  palette: {
    primary: { main: '#15c586' },
    secondary: { main: '#2b79ee' },
    background: { default: '#f4f5f7' },
  },
  shape: { borderRadius: 10 },
});

createRoot(document.getElementById('root')).render(
  <ThemeProvider theme={theme}>
    <CssBaseline />
    <App />
  </ThemeProvider>,
);
