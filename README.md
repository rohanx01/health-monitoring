# 🏥 Health Monitoring System for Microservices

A comprehensive, enterprise-grade health monitoring system for microservices architecture built with FastAPI, MongoDB, Docker, and Prometheus. Features AI-powered root cause analysis using Ollama LLaMA 3.

## 🚀 Features

### ✅ **Enhanced Metrics & Monitoring**

- **Industry-standard Prometheus metrics** for all services
- **Comprehensive HTTP metrics** (requests, duration, status codes)
- **Business metrics** (orders, products, auth attempts)
- **Database operation metrics** with timing
- **External service call tracking**
- **System metrics** (CPU, memory usage)
- **Error tracking** with categorization

### ✅ **Advanced Logging & Observability**

- **Structured JSON logging** for all services
- **Request/response logging** with timing
- **Error tracking** with context
- **Service-specific log correlation**
- **Real-time log analysis**

### ✅ **AI-Powered Root Cause Analysis**

- **Ollama LLaMA 3 integration** for intelligent analysis
- **Anomaly detection** with multiple algorithms
- **Time-series analysis** for trend detection
- **Service-specific error analysis**
- **Actionable recommendations**

### ✅ **Comprehensive Dashboard**

- **Real-time monitoring dashboard** (HTML)
- **Performance metrics visualization**
- **Error analysis and trends**
- **Service health status**
- **Prometheus metrics display**
- **Auto-refresh capabilities**

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Auth Service  │    │ Catalog Service │    │  Order Service  │
│   Port: 8001    │    │   Port: 8005    │    │   Port: 8003    │
│   Metrics: 8002 │    │  Metrics: 8006  │    │  Metrics: 8004  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MongoDB       │
                    │   Port: 27017   │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Prometheus    │
                    │   Port: 9090    │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Controller    │    │Monitoring Engine│    │  Mongo Express  │
│   (Traffic Gen) │    │   Port: 8000    │    │   Port: 8081    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Metrics Collected

### **HTTP Metrics**

- `http_requests_total` - Total requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histograms
- `response_time_seconds` - Response time summaries

### **Business Metrics**

- `auth_attempts_total` - Authentication attempts
- `jwt_tokens_issued_total` - JWT tokens issued
- `order_operations_total` - Order operations
- `product_operations_total` - Product operations
- `stock_updates_total` - Stock update operations

### **Database Metrics**

- `db_operations_total` - Database operations by type
- `db_operation_duration_seconds` - Database operation timing

### **System Metrics**

- `cpu_percent` - CPU usage percentage
- `memory_used_mb` - Memory usage in MB

### **Error Metrics**

- `errors_total` - Total errors by type and service

## 🛠️ Installation & Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Ollama (optional, for AI analysis)

### Quick Start

1. **Clone the repository**

```bash
git clone <repository-url>
cd health-monitoring-auth_service_dev
```

2. **Start all services**

```bash
docker-compose up -d
```

3. **Access the services**

- **Monitoring Dashboard**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Mongo Express**: http://localhost:8081
- **Auth Service**: http://localhost:8001
- **Order Service**: http://localhost:8003
- **Catalog Service**: http://localhost:8005

4. **View the HTML Dashboard**

```bash
# Open monitoring_dashboard.html in your browser
open monitoring_dashboard.html
```

## 📈 Monitoring Endpoints

### **Monitoring Engine APIs**

- `GET /api/health` - Overall system health
- `GET /api/summary` - Metrics summary
- `GET /api/metrics` - Detailed metrics
- `GET /api/performance` - Performance analytics
- `GET /api/errors/analysis` - Error analysis
- `GET /api/prometheus/status` - Prometheus status
- `GET /api/root_cause` - AI-powered root cause analysis
- `GET /api/analytics` - Comprehensive analytics
- `GET /api/ollama/test` - Test Ollama connection

### **Service Health Endpoints**

- `GET /ping` - Basic health check
- `GET /health` - Detailed health information

