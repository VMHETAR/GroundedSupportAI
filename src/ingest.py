"""Ingest IRS Pub 334 + 587 PDFs -> chunks -> Qdrant + data/chunks.jsonl.

Usage: .venv/bin/python -m src.ingest [--reindex]
Public domain (US federal government work, 17 U.S.C. 105).
"""
import os, re, sys, json, requests

DATA = "data"
CORPUS = os.path.join(DATA, "corpus")
CHUNKS = os.path.join(DATA, "chunks.jsonl")

PUBS = [
    {"id": "p334", "pdf": "https://www.irs.gov/pub/irs-pdf/p334.pdf", "title": "Publication 334, Tax Guide for Small Business"},
    {"id": "p587", "pdf": "https://www.irs.gov/pub/irs-pdf/p587.pdf", "title": "Publication 587, Business Use of Your Home"},
]

# heading regex -> section id (must match eval expected sources)
SECTION_PATTERNS = [
    (r"are you self-employed", "p334-are-you-self-employed"),
    (r"statutory employee", "p334-are-you-self-employed"),
    (r"business income", "p334-business-income"),
    (r"cost of goods sold", "p334-business-income"),
    (r"gross profit", "p334-business-income"),
    (r"business expenses", "p334-business-expenses-general"),
    (r"bad debts?", "p334-business-expenses-general"),
    (r"car and truck expenses|local transportation|standard mileage rate", "p334-car-truck"),
    (r"depreciation|section 179", "p334-business-expenses-general"),
    (r"travel and meals|travel expenses", "p334-travel-meals"),
    (r"business use of your home|office in the home", "p587-home-use"),
    (r"exclusive use|regular use", "p587-exclusive-regular-use"),
    (r"principal place of business", "p587-principal-place"),
    (r"simplified method", "p587-simplified-method"),
    (r"actual expenses|actual expense method|depreciation.*home|form 8829", "p587-actual-expenses"),
    (r"self-employment.*tax|who must pay se tax|se tax rate|figuring earnings subject", "p334-se-tax"),
    (r"figuring net profit|net operating losses", "p334-business-income"),
]

def download():
    os.makedirs(CORPUS, exist_ok=True)
    for p in PUBS:
        dest = os.path.join(CORPUS, p["id"] + ".pdf")
        if os.path.exists(dest) and os.path.getsize(dest) > 100000:
            print(f"cached {dest}")
            continue
        print(f"downloading {p['pdf']} ...")
        r = requests.get(p["pdf"], headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}, timeout=120)
        r.raise_for_status()
        open(dest, "wb").write(r.content)
        print(f"saved {dest} ({len(r.content)} bytes)")

def extract_text(pdf_path):
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    pages = []
    for i, pg in enumerate(reader.pages):
        try:
            t = pg.extract_text() or ""
        except Exception:
            t = ""
        pages.append((i + 1, t))
    return pages

def detect_section(paragraph, current):
    low = paragraph.lower()[:200]
    for pat, sec in SECTION_PATTERNS:
        if re.search(pat, low):
            return sec
    return current

def chunk_text(text, size=1800, overlap=200):
    # clean PDF hyphenation/ligature artifacts that hurt retrieval + Tier1
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)  # join hyphenated breaks
    text = re.sub(r"(?<=\w) (?=\w)", " ", text)  # keep single spaces (no-op guard)
    text = re.sub(r"\s+", " ", text).strip()
    # fix common pypdf spaced headings ("T ravel", "T ax", "Y ou")
    text = re.sub(r"\b([A-Z]) ([a-z]{2,})", r"\1\2", text)
    chunks = []
    i = 0
    while i < len(text):
        j = min(len(text), i + size)
        # extend to sentence boundary
        if j < len(text):
            k = text.rfind(". ", i, j + 200)
            if k > i + size // 2:
                j = k + 1
        chunks.append(text[i:j].strip())
        if j >= len(text):
            break
        i = max(i + 1, j - overlap)
    return [c for c in chunks if len(c) > 200]

def main():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.config import load_config
    cfg = load_config()
    size = cfg["corpus"]["chunk_chars"]
    overlap = cfg["corpus"]["chunk_overlap_chars"]
    download()
    all_chunks = []
    for p in PUBS:
        pages = extract_text(os.path.join(CORPUS, p["id"] + ".pdf"))
        # line-based section tracking (pypdf uses single newlines)
        lines = []
        for _, t in pages:
            lines.extend(t.split("\n"))
        current = p["id"] + "-general"
        buf = []
        sections_blobs = []  # (section, text)
        for line in lines:
            s = line.strip()
            if len(s) < 3:
                continue
            # skip print-production headers
            if s.startswith("Userid:") or s.startswith("Fileid:") or s.startswith("Page ") and "of" in s:
                continue
            if "Ok to Print" in s or "MUST be removed before printing" in s:
                continue
            new_sec = detect_section(s, None)
            if new_sec is not None and new_sec != current and len(s) < 120:
                # heading line -> flush buffer
                if buf:
                    sections_blobs.append((current, " ".join(buf)))
                    buf = []
                current = new_sec
                continue
            # also allow mid-paragraph section cues to switch without flush loss
            mid = detect_section(s, None)
            if mid is not None and len(s) >= 120 and mid != current:
                # long paragraph containing a heading phrase: start new blob
                if buf:
                    sections_blobs.append((current, " ".join(buf)))
                    buf = []
                current = mid
            buf.append(s)
        if buf:
            sections_blobs.append((current, " ".join(buf)))
        # merge blobs by section then chunk
        by_sec = {}
        for sec, blob in sections_blobs:
            by_sec.setdefault(sec, []).append(blob)
        for sec, blist in by_sec.items():
            blob = "\n\n".join(blist)
            for k, ch in enumerate(chunk_text(blob, size, overlap)):
                all_chunks.append({"id": f"{sec}-{k:03d}", "source": p["id"],
                                   "section": sec, "title": p["title"], "text": ch})
    print(f"total chunks: {len(all_chunks)}")
    from collections import Counter
    print(Counter(c["section"] for c in all_chunks))
    os.makedirs(DATA, exist_ok=True)
    with open(CHUNKS, "w") as f:
        for c in all_chunks:
            f.write(json.dumps(c) + "\n")
    # embed + index into Qdrant
    from src import embeddings, vector_store
    vecs = embeddings.embed([c["text"] for c in all_chunks])
    dim = vecs.shape[1]
    client = vector_store.get_client(cfg["qdrant"]["path"])
    vector_store.ensure_collection(client, cfg["qdrant"]["collection"], dim)
    vector_store.upsert(client, cfg["qdrant"]["collection"],
                        [c["id"] for c in all_chunks], vecs,
                        [{"text": c["text"], "source": c["source"],
                          "section": c["section"], "title": c["title"]} for c in all_chunks])
    print(f"indexed {len(all_chunks)} chunks into Qdrant ({cfg['qdrant']['collection']}, dim={dim})")

if __name__ == "__main__":
    main()
