"""Read-only HTML browser for the local SQLite database."""

from html import escape
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_database_session

router = APIRouter(include_in_schema=False)


def _cell(value: object) -> str:
    """Render a database value safely inside an HTML table cell."""
    if value is None:
        return '<span class="null">NULL</span>'
    if isinstance(value, bytes):
        return f"&lt;BLOB {len(value)} bytes&gt;"
    return escape(str(value))


def _page(body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sai42 Database</title>
  <style>
    :root {{ color-scheme: light dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
    body {{ margin: 0; background: #0f172a; color: #e2e8f0; }}
    header {{ padding: 20px 28px; border-bottom: 1px solid #334155; }}
    h1 {{ margin: 0 0 6px; font-size: 22px; }}
    header p {{ margin: 0; color: #94a3b8; }}
    main {{ display: grid; grid-template-columns: 240px minmax(0, 1fr);
      min-height: calc(100vh - 86px); }}
    nav {{ padding: 20px; border-right: 1px solid #334155; }}
    nav a {{ display: block; padding: 9px 11px; color: #cbd5e1; text-decoration: none;
      border-radius: 6px; overflow-wrap: anywhere; }}
    nav a:hover, nav a.active {{ background: #1e293b; color: #fff; }}
    section {{ min-width: 0; padding: 20px 28px; }}
    .meta {{ margin: 0 0 14px; color: #94a3b8; }}
    .table-wrap {{ overflow: auto; border: 1px solid #334155; border-radius: 8px; }}
    table {{ border-collapse: collapse; width: 100%; font-family: ui-monospace, monospace;
      font-size: 13px; }}
    th, td {{ padding: 9px 11px; border-bottom: 1px solid #334155; text-align: left;
      white-space: nowrap; max-width: 420px; overflow: hidden; text-overflow: ellipsis; }}
    th {{ position: sticky; top: 0; background: #1e293b; color: #f8fafc; }}
    tr:last-child td {{ border-bottom: 0; }}
    .null {{ color: #64748b; font-style: italic; }}
    .pager {{ display: flex; gap: 8px; margin-top: 16px; }}
    .pager a {{ padding: 8px 12px; border: 1px solid #475569; border-radius: 6px;
      color: #e2e8f0; text-decoration: none; }}
    .empty {{ color: #94a3b8; }}
    @media (max-width: 720px) {{
      main {{ grid-template-columns: 1fr; }}
      nav {{ border-right: 0; border-bottom: 1px solid #334155; }}
    }}
  </style>
</head>
<body>
  <header><h1>Sai42 Database</h1><p>SQLite read-only table browser</p></header>
  {body}
</body>
</html>"""
    )


@router.get("/db", response_class=HTMLResponse)
async def browse_database(
    session: Annotated[AsyncSession, Depends(get_database_session)],
    table: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> HTMLResponse:
    """Show SQLite tables and paginated rows without mutation controls."""
    table_result = await session.execute(
        text(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    )
    tables = [str(name) for name in table_result.scalars()]
    selected = table if table in tables else (tables[0] if tables else None)

    links = "".join(
        f'<a class="{"active" if name == selected else ""}" '
        f'href="/db?table={quote(name)}">{escape(name)}</a>'
        for name in tables
    )
    empty_navigation = '<p class="empty">테이블이 없습니다.</p>'
    navigation = f"<nav>{links or empty_navigation}</nav>"

    if selected is None:
        empty_content = '<section><p class="empty">조회할 테이블이 없습니다.</p></section>'
        return _page(f"<main>{navigation}{empty_content}</main>")

    # `selected` is safe to quote because it must exactly match sqlite_master.
    quoted_table = '"' + selected.replace('"', '""') + '"'
    count = int((await session.execute(text(f"SELECT COUNT(*) FROM {quoted_table}"))).scalar_one())
    offset = (page - 1) * page_size
    result = await session.execute(
        text(f"SELECT * FROM {quoted_table} LIMIT :limit OFFSET :offset"),
        {"limit": page_size, "offset": offset},
    )
    columns = list(result.keys())
    rows = result.all()

    head = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    row_html = "".join(
        "<tr>"
        + "".join(
            f'<td title="{escape(str(value), quote=True)}">{_cell(value)}</td>' for value in row
        )
        + "</tr>"
        for row in rows
    )
    if not rows:
        colspan = max(1, len(columns))
        row_html = f'<tr><td class="empty" colspan="{colspan}">데이터가 없습니다.</td></tr>'

    base = f"/db?table={quote(selected)}&page_size={page_size}"
    previous = f'<a href="{base}&page={page - 1}">← 이전</a>' if page > 1 else ""
    following = f'<a href="{base}&page={page + 1}">다음 →</a>' if offset + len(rows) < count else ""
    content = f"""<section>
      <h2>{escape(selected)}</h2>
      <p class="meta">총 {count:,}개 행 · {page}페이지 · 페이지당 {page_size}개</p>
      <div class="table-wrap">
        <table><thead><tr>{head}</tr></thead><tbody>{row_html}</tbody></table>
      </div>
      <div class="pager">{previous}{following}</div>
    </section>"""
    return _page(f"<main>{navigation}{content}</main>")
