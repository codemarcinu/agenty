import asyncio
import subprocess

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/devops", tags=["DevOps"])


class ActionResponse(BaseModel):
    success: bool
    message: str
    details: dict[str, str] | None = None


class ContainerInfo(BaseModel):
    id: str
    name: str
    image: str
    status: str
    ports: str
    created: str
    size: str


class ContainerActionRequest(BaseModel):
    container_id: str | None = None
    service_name: str | None = None


async def run_shell(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command asynchronously and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()


async def check_docker_service() -> bool:
    """Check if Docker service is running."""
    try:
        code, _, _ = await run_shell(["systemctl", "is-active", "--quiet", "docker"])
        return code == 0
    except:
        return False


# Docker Container Management
@router.post("/docker/start-all", response_model=ActionResponse)
async def start_all_containers():
    """Start all Docker containers (docker compose up -d)."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    code, out, err = await run_shell(["docker", "compose", "up", "-d"])
    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd uruchamiania kontenerów: {err}"
        )
    return ActionResponse(
        success=True,
        message="Wszystkie kontenery uruchomione pomyślnie.",
        details={"output": out},
    )


@router.post("/docker/stop-all", response_model=ActionResponse)
async def stop_all_containers():
    """Stop all Docker containers (docker compose down)."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    code, out, err = await run_shell(["docker", "compose", "down"])
    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd zatrzymywania kontenerów: {err}"
        )
    return ActionResponse(
        success=True,
        message="Wszystkie kontenery zatrzymane pomyślnie.",
        details={"output": out},
    )


@router.post("/docker/restart-all", response_model=ActionResponse)
async def restart_all_containers():
    """Restart all Docker containers."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    # Stop all containers
    code, out, err = await run_shell(["docker", "compose", "down"])
    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd zatrzymywania kontenerów: {err}"
        )

    # Start all containers
    code, out, err = await run_shell(["docker", "compose", "up", "-d"])
    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd uruchamiania kontenerów: {err}"
        )

    return ActionResponse(
        success=True,
        message="Wszystkie kontenery zrestartowane pomyślnie.",
        details={"output": out},
    )


@router.post("/docker/rebuild-all", response_model=ActionResponse)
async def rebuild_all_containers():
    """Rebuild all Docker containers (docker compose up -d --build)."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    code, out, err = await run_shell(["docker", "compose", "up", "-d", "--build"])
    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd rebuildowania kontenerów: {err}"
        )
    return ActionResponse(
        success=True,
        message="Wszystkie kontenery zrebuildowane pomyślnie.",
        details={"output": out},
    )


@router.get("/docker/status", response_model=ActionResponse)
async def docker_status():
    """Get status of all Docker containers (docker compose ps)."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    code, out, err = await run_shell(["docker", "compose", "ps"])
    if code != 0:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania statusu: {err}")
    return ActionResponse(
        success=True, message="Status kontenerów:", details={"ps": out}
    )


@router.get("/docker/containers", response_model=ActionResponse)
async def get_containers():
    """Get detailed information about all containers."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    code, out, err = await run_shell(
        [
            "docker",
            "ps",
            "-a",
            "--format",
            "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.CreatedAt}}\t{{.Size}}",
        ]
    )
    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd pobierania listy kontenerów: {err}"
        )

    return ActionResponse(
        success=True, message="Lista kontenerów:", details={"containers": out}
    )


@router.post("/docker/container/start", response_model=ActionResponse)
async def start_container(request: ContainerActionRequest):
    """Start a specific container."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    if request.container_id:
        code, out, err = await run_shell(["docker", "start", request.container_id])
    elif request.service_name:
        code, out, err = await run_shell(
            ["docker", "compose", "up", "-d", request.service_name]
        )
    else:
        raise HTTPException(
            status_code=400, detail="Musisz podać container_id lub service_name"
        )

    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd uruchamiania kontenera: {err}"
        )

    return ActionResponse(
        success=True, message="Kontener uruchomiony pomyślnie.", details={"output": out}
    )


@router.post("/docker/container/stop", response_model=ActionResponse)
async def stop_container(request: ContainerActionRequest):
    """Stop a specific container."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    if request.container_id:
        code, out, err = await run_shell(["docker", "stop", request.container_id])
    elif request.service_name:
        code, out, err = await run_shell(
            ["docker", "compose", "stop", request.service_name]
        )
    else:
        raise HTTPException(
            status_code=400, detail="Musisz podać container_id lub service_name"
        )

    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd zatrzymywania kontenera: {err}"
        )

    return ActionResponse(
        success=True, message="Kontener zatrzymany pomyślnie.", details={"output": out}
    )