### **Metrics Endpoints**

- `GET /metrics` - Prometheus metrics (ports 8002, 8004, 8006)

## 🔍 Root Cause Analysis

The system uses Ollama LLaMA 3 for intelligent root cause analysis:

### **Anomaly Detection**

- Error rate spikes
- HTTP 500 error increases
- Authentication failure patterns
- Latency anomalies
- Service-specific error patterns

### **AI Analysis Features**

- Pattern recognition in logs
- Service dependency analysis
- Performance bottleneck identification
- Actionable recommendations
- Historical trend analysis

### **Setup Ollama**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull LLaMA 3 model
ollama pull llama3

# Start Ollama service
ollama serve
```

## 📊 Dashboard Features

### **Real-time Monitoring**

- Live system health status
- Performance metrics visualization
- Error rate tracking
- Service status indicators

### **Interactive Elements**

- Auto-refresh every 30 seconds
- Manual refresh button
- Color-coded status indicators
- Expandable sections

### **Comprehensive Views**

- System overview
- Performance analytics
- Error analysis
- Service status
- Prometheus metrics
- Root cause analysis
- Recent logs

## 🔧 Configuration

### **Environment Variables**

```bash
# MongoDB
MONGO_URI=mongodb://admin:secret@mongodb:27017

# JWT
JWT_SECRET=mysecretkey

# Service URLs
AUTH_SERVICE_URL=http://auth_service:8000
ORDER_SERVICE_URL=http://order_service:8000
CATALOG_SERVICE_URL=http://catalog_service:8000

# Monitoring
PROMETHEUS_URL=http://localhost:9090
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### **Prometheus Configuration**

The system automatically configures Prometheus to scrape metrics from:

- Auth Service: `auth_service:8002`
- Order Service: `order_service:8004`
- Catalog Service: `catalog_service:8006`

## 🧪 Testing

### **Generate Traffic**

The controller automatically generates realistic traffic:

```bash
# View controller logs
docker logs controller

# Check traffic generation
curl http://localhost:8000/api/summary
```

### **Test Error Scenarios**

The controller includes controlled error generation (5% chance):

- Invalid authentication
- Non-existent products
- Invalid orders
- Server error simulation

### **Manual Testing**

```bash
# Test auth service
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Test catalog service
curl http://localhost:8005/api/v1/all_products \
  -H "Authorization: Bearer <token>"

# Test order service
curl -X POST http://localhost:8003/api/v1/order \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"item_id":"<product_id>","quantity":1}'
```

## 📈 Performance Optimization

### **Metrics Optimization**

- Efficient Prometheus metric collection
- Optimized database queries
- Cached product lists
- Background metric collection

### **Logging Optimization**

- Structured JSON logging
- Efficient log parsing
- Background log scanning
- Memory-efficient storage

### **Monitoring Optimization**

- 30-second refresh intervals
- Parallel data fetching
- Error handling and retries
- Graceful degradation

## 🔒 Security Features

### **Authentication & Authorization**

- JWT-based authentication
- Token validation middleware
- Secure password handling
- Service-to-service authentication

### **Data Protection**

- Environment variable configuration
- Secure MongoDB setup
- Input validation
- Error message sanitization

## 🚀 Production Deployment

### **Docker Compose Production**

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale auth_service=3 --scale order_service=3
```

### **Kubernetes Deployment**

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Monitor deployment
kubectl get pods -n health-monitoring
```

## 📝 Logging & Debugging

### **Log Locations**

- **Application logs**: `/app/logs/metrics.log`
- **Docker logs**: `docker logs <service-name>`
- **Prometheus logs**: `docker logs prometheus`

### **Debug Commands**

```bash
# Check service health
curl http://localhost:8000/api/health

# View Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test Ollama connection
curl http://localhost:8000/api/ollama/test

# View recent errors
curl http://localhost:8000/api/errors/analysis
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide

---

**Built with ❤️ for enterprise-grade microservices monitoring**
