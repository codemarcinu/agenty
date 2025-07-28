# Quick Start Guide: Multi-Agent System Optimization

This guide provides step-by-step instructions for implementing the multi-agent system optimizations in your MyAppAssistant project.

## Prerequisites

- Python 3.12+
- Redis server running
- PostgreSQL database
- Basic understanding of async/await patterns

## Step 1: Install Dependencies

Add the following dependencies to your `requirements.txt`:

```txt
psutil>=5.9.0
pybreaker>=1.0.1
redis>=4.5.0
```

## Step 2: Configure Environment Variables

Add these environment variables to your `.env` file:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_USE_CACHE=true

# Agent Pool Configuration
AGENT_POOL_SIZE=10
AGENT_HEALTH_CHECK_INTERVAL=30
AGENT_LOAD_BALANCING_STRATEGY=adaptive

# Cache Configuration
CACHE_TTL=3600
CACHE_MAX_SIZE=10000
CACHE_COORDINATION_STRATEGY=voting

# Event Bus Configuration
EVENT_QUEUE_MAX_SIZE=10000
EVENT_CLEANUP_INTERVAL=60
```

## Step 3: Initialize the Optimized System

### Basic Setup

```python
import asyncio
from backend.core.event_bus import EventDrivenAgentCommunication, global_event_bus
from backend.orchestrator_management.intelligent_pool import IntelligentAgentPool, LoadBalancingStrategy
from backend.core.multi_agent_cache import MultiAgentCacheManager, CacheStrategy

async def setup_optimized_system():
    # Initialize event communication
    event_comm = EventDrivenAgentCommunication("main_system")
    await event_comm.initialize()
    
    # Initialize intelligent pool
    agent_pool = IntelligentAgentPool(
        pool_id="main_pool",
        strategy=LoadBalancingStrategy.ADAPTIVE
    )
    await agent_pool.initialize()
    
    # Initialize cache manager
    cache_manager = MultiAgentCacheManager(
        agent_id="main_system",
        coordination_strategy=CacheStrategy.VOTING
    )
    await cache_manager.initialize()
    
    # Register with global event bus
    await global_event_bus.register_agent("main_system", event_comm)
    
    return event_comm, agent_pool, cache_manager
```

### Advanced Setup with Hierarchical Architecture

```python
from backend.agents.hierarchical_architecture import HierarchicalAgentSystem
from backend.core.reactive_patterns import ReactiveAgentOrchestrator

async def setup_advanced_system():
    # Basic components
    event_comm, agent_pool, cache_manager = await setup_optimized_system()
    
    # Hierarchical system
    hierarchical_system = HierarchicalAgentSystem()
    
    # Reactive orchestrator
    reactive_orchestrator = ReactiveAgentOrchestrator("main_reactive")
    await reactive_orchestrator.initialize()
    
    # Create manager and workers
    manager = await hierarchical_system.create_manager("main_manager")
    await manager.initialize()
    
    # Create workers
    workers = []
    worker_configs = [
        ("search_worker", "search", ["text_search", "image_search"]),
        ("analysis_worker", "analysis", ["data_analysis", "text_analysis"]),
        ("processing_worker", "processing", ["image_processing", "data_processing"])
    ]
    
    for worker_id, agent_type, capabilities in worker_configs:
        worker = await hierarchical_system.create_worker(
            worker_id, agent_type, capabilities, "main_manager"
        )
        await worker.initialize()
        
        # Register with intelligent pool
        await agent_pool.register_agent(
            agent_id=worker_id,
            agent_instance=worker,
            agent_type=agent_type,
            load_capacity=15,
            weight=1.0
        )
        
        workers.append(worker)
    
    return {
        "event_comm": event_comm,
        "agent_pool": agent_pool,
        "cache_manager": cache_manager,
        "hierarchical_system": hierarchical_system,
        "reactive_orchestrator": reactive_orchestrator,
        "manager": manager,
        "workers": workers
    }
```

## Step 4: Process Requests

### Basic Request Processing

```python
async def process_request_basic(agent_pool, cache_manager, request_data):
    start_time = time.time()
    
    # Check cache first
    cache_key = f"request_{hash(str(request_data))}"
    cached_result = await cache_manager.get(cache_key, CacheLevel.SHARED)
    
    if cached_result:
        return {
            "success": True,
            "result": cached_result,
            "source": "cache",
            "response_time": time.time() - start_time
        }
    
    # Get agent from pool
    task_type = request_data.get("task_type", "general")
    priority = request_data.get("priority", 1)
    
    agent = await agent_pool.get_agent(task_type=task_type, priority=priority)
    
    if not agent:
        return {
            "success": False,
            "error": "No suitable agent available"
        }
    
    # Process request
    result = await agent.process_task(request_data)
    
    # Cache result
    await cache_manager.set(cache_key, result, ttl=3600, cache_level=CacheLevel.SHARED)
    
    # Release agent
    response_time = time.time() - start_time
    await agent_pool.release_agent(
        agent.worker_id, 
        success=True, 
        response_time=response_time
    )
    
    return {
        "success": True,
        "result": result,
        "source": "agent",
        "response_time": response_time
    }
```

### Advanced Request Processing with Events

```python
async def process_request_advanced(system_components, request_data):
    # Publish request event
    await system_components["event_comm"].publish_event(
        EventType.USER_INPUT,
        request_data,
        priority=EventPriority.HIGH
    )
    
    # Process with reactive patterns
    stimulus = Stimulus(
        type=StimulusType.USER_INPUT,
        source="user",
        data=request_data
    )
    
    response_ids = await system_components["reactive_orchestrator"].handle_stimulus(stimulus)
    
    # Process request normally
    result = await process_request_basic(
        system_components["agent_pool"],
        system_components["cache_manager"],
        request_data
    )
    
    # Publish completion event
    await system_components["event_comm"].publish_event(
        EventType.TASK_COMPLETION,
        {
            "request_id": request_data.get("id"),
            "success": result["success"],
            "response_time": result["response_time"]
        }
    )
    
    return result
```

## Step 5: Set Up Reactive Patterns

```python
async def setup_reactive_patterns(reactive_orchestrator, agent_pool, cache_manager):
    # Load balancing pattern
    async def load_balance_handler(parameters):
        pool_stats = agent_pool.get_pool_stats()
        if pool_stats["system_metrics"]["system_load"] > 80:
            await agent_pool._trigger_rebalancing()
            return {"action": "rebalancing_triggered"}
        return {"action": "no_action_needed"}
    
    await reactive_orchestrator.register_reactive_pattern(
        stimulus_type=StimulusType.RESOURCE_UPDATE,
        response_type=ResponseType.IMMEDIATE,
        handler=load_balance_handler,
        name="load_balancing_pattern"
    )
    
    # Error recovery pattern
    async def error_recovery_handler(parameters):
        agent_id = parameters.get("agent_id")
        if agent_id:
            # Attempt to recover agent
            return {"action": "agent_recovery_attempted", "agent_id": agent_id}
        return {"action": "no_recovery_needed"}
    
    await reactive_orchestrator.register_reactive_pattern(
        stimulus_type=StimulusType.ERROR_OCCURRED,
        response_type=ResponseType.IMMEDIATE,
        handler=error_recovery_handler,
        name="error_recovery_pattern"
    )
    
    # Cache optimization pattern
    async def cache_optimization_handler(parameters):
        cache_stats = await cache_manager.get_cache_stats()
        if cache_stats["local_hits"] < cache_stats["local_misses"]:
            await cache_manager.clear_cache(CacheLevel.LOCAL)
            return {"action": "cache_cleared"}
        return {"action": "no_cache_optimization_needed"}
    
    await reactive_orchestrator.register_reactive_pattern(
        stimulus_type=StimulusType.PERFORMANCE_ALERT,
        response_type=ResponseType.DELAYED,
        handler=cache_optimization_handler,
        name="cache_optimization_pattern"
    )
```

## Step 6: Monitor and Optimize

### Get System Statistics

```python
async def get_system_stats(system_components):
    return {
        "pool_stats": system_components["agent_pool"].get_pool_stats(),
        "cache_stats": await system_components["cache_manager"].get_cache_stats(),
        "reactive_stats": system_components["reactive_orchestrator"].get_orchestrator_stats(),
        "event_stats": system_components["event_comm"].get_metrics()
    }
```

### Performance Monitoring

```python
async def monitor_performance(system_components):
    while True:
        stats = await get_system_stats(system_components)
        
        # Log key metrics
        logger.info(f"System Load: {stats['pool_stats']['system_metrics']['system_load']}%")
        logger.info(f"Cache Hit Rate: {stats['cache_stats']['hit_rate']}%")
        logger.info(f"Active Agents: {stats['pool_stats']['healthy_agents']}")
        logger.info(f"Event Queue Size: {stats['event_stats']['queue_size']}")
        
        # Check for optimization triggers
        if stats['pool_stats']['system_metrics']['system_load'] > 80:
            logger.warning("High system load detected")
        
        if stats['cache_stats']['hit_rate'] < 50:
            logger.warning("Low cache hit rate detected")
        
        await asyncio.sleep(60)  # Check every minute
