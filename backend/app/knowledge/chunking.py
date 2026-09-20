import re
from dataclasses import dataclass
import pymupdf
from app.knowledge.concepts import categories
from app.knowledge.contracts import KnowledgeError, SourceSpec

PARSER_VERSION = 'hk-sections-v5'
CLAUSE = re.compile(r'^(\d+(?:\.\d+){1,3}(?:\([a-z]\))?)(?:\s|$)')
SUBCLAUSE = re.compile(r'^\(([a-z])\)\s')
@dataclass
class Passage:
    section: str
    section_heading: str
    page_number: int
    text: str
    hazard_categories: list[str]
    active: bool

def extract(data: bytes, spec: SourceSpec) -> tuple[list[Passage], list[str]]:
    try:
        pdf = pymupdf.open(stream=data, filetype='pdf')
    except Exception:
        raise KnowledgeError('PDF cannot be parsed.') from None
    if pdf.is_encrypted or len(pdf) > 300:
        pdf.close()
        raise KnowledgeError('Encrypted or excessively long PDF is not supported.')
    passages, notes = [], []
    if not spec.retrieval_enabled:
        notes.append('Reference-only amendment table: old/new columns retained for traceability but excluded from retrieval.')
    section, heading = '', ''
    total_letters = 0
    with pdf:
        for page_index, page in enumerate(pdf):
            page_number = page_index + 1
            if page_number < spec.index_page_start or page_number > spec.index_page_end:
                notes.append(f'PDF page {page_number}: reviewed cover/contents/reference/figure/contact page excluded')
                continue
            raw = page.get_text()
            total_letters += len(re.findall('[a-zA-Z]',raw))
            # Contents/reproduction/contact pages are not substantive evidence.
            if ('Contents' in raw and len(re.findall(r'\.{3,}',raw)) > 2) or ('Contents' in raw and page_index < 6):
                notes.append(f'PDF page {page_number}: contents excluded')
                continue
            # Reviewed layouts: handbook native stream preserves its illustrated panels;
            # electrical PDF spreads require left-page then right-page reading order.
            blocks = page.get_text('blocks', sort=spec.key != 'handbook')
            if spec.key == 'electrical':
                blocks.sort(key=lambda b:(b[0]>=page.rect.width/2,b[1],b[0]))
            buffer = []
            buffer_section, buffer_heading = section, heading
            def flush():
                nonlocal buffer
                if not buffer:
                    return
                text = '\n'.join(buffer)
                tags = categories(text, [str(h) for h in spec.hazards])
                excluded = any(buffer_section.startswith(code) or code in text for code in spec.excluded_sections)
                # Keep historical text for traceability; never retrieve known amended sections.
                actionable = bool(re.search(r'\b(shall|should|must|ensure|wear|keep|provide|use|avoid|never|remove|maintain|inspect|check|protect|clear|restrict|required|damaged|obstruction|risk|hazard)\b',text,re.I))
                active = spec.retrieval_enabled and bool(tags) and not excluded and len(text) <= 2200 and len(text.split()) >= 8 and actionable
                if excluded:
                    notes.append(f'PDF page {page_number}, {buffer_section}: excluded due to current amendment')
                if len(text) > 2200:
                    notes.append(f'PDF page {page_number}, {buffer_section}: oversized paragraph retained but not indexed')
                passages.append(Passage(buffer_section or f'PDF page {page_number}', buffer_heading,
                    page_number, text, tags, active))
                buffer = []
            for block in blocks:
                if len(block) > 6 and block[6] != 0:
                    continue
                text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', block[4])
                lines = text.splitlines()
                clean_lines = [line for line in lines if not re.search(r'\b[a-zA-Z]{35,}\b',line)]
                if len(clean_lines) != len(lines):
                    notes.append(f'PDF page {page_number}: malformed concatenated line excluded; surrounding paragraph preserved')
                text = '\n'.join(clean_lines)
                text = re.sub(r'(?<=\w)-\n(?=[a-z])', '',text)
                text = re.sub(r'\s+', ' ', text).strip()
                if not text or re.fullmatch(r'[-\s\d]+',text):
                    continue
                if (text.upper().startswith('CODE OF PRACTICE FOR ') and len(text)<100
                    or text.startswith('Guidance Notes on the Selection, Use and Maintenance of SAFETY HELMETS')):
                    continue
                # Drop non-English bilingual duplicates; preserve English extraction without OCR.
                if len(re.findall('[a-zA-Z]',text)) < 2:
                    continue
                if any(t in text.lower() for t in ['complaint hotline','enquiry@','all complaints','freely reproduced','printed by the government','this publication is issued']):
                    continue
                if len(re.findall(r'\b[a-zA-Z]{35,}\b',text)) or text.count('\ufffd') > max(2,len(text)//100):
                    notes.append(f'PDF page {page_number}: malformed text block excluded')
                    continue
                clause = CLAUSE.match(text)
                subclause = SUBCLAUSE.match(text)
                is_heading = len(text)<100 and text[0].isupper() and not re.search(r'[.;:,!?]',text) and len(text.split()) < 12 and not text.lower().startswith(('the ','a ','an ','to ','and ','or ','if ','when '))
                if clause or subclause or is_heading:
                    flush()
                    if clause:
                        section = clause.group(1)
                    elif text.startswith(('Appendix ', 'Annex')):
                        section = text[:150]
                    if is_heading:
                        heading = text[:300]
                    buffer_section, buffer_heading = section, heading
                if buffer and sum(len(x) for x in buffer) + len(text) > 1400:
                    flush()
                    buffer_section, buffer_heading = section, heading
                buffer.append(text)
            flush()
    if total_letters < 250 or not passages:
        raise KnowledgeError('No usable native English text. Scanned/garbled PDFs are not silently OCRed or verified.')
    return passages, list(dict.fromkeys(notes))
