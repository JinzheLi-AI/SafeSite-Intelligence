import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import select, update
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.knowledge.models import OfficialDocument, SourceChunk
from app.knowledge.registry import source_set, require_registered
from app.knowledge.contracts import KnowledgeError
from app.knowledge.download import fetch
from app.knowledge.chunking import extract, PARSER_VERSION
from app.knowledge.embeddings import Embedder, validate_vectors

def ingest_document(db, spec, data, retrieved_at, embedder=None, *, allow_download=False, rebuild=False):
    require_registered(spec)
    embedder = embedder or Embedder()
    checksum = hashlib.sha256(data).hexdigest()
    if checksum != spec.sha256:
        raise KnowledgeError('Official PDF changed from its reviewed checksum. Review source/version metadata and update the controlled manifest before ingestion.')
    parser_version = PARSER_VERSION + ':' + hashlib.sha256(spec.model_dump_json().encode()).hexdigest()[:12]
    existing = db.scalar(select(OfficialDocument).where(OfficialDocument.source_key == spec.key,
        OfficialDocument.checksum == checksum, OfficialDocument.embedding_signature == embedder.signature,
        OfficialDocument.parser_version == parser_version))
    if existing and not rebuild:
        return existing, False
    passages, notes = extract(data,spec)
    eligible = [p for p in passages if p.active]
    vectors = embedder.encode([p.section_heading+'\n'+p.text for p in eligible], allow_download=allow_download) if eligible else []
    if eligible:
        validate_vectors(vectors,len(eligible))
    # A document revision and its vectors become visible atomically, never as a partial index.
    db.execute(update(OfficialDocument).where(OfficialDocument.source_key == spec.key).values(active=False))
    if existing:
        # Rebuild embeddings in place; immutable chunk text / citation IDs are preserved.
        old_chunks = list(db.scalars(select(SourceChunk).where(SourceChunk.document_id == existing.id).order_by(SourceChunk.ordinal)))
        if [c.text for c in old_chunks] != [p.text for p in passages]:
            raise KnowledgeError('Parser output changed without a parser version increment.')
        iterator = iter(vectors)
        for chunk, passage in zip(old_chunks, passages):
            chunk.embedding = next(iterator) if passage.active else []
            chunk.active = passage.active
        existing.active = spec.active
        existing.quality_notes = notes
        return existing, True
    document = OfficialDocument(source_key=spec.key, title=spec.title, authority=spec.authority,
        jurisdiction=spec.jurisdiction, document_type=spec.document_type, source_url=spec.source_url,
        catalog_url=spec.catalog_url, publication_date=spec.publication_date, effective_date=spec.effective_date,
        version=spec.version, language=spec.language, verified=True, active=spec.active,
        related_source_key=spec.related_source_key, checksum=checksum, embedding_signature=embedder.signature,
        parser_version=parser_version, retrieved_at=retrieved_at, quality_notes=notes)
    db.add(document)
    db.flush()
    iterator = iter(vectors)
    for i,p in enumerate(passages):
        db.add(SourceChunk(document_id=document.id, ordinal=i, section=p.section[:150],
            section_heading=p.section_heading[:300], page_number=p.page_number, text=p.text,
            hazard_categories=p.hazard_categories, embedding=next(iterator) if p.active else [], active=p.active))
    db.flush()
    return document, True

def main():
    parser = argparse.ArgumentParser(description='Ingest the reviewed official Hong Kong Labour Department corpus.')
    parser.add_argument('--source-set', choices=['hk_core'], default='hk_core')
    parser.add_argument('--offline', action='store_true', help='Use previously downloaded, checksum-pinned official PDFs and cached embeddings model.')
    parser.add_argument('--rebuild', action='store_true', help='Recompute vectors while retaining immutable citation passages.')
    args = parser.parse_args()
    Base.metadata.create_all(engine)
    results = []
    for spec in source_set(args.source_set):
        try:
            if args.offline:
                cached = settings.knowledge_source_dir / (spec.key+'-'+spec.sha256+'.pdf')
                receipt = json.loads(cached.with_suffix('.pdf.json').read_text(encoding='utf-8'))
                if receipt['source_url'] != spec.source_url or receipt['sha256'] != spec.sha256:
                    raise KnowledgeError('Cached source receipt does not match the registered official source.')
                data, checksum = cached.read_bytes(), spec.sha256
                retrieved_at = datetime.fromisoformat(receipt['retrieved_at'])
            else:
                data, checksum, retrieved_at = fetch(spec, settings.knowledge_source_dir)
            with SessionLocal() as db:
                document, changed = ingest_document(db,spec,data,retrieved_at,allow_download=not args.offline,rebuild=args.rebuild)
                count = len(list(db.scalars(select(SourceChunk).where(SourceChunk.document_id==document.id))))
                db.commit()
                result = {'source':spec.key,'status':'indexed' if changed else 'unchanged',
                          'document_id':document.id,'chunks':count,'sha256':checksum,'quality_notes':document.quality_notes}
        except Exception as exc:
            result = {'source':spec.key,'status':'failed','error_type':type(exc).__name__,
                      'message':str(exc) if isinstance(exc,KnowledgeError) else 'Download or indexing failed; no partial document was activated.'}
        results.append(result)
        print(json.dumps(result,ensure_ascii=True),flush=True)
    settings.knowledge_source_dir.mkdir(parents=True,exist_ok=True)
    (settings.knowledge_source_dir/'ingestion-report.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    if any(r['status']=='failed' for r in results):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
