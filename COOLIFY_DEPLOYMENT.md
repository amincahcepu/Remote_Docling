# Coolify Deployment Guide

This guide will help you deploy the Docling PDF Processing Service to Coolify.

## 📋 Prerequisites

- A Coolify instance running (self-hosted or Coolify Cloud)
- Git repository with the project code
- Basic understanding of Coolify's interface

## 🚀 Quick Start

### 1. Prepare Your Repository

Ensure your repository contains:
- `docling_service.py` - Main application file
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies
- `.dockerignore` - Docker build optimization

### 2. Create Application in Coolify

1. Log in to your Coolify dashboard
2. Click **"New Application"** or **"New Service"**
3. Select **"Dockerfile"** as the build type
4. Connect your Git repository (GitHub, GitLab, Bitbucket, etc.)
5. Select the branch to deploy (usually `main` or `master`)

### 3. Configure Build Settings

- **Build Context**: `.` (root directory)
- **Dockerfile Path**: `Dockerfile`
- **Docker Compose Path**: Leave empty (not needed)

### 4. Set Environment Variables

Add these environment variables in Coolify:

#### Required Variables
```bash
DOCLING_SERVICE_API_KEY=your-secure-api-key-here
```

#### Optional Variables (with defaults)
```bash
PORT=8000                    # Service port (default: 8000)
WORKERS=2                    # Number of worker processes (default: 2)
MAX_FILE_SIZE=52428800      # Max file size in bytes (default: 50MB)
ALLOWED_ORIGINS=*            # CORS allowed origins (default: *)
```

**Example for production:**
```bash
DOCLING_SERVICE_API_KEY=prod-secure-key-12345
PORT=8000
WORKERS=4
MAX_FILE_SIZE=104857600      # 100MB
ALLOWED_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
```

### 5. Configure Resource Limits

#### Recommended Settings for Production

| Setting | Value | Notes |
|---------|-------|-------|
| **Memory** | 2-4 GB | PDF processing is memory-intensive |
| **CPU** | 2-4 cores | OCR operations are CPU-intensive |
| **Disk** | 10 GB | For temporary files and logs |
| **Timeout** | 300s | For large PDF conversions |

### 6. Configure Health Check

Coolify will automatically use the health check defined in the Dockerfile:
- **Endpoint**: `/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start Period**: 5 seconds
- **Retries**: 3

### 7. Configure Networking

- **Port Mapping**: `8000:8000` (or your custom PORT)
- **Protocol**: HTTP
- **Domain**: Add your custom domain if needed

### 8. Deploy!

Click **"Deploy"** and wait for the build to complete.

## 🔍 Verification

After deployment, verify the service is working:

### Health Check
```bash
curl https://your-app-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "docling-pdf-processor",
  "version": "1.0.0"
}
```

### Test PDF Conversion
```bash
curl -X POST https://your-app-url/convert-pdf \
  -H "X-API-Key: your-secure-api-key-here" \
  -F "file=@test.pdf"
```

## 📊 Monitoring

### View Logs
In Coolify, go to your application → **Logs** tab to see:
- Structured JSON logs
- Conversion events
- Error messages
- Performance metrics

### Key Log Events to Monitor
- `service_starting` - Service startup
- `processing_file` - File processing started
- `conversion_successful` - Successful conversion
- `conversion_error` - Conversion failures
- `invalid_api_key_attempt` - Security alerts
- `file_too_large` - Size limit violations

## 🔄 Updates and Scaling

### Automatic Deployments
Coolify can automatically deploy when you push to your Git repository:
1. Go to **Settings** → **Git**
2. Enable **"Auto Deploy on Push"**
3. Select the branch to watch

### Manual Deployments
1. Push changes to your Git repository
2. In Coolify, click **"Redeploy"**
3. Wait for the build and deployment to complete

### Horizontal Scaling
For high traffic, scale horizontally:
1. Go to **Settings** → **Scaling**
2. Set **"Replicas"** to desired number (e.g., 3)
3. Coolify will load balance across instances

## 🛠️ Troubleshooting

### Build Fails

**Problem**: Docker build fails
**Solutions**:
- Check Dockerfile syntax
- Verify requirements.txt is valid
- Ensure all files are committed to Git
- Check Coolify build logs for specific errors

### 502 Bad Gateway

**Problem**: Service not responding
**Solutions**:
- Verify PORT environment variable matches Dockerfile
- Check if service is running: `curl http://localhost:8000/health`
- Review application logs for startup errors
- Ensure health check endpoint is accessible

### Out of Memory

**Problem**: Container crashes with OOM
**Solutions**:
- Increase memory limit in Coolify (recommend 2-4GB)
- Reduce MAX_FILE_SIZE environment variable
- Reduce WORKERS count
- Monitor memory usage during conversions

### Slow Conversions

**Problem**: PDF processing is slow
**Solutions**:
- Increase CPU allocation
- Increase WORKERS count
- Check if OCR is needed (can disable for text-only PDFs)
- Monitor system resources

### Health Check Failing

**Problem**: Health check returns errors
**Solutions**:
- Verify `/health` endpoint is accessible
- Check application logs for errors
- Ensure service has fully started (increase start-period if needed)
- Verify no port conflicts

### API Key Errors

**Problem**: 401 Unauthorized responses
**Solutions**:
- Verify DOCLING_SERVICE_API_KEY is set correctly
- Check client is sending `X-API-Key` header
- Ensure no whitespace in API key
- Regenerate API key if compromised

## 🔒 Security Best Practices

1. **API Key Management**
   - Use strong, random API keys
   - Rotate keys regularly
   - Never commit API keys to Git
   - Use Coolify's secret management

2. **CORS Configuration**
   - Set specific allowed origins in production
   - Don't use `*` in production environments

3. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Use Coolify's built-in SSL/TLS

4. **Resource Limits**
   - Set appropriate memory/CPU limits
   - Monitor resource usage
   - Set file size limits

5. **Logging**
   - Don't log sensitive data
   - Review logs regularly
   - Set up log retention policies

## 📚 API Usage

### Endpoints

#### GET `/`
Service information
```bash
curl https://your-app-url/
```

#### GET `/health`
Health check
```bash
curl https://your-app-url/health
```

#### POST `/convert-pdf`
Convert PDF to markdown
```bash
curl -X POST https://your-app-url/convert-pdf \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf"
```

### Response Format
```json
{
  "status": "success",
  "filename": "document.pdf",
  "text_length": 12345,
  "markdown": "# Document Content\n..."
}
```

## 🆘 Support

For issues or questions:
- Check Coolify documentation: https://coolify.io/docs
- Review application logs in Coolify
- Check Docling documentation: https://github.com/DS4SD/docling
- Enable debug logging by setting `LOG_LEVEL=debug`

## 📝 Environment Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DOCLING_SERVICE_API_KEY` | string | - | Required API key for authentication |
| `PORT` | integer | 8000 | Port the service listens on |
| `WORKERS` | integer | 2 | Number of worker processes |
| `MAX_FILE_SIZE` | integer | 52428800 | Maximum file size in bytes (50MB) |
| `ALLOWED_ORIGINS` | string | * | Comma-separated list of allowed CORS origins for API access |
| `LOG_LEVEL` | string | info | Logging level (debug, info, warning, error) |

## 🎯 Next Steps

1. ✅ Deploy to Coolify using this guide
2. ✅ Test with sample PDF files
3. ✅ Set up monitoring and alerts
4. ✅ Configure backup strategy
5. ✅ Document your API key management process
6. ✅ Set up CI/CD pipeline for automated deployments

---

**Happy deploying! 🚀**