FROM n8nio/n8n:latest

# Install nodemailer untuk kirim email via SMTP
RUN npm install nodemailer --save

# Set environment variables (opsional)
ENV N8N_BASIC_AUTH_ACTIVE=false
ENV N8N_HOST=0.0.0.0
ENV WEBHOOK_TUNNEL_URL=https://trading-bot-lu82.onrender.com

# Expose port
EXPOSE 5678

# Start n8n
CMD ["n8n", "start", "--tunnel"]
