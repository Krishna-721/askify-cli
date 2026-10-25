
import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import hashlib
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_DIR = ".askify/store"

model = None


def get_model():
    global model

    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    return model


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection("askify_collection")


def get_source_hashes(existing: dict) -> set:
    """Extract source fingerprints from existing ChromaDB metadata."""
    return {
        metadata.get("source_hash", metadata.get("hash"))
        for metadata in existing["metadatas"]
        if metadata is not None
    }


def file_needs_reindex(
    chunk: dict,
    collection,
    existing: dict | None = None,
) -> bool:
    """Check whether this source has a different source fingerprint."""
    source = chunk["source"]
    source_hash = chunk.get("source_hash", chunk["hash"])

    if existing is None:
        existing = collection.get(
            where={"source": source},
            include=["metadatas"],
        )

    if not existing["ids"]:
        return True

    existing_source_hashes = get_source_hashes(existing)

    return existing_source_hashes != {source_hash}


def make_id(source: str, content: str) -> str:
    return hashlib.md5(
        (source + content).encode("utf-8")
    ).hexdigest()


def embed_chunks(
    chunks: list[dict],
    scan_path: str | None = None,
):
    collection = get_collection()

    chunks_by_source = {}

    for chunk in chunks:
        chunks_by_source.setdefault(
            chunk["source"], []
        ).append(chunk)

    changed_sources = set()

    # Keep the old IDs so we can remove obsolete chunks
    # only after the new chunks have been stored successfully.
    old_ids_by_source = {}

    for source, source_chunks in chunks_by_source.items():
        source_hashes = {
            chunk.get("source_hash", chunk["hash"])
            for chunk in source_chunks
        }

        if len(source_hashes) != 1:
            raise ValueError(
                f"Inconsistent source fingerprints for {source!r}: "
                f"{source_hashes}"
            )

        # Fetch existing records once per source.
        existing = collection.get(
            where={"source": source},
            include=["metadatas"],
        )

        if file_needs_reindex(
            source_chunks[0],
            collection,
            existing=existing,
        ):
            changed_sources.add(source)
            old_ids_by_source[source] = existing["ids"]

    chunks_to_index = [
        chunk
        for source, source_chunks in chunks_by_source.items()
        if source in changed_sources
        for chunk in source_chunks
    ]

    if chunks_to_index:
        contents = [
            chunk["content"]
            for chunk in chunks_to_index
        ]

        embeddings = get_model().encode(contents).tolist()

        ids = [
            make_id(chunk["source"], chunk["content"])
            for chunk in chunks_to_index
        ]

        metadatas = [
            {
                "source": chunk["source"],
                "type": chunk["type"],
                "source_hash": chunk.get(
                    "source_hash", chunk["hash"]
                ),
                "chunk_hash": hashlib.sha256(
                    chunk["content"].encode("utf-8")
                ).hexdigest(),
                "hash": chunk.get(
                    "source_hash", chunk["hash"]
                ),
            }
            for chunk in chunks_to_index
        ]

        # Store the new chunks first.
        # If this fails, the old chunks have not been deleted.
        collection.upsert(
            ids=ids,
            documents=contents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        # Group new IDs by source.
        new_ids_by_source = {}

        for chunk, chunk_id in zip(chunks_to_index, ids):
            new_ids_by_source.setdefault(
                chunk["source"], set()
            ).add(chunk_id)

        # Delete only old IDs that are not reused by the new version.
        for source in changed_sources:
            old_ids = set(old_ids_by_source[source])
            new_ids = new_ids_by_source.get(source, set())

            obsolete_ids = list(old_ids - new_ids)

            if obsolete_ids:
                collection.delete(ids=obsolete_ids)

        print(
            f"[askify] Reindexed {len(changed_sources)} sources "
            f"({len(chunks_to_index)} chunks)"
        )

    else:
        print("[askify] No new or changed sources")

    # Cleanup only when the caller supplies a successfully scanned path.
    if scan_path is not None:
        delete_stale_sources(
            active_sources=set(chunks_by_source),
            collection=collection,
            scan_path=scan_path,
        )


def delete_stale_sources(
    active_sources: set[str],
    collection,
    scan_path: str,
):
    """Delete indexed sources missing from the current scan scope."""
    root = Path(scan_path).resolve()

    existing = collection.get(include=["metadatas"])

    source_to_ids = {}

    for chunk_id, metadata in zip(
        existing["ids"],
        existing["metadatas"],
    ):
        if metadata is None:
            continue

        source = metadata.get("source")

        if source is None:
            continue

        source_to_ids.setdefault(source, []).append(chunk_id)

    stale_sources = set()

    for source in source_to_ids:
        # Graph chunks use a separate source identity.
        original_source = source.removeprefix("graph:")

        # PDF page chunks use the original PDF as their source.
        original_source = original_source.split("::page", 1)[0]

        source_path = Path(original_source).resolve()

        if root.is_file():
            in_scope = source_path == root
        else:
            in_scope = source_path.is_relative_to(root)

        if in_scope and source not in active_sources:
            stale_sources.add(source)

    for source in stale_sources:
        collection.delete(ids=source_to_ids[source])

    if stale_sources:
        print(
            f"[askify] Removed {len(stale_sources)} stale sources"
        )
