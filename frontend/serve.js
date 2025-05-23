const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = process.env.PORT || 3001;

// Function to determine the content type based on file extension
function getContentType(filePath) {
  const extname = path.extname(filePath);
  switch (extname) {
    case '.html':
      return 'text/html';
    case '.js':
      return 'text/javascript';
    case '.css':
      return 'text/css';
    case '.json':
      return 'application/json';
    case '.png':
      return 'image/png';
    case '.jpg':
    case '.jpeg':
      return 'image/jpeg';
    case '.gif':
      return 'image/gif';
    case '.svg':
      return 'image/svg+xml';
    default:
      return 'text/plain';
  }
}

// Explicitly set backend port to 5000 for consistency
let BACKEND_PORT = 5000;
// Hardcoding port 5000 as requested by the user for consistency
console.log('Using hardcoded backend port 5000 for API server (ignoring backend_port.txt)');

process.env.BACKEND_PORT = BACKEND_PORT.toString();
console.log(`Using backend port ${BACKEND_PORT} to connect to the API server`);

// Create a simple HTTP server
const server = http.createServer((req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Parse URL and query parameters
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const query = parsedUrl.query;
  
  // Enhance logging for debugging
  console.log(`Request received: ${req.method} ${req.url}`);
  console.log(`Parsed pathname: ${pathname}, Query params:`, query);
  
  // Handle OPTIONS request
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  // Define routes that should serve the React app
  const reactRoutes = ['/agents', '/agent-overview', '/analytics', '/settings'];
  
  // Define routes that should serve the static app
  const staticRoutes = ['/', '/index.html', '/dashboard'];
  
  // If the request is for one of the React app routes, serve the React app HTML
  if (reactRoutes.includes(pathname) || pathname.startsWith('/agents/')) {
    console.log(`Serving React application for route: ${pathname}`);
    fs.readFile(path.join(__dirname, 'react-app.html'), (err, data) => {
      if (err) {
        console.error('Error reading react-app.html:', err);
        res.writeHead(500);
        res.end('Error loading react-app.html');
        return;
      }
      
      res.writeHead(200, { 
        'Content-Type': 'text/html',
        'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'no-store'
      });
      res.end(data);
    });
    return;
  }
  
  // If the request is for one of the static app routes, serve the static app HTML
  if (staticRoutes.includes(pathname)) {
    console.log(`Serving static application for route: ${pathname}`);
    fs.readFile(path.join(__dirname, 'static-app.html'), (err, data) => {
      if (err) {
        console.error('Error reading static-app.html:', err);
        res.writeHead(500);
        res.end('Error loading static-app.html');
        return;
      }
      
      res.writeHead(200, { 
        'Content-Type': 'text/html',
        'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'no-store'
      });
      res.end(data);
    });
    return;
  }
  
  // Handle chat specifically
  if (pathname === '/chat' || pathname.startsWith('/chat/')) {
    console.log('Serving chat interface');
    fs.readFile(path.join(__dirname, 'simple-chat.html'), (err, data) => {
      if (err) {
        console.error('Error reading simple-chat.html:', err);
        res.writeHead(500);
        res.end('Error loading simple-chat.html');
        return;
      }
      
      res.writeHead(200, { 
        'Content-Type': 'text/html',
        'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'no-store'
      });
      res.end(data);
    });
    return;
  }
  
  // Serve the agent routing architecture diagram
  if (pathname === '/routing-architecture' || pathname === '/agent_routing_architecture.html') {
    fs.readFile(path.join(__dirname, 'agent_routing_architecture.html'), (err, data) => {
      if (err) {
        res.writeHead(500);
        res.end('Error loading agent_routing_architecture.html');
        return;
      }
      
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(data);
    });
    return;
  }
  
  // Serve the test page - check pathname and query parameters
  if (pathname === '/test' || 
      pathname === '/test.html' || 
      (pathname === '/' && (query.frontend_page === 'test' || query.page === 'test'))) {
    
    console.log('Serving test page');
    fs.readFile(path.join(__dirname, 'test.html'), (err, data) => {
      if (err) {
        res.writeHead(500);
        res.end('Error loading test.html');
        return;
      }
      
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(data);
    });
    return;
  }
  
  // Directly serve react-app.html when requested
  if (pathname === '/react-app.html') {
    console.log('Serving react-app.html directly');
    fs.readFile(path.join(__dirname, 'react-app.html'), (err, data) => {
      if (err) {
        console.error('Error reading react-app.html:', err);
        res.writeHead(500);
        res.end('Error loading react-app.html');
        return;
      }
      
      res.writeHead(200, { 
        'Content-Type': 'text/html',
        'X-Content-Type-Options': 'nosniff',
        'Cache-Control': 'no-store'
      });
      res.end(data);
    });
    return;
  }
  
  // Serve static assets for the React application (JavaScript, CSS, etc.)
  // Skip API paths - they should always be proxied to the backend
  if (!pathname.startsWith('/api/') && 
      (pathname.startsWith('/static/') || pathname.includes('.js') || pathname.includes('.css') || 
      pathname.includes('.png') || pathname.includes('.jpg') || pathname.includes('.svg') || 
      pathname.includes('.json'))) {
    console.log(`Static asset request: ${pathname}`);
    
    // Try serving from the React app's src directory first
    const srcPath = path.join(__dirname, 'src', pathname);
    
    if (fs.existsSync(srcPath)) {
      const contentType = getContentType(srcPath);
      fs.readFile(srcPath, (err, data) => {
        if (err) {
          res.writeHead(500);
          res.end(`Error loading ${pathname}`);
          return;
        }
        
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(data);
      });
      return;
    }
    
    // If not found in src directory, look in the node_modules
    const nodeModulesPath = path.join(__dirname, 'node_modules', pathname.replace('/static/', ''));
    
    if (fs.existsSync(nodeModulesPath)) {
      const contentType = getContentType(nodeModulesPath);
      fs.readFile(nodeModulesPath, (err, data) => {
        if (err) {
          res.writeHead(500);
          res.end(`Error loading ${pathname}`);
          return;
        }
        
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(data);
      });
      return;
    }
    
    // If asset not found, try a fallback
    res.writeHead(404);
    res.end(`Static asset not found: ${pathname}`);
    return;
  }
  
  // Handle API requests by proxying them to the backend
  if (req.url.startsWith('/api/')) {
    console.log(`API request received: ${req.method} ${req.url}`);
    
    // All API requests are proxied to the backend
    const backendHost = '127.0.0.1';
    const backendPort = process.env.BACKEND_PORT || BACKEND_PORT;
    
    console.log(`Proxying API request to ${backendHost}:${backendPort}${req.url}`);
    
    // Copy headers from original request but clean them up
    const headers = {};
    for (const [key, value] of Object.entries(req.headers)) {
      // Skip headers that might cause issues when proxying
      if (['host', 'connection', 'origin', 'referer'].includes(key.toLowerCase())) {
        continue;
      }
      headers[key] = value;
    }
    
    // Set clean headers needed for the proxy
    headers['host'] = `${backendHost}:${backendPort}`;
    headers['connection'] = 'keep-alive';
    
    // Special handling for Swagger/OpenAPI routes - don't force application/json
    const isSwaggerRequest = req.url.includes('/docs') || req.url.includes('/redoc') || req.url.includes('/openapi.json');
    
    if (!isSwaggerRequest) {
      // Only set these for regular API requests, not for Swagger UI or OpenAPI schema
      headers['content-type'] = 'application/json';
      headers['accept'] = 'application/json';
    }
    
    // Create proxy request to backend API server
    const options = {
      hostname: backendHost,
      port: backendPort,
      path: req.url,
      method: req.method,
      headers: headers,
      timeout: 30000 // 30 second timeout
    };
    
    // Log complete options for debugging
    console.log('Proxy request options:', {
      url: `${backendHost}:${backendPort}${req.url}`,
      method: req.method,
      headers: headers
    });
    console.log(`BACKEND DEBUG: Connecting to backend port ${backendPort} for ${req.method} ${req.url}`);
    
    // Create proxy request to backend
    const proxyReq = http.request(options, (proxyRes) => {
      console.log(`Got response from backend: status ${proxyRes.statusCode}`);
      
      // Set response headers
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      
      // Handling response appropriately based on request type
      if (isSwaggerRequest) {
        // For Swagger UI or OpenAPI schema, pipe the response directly without logging
        // This avoids logging large response bodies
        proxyRes.pipe(res);
      } else {
        // For regular API requests, collect and log the response body for debugging
        let responseBody = '';
        proxyRes.on('data', (chunk) => {
          responseBody += chunk;
        });
        
        proxyRes.on('end', () => {
          // Log up to first 1000 characters to avoid huge log entries
          const truncatedBody = responseBody.length > 1000 
            ? responseBody.substring(0, 1000) + '...<response clipped>'
            : responseBody;
          
          console.log('Backend API response body:', truncatedBody);
          
          // Send the response to the client
          res.end(responseBody);
        });
      }
    });
    
    // Handle errors
    proxyReq.on('error', (error) => {
      console.error(`Error proxying request to ${options.hostname}:${options.port}${req.url}:`, error.message);
      
      // Return a fallback response when backend is unavailable
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: false,
        error: 'Backend service unavailable',
        message: `Cannot connect to backend at ${options.hostname}:${options.port}. Please check if the API server is running.`
      }));
    });
    
    // Forward request body to backend
    if (req.method === 'POST' || req.method === 'PUT') {
      req.on('data', (chunk) => {
        proxyReq.write(chunk);
      });
      
      req.on('end', () => {
        proxyReq.end();
      });
    } else {
      proxyReq.end();
    }
    
    return;
  }
  
  // For any other request, return 404
  res.writeHead(404);
  res.end('Not found');
});

// Start the server
server.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running at http://0.0.0.0:${PORT}`);
  console.log(`Backend API server expected at http://127.0.0.1:${BACKEND_PORT}`);
  console.log(`API requests will be proxied from /api/* to http://127.0.0.1:${BACKEND_PORT}/api/*`);
});