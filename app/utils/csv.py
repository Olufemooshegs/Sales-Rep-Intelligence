import io
import csv
from starlette.responses import StreamingResponse
from typing import Iterable, Dict


def generate_csv_stream(rows: Iterable[Dict], headers: Iterable[str], filename: str = "export.csv") -> StreamingResponse:
    def iter_csv():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for row in rows:
            writer.writerow([row.get(h, "") for h in headers])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    response = StreamingResponse(iter_csv(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
