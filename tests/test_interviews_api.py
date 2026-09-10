import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_interview_create_and_fetch_lifecycle(client: AsyncClient):
    payload = {
        "candidate_name": "Jordan Lee",
        "candidate_email": "jordan.lee@example.com",
        "role_title": "Fullstack Engineer",
        "transcript": (
            "Interviewer: How do you handle state management and backend APIs? "
            "Candidate: I design asynchronous REST APIs using FastAPI and relational databases. "
            "In our microservices architecture, we collaborated on modular component design."
        ),
    }

    # 1. Create interview
    create_resp = await client.post("/interviews/", json=payload)
    assert create_resp.status_code == 201
    create_data = create_resp.json()
    assert "task_id" in create_data
    task_id = create_data["task_id"]

    # 2. Fetch interview details (in-process background execution runs immediately in test)
    get_resp = await client.get(f"/interviews/{task_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["task_id"] == task_id
    assert get_data["candidate_name"] == "Jordan Lee"
    assert get_data["role_title"] == "Fullstack Engineer"
    assert get_data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]

    # If already completed by background task:
    if get_data["status"] == "COMPLETED":
        assert get_data["scorecard"] is not None
        assert "coding_score" in get_data["scorecard"]
        assert "communication_rating" in get_data["scorecard"]


@pytest.mark.asyncio
async def test_interview_list_pagination(client: AsyncClient):
    # Create two interviews
    for name in ["Candidate One", "Candidate Two"]:
        await client.post(
            "/interviews/",
            json={
                "candidate_name": name,
                "role_title": "Software Engineer",
                "transcript": "Interviewer: Tell me about your skills. Candidate: I write Python and test my code.",
            },
        )

    # List interviews
    list_resp = await client.get("/interviews/?page=1&size=10")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 2
    assert len(list_data["items"]) >= 2
    assert list_data["page"] == 1


@pytest.mark.asyncio
async def test_presigned_upload_endpoint(client: AsyncClient):
    payload = {"filename": "interview_transcript.txt", "content_type": "text/plain"}
    resp = await client.post("/interviews/presigned-upload", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "upload_url" in data
    assert "storage_key" in data
    assert "interview_transcript.txt" in data["storage_key"]


@pytest.mark.asyncio
async def test_direct_file_upload(client: AsyncClient):
    from app.services.storage import storage_service
    files = {"file": ("interview.txt", b"Interviewer: Hello. Candidate: Hi, let's discuss algorithms.", "text/plain")}
    resp = await client.post("/interviews/upload-file", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "interview.txt"
    assert "storage_key" in data
    assert data["bytes"] > 0
    # Clean up uploaded test artifact
    storage_service.delete(data["storage_key"])


@pytest.mark.asyncio
async def test_delete_interview(client: AsyncClient):
    # Create
    create_resp = await client.post(
        "/interviews/",
        json={
            "candidate_name": "To Be Deleted",
            "role_title": "QA Engineer",
            "transcript": "Quick interview transcript.",
        },
    )
    task_id = create_resp.json()["task_id"]

    # Delete
    del_resp = await client.delete(f"/interviews/{task_id}")
    assert del_resp.status_code == 204

    # Verify not found
    get_resp = await client.get(f"/interviews/{task_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_audit_log_endpoint(client: AsyncClient):
    resp = await client.get("/interviews/audit-log")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert isinstance(data["events"], list)


@pytest.mark.asyncio
async def test_input_validation_rules(client: AsyncClient):
    # 1. Empty candidate name
    r1 = await client.post("/interviews/", json={"candidate_name": "", "role_title": "Engineer"})
    assert r1.status_code == 422

    # 2. Whitespace-only candidate name
    r2 = await client.post("/interviews/", json={"candidate_name": "   ", "role_title": "Engineer"})
    assert r2.status_code == 422

    # 3. Invalid candidate email
    r3 = await client.post(
        "/interviews/",
        json={"candidate_name": "Valid Name", "candidate_email": "not-an-email", "role_title": "Engineer"},
    )
    assert r3.status_code == 422

    # 4. Missing role_title
    r4 = await client.post("/interviews/", json={"candidate_name": "Valid Name"})
    assert r4.status_code == 422

    # 5. Non-existent interview ID
    r5 = await client.get("/interviews/non-existent-uuid-12345")
    assert r5.status_code == 404

    # 6. Delete non-existent interview ID
    r6 = await client.delete("/interviews/non-existent-uuid-12345")
    assert r6.status_code == 404


@pytest.mark.asyncio
async def test_media_streaming_and_path_traversal_protection(client: AsyncClient):
    from app.services.storage import storage_service

    # Upload real content
    raw_content = b"Candidate audio or transcript binary payload."
    files = {"file": ("recording.mp3", raw_content, "audio/mpeg")}
    upload_resp = await client.post("/interviews/upload-file", files=files)
    assert upload_resp.status_code == 200
    key = upload_resp.json()["storage_key"]

    try:
        # 1. Fetch media artifact via GET /interviews/media/{key}
        media_resp = await client.get(f"/interviews/media/{key}")
        assert media_resp.status_code == 200
        assert media_resp.content == raw_content

        # 2. Security: Path traversal protection
        traversal_resp = await client.get("/interviews/media/../../etc/passwd")
        assert traversal_resp.status_code in [400, 403, 404]

        # 3. Non-existent media artifact
        missing_resp = await client.get("/interviews/media/transcripts/does-not-exist.mp3")
        assert missing_resp.status_code == 404
    finally:
        storage_service.delete(key)


