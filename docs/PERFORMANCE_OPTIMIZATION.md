# Performance Optimization Guide

## Overview

This document outlines the performance optimizations implemented in the FoodSave AI system to ensure optimal performance across all containers and services.

## Frontend Optimizations

### Next.js Configuration
- **Bundle Optimization**: Implemented code splitting with vendor and common chunks
- **Image Optimization**: Added WebP and AVIF format support with caching
- **Compression**: Enabled gzip compression for static assets
- **Cache Headers**: Added appropriate cache-control headers for static and API routes
- **Font Optimization**: Implemented font display swap and preloading

### React Optimizations
- **Memoization**: Used `React.memo` for expensive components
- **useMemo**: Memoized expensive calculations and data structures
- **Lazy Loading**: Implemented lazy loading for non-critical components
- **Bundle Splitting**: Optimized imports to reduce bundle size

### TypeScript Optimizations
- **Target ES2022**: Updated TypeScript target for better performance
- **Strict Mode**: Enabled strict type checking for better code quality
- **Exact Types**: Added exact optional property types for better type safety

### CSS Optimizations
- **PostCSS**: Added autoprefixer and cssnano for production builds
- **Tailwind CSS v4**: Using latest version with optimized PostCSS configuration
- **PurgeCSS**: Automatic unused CSS removal in production

## Backend Optimizations

### FastAPI Configuration
- **Worker Configuration**: Optimized worker processes per core
- **Memory Management**: Set appropriate memory limits for containers
- **Async Processing**: Implemented Celery for background tasks
- **Caching**: Redis-based caching for frequently accessed data

### Database Optimizations
- **Connection Pooling**: Optimized database connection management
- **Query Optimization**: Implemented efficient database queries
- **Indexing**: Added appropriate database indexes

## Container Optimizations

### Docker Configuration
- **Multi-stage Builds**: Reduced image sizes significantly
- **Layer Caching**: Optimized Docker layer caching
- **Resource Limits**: Set appropriate CPU and memory limits
- **Health Checks**: Implemented comprehensive health checks

### Resource Management
```yaml
# Frontend
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'

# Backend
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'

# Redis
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.25'
    reservations:
      memory: 256M
      cpus: '0.1'

# Ollama
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 2G
      cpus: '1.0'
```

## Redis Optimizations

### Configuration
```bash
redis-server \
  --appendonly yes \
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru \
  --save 900 1 \
  --save 300 10 \
  --save 60 10000
```

### Features
- **LRU Eviction**: Least Recently Used eviction policy
- **Persistence**: Optimized save intervals
- **Memory Limits**: 256MB memory limit with LRU eviction

## Ollama Optimizations

### Configuration
```bash
OLLAMA_NUM_PARALLEL=2
OLLAMA_GPU_LAYERS=35
OLLAMA_KEEP_ALIVE=24h
```

### Features
- **Parallel Processing**: Multiple parallel model requests
- **GPU Acceleration**: Optimized GPU layer usage
- **Keep Alive**: Maintained model in memory

## Monitoring and Performance

### Performance Monitoring Script
```bash
./scripts/monitor-performance.sh
```

### Metrics Tracked
- Container health status
- Resource usage (CPU, Memory)
- API response times
- System resource utilization
- Network connections

### Performance Targets
- **Frontend**: < 500ms response time
- **Backend**: < 1000ms response time
- **Redis**: < 10ms response time
- **Ollama**: < 5000ms for model inference

## Caching Strategy

### Frontend Caching
- **Static Assets**: 1 year cache with immutable headers
- **API Responses**: No-cache for dynamic data
- **Bundle Caching**: Optimized chunk caching

### Backend Caching
- **Redis Cache**: Frequently accessed data
- **Database Query Cache**: Optimized query results
- **Session Storage**: User session data

## Bundle Optimization

### Frontend Bundle
- **Code Splitting**: Automatic route-based splitting
- **Tree Shaking**: Unused code elimination
- **Minification**: Production code minification
- **Gzip Compression**: Text-based asset compression

### Vendor Bundle
- **Separate Chunks**: Vendor libraries in separate chunks
- **Common Chunks**: Shared dependencies optimization
- **Dynamic Imports**: Lazy loading for large libraries

## Development vs Production

### Development Optimizations
- **Hot Reload**: Fast development feedback
- **Source Maps**: Debug-friendly builds
- **Development Server**: Optimized for development

### Production Optimizations
- **Minification**: Code and asset minification
- **Compression**: Gzip and Brotli compression
- **CDN Ready**: Static asset optimization
- **Security Headers**: Production security configuration

## Performance Monitoring

### Real-time Monitoring
```bash
# Monitor container performance
docker stats

# Check API health
curl -f http://localhost:8000/health
curl -f http://localhost:8085/api/health

# Monitor system resources
htop
iotop
```

### Logging
- **Structured Logs**: JSON-formatted logs
- **Log Levels**: Configurable log verbosity
- **Log Rotation**: Automatic log management

## Troubleshooting

### Common Performance Issues

#### High Memory Usage
1. Check container memory limits
2. Monitor memory usage patterns
3. Optimize application memory usage
4. Consider increasing memory limits

#### Slow Response Times
1. Check API endpoint performance
2. Monitor database query performance
3. Verify Redis cache hit rates
4. Check network connectivity

#### High CPU Usage
1. Monitor CPU usage per container
2. Check for infinite loops or heavy computations
3. Optimize algorithms and data structures
4. Consider scaling horizontally

### Performance Debugging
```bash
# Check container logs
docker logs foodsave-backend
docker logs foodsave-frontend

# Monitor resource usage
docker stats --no-stream

# Check network connectivity
docker network inspect foodsave-network
```

## Best Practices

### Development
1. **Profile Early**: Use performance profiling tools
2. **Monitor Metrics**: Track key performance indicators
3. **Optimize Incrementally**: Make small, measurable improvements
4. **Test Performance**: Include performance tests in CI/CD

### Production
1. **Monitor Continuously**: Use automated monitoring
2. **Set Alerts**: Configure performance alerts
3. **Scale Proactively**: Scale before hitting limits
4. **Backup Performance**: Maintain performance during updates

## Future Optimizations

### Planned Improvements
- **CDN Integration**: Global content delivery
- **Service Workers**: Offline functionality
- **WebAssembly**: Performance-critical components
- **Edge Computing**: Distributed processing
- **GraphQL**: Optimized data fetching

### Performance Roadmap
1. **Q1**: Implement CDN and edge caching
2. **Q2**: Add service worker for offline support
3. **Q3**: Optimize AI model inference
4. **Q4**: Implement advanced caching strategies

## Conclusion

These optimizations provide a solid foundation for high-performance operation of the FoodSave AI system. Regular monitoring and continuous optimization ensure the system remains performant as it scales.

For questions or issues, refer to the monitoring script and container logs for detailed diagnostics. 