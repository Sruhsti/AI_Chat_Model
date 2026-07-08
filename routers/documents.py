import asyncio
from fastapi import APIRouter, Depends,HTTPException,status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Annotated
from database import get_db
from models import Document, DocumentChunk
from schemas import DocumentPublic,DocumentUploadResponse
from dependencies import CurrentUser
from services.document_service import extract_text_from_pdf,chunk_text
from services.embedding_service import get_embeddings, embeddings_to_str
from io import BytesIO

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload",response_model=DocumentUploadResponse)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)]
):
    print(f"Uploading file: {file.filename}")

    if file.content_type != "application/pdf":
        print(f"Rejected upload: unsupported content type {file.content_type}")
        raise HTTPException(
        status_code=400,
        detail="Only PDF files are allowed"
    )

    file_bytes = await file.read()
    full_text = extract_text_from_pdf(BytesIO(file_bytes))
    if not full_text:
        print(f"Rejected upload: no extractable text in {file.filename}")
        raise HTTPException(
        status_code=400,
        detail="Could not extract text from PDF"
    )
    chunks = chunk_text(full_text)
    print(f"Total chunks created: {len(chunks)}")

    # save document first to get its id
    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        content=full_text
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # embed all chunks in one batch, off the event loop thread
    embeddings = await asyncio.to_thread(get_embeddings, chunks)

    # save all chunks with embeddings
    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        embedding_str = embeddings_to_str(embedding)
        document_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index = index,
            chunk_text=chunk,
            embedding=embedding_str
        )
        db.add(document_chunk)
    db.commit()

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        message="Document uploaded and processed successfully"
    )

@router.get("/", response_model=list[DocumentPublic])
def get_all_documents(db: Annotated[Session, Depends(get_db)], current_user: CurrentUser):
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents 

@router.delete("/{document_id}")
def delete_document(document_id: int, db: Annotated[Session, Depends(get_db)], current_user: CurrentUser):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    print(f"Deleting document: {document.filename} (id={document.id})")

    db.delete(document)
    db.commit()
    return {"message": "Document deleted successfully"}




