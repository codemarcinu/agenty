# Hardware Optimization Guide for FoodSave AI

## 🖥️ System Requirements Analysis

### Minimum Requirements
- **CPU**: 4 cores, 2.0 GHz
- **RAM**: 8GB
- **Storage**: 20GB free space
- **GPU**: Optional (CPU-only mode available)

### Recommended Requirements
- **CPU**: 6+ cores, 3.0+ GHz
- **RAM**: 16GB+
- **Storage**: 50GB+ SSD
- **GPU**: NVIDIA RTX 3060+ (8GB+ VRAM)

### Optimal Requirements (Your Setup)
- **CPU**: AMD Ryzen 5 5500 (6 cores, 12 threads) ✅
- **RAM**: 32GB ✅
- **Storage**: SSD recommended ✅
- **GPU**: NVIDIA RTX 3060 (12GB VRAM) ✅

## 🚀 RTX 3060 Optimization

### GPU Configuration
```bash
# Environment variables for optimal performance
export CUDA_VISIBLE_DEVICES=0
export CUDA_LAUNCH_BLOCKING=0
export TORCH_CUDA_ARCH_LIST=8.6
export CUDA_MEMORY_FRACTION=0.8
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export CUDA_MEMORY_POOL_SIZE=1073741824
```

### Ollama Settings for RTX 3060
```json
{
  "gpu_layers": 35,
  "cpu_layers": 10,
  "num_parallel": 6,
  "num_gpu": 1
}
```

### Model Recommendations
| Model | VRAM Usage | Performance | Quality |
|-------|------------|-------------|---------|
| Bielik-4.5B Q8_0 | ~6GB | Fast | Excellent |
| Bielik-11B Q5_K_M | ~10GB | Medium | Outstanding |
| Gemma3:12B | ~8GB | Fast | Very Good |
| Mistral:7B | ~5GB | Very Fast | Good |

## 📊 Performance Benchmarks

### RTX 3060 Performance
```
Model Loading Time:
- Bielik-4.5B: 20-40 seconds
- Bielik-11B: 30-60 seconds
- Gemma3:12B: 25-45 seconds

Response Time:
- Simple queries: 1-3 seconds
- Complex analysis: 3-8 seconds
- Receipt processing: 2-5 seconds

Memory Usage:
- Backend: ~500MB
- Ollama: ~6-10GB VRAM
- Total system: ~4GB RAM + 8GB VRAM
```

## 🔧 Optimization Scripts

### Quick Optimization
```bash
# Run RTX 3060 optimization
./scripts/optimize_for_rtx3060.sh

# Start optimized system
./scripts/start_optimized.sh

# Monitor performance
./scripts/monitor_rtx3060.sh
```

### Manual Optimization Steps

1. **GPU Driver Setup**
   ```bash
   # Check GPU status
   nvidia-smi
   
   # Install NVIDIA Container Toolkit
   sudo apt-get install nvidia-container-toolkit
   sudo systemctl restart docker
   ```

2. **Docker Configuration**
   ```bash
   # Use optimized compose file
   docker-compose -f docker-compose.yaml -f docker-compose.rtx3060.override.yml up -d
   ```

3. **System Tuning**
   ```bash
   # Reduce swappiness for better performance
   sudo sysctl vm.swappiness=10
   
   # Check memory usage
   free -h
   ```

## 📈 Monitoring and Troubleshooting

### Performance Monitoring
```bash
# GPU usage
nvidia-smi -l 1

# System resources
htop

# Docker containers
docker stats

# Application logs
docker logs foodsave-backend
docker logs foodsave-ollama
```

### Common Issues and Solutions

#### High GPU Memory Usage
```bash
# Reduce model size
export OLLAMA_MODEL=SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0

# Increase CPU layers
export OLLAMA_CPU_LAYERS=15
```

#### Slow Response Times
```bash
# Check GPU utilization
nvidia-smi

# Verify model loading
curl http://localhost:11434/api/tags

# Check system resources
./scripts/monitor_rtx3060.sh
```

#### Memory Issues
```bash
# Clear Docker cache
docker system prune -a

# Restart services
docker-compose restart ollama backend

# Check for memory leaks
docker stats --no-stream
```

## 🎯 Optimization Checklist

### Pre-Deployment
- [ ] NVIDIA drivers installed and updated
- [ ] NVIDIA Container Toolkit configured
- [ ] Docker with GPU support enabled
- [ ] Sufficient disk space (50GB+)
- [ ] System swappiness optimized

### Runtime Optimization
- [ ] GPU layers configured (35 for RTX 3060)
- [ ] Memory limits set appropriately
- [ ] Model quantization applied
- [ ] Caching enabled
- [ ] Monitoring active

### Performance Verification
- [ ] Model loading time < 60 seconds
- [ ] Response time < 10 seconds
- [ ] GPU utilization > 50% during processing
- [ ] Memory usage stable
- [ ] No error messages in logs

## 🔍 Hardware-Specific Configurations

### AMD Ryzen 5 5500
- **CPU Cores**: 6 physical, 12 logical
- **Cache**: 16MB L3 cache
- **Optimization**: Enable SMT, use all cores

### 32GB RAM
- **Allocation**: 8GB for AI models, 4GB for system
- **Swap**: Minimal (10% swappiness)
- **Monitoring**: Watch for memory pressure

### RTX 3060 12GB
- **VRAM**: 12GB total, 10GB usable
- **Architecture**: Ampere (8.6)
- **Optimization**: 35 GPU layers, 10 CPU layers

## 📋 Maintenance Schedule

### Daily
- Monitor GPU temperature and usage
- Check system memory usage
- Review application logs

### Weekly
- Update GPU drivers if needed
- Clean Docker cache
- Verify model performance

### Monthly
- Full system optimization
- Performance benchmarking
- Configuration review

## 🚨 Emergency Procedures

### System Overload
```bash
# Stop all services
docker-compose down

# Clear GPU memory
sudo nvidia-smi --gpu-reset

# Restart with reduced load
docker-compose up -d postgres redis
docker-compose up -d backend
docker-compose up -d ollama
```

### GPU Issues
```bash
# Check GPU status
nvidia-smi

# Restart GPU services
sudo systemctl restart nvidia-persistenced

# Fallback to CPU mode
export OLLAMA_GPU_LAYERS=0
docker-compose restart ollama
```

### Memory Issues
```bash
# Check memory usage
free -h

# Clear caches
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# Restart with memory limits
docker-compose down
docker-compose up -d
```

## 📚 Additional Resources

- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [Ollama GPU Optimization](https://github.com/ollama/ollama/blob/main/docs/gpu.md)
- [Docker GPU Support](https://docs.docker.com/config/containers/resource_constraints/#gpu)
- [AMD Ryzen Optimization](https://www.amd.com/en/support) 