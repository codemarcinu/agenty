"""
Model Context Protocol (MCP) Integration for FoodSave AI

This module implements MCP (Model Context Protocol) support for standardized
agent-to-agent communication and tool sharing across the system.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any
import uuid

from agents.interfaces import AgentType, BaseAgent
from core.async_agent_communication import AgentMessage, AsyncAgentCommunicator

logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP-specific message types"""

    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RESPONSE = "resource_response"
    CAPABILITY_DISCOVERY = "capability_discovery"
    CAPABILITY_RESPONSE = "capability_response"


class MCPPermission(Enum):
    """MCP permission levels"""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class MCPTool:
    """MCP tool definition"""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable
    permissions: list[MCPPermission] = field(default_factory=list)
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)

    def to_schema(self) -> dict[str, Any]:
        """Convert tool to MCP schema format"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "permissions": [p.value for p in self.permissions],
            "version": self.version,
            "tags": self.tags,
            "examples": self.examples,
        }


@dataclass
class MCPResource:
    """MCP resource definition"""

    name: str
    type: str
    description: str
    uri: str
    metadata: dict[str, Any] = field(default_factory=dict)
    permissions: list[MCPPermission] = field(default_factory=list)
    version: str = "1.0.0"

    def to_schema(self) -> dict[str, Any]:
        """Convert resource to MCP schema format"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "uri": self.uri,
            "metadata": self.metadata,
            "permissions": [p.value for p in self.permissions],
            "version": self.version,
        }


@dataclass
class MCPCapability:
    """MCP capability definition"""

    name: str
    version: str
    description: str
    tools: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    protocols: list[str] = field(default_factory=list)

    def to_schema(self) -> dict[str, Any]:
        """Convert capability to MCP schema format"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tools": self.tools,
            "resources": self.resources,
            "protocols": self.protocols,
        }


class MCPServer:
    """MCP Server implementation for agent tool sharing"""

    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.tools: dict[str, MCPTool] = {}
        self.resources: dict[str, MCPResource] = {}
        self.capabilities: dict[str, MCPCapability] = {}
        self.communicator: AsyncAgentCommunicator | None = None
        self.is_running = False

        logger.info(f"Initialized MCP Server for agent {agent_id} ({agent_type.value})")

    async def initialize(self) -> None:
        """Initialize MCP server and communication"""
        self.communicator = AsyncAgentCommunicator(f"mcp_{self.agent_id}")
        await self.communicator.connect()
        await self.communicator.start_processing()

        # Register MCP message handlers
        self.communicator.register_handler(
            MCPMessageType.TOOL_CALL, self._handle_tool_call
        )
        self.communicator.register_handler(
            MCPMessageType.RESOURCE_REQUEST, self._handle_resource_request
        )
        self.communicator.register_handler(
            MCPMessageType.CAPABILITY_DISCOVERY, self._handle_capability_discovery
        )

        self.is_running = True
        logger.info(f"MCP Server for {self.agent_id} initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown MCP server"""
        self.is_running = False
        if self.communicator:
            await self.communicator.disconnect()
        logger.info(f"MCP Server for {self.agent_id} shutdown")

    def register_tool(self, tool: MCPTool) -> None:
        """Register a tool with the MCP server"""
        self.tools[tool.name] = tool
        logger.info(f"Registered MCP tool: {tool.name} on agent {self.agent_id}")

    def register_resource(self, resource: MCPResource) -> None:
        """Register a resource with the MCP server"""
        self.resources[resource.name] = resource
        logger.info(
            f"Registered MCP resource: {resource.name} on agent {self.agent_id}"
        )

    def register_capability(self, capability: MCPCapability) -> None:
        """Register a capability with the MCP server"""
        self.capabilities[capability.name] = capability
        logger.info(
            f"Registered MCP capability: {capability.name} on agent {self.agent_id}"
        )

    async def _handle_tool_call(self, message: AgentMessage) -> None:
        """Handle incoming tool call requests"""
        try:
            tool_name = message.data.get("tool_name")
            parameters = message.data.get("parameters", {})
            call_id = message.data.get("call_id", str(uuid.uuid4()))

            if tool_name not in self.tools:
                await self._send_tool_error(
                    message, f"Tool '{tool_name}' not found", call_id
                )
                return

            tool = self.tools[tool_name]

            # Check permissions
            required_permission = MCPPermission.EXECUTE
            if required_permission not in tool.permissions:
                await self._send_tool_error(
                    message, f"Permission denied for tool '{tool_name}'", call_id
                )
                return

            # Execute tool
            try:
                if asyncio.iscoroutinefunction(tool.handler):
                    result = await tool.handler(**parameters)
                else:
                    result = tool.handler(**parameters)

                # Send successful response
                response_message = AgentMessage(
                    type=MCPMessageType.TOOL_RESPONSE,
                    source_agent=self.agent_id,
                    target_agent=message.source_agent,
                    data={
                        "call_id": call_id,
                        "success": True,
                        "result": result,
                        "tool_name": tool_name,
                    },
                    correlation_id=message.id,
                )

                await self.communicator.send_message(response_message)

            except Exception as e:
                await self._send_tool_error(message, str(e), call_id)

        except Exception as e:
            logger.error(f"Error handling tool call: {e}")

    async def _handle_resource_request(self, message: AgentMessage) -> None:
        """Handle resource access requests"""
        try:
            resource_name = message.data.get("resource_name")
            operation = message.data.get("operation", "read")
            request_id = message.data.get("request_id", str(uuid.uuid4()))

            if resource_name not in self.resources:
                await self._send_resource_error(
                    message, f"Resource '{resource_name}' not found", request_id
                )
                return

            resource = self.resources[resource_name]

            # Check permissions
            required_permission = MCPPermission(operation.lower())
            if required_permission not in resource.permissions:
                await self._send_resource_error(
                    message,
                    f"Permission denied for operation '{operation}'",
                    request_id,
                )
                return

            # Handle resource access based on type
            resource_data = await self._access_resource(
                resource, operation, message.data.get("params", {})
            )

            response_message = AgentMessage(
                type=MCPMessageType.RESOURCE_RESPONSE,
                source_agent=self.agent_id,
                target_agent=message.source_agent,
                data={
                    "request_id": request_id,
                    "success": True,
                    "resource_name": resource_name,
                    "operation": operation,
                    "data": resource_data,
                },
                correlation_id=message.id,
            )

            await self.communicator.send_message(response_message)

        except Exception as e:
            logger.error(f"Error handling resource request: {e}")

    async def _handle_capability_discovery(self, message: AgentMessage) -> None:
        """Handle capability discovery requests"""
        try:
            discovery_id = message.data.get("discovery_id", str(uuid.uuid4()))

            capabilities_data = {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type.value,
                "tools": {name: tool.to_schema() for name, tool in self.tools.items()},
                "resources": {
                    name: resource.to_schema()
                    for name, resource in self.resources.items()
                },
                "capabilities": {
                    name: cap.to_schema() for name, cap in self.capabilities.items()
                },
                "mcp_version": "1.0.0",
                "protocols_supported": [
                    "tool_call",
                    "resource_access",
                    "capability_discovery",
                ],
            }

            response_message = AgentMessage(
                type=MCPMessageType.CAPABILITY_RESPONSE,
                source_agent=self.agent_id,
                target_agent=message.source_agent,
                data={"discovery_id": discovery_id, "capabilities": capabilities_data},
                correlation_id=message.id,
            )

            await self.communicator.send_message(response_message)

        except Exception as e:
            logger.error(f"Error handling capability discovery: {e}")

    async def _send_tool_error(
        self, original_message: AgentMessage, error: str, call_id: str
    ) -> None:
        """Send tool error response"""
        error_message = AgentMessage(
            type=MCPMessageType.TOOL_RESPONSE,
            source_agent=self.agent_id,
            target_agent=original_message.source_agent,
            data={"call_id": call_id, "success": False, "error": error},
            correlation_id=original_message.id,
        )

        await self.communicator.send_message(error_message)

    async def _send_resource_error(
        self, original_message: AgentMessage, error: str, request_id: str
    ) -> None:
        """Send resource error response"""
        error_message = AgentMessage(
            type=MCPMessageType.RESOURCE_RESPONSE,
            source_agent=self.agent_id,
            target_agent=original_message.source_agent,
            data={"request_id": request_id, "success": False, "error": error},
            correlation_id=original_message.id,
        )

        await self.communicator.send_message(error_message)

    async def _access_resource(
        self, resource: MCPResource, operation: str, params: dict[str, Any]
    ) -> Any:
        """Access resource based on its type and operation"""
        # This would be implemented based on resource type
        # For now, return basic resource information
        return {
            "resource_uri": resource.uri,
            "metadata": resource.metadata,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
        }


