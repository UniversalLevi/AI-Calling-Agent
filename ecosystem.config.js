module.exports = {
  apps: [
    {
      name: 'sara-voice-bot',
      script: 'main.py',
      interpreter: './venv/bin/python',
      cwd: __dirname,
      env: {
        FLASK_ENV: 'production',
        PORT: 8080
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,
      error_file: './logs/voice-bot-error.log',
      out_file: './logs/voice-bot-out.log',
      time: true
    },
    {
      name: 'sara-dashboard-api',
      script: 'server.js',
      cwd: './sara-dashboard/backend',
      env: {
        NODE_ENV: 'production',
        PORT: 5000
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,
      error_file: '../../logs/dashboard-api-error.log',
      out_file: '../../logs/dashboard-api-out.log',
      time: true
    }
  ]
};

