"""
Log viewing API endpoints
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math

from app.dependencies import get_db
from app.models.log import ApiLog
from app.schemas.log import ApiLogResponse
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[ApiLogResponse]])
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[str] = Query(None, description="Filter logs from this date (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="Filter logs until this date (ISO 8601 format)"),
    method: Optional[str] = Query(None, description="Filter logs by HTTP method (GET, POST, etc.)"),
    resource: Optional[str] = Query(None, description="Filter logs by resource (e.g., devices/controllers)"),
    client_uuid: Optional[str] = Query(None, description="Filter logs by client UUID"),
    db: Session = Depends(get_db)
):
    """
    Get API logs with pagination and filtering

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        start_date: Filter logs from this date (ISO 8601 format)
        end_date: Filter logs until this date (ISO 8601 format)
        method: Filter logs by HTTP method (GET, POST, etc.)
        resource: Filter logs by resource (e.g., devices/controllers)
        client_uuid: Filter logs by client UUID

    Returns:
        ApiResponse with list of API logs and pagination metadata
    """
    query = db.query(ApiLog)

    # Apply date range filtering
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(ApiLog.timestamp >= start_dt)

    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(ApiLog.timestamp <= end_dt)

    # Apply method filtering
    if method:
        query = query.filter(ApiLog.method == method)

    # Apply resource filtering
    if resource:
        query = query.filter(ApiLog.resource == resource)

    # Apply client_uuid filtering
    if client_uuid:
        query = query.filter(ApiLog.client_uuid == client_uuid)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Apply pagination and ordering (most recent first)
    logs = query.order_by(ApiLog.timestamp.desc()).offset(skip).limit(limit).all()

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Logs retrieved successfully",
        data=logs,
        pagination=pagination
    )


@router.get("/viewer", response_class=HTMLResponse)
async def log_viewer():
    """
    Log viewer web page with pagination and filtering
    """
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GOP API Log Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }

        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }

        .filters {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }

        .filter-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .filter-item {
            display: flex;
            flex-direction: column;
        }

        .filter-item label {
            font-weight: 600;
            margin-bottom: 5px;
            color: #495057;
            font-size: 0.9em;
        }

        .filter-item input,
        .filter-item select {
            padding: 10px;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            font-size: 0.95em;
            transition: all 0.3s;
        }

        .filter-item input:focus,
        .filter-item select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .filter-actions {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.95em;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .stats {
            padding: 20px 30px;
            background: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #e9ecef;
        }

        .stats-info {
            font-size: 0.95em;
            color: #6c757d;
        }

        .stats-info strong {
            color: #495057;
        }

        .table-container {
            padding: 30px;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }

        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        th {
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }

        tbody tr {
            transition: background-color 0.2s;
        }

        tbody tr:hover {
            background: #f8f9fa;
        }

        .method-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.8em;
            text-align: center;
            min-width: 60px;
        }

        .method-GET { background: #d1ecf1; color: #0c5460; }
        .method-POST { background: #d4edda; color: #155724; }
        .method-PUT { background: #fff3cd; color: #856404; }
        .method-PATCH { background: #e7e3ff; color: #4a148c; }
        .method-DELETE { background: #f8d7da; color: #721c24; }

        .status-code {
            font-weight: 600;
        }

        .status-2xx { color: #28a745; }
        .status-3xx { color: #17a2b8; }
        .status-4xx { color: #ffc107; }
        .status-5xx { color: #dc3545; }

        .pagination {
            padding: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            background: #f8f9fa;
        }

        .pagination button {
            padding: 8px 16px;
            border: 2px solid #dee2e6;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }

        .pagination button:hover:not(:disabled) {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .pagination .page-info {
            padding: 8px 16px;
            font-weight: 600;
            color: #495057;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-size: 1.1em;
        }

        .loading::after {
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            margin: 20px 30px;
            border-radius: 6px;
            border-left: 4px solid #dc3545;
        }

        .no-data {
            text-align: center;
            padding: 60px 30px;
            color: #6c757d;
            font-size: 1.1em;
        }

        .timestamp {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #6c757d;
        }

        .client-uuid {
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
            color: #6c757d;
            word-break: break-all;
        }

        .request-id {
            font-family: 'Courier New', monospace;
            font-size: 0.75em;
            color: #adb5bd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 GOP API Log Viewer</h1>
            <p>Real-time API request monitoring and analysis</p>
        </div>

        <div class="filters">
            <div class="filter-group">
                <div class="filter-item">
                    <label for="method">HTTP Method</label>
                    <select id="method">
                        <option value="">All Methods</option>
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="PATCH">PATCH</option>
                        <option value="DELETE">DELETE</option>
                    </select>
                </div>

                <div class="filter-item">
                    <label for="resource">Resource</label>
                    <input type="text" id="resource" placeholder="e.g., devices/controllers">
                </div>

                <div class="filter-item">
                    <label for="client_uuid">Client UUID</label>
                    <input type="text" id="client_uuid" placeholder="Client identifier">
                </div>

                <div class="filter-item">
                    <label for="start_date">Start Date</label>
                    <input type="datetime-local" id="start_date">
                </div>

                <div class="filter-item">
                    <label for="end_date">End Date</label>
                    <input type="datetime-local" id="end_date">
                </div>

                <div class="filter-item">
                    <label for="limit">Items per Page</label>
                    <select id="limit">
                        <option value="10">10</option>
                        <option value="20" selected>20</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
            </div>

            <div class="filter-actions">
                <button class="btn btn-secondary" onclick="clearFilters()">Clear Filters</button>
                <button class="btn btn-primary" onclick="loadLogs(1)">Apply Filters</button>
            </div>
        </div>

        <div class="stats" id="stats" style="display: none;">
            <div class="stats-info">
                <strong>Total Records:</strong> <span id="total-records">0</span> |
                <strong>Page:</strong> <span id="current-page">1</span> / <span id="total-pages">1</span>
            </div>
            <div class="stats-info">
                <button class="btn btn-secondary" onclick="loadLogs(currentPage)" style="padding: 8px 16px;">
                    🔄 Refresh
                </button>
            </div>
        </div>

        <div class="table-container">
            <div id="loading" class="loading">Loading logs</div>
            <div id="error" class="error" style="display: none;"></div>
            <div id="no-data" class="no-data" style="display: none;">
                📭 No logs found matching your criteria
            </div>
            <table id="logs-table" style="display: none;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Timestamp</th>
                        <th>Method</th>
                        <th>Resource</th>
                        <th>Status</th>
                        <th>Description</th>
                        <th>Client UUID</th>
                        <th>Request ID</th>
                    </tr>
                </thead>
                <tbody id="logs-tbody">
                </tbody>
            </table>
        </div>

        <div class="pagination" id="pagination" style="display: none;">
            <button onclick="loadLogs(1)" id="first-page">First</button>
            <button onclick="loadLogs(currentPage - 1)" id="prev-page">Previous</button>
            <span class="page-info">
                Page <span id="page-display">1</span> of <span id="pages-display">1</span>
            </span>
            <button onclick="loadLogs(currentPage + 1)" id="next-page">Next</button>
            <button onclick="loadLogs(totalPages)" id="last-page">Last</button>
        </div>
    </div>

    <script>
        let currentPage = 1;
        let totalPages = 1;
        let totalRecords = 0;

        function getStatusClass(status) {
            if (status >= 200 && status < 300) return 'status-2xx';
            if (status >= 300 && status < 400) return 'status-3xx';
            if (status >= 400 && status < 500) return 'status-4xx';
            if (status >= 500) return 'status-5xx';
            return '';
        }

        function formatTimestamp(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleString('ko-KR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        }

        function buildQueryString(page) {
            const params = new URLSearchParams();
            params.append('page', page);
            params.append('limit', document.getElementById('limit').value);

            const method = document.getElementById('method').value;
            if (method) params.append('method', method);

            const resource = document.getElementById('resource').value;
            if (resource) params.append('resource', resource);

            const clientUuid = document.getElementById('client_uuid').value;
            if (clientUuid) params.append('client_uuid', clientUuid);

            const startDate = document.getElementById('start_date').value;
            if (startDate) params.append('start_date', new Date(startDate).toISOString());

            const endDate = document.getElementById('end_date').value;
            if (endDate) params.append('end_date', new Date(endDate).toISOString());

            return params.toString();
        }

        async function loadLogs(page = 1) {
            currentPage = page;

            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';
            document.getElementById('no-data').style.display = 'none';
            document.getElementById('logs-table').style.display = 'none';
            document.getElementById('stats').style.display = 'none';
            document.getElementById('pagination').style.display = 'none';

            try {
                const queryString = buildQueryString(page);
                const response = await fetch(`/api/logs?${queryString}`);
                const result = await response.json();

                if (!result.success) {
                    throw new Error(result.message || 'Failed to load logs');
                }

                const logs = result.data;
                const pagination = result.pagination;

                totalRecords = pagination.total;
                totalPages = pagination.total_pages;
                currentPage = pagination.page;

                document.getElementById('loading').style.display = 'none';

                if (logs.length === 0) {
                    document.getElementById('no-data').style.display = 'block';
                    return;
                }

                // Update stats
                document.getElementById('total-records').textContent = totalRecords;
                document.getElementById('current-page').textContent = currentPage;
                document.getElementById('total-pages').textContent = totalPages;
                document.getElementById('stats').style.display = 'flex';

                // Update table
                const tbody = document.getElementById('logs-tbody');
                tbody.innerHTML = logs.map(log => `
                    <tr>
                        <td>${log.id}</td>
                        <td class="timestamp">${formatTimestamp(log.timestamp)}</td>
                        <td><span class="method-badge method-${log.method}">${log.method}</span></td>
                        <td>${log.resource || '-'}</td>
                        <td class="status-code ${getStatusClass(log.status_code)}">${log.status_code}</td>
                        <td>${log.description || '-'}</td>
                        <td class="client-uuid">${log.client_uuid || '-'}</td>
                        <td class="request-id">${log.request_id || '-'}</td>
                    </tr>
                `).join('');

                document.getElementById('logs-table').style.display = 'table';

                // Update pagination
                document.getElementById('page-display').textContent = currentPage;
                document.getElementById('pages-display').textContent = totalPages;
                document.getElementById('first-page').disabled = currentPage === 1;
                document.getElementById('prev-page').disabled = currentPage === 1;
                document.getElementById('next-page').disabled = currentPage === totalPages;
                document.getElementById('last-page').disabled = currentPage === totalPages;
                document.getElementById('pagination').style.display = 'flex';

            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').textContent = `Error: ${error.message}`;
                document.getElementById('error').style.display = 'block';
            }
        }

        function clearFilters() {
            document.getElementById('method').value = '';
            document.getElementById('resource').value = '';
            document.getElementById('client_uuid').value = '';
            document.getElementById('start_date').value = '';
            document.getElementById('end_date').value = '';
            document.getElementById('limit').value = '20';
            loadLogs(1);
        }

        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                loadLogs(currentPage);
            }
        }, 30000);

        // Load initial data
        loadLogs(1);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)