class MCPClient:
    """MCP Client for calling tools on other agents"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.communicator: AsyncAgentCommunicator | None = None
        self.discovered_agents: dict[str, dict[str, Any]] = {}
        self.is_running = False

    async def initialize(self) -> None:
        """Initialize MCP client"""
        self.communicator = AsyncAgentCommunicator(f"mcp_client_{self.agent_id}")
        await self.communicator.connect()
        await self.communicator.start_processing()

        # Register response handlers
        self.communicator.register_handler(
            MCPMessageType.TOOL_RESPONSE, self._handle_tool_response
        )
        self.communicator.register_handler(
            MCPMessageType.RESOURCE_RESPONSE, self._handle_resource_response
        )
        self.communicator.register_handler(
            MCPMessageType.CAPABILITY_RESPONSE, self._handle_capability_response
        )

        self.is_running = True
        logger.info(f"MCP Client for {self.agent_id} initialized")

    async def shutdown(self) -> None:
        """Shutdown MCP client"""
        self.is_running = False
        if self.communicator:
            await self.communicator.disconnect()

    async def discover_capabilities(
        self, target_agent: str, timeout: float = 10.0
    ) -> dict[str, Any] | None:
        """Discover capabilities of a target agent"""
        discovery_message = AgentMessage(
            type=MCPMessageType.CAPABILITY_DISCOVERY,
            source_agent=self.agent_id,
            target_agent=target_agent,
            data={"discovery_id": str(uuid.uuid4())},
        )

        try:
            response = await self.communicator.send_message(
                discovery_message, wait_for_response=True, timeout=timeout
            )
            if response and response.data.get("capabilities"):
                capabilities = response.data["capabilities"]
                self.discovered_agents[target_agent] = capabilities
                return capabilities
        except Exception as e:
            logger.error(f"Failed to discover capabilities for {target_agent}: {e}")

        return None

    async def call_tool(
        self,
        target_agent: str,
        tool_name: str,
        parameters: dict[str, Any],
        timeout: float = 30.0,
    ) -> Any | None:
        """Call a tool on a target agent"""
        call_id = str(uuid.uuid4())

        tool_call_message = AgentMessage(
            type=MCPMessageType.TOOL_CALL,
            source_agent=self.agent_id,
            target_agent=target_agent,
            data={"call_id": call_id, "tool_name": tool_name, "parameters": parameters},
        )

        try:
            response = await self.communicator.send_message(
                tool_call_message, wait_for_response=True, timeout=timeout
            )
            if response and response.data.get("success"):
                return response.data.get("result")
            elif response:
                logger.error(f"Tool call failed: {response.data.get('error')}")
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on {target_agent}: {e}")

        return None

    async def access_resource(
        self,
        target_agent: str,
        resource_name: str,
        operation: str = "read",
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any | None:
        """Access a resource on a target agent"""
        request_id = str(uuid.uuid4())

        resource_request = AgentMessage(
            type=MCPMessageType.RESOURCE_REQUEST,
            source_agent=self.agent_id,
            target_agent=target_agent,
            data={
                "request_id": request_id,
                "resource_name": resource_name,
                "operation": operation,
                "params": params or {},
            },
        )

        try:
            response = await self.communicator.send_message(
                resource_request, wait_for_response=True, timeout=timeout
            )
            if response and response.data.get("success"):
                return response.data.get("data")
            elif response:
                logger.error(f"Resource access failed: {response.data.get('error')}")
        except Exception as e:
            logger.error(
                f"Failed to access resource {resource_name} on {target_agent}: {e}"
            )

        return None

    async def _handle_tool_response(self, message: AgentMessage) -> None:
        """Handle tool call responses"""
        # These are handled by the send_message method when wait_for_response=True

    async def _handle_resource_response(self, message: AgentMessage) -> None:
        """Handle resource access responses"""
        # These are handled by the send_message method when wait_for_response=True

    async def _handle_capability_response(self, message: AgentMessage) -> None:
        """Handle capability discovery responses"""
        # These are handled by the send_message method when wait_for_response=True


class MCPAgentAdapter:
    """Adapter to integrate MCP with existing FoodSave AI agents"""

    def __init__(self, agent: BaseAgent, agent_id: str, agent_type: AgentType):
        self.agent = agent
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.mcp_server: MCPServer | None = None
        self.mcp_client: MCPClient | None = None

    async def initialize_mcp(self) -> None:
        """Initialize MCP server and client for this agent"""
        # Initialize MCP server
        self.mcp_server = MCPServer(self.agent_id, self.agent_type)
        await self.mcp_server.initialize()

        # Initialize MCP client
        self.mcp_client = MCPClient(self.agent_id)
        await self.mcp_client.initialize()

        # Register agent-specific tools and resources
        await self._register_agent_tools()
        await self._register_agent_resources()

        logger.info(f"MCP integration initialized for agent {self.agent_id}")

    async def shutdown_mcp(self) -> None:
        """Shutdown MCP integration"""
        if self.mcp_server:
            await self.mcp_server.shutdown()
        if self.mcp_client:
            await self.mcp_client.shutdown()

    async def _register_agent_tools(self) -> None:
        """Register agent-specific tools based on agent type"""
        if self.agent_type == AgentType.CHEF:
            await self._register_chef_tools()
        elif self.agent_type == AgentType.OCR:
            await self._register_ocr_tools()
        elif self.agent_type == AgentType.SEARCH:
            await self._register_search_tools()
        elif self.agent_type == AgentType.RAG:
            await self._register_rag_tools()
        # Add more agent types as needed

    async def _register_chef_tools(self) -> None:
        """Register Chef agent tools"""
        if not self.mcp_server:
            return

        # Recipe generation tool
        recipe_tool = MCPTool(
            name="generate_recipe",
            description="Generate a recipe based on ingredients and preferences",
            parameters={
                "type": "object",
                "properties": {
                    "ingredients": {"type": "array", "items": {"type": "string"}},
                    "cuisine_type": {"type": "string"},
                    "dietary_restrictions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["ingredients"],
            },
            handler=self._generate_recipe_handler,
            permissions=[MCPPermission.EXECUTE],
            tags=["cooking", "recipe", "food"],
        )

        self.mcp_server.register_tool(recipe_tool)

    async def _register_ocr_tools(self) -> None:
        """Register OCR agent tools"""
        if not self.mcp_server:
            return

        # Receipt processing tool
        ocr_tool = MCPTool(
            name="process_receipt",
            description="Process receipt image and extract structured data",
            parameters={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "language": {"type": "string", "default": "en"},
                },
                "required": ["image_path"],
            },
            handler=self._process_receipt_handler,
            permissions=[MCPPermission.EXECUTE],
            tags=["ocr", "receipt", "extraction"],
        )

        self.mcp_server.register_tool(ocr_tool)

    async def _register_search_tools(self) -> None:
        """Register Search agent tools"""
        if not self.mcp_server:
            return

        # Web search tool
        search_tool = MCPTool(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
            handler=self._web_search_handler,
            permissions=[MCPPermission.EXECUTE],
            tags=["search", "web", "information"],
        )

        self.mcp_server.register_tool(search_tool)

    async def _register_rag_tools(self) -> None:
        """Register RAG agent tools"""
        if not self.mcp_server:
            return

        # Knowledge search tool
        rag_tool = MCPTool(
            name="search_knowledge",
            description="Search knowledge base for relevant information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "collection": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            handler=self._search_knowledge_handler,
            permissions=[MCPPermission.EXECUTE],
            tags=["rag", "knowledge", "search"],
        )

        self.mcp_server.register_tool(rag_tool)

    async def _register_agent_resources(self) -> None:
        """Register agent-specific resources"""
        if not self.mcp_server:
            return

        # Agent metadata resource
        metadata_resource = MCPResource(
            name="agent_metadata",
            type="metadata",
            description="Agent metadata and capabilities",
            uri=f"agent://{self.agent_id}/metadata",
            permissions=[MCPPermission.READ],
        )

        self.mcp_server.register_resource(metadata_resource)

    # Tool handlers - these would delegate to the actual agent

    async def _generate_recipe_handler(self, **kwargs) -> dict[str, Any]:
        """Handle recipe generation"""
        response = await self.agent.process(kwargs)
        return {"recipe": response.data, "success": response.success}

    async def _process_receipt_handler(self, **kwargs) -> dict[str, Any]:
        """Handle receipt processing"""
        response = await self.agent.process(kwargs)
        return {"receipt_data": response.data, "success": response.success}

    async def _web_search_handler(self, **kwargs) -> dict[str, Any]:
        """Handle web search"""
        response = await self.agent.process(kwargs)
        return {"search_results": response.data, "success": response.success}

    async def _search_knowledge_handler(self, **kwargs) -> dict[str, Any]:
        """Handle knowledge search"""
        response = await self.agent.process(kwargs)
        return {"knowledge_results": response.data, "success": response.success}


# Utility functions for MCP integration


async def create_mcp_enabled_agent(
    agent: BaseAgent, agent_id: str, agent_type: AgentType
) -> MCPAgentAdapter:
    """Create an MCP-enabled agent adapter"""
    adapter = MCPAgentAdapter(agent, agent_id, agent_type)
    await adapter.initialize_mcp()
    return adapter


async def discover_all_agent_capabilities(
    client: MCPClient, agent_ids: list[str]
) -> dict[str, dict[str, Any]]:
    """Discover capabilities of multiple agents"""
    capabilities = {}

    for agent_id in agent_ids:
        try:
            agent_caps = await client.discover_capabilities(agent_id)
            if agent_caps:
                capabilities[agent_id] = agent_caps
        except Exception as e:
            logger.error(f"Failed to discover capabilities for {agent_id}: {e}")

    return capabilities


def create_mcp_tool_from_function(
    func: Callable,
    name: str,
    description: str,
    parameters: dict[str, Any],
    permissions: list[MCPPermission] | None = None,
) -> MCPTool:
    """Create an MCP tool from a Python function"""
    return MCPTool(
        name=name,
        description=description,
        parameters=parameters,
        handler=func,
        permissions=permissions or [MCPPermission.EXECUTE],
    )