@router.post("/docker/container/restart", response_model=ActionResponse)
async def restart_container(request: ContainerActionRequest):
    """Restart a specific container."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    if request.container_id:
        code, out, err = await run_shell(["docker", "restart", request.container_id])
    elif request.service_name:
        code, out, err = await run_shell(
            ["docker", "compose", "restart", request.service_name]
        )
    else:
        raise HTTPException(
            status_code=400, detail="Musisz podać container_id lub service_name"
        )

    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd restartowania kontenera: {err}"
        )

    return ActionResponse(
        success=True,
        message="Kontener zrestartowany pomyślnie.",
        details={"output": out},
    )


@router.get("/docker/container/logs/{container_id}")
async def get_container_logs(container_id: str, lines: int = 100):
    """Get logs from a specific container."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    code, out, err = await run_shell(
        ["docker", "logs", "--tail", str(lines), container_id]
    )
    if code != 0:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania logów: {err}")

    return ActionResponse(
        success=True,
        message="Logi kontenera:",
        details={"logs": out, "container_id": container_id},
    )


@router.get("/docker/system-info", response_model=ActionResponse)
async def get_docker_system_info():
    """Get Docker system information."""
    if not await check_docker_service():
        raise HTTPException(
            status_code=500, detail="Usługa Docker nie jest uruchomiona"
        )

    # Docker info
    code, info_out, info_err = await run_shell(["docker", "info"])
    if code != 0:
        raise HTTPException(
            status_code=500, detail=f"Błąd pobierania informacji o Docker: {info_err}"
        )

    # Docker system df
    code, df_out, df_err = await run_shell(["docker", "system", "df"])
    if code != 0:
        df_out = "Błąd pobierania informacji o dysku"

    return ActionResponse(
        success=True,
        message="Informacje o systemie Docker:",
        details={"info": info_out, "disk_usage": df_out},
    )


# Tauri Management
@router.post("/tauri/start", response_model=ActionResponse)
async def start_tauri_dev():
    """Start Tauri dev mode (tauri dev)."""
    # Start as background process (screen/tmux/nohup recommended in prod)
    try:
        subprocess.Popen(
            [
                "bash",
                "-c",
                "cd ../../myappassistant-chat-frontend && npx tauri dev > tauri-dev.log 2>&1 &",
            ]
        )
        return ActionResponse(success=True, message="Tauri dev uruchomione w tle.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tauri/stop", response_model=ActionResponse)
async def stop_tauri_dev():
    """Stop Tauri dev mode (killall tauri dev)."""
    code, out, err = await run_shell(["pkill", "-f", "tauri dev"])
    if code not in {0, 1}:  # 1 = not running
        raise HTTPException(status_code=500, detail=err)
    return ActionResponse(success=True, message="Tauri dev zatrzymane.")


@router.get("/tauri/status", response_model=ActionResponse)
async def tauri_status():
    """Check if Tauri dev is running."""
    code, out, err = await run_shell(["pgrep", "-f", "tauri dev"])
    running = code == 0
    return ActionResponse(
        success=True,
        message="Tauri dev uruchomione." if running else "Tauri dev zatrzymane.",
        details={"running": str(running)},
    )


@router.get("/tauri/logs", response_model=ActionResponse)
async def tauri_logs():
    """Get last 100 lines of Tauri dev log."""
    code, out, err = await run_shell(
        ["tail", "-n", "100", "../../myappassistant-chat-frontend/tauri-dev.log"]
    )
    if code != 0:
        raise HTTPException(status_code=500, detail=err)
    return ActionResponse(
        success=True, message="Logi Tauri dev:", details={"logs": out}
    )
