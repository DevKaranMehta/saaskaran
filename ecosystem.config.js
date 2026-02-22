module.exports = {
  apps: [
    {
      name: 'saaskaran-backend',
      cwd: '/home/chatwoot/saaskaran/backend',
      script: '/home/chatwoot/saaskaran/.venv/bin/uvicorn',
      args: 'main:app --host 127.0.0.1 --port 8000',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
      },
    },
    {
      name: 'saaskaran-frontend',
      cwd: '/home/chatwoot/saaskaran/frontend',
      script: 'npm',
      args: 'run start',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '400M',
      env: {
        PORT: '3001',
        NODE_ENV: 'production',
      },
    },
    {
      name: 'ai-layer',
      cwd: '/home/chatwoot/ai-layer',
      script: '/home/chatwoot/ai-layer/.venv/bin/uvicorn',
      args: 'main:app --host 127.0.0.1 --port 8010',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
      },
    },
  ],
}
