"""Phase 3 write tool stubs for RED-state test collection."""


async def page_create(ctx, name: str, properties: dict | None = None, blocks: list | None = None) -> str:
    raise NotImplementedError("page_create is not implemented yet")


async def block_append(ctx, page: str, blocks: list) -> str:
    raise NotImplementedError("block_append is not implemented yet")


async def block_update(ctx, uuid: str, content: str) -> str:
    raise NotImplementedError("block_update is not implemented yet")


async def block_delete(ctx, uuid: str) -> str:
    raise NotImplementedError("block_delete is not implemented yet")
