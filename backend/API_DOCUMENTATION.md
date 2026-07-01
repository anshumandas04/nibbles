# CloudSync Backup API Documentation

Complete API reference for the CloudSync Backup backend with all endpoints, request/response schemas, and examples.

## Base URL

```
http://34.93.132.137
```

## Authentication

All endpoints require the `X-API-Key` header:

```
X-API-Key: vreplaced....dWT1sqsw8-0pCRPvJgT5Whx1SA
```

---

## 📊 Backup Management Endpoints

### 1. Start a Backup Session

**POST** `/backup/start`

Initialize a backup session for a device. Returns a session ID needed for subsequent requests.

**Request:**
```json
{
  "device_id": "device-001",
  "device_name": "My Phone",
  "platform": "android",
  "total_files": 150,
  "total_bytes": 5000000000
}
```

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "device-001",
  "status": "active",
  "started_at": "2026-07-02T10:30:45.123Z"
}
```

**Fields:**
- `device_id` (string, required): Unique device identifier (1-255 chars)
- `device_name` (string, optional): Human-readable name for dashboard
- `platform` (string, optional): `android`, `ios`, or `unknown`
- `total_files` (integer, optional): Expected number of files
- `total_bytes` (integer, optional): Expected total size in bytes

**cURL Example:**
```bash
curl -X POST http://34.93.132.132/backup/start \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-001",
    "device_name": "My Phone",
    "platform": "android",
    "total_files": 150,
    "total_bytes": 5000000000
  }'