```

## Step 7: Integration with Existing Code

### Update Orchestrator

```python
# In your existing orchestrator.py
from backend.orchestrator_management.intelligent_pool import IntelligentAgentPool
from backend.core.multi_agent_cache import MultiAgentCacheManager

class EnhancedOrchestrator:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add optimized components
        self.intelligent_pool = IntelligentAgentPool("orchestrator_pool")
        self.cache_manager = MultiAgentCacheManager("orchestrator_cache")
    
    async def initialize(self):
        await super().initialize()
        await self.intelligent_pool.initialize()
        await self.cache_manager.initialize()
    
    async def process_command(self, user_command, session_id, **kwargs):
        # Use intelligent pool for agent selection
        agent = await self.intelligent_pool.get_agent(
            task_type=self._determine_task_type(user_command),
            priority=kwargs.get("priority", 1)
        )
        
        if agent:
            result = await agent.process(user_command)
            await self.intelligent_pool.release_agent(agent.id, success=True)
            return result
        else:
            return await super().process_command(user_command, session_id, **kwargs)
```

### Update Agent Factory

```python
# In your existing agent_factory.py
from backend.core.event_bus import EventDrivenAgentCommunication

class EnhancedAgentFactory(AgentFactory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_communication = EventDrivenAgentCommunication("agent_factory")
    
    async def initialize(self):
        await self.event_communication.initialize()
    
    def create_agent(self, agent_type, **kwargs):
        agent = super().create_agent(agent_type, **kwargs)
        
        # Add event communication to agent
        if hasattr(agent, 'event_communication'):
            agent.event_communication = self.event_communication
        
        return agent
```

## Step 8: Testing

### Unit Tests

```python
import pytest
from backend.orchestrator_management.intelligent_pool import IntelligentAgentPool

@pytest.mark.asyncio
async def test_intelligent_pool():
    pool = IntelligentAgentPool("test_pool")
    await pool.initialize()
    
    # Test agent registration
    success = await pool.register_agent(
        "test_agent", 
        mock_agent, 
        "test_type", 
        load_capacity=10
    )
    assert success is True
    
    # Test agent selection
    agent = await pool.get_agent(task_type="test_type")
    assert agent is not None
    
    await pool.shutdown()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_optimized_system_integration():
    system = await setup_advanced_system()
    
    # Test request processing
    request_data = {
        "task_type": "search",
        "query": "test query",
        "priority": 2
    }
    
    result = await process_request_advanced(system, request_data)
    assert result["success"] is True
    
    # Test caching
    cached_result = await process_request_advanced(system, request_data)
    assert cached_result["source"] == "cache"
    
    # Cleanup
    await cleanup_system(system)
```

## Step 9: Production Deployment

### Docker Configuration

```dockerfile
# Add to your Dockerfile
RUN pip install psutil pybreaker redis

# Environment variables
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV AGENT_POOL_SIZE=20
ENV AGENT_LOAD_BALANCING_STRATEGY=adaptive
```

### Kubernetes Configuration

```yaml
# Add to your deployment.yaml
env:
- name: REDIS_HOST
  value: "redis-service"
- name: AGENT_POOL_SIZE
  value: "20"
- name: AGENT_LOAD_BALANCING_STRATEGY
  value: "adaptive"

resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   - Check Redis server is running
   - Verify connection parameters
   - Test with redis-cli

2. **Agent Pool Issues**
   - Check agent health status
   - Verify load balancing strategy
   - Monitor system metrics

3. **Event Bus Problems**
   - Check event queue size
   - Verify event handlers
   - Monitor event processing time

### Performance Tuning

1. **Adjust Pool Size**
   ```python
   # Increase for high load
   AGENT_POOL_SIZE=50
   ```

2. **Optimize Cache Settings**
   ```python
   # Increase TTL for stable data
   CACHE_TTL=7200
   ```

3. **Tune Load Balancing**
   ```python
   # Use adaptive for dynamic workloads
   AGENT_LOAD_BALANCING_STRATEGY=adaptive
   ```

## Next Steps

1. **Monitor Performance**: Use the provided monitoring tools to track system performance
2. **Optimize Configuration**: Adjust settings based on your specific workload
3. **Add Custom Patterns**: Implement reactive patterns specific to your use case
4. **Scale Horizontally**: Add more agent instances as needed
5. **Implement Advanced Features**: Add distributed tracing, advanced metrics, etc.

## Support

For issues and questions:
- Check the comprehensive documentation in `docs/architecture/MULTI_AGENT_OPTIMIZATION_PLAN.md`
- Review the example implementation in `src/backend/examples/multi_agent_optimization_example.py`
- Monitor system logs for detailed error information 