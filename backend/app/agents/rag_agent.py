"""RAG Agent for finding enrichment and assistant knowledge retrieval."""
from __future__ import annotations

import hashlib
import json
import re
import asyncio
from typing import Any, Optional


from app.core.config import get_settings
from app.core.llm import BaseLLMClient, get_llm_client
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.core.template_loader import get_prompt_loader
from app.models.finding import Finding

logger = get_logger(__name__)


class RAGAgent:
    """Vector-search RAG agent with Gemini enrichment when configured."""

    def __init__(self, llm: Optional[BaseLLMClient] = None) -> None:
        self._settings = get_settings()
        self._repo_config = get_repository_config()
        self._prompt_loader = get_prompt_loader()
        self._llm = llm or self._build_llm()
        self._client = self._build_chroma_client()
        self._collection: Any = None
        self._init_lock = asyncio.Lock()
        self._init_error: Optional[Exception] = None

    async def _ensure_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        if self._init_error is not None:
            raise self._init_error
        async with self._init_lock:
            if self._collection is None:
                try:
                    logger.info("RAGAgent: lazily initializing embedding model and collection")
                    self._collection = self._get_or_seed_collection()
                    logger.info("RAGAgent: embedding model and collection initialized")
                except Exception as exc:
                    logger.error("RAGAgent: failed to initialize embedding model/collection: %s", exc, exc_info=True)
                    self._init_error = exc
                    raise
        return self._collection

    async def enrich_findings_batch(self, findings: list[Finding]) -> list[Finding]:
        """Enrich findings from RAG context and Gemini-generated JSON (async)."""
        if not findings:
            return findings
        # Limit RAG enrichment to top 8 findings to reduce LLM calls and latency
        findings_to_enrich = findings[:8]
        remaining = findings[8:]
        contexts = [await self.retrieve_context(f"{f.rule_id} {f.title} {f.description}") for f in findings_to_enrich]
        if self._llm is not None:
            try:
                enriched = await self._batch_enrich_with_llm(findings_to_enrich, contexts)
                return enriched + remaining
            except Exception as exc:
                logger.warning("RAG Gemini enrichment failed; using retrieval-only enrichment: %s", exc)
        return self._rag_only_enrich(findings_to_enrich, contexts) + remaining

    def enrich_finding(self, finding: Finding) -> Finding:
        """Enrich a single finding."""
        enriched = self.enrich_findings_batch([finding])
        return enriched[0] if enriched else finding

    async def answer(self, query: str, context: Optional[str] = None) -> tuple[str, list[str]]:
        """Answer a developer question using retrieved context and Gemini (async)."""
        chunks, sources = await self._retrieve(query)
        retrieved_context = "\n\n".join(chunks)
        if self._llm is None:
            reporting = self._repo_config.load("reporting.json")
            return str(reporting.get("no_context_answer")), sources
        prompt = self._prompt_loader.render(
            "rag_answer.txt",
            context=context or "",
            retrieved_context=retrieved_context,
            question=query,
        )
        return await self._llm.agenerate(prompt, temperature=self._settings.llm_default_temperature, max_tokens=self._settings.llm_default_max_tokens), sources

    async def retrieve_context(self, query: str) -> dict[str, Any]:
        """Return retrieved chunks and source names for a query."""
        chunks, sources = await self._retrieve(query)
        return {"chunks": chunks, "sources": sources}

    def _build_llm(self) -> BaseLLMClient | None:
        try:
            return get_llm_client()
        except Exception as exc:
            logger.warning("LLM client unavailable for RAGAgent: %s", exc)
            return None

    async def _batch_enrich_with_llm(self, findings: list[Finding], contexts: list[dict[str, Any]]) -> list[Finding]:
        finding_blocks = []
        for index, (finding, ctx) in enumerate(zip(findings, contexts), start=1):
            key_sentences = self._extract_key_sentences(ctx.get("chunks", []))
            finding_blocks.append(
                json.dumps(
                    {
                        "index": index,
                        "rule_id": finding.rule_id,
                        "severity": finding.severity.value,
                        "category": finding.category,
                        "tool": finding.tool_source,
                        "title": finding.title,
                        "description": finding.description,
                        "evidence": finding.evidence,
                        "retrieved_context": key_sentences,
                    },
                    ensure_ascii=True,
                )
            )
        try:
            prompt = self._prompt_loader.render("rag_enrich_batch.txt", findings="\n".join(finding_blocks), count=len(findings))
        except Exception as exc:
            logger.error("RAGAgent prompt rendering failed: %s", exc, exc_info=True)
            raise
        try:
            raw = await self._llm.agenerate(
                prompt,
                temperature=0.1,
                max_tokens=3000
            ) if self._llm else ""
        except Exception as exc:
            logger.error("RAGAgent LLM call failed: %s", exc, exc_info=True)
            raise

        try:
            enrichment_map = self._parse_batch_json(raw)
        except Exception as exc:
            logger.error("RAGAgent _parse_batch_json failed: %s", exc, exc_info=True)
            raise

        result: list[Finding] = []

        for index, finding in enumerate(findings, start=1):
            entry = enrichment_map.get(index, {})
            try:
                updates = self._entry_updates(entry, finding)
            except Exception as exc:
                logger.error("RAGAgent _entry_updates failed for index %d: %s — entry=%r", index, exc, entry)
                raise
            try:
                new_finding = finding.model_copy(update=updates) if updates else finding
            except Exception as exc:
                logger.error("RAGAgent model_copy failed for index %d: %s — updates=%r", index, exc, updates)
                raise
            result.append(new_finding)

        return result

    def _entry_updates(
        self,
        entry: dict[str, Any],
        finding: Finding,
    ) -> dict[str, Any]:

        updates = {}

        fields = [
            "title",
            "explanation",
            "root_cause",
            "corrected_code",
            "best_practice",
        ]

        for field in fields:

            value = entry.get(field)

            if value:
                updates[field] = str(value).strip()

        remediation = entry.get("remediation")

        if remediation:
            updates["remediation"] = str(remediation).strip()

        owasp = entry.get("owasp_reference")

        if owasp:
            updates["owasp_reference"] = str(owasp).strip()

        return updates

    @staticmethod
    def _parse_batch_json(raw: str) -> dict[int, dict[str, Any]]:
        text = raw.strip()
        if text.startswith("```"):
            text = "\n".join(line for line in text.splitlines() if not line.strip().startswith("```")).strip()
        # Try to extract JSON array from text
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("RAGAgent could not parse Gemini JSON: %s — raw[:200]=%r", exc, raw[:200])
            return {}
        if isinstance(parsed, list):
            return {int(item.get("index", index + 1)): item for index, item in enumerate(parsed) if isinstance(item, dict)}
        if isinstance(parsed, dict):
            return {int(parsed.get("index", 1)): parsed}
        return {}

    def _rag_only_enrich(self, findings: list[Finding], contexts: list[dict[str, Any]]) -> list[Finding]:
        result: list[Finding] = []
        for finding, ctx in zip(findings, contexts):
            chunks = ctx.get("chunks", [])
            sources = ctx.get("sources", [])
            if not chunks:
                result.append(finding)
                continue
            
            # Combine all chunks for analysis
            combined_text = "\n\n".join(chunks)
            key_sentences = self._extract_key_sentences(chunks)
            
            updates: dict[str, Any] = {}
            
            # Extract explanation
            if key_sentences and not finding.explanation:
                updates["explanation"] = " ".join(key_sentences[:2])
            
            # Extract remediation
            if key_sentences and not finding.remediation:
                updates["remediation"] = "\n".join(f"{idx + 1}. {sentence}" for idx, sentence in enumerate(key_sentences[:3]))
            
            # For remaining fields, provide structured fallback based on available context
            if not finding.root_cause:
                updates["root_cause"] = self._derive_fallback_field(finding, "root_cause", combined_text)
            
            if not finding.corrected_code:
                updates["corrected_code"] = self._derive_fallback_field(finding, "corrected_code", combined_text)
            
            if not finding.secure_alternative:
                updates["secure_alternative"] = self._derive_fallback_field(finding, "secure_alternative", combined_text)
            
            if not finding.best_practice:
                updates["best_practice"] = self._derive_fallback_field(finding, "best_practice", combined_text)
            
            if not finding.prevention:
                updates["prevention"] = self._derive_fallback_field(finding, "prevention", combined_text)
            
            if not finding.maintainability_impact:
                if finding.category == "quality":
                    updates["maintainability_impact"] = self._derive_fallback_field(finding, "maintainability_impact", combined_text)
                else:
                    # For security findings, set to N/A
                    updates["maintainability_impact"] = "N/A"
            
            # Infer OWASP reference
            if not finding.owasp_reference:
                inferred = self._infer_owasp_from_sources(sources, finding)
                if inferred:
                    updates["owasp_reference"] = inferred
            
            result.append(finding.model_copy(update=updates) if updates else finding)
        return result

    @staticmethod
    def _extract_key_sentences(chunks: list[str], max_sentences: int = 6) -> list[str]:
        sentences: list[str] = []
        for chunk in chunks[:2]:
            for sentence in chunk.replace("\n", " ").split(". "):
                cleaned = sentence.strip()
                if cleaned:
                    sentences.append(cleaned)
                if len(sentences) >= max_sentences:
                    return sentences
        return sentences

    @staticmethod
    def _extract_section(text: str, keywords: list[str]) -> str | None:
        """
        Extract only a short relevant paragraph instead of the whole markdown.
        """

        paragraphs = text.split("\n\n")

        for para in paragraphs:
            lower = para.lower()

            if any(k in lower for k in keywords):

                para = re.sub(r"```.*?```", "", para, flags=re.DOTALL)
                para = para.replace("\n", " ").strip()

                if len(para) > 300:
                    para = para[:300]

                return para

        return None

    @staticmethod
    def _extract_code_blocks(text: str, keywords: list[str]) -> str | None:

        blocks = re.findall(
            r"```(?:python|java)?\n(.*?)```",
            text,
            flags=re.DOTALL,
        )

        for block in blocks:

            if any(k in block.lower() for k in keywords):

                lines = block.strip().splitlines()

                return "\n".join(lines[:12])

        return None

    def _derive_fallback_field(
        self,
        finding: Finding,
        field_name: str,
        context_text: str,
    ) -> str:

        templates = {

            "root_cause":
            f"{finding.description}. The issue exists because insecure coding practices were used.",

            "corrected_code":
            f"Refer to the secure code example for {finding.rule_id}.",

            "secure_alternative":
            "Use the secure implementation shown in the OWASP cheat sheet.",

            "best_practice":
            "Follow OWASP Secure Coding Guidelines and avoid insecure APIs.",

            "prevention":
            "Use code reviews, static analysis, and secure coding practices to prevent this issue.",

            "maintainability_impact":
            "This issue makes the code harder to maintain and increases future security risks."
        }

        if field_name == "corrected_code":

            code = self._extract_code_blocks(
                context_text,
                [
                    "safe",
                    "secure",
                    "bcrypt",
                    "preparedstatement",
                    "parameterized",
                    "literal_eval",
                ],
            )

            if code:
                return code

        keywords = {
            "root_cause": ["root cause", "cause"],
            "secure_alternative": ["safe", "secure"],
            "best_practice": ["best practice"],
            "prevention": ["prevent", "prevention"],
            "maintainability_impact": ["impact"],
        }

        if field_name in keywords:

            section = self._extract_section(
                context_text,
                keywords[field_name],
            )

            if section:
                return section

        return templates.get(field_name, "")

    def _infer_owasp_from_sources(self, sources: list[str], finding: Finding) -> Optional[str]:
        config = self._repo_config.load("owasp_mappings.json")
        source_map = config.get("source_map", {})
        source_set = {source.lower() for source in sources}
        combined = f"{finding.rule_id} {finding.description}".lower()
        for item in config.get("rule_patterns", []):
            if any(token in combined for token in item.get("tokens", [])):
                return item.get("owasp")
        for source in source_set:
            if source in source_map:
                return source_map[source]
        return None

    async def _retrieve(self, query: str) -> tuple[list[str], list[str]]:
        try:
            collection = await self._ensure_collection()
            count = collection.count()
            if count == 0:
                return [], []
            results = collection.query(query_texts=[query], n_results=min(self._settings.retrieval_count, count))
            docs = (results.get("documents") or [[]])[0]
            metas = (results.get("metadatas") or [[]])[0]
            sources = [metadata.get("source", self._settings.knowledge_base_dir) for metadata in metas]

            # Deduplicate chunks while preserving order
            seen: set[str] = set()
            unique_docs: list[str] = []
            unique_sources: list[str] = []
            for doc, source in zip(docs, sources):
                normalized = " ".join(doc.split())
                if normalized not in seen:
                    seen.add(normalized)
                    unique_docs.append(doc)
                    unique_sources.append(source)

            # Only return chunks that share meaningful words with the query
            query_words = set(query.lower().split())
            relevant: list[str] = []
            relevant_sources: list[str] = []
            for doc, source in zip(unique_docs, unique_sources):
                doc_lower = doc.lower()
                matches = sum(1 for word in query_words if len(word) > 3 and word in doc_lower)
                if matches >= 1:
                    relevant.append(doc)
                    relevant_sources.append(source)

            # If nothing matched, fall back to all retrieved chunks but kept short
            if not relevant:
                return unique_docs[:2], unique_sources[:2]
            return relevant, relevant_sources
        except Exception as exc:
            logger.error("ChromaDB retrieval failed: %s", exc)
            return [], []

    def _build_chroma_client(self) -> Any:
        # Import chromadb lazily to avoid importing optional heavy deps at module import time
        try:
            import chromadb
        except Exception as exc:  # pragma: no cover - environment-specific
            logger.warning("chromadb is not available: %s", exc)
            raise
        db_path = self._settings.vector_db_path
        db_path.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(db_path))

    def _get_or_seed_collection(self) -> Any:
        # Import embedding helper lazily to avoid optional dependency import during tests
        try:
            from chromadb.utils import embedding_functions
        except Exception as exc:  # pragma: no cover - environment-specific
            logger.warning("chromadb embedding utilities are not available: %s", exc)
            raise
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self._settings.embedding_model
        )
        collection = self._client.get_or_create_collection(
            name=self._settings.rag_collection,
            embedding_function=embedding_function,
        )
        # Always check for new/un-indexed knowledge-base files and ingest them.
        # This ensures newly added reference files (e.g. python_security.md,
        # java_security.md, secure_coding.md, deserialization.md) are loaded,
        # chunked, embedded, and available for RAG retrieval without requiring
        # a manual DB wipe.
        self._seed_collection(collection)
        return collection

    def _seed_collection(self, collection: Any) -> None:
        """Ingest knowledge-base markdown files into the Chroma collection.

        Only newly added chunks are upserted. Existing chunks are left untouched,
        so restarting the app does not re-embed the entire knowledge base.
        """
        kb_path = self._settings.knowledge_base_path
        if not kb_path.exists():
            logger.warning("Knowledge base path '%s' does not exist; RAG disabled", kb_path)
            return

        # Fetch IDs already present in the collection so we only add new chunks.
        existing_ids: set[str] = set()
        try:
            count = collection.count()
            if count > 0:
                # Get all existing IDs in batches to avoid pulling everything at once.
                existing = collection.get(include=[])  # only IDs
                existing_ids = set(existing.get("ids", []) or [])
        except Exception as exc:
            logger.warning("Could not read existing Chroma IDs; will upsert all: %s", exc)

        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []
        for md_file in sorted(kb_path.glob("**/*.md")):
            source_name = md_file.stem
            content = md_file.read_text(encoding="utf-8")
            for index, chunk in enumerate(self._chunk_text(content)):
                doc_id = hashlib.md5(f"{source_name}-{index}".encode()).hexdigest()
                if doc_id in existing_ids:
                    continue
                documents.append(chunk)
                metadatas.append({"source": source_name, "chunk": index})
                ids.append(doc_id)

        if documents:
            logger.info("Seeding RAG collection with %d new chunk(s)", len(documents))
            collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        else:
            logger.info("RAG collection is up to date; no new chunks to seed")

    def _chunk_text(self, text: str) -> list[str]:
        words = text.split()
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        overlap = self._settings.chunk_overlap
        for word in words:
            current.append(word)
            current_len += len(word) + 1
            if current_len >= self._settings.chunk_size:
                chunks.append(" ".join(current))
                current = current[-overlap:]
                current_len = sum(len(item) + 1 for item in current)
        if current:
            chunks.append(" ".join(current))
        return chunks