```

---

### 2. Check File Manifest (Delta Sync)

**POST** `/backup/manifest`

Send file hashes to the server. It responds with which files are missing and need uploading.

**Request:**
```json
{
  "device_id": "device-001",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "files": [
    {
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 1500000,
      "filename": "photo_001.jpg",
      "mime_type": "image/jpeg"
    },
    {
      "sha256": "4a28f8df4d877e68afbf4c8996fb92427ae41e4649b934ca495991b7852b800",
      "size": 2000000,
      "filename": "photo_002.jpg",
      "mime_type": "image/jpeg"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "total_received": 2,
  "already_exists": 1,
  "missing": [
    "4a28f8df4d877e68afbf4c8996fb92427ae41e4649b934ca495991b7852b800"
  ],
  "bytes_saved": 1500000
}
```

**Fields:**
- `device_id` (string, required): Device identifier
- `session_id` (string, optional): Session ID from /backup/start
- `files` (array, required): List of file entries
  - `sha256` (string, required): 64-character SHA-256 hash
  - `size` (integer, required): File size in bytes
  - `filename` (string, required): Original filename
  - `mime_type` (string, optional): MIME type (e.g., image/jpeg)

**Benefits:**
- **Deduplication**: Server identifies files already stored
- **Bandwidth saving**: Only missing files need to be uploaded
- `bytes_saved` shows how much data was saved

---

### 3. Get Session Details

**GET** `/backup/session/{session_id}`

Retrieve complete session information including upload progress.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "device-001",
  "started_at": "2026-07-02T10:30:45.123Z",
  "completed_at": null,
  "status": "active",
  "total_files": 150,
  "uploaded_files": 75,
  "total_bytes": 5000000000,
  "uploaded_bytes": 2500000000,
  "progress_percent": 50.0
}
```

**cURL Example:**
```bash
curl -X GET http://34.93.132.132/backup/session/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: your-api-key"
```

---

### 4. Delete Session

**DELETE** `/backup/session/{session_id}`

Delete a backup session record (metadata only, files remain).

**Response (200 OK):**
```json
{
  "message": "Backup session deleted successfully"
}
```

---

## 📤 File Upload Endpoints

### 5. Upload a File

**POST** `/upload`

Stream upload a media file to the server.

**Request:** `multipart/form-data`

**Form Fields:**
- `file` (file, required): The actual file to upload
- `device_id` (string, required): Device identifier
- `sha256` (string, required): 64-character SHA-256 hash
- `mime_type` (string, required): MIME type (e.g., image/jpeg)
- `original_filename` (string, required): Original filename
- `session_id` (string, optional): Session ID from /backup/start
- `created_time` (string, optional): ISO 8601 timestamp of original file

**Response (200 OK):**
```json
{
  "success": true,
  "upload_id": "3be5cf22-901d-4008-8e6d-2dcf1e73998b",
  "stored_filename": "cb03164ad0e74f828a2a89feeb61d0bf.jpg",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "size": 2000000,
  "is_duplicate": false,
  "created_at": "2026-07-02T10:35:20.789Z"
}
```

**cURL Example:**
```bash
curl -X POST http://34.93.132.132/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@/path/to/photo.jpg;type=image/jpeg" \
  -F "device_id=device-001" \
  -F "sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" \
  -F "mime_type=image/jpeg" \
  -F "original_filename=photo.jpg" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440000"
```

---

### 6. Verify Upload Integrity

**POST** `/upload/complete`

Verify the uploaded file's SHA-256 hash to ensure zero corruption.

**Request:**
```json
{
  "upload_id": "3be5cf22-901d-4008-8e6d-2dcf1e73998b",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "upload_id": "3be5cf22-901d-4008-8e6d-2dcf1e73998b",
  "verified": true,
  "message": "Verification successful"
}
```

**cURL Example:**
```bash
curl -X POST http://34.93.132.132/upload/complete \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "3be5cf22-901d-4008-8e6d-2dcf1e73998b",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }'
```

---

### 7. Report Upload Failure

**POST** `/upload/failure`

Report a failed upload attempt for logging and diagnostics.

**Request:**
```json
{
  "device_id": "device-001",
  "original_filename": "photo.jpg",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "error_message": "Network timeout after 2 retries"
}
```

**Response (200 OK):**
```json
{
  "message": "Failure report recorded"
}
```

---

### 8. Get Upload Status

**GET** `/upload/status/{device_id}`

Get current upload status and recent uploads for a device.

**Response (200 OK):**
```json
{
  "device_id": "device-001",
  "active_session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "device_id": "device-001",
    "started_at": "2026-07-02T10:30:45.123Z",
    "status": "active",
    "total_files": 150,
    "uploaded_files": 75,
    "total_bytes": 5000000000,
    "uploaded_bytes": 2500000000,
    "progress_percent": 50.0
  },
  "recent_uploads": [
    {
      "id": "3be5cf22-901d-4008-8e6d-2dcf1e73998b",
      "original_filename": "photo_001.jpg",
      "size": 2000000,
      "status": "completed",
      "uploaded_time": "2026-07-02T10:35:20.789Z"
    }
  ],
  "failed_count": 0
}
```

---

## 📁 Media Management Endpoints

### 9. List Media Files

**GET** `/media`

Retrieve paginated list of all stored media files.

**Query Parameters:**
- `page` (integer, default=1): Page number (1-indexed)
- `page_size` (integer, default=20, max=100): Items per page
- `device_id` (string, optional): Filter by device

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "device_id": "device-001",
      "session_id": "550e8400-e29b-41d4-a716-446655440001",
      "original_filename": "photo_001.jpg",
      "stored_filename": "cb03164ad0e74f828a2a89feeb61d0bf.jpg",
      "mime_type": "image/jpeg",
      "file_size": 2000000,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "thumbnail_path": "thumbnails/thumb_cb03164ad0e74f828a2a89feeb61d0bf.jpg",
      "status": "completed",
      "is_complete": true,
      "uploaded_time": "2026-07-02T10:35:20.789Z",
      "created_time": "2026-07-01T15:30:00.000Z"
    }
  ],
  "total": 500,
  "page": 1,
  "page_size": 20
}
```

**cURL Example:**
```bash
curl -X GET "http://34.93.132.132/media?page=1&page_size=20" \
  -H "X-API-Key: your-api-key"
```

---

### 10. Get Media Details

**GET** `/media/{media_id}`

Retrieve details for a specific media file.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "device-001",
  "original_filename": "photo_001.jpg",
  "stored_filename": "cb03164ad0e74f828a2a89feeb61d0bf.jpg",
  "mime_type": "image/jpeg",
  "file_size": 2000000,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "completed",
  "is_complete": true,
  "uploaded_time": "2026-07-02T10:35:20.789Z"
}
```

---

### 11. Delete Media File

**DELETE** `/media/{media_id}`

Delete a media file and its database record.

**Response (200 OK):**
```json
{
  "message": "Media file and record deleted successfully"
}
```

---

## 📥 Download Endpoints

### 12. Download Media File

**GET** `/download/{media_id}`

Download a stored media file (streams file with proper MIME type).

