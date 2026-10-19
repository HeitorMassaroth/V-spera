"""Gerenciador de conexões WebSocket para streaming em tempo real."""

from __future__ import annotations
import json
import logging
from typing import Set, Any
from fastapi import WebSocket

logger = logging.getLogger("vespera.websocket")


class WebSocketManager:
    """Gerencia conexões ativas e transmissão de deltas de simulação."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Aceita e armazena uma nova conexão WebSocket."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Cliente conectado. Total de conexões ativas: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a conexão ao desconectar."""
        self.active_connections.discard(websocket)
        logger.info(f"Cliente desconectado. Total de conexões ativas: {len(self.active_connections)}")

    async def broadcast(self, message: Any) -> None:
        """Transmite mensagem serializada para todos os clientes ativos de forma assíncrona."""
        if not self.active_connections:
            return

        payload = json.dumps(message)
        dead_connections: Set[WebSocket] = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Erro ao transmitir para cliente WebSocket: {e}")
                dead_connections.add(connection)

        for dead in dead_connections:
            self.disconnect(dead)