**Response:**
- Status: 200 OK
- Content-Type: Matches original MIME type (image/jpeg, video/mp4, etc.)
- Content-Disposition: attachment; filename="original_filename"
- Supports HTTP Range requests for resume capability

**cURL Example:**
```bash
curl -X GET http://34.93.132.132/download/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: your-api-key" \
  -o downloaded_file.jpg
```

**Resume Download (Range Request):**
```bash
curl -X GET http://34.93.132.132/download/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: your-api-key" \
  -H "Range: bytes=1000000-" \
  -o downloaded_file.jpg
```

---

## 📱 Device Endpoints

### 13. Get Device Sync Status

**GET** `/device/sync`

Get synchronization status for a device.

**Query Parameters:**
- `device_id` (string, required): Device identifier

**Response (200 OK):**
```json
{
  "device_id": "device-001",
  "last_backup": "2026-07-02T10:35:20.789Z",
  "uploaded_count": 150,
  "total_size_bytes": 5000000000,
  "remaining": 50,
  "last_seen": "2026-07-02T11:00:00.000Z"
}
```

**cURL Example:**
```bash
curl -X GET "http://34.93.132.132/device/sync?device_id=device-001" \
  -H "X-API-Key: your-api-key"
```

---

## 🏥 Health & System Endpoints

### 14. Health Check

**GET** `/health`

Check server health status (no authentication required).

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

**cURL Example:**
```bash
curl -X GET http://34.93.132.132/health
```

---

## Complete Backup Flow Example

### Step 1: Start Session
```bash
curl -X POST http://34.93.132.132/backup/start \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "phone-001",
    "device_name": "My Phone",
    "platform": "android",
    "total_files": 3,
    "total_bytes": 5500000
  }'
```
Response: `session_id: "abc-123"`

### Step 2: Send Manifest
```bash
curl -X POST http://34.93.132.132/backup/manifest \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "phone-001",
    "session_id": "abc-123",
    "files": [
      {"sha256": "hash1", "size": 1500000, "filename": "photo1.jpg", "mime_type": "image/jpeg"},
      {"sha256": "hash2", "size": 2000000, "filename": "photo2.jpg", "mime_type": "image/jpeg"},
      {"sha256": "hash3", "size": 2000000, "filename": "photo3.jpg", "mime_type": "image/jpeg"}
    ]
  }'
```
Response: `missing: ["hash2", "hash3"]`

### Step 3: Upload Missing Files
```bash
curl -X POST http://34.93.132.132/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@photo2.jpg;type=image/jpeg" \
  -F "device_id=phone-001" \
  -F "sha256=hash2" \
  -F "mime_type=image/jpeg" \
  -F "original_filename=photo2.jpg" \
  -F "session_id=abc-123"
```
Response: `upload_id: "upload-456"`

### Step 4: Verify Upload
```bash
curl -X POST http://34.93.132.132/upload/complete \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"upload_id": "upload-456", "sha256": "hash2"}'
```
Response: `verified: true`

### Step 5: Check Status
```bash
curl -X GET http://34.93.132.132/upload/status/phone-001 \
  -H "X-API-Key: your-api-key"
```

---

## Error Responses

All endpoints return proper HTTP status codes:

| Code | Meaning |
|---|---|
| 200 | Success |
| 401 | Invalid/missing API key |
| 404 | Resource not found |
| 422 | Invalid request body |
| 500 | Server error |

**Error Response Format:**
```json
{
  "detail": "Error message or validation error details"
}
```

---

## Rate Limiting

- **Limit:** 100 requests per minute per IP
- **Header:** `RateLimit-Remaining` shows remaining requests
- **Exceeding limit:** Returns 429 Too Many Requests

---

## Swagger UI

View interactive API documentation at:

```
http://34.93.132.132/docs
```

(Requires the server to generate Swagger docs)

---

## Implementation Checklist for FlutterFlow

- [ ] Set base URL to `http://34.93.132.132`
- [ ] Add `X-API-Key` header to all requests
- [ ] Implement SHA-256 hashing for files
- [ ] Call `/backup/start` when user initiates backup
- [ ] Call `/backup/manifest` with file list
- [ ] Upload only files in `missing` list
- [ ] Call `/upload/complete` for each file
- [ ] Show progress from `/upload/status/{device_id}`
- [ ] Handle network errors and retry uploads
- [ ] Cache session_id and upload_id in app state

---
