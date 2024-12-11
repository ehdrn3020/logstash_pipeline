from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import aiomysql

app = FastAPI()

# Models for API response
class StatsResponse(BaseModel):
    item_id: str
    ratio: float
    rank: int

class CountResponse(BaseModel):
    item_id: str
    count: int

# Database connection details
DB_CONFIG = {
    "host": "localhost",      # MySQL 호스트 주소
    "port": 3306,             # MySQL 포트 번호
    "user": "dgk",      # MySQL 사용자 이름
    "password": "1234",  # MySQL 비밀번호
    "db": "data",             # 데이터베이스 이름
}


async def get_data_from_db(query: str, params: tuple = ()):
    """
    Helper function to fetch data from MySQL database
    """
    async with aiomysql.connect(**DB_CONFIG) as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()

def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Custom parser for datetime values."""
    if value is None:
        return None
    try:
        print(datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f"))
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="요청에러입니다. 잘못된 datetime 형식입니다."
        )

@app.get("/api/stats", response_model=List[StatsResponse])
async def get_stats():
    """
    아이템들의 건수를 기준으로 비율과 랭크를 반환
    """
    query = "SELECT item_id, COUNT(*) AS count FROM collector GROUP BY item_id"
    rows = await get_data_from_db(query)

    total = sum(row[1] for row in rows)  # 총 건수 계산
    sorted_items = sorted(rows, key=lambda x: x[1], reverse=True)  # 건수 기준 정렬
    response = [
        {
            "item_id": item[0],
            "ratio": round(item[1] / total, 2),
            "rank": rank + 1,
        }
        for rank, item in enumerate(sorted_items)
    ]
    return response


@app.get("/api/count", response_model=List[CountResponse])
async def get_count(
    item_id: Optional[str] = Query(None, description="아이템 ID"),
    from_date: Optional[str] = Query(None, alias="from", description="시작 시간"),
    to_date: Optional[str] = Query(None, alias="to", description="종료 시간"),
):
    """
    특정 기간의 아이템 건수를 반환
    """
    try:
        base_query = "SELECT item_id, COUNT(*) AS count FROM collector WHERE 1=1"
        params = []
        parsed_from_date = parse_datetime(from_date)
        parsed_to_date = parse_datetime(to_date)
        print(f"from_date: {parsed_from_date}, to_date: {parsed_to_date}")

        if item_id:
            base_query += " AND item_id = %s"
            params.append(item_id)
        if parsed_from_date:
            base_query += " AND created_at >= %s"
            params.append(parsed_from_date)
        if parsed_to_date:
            base_query += " AND created_at <= %s"
            params.append(parsed_to_date)

        base_query += " GROUP BY item_id"
        rows = await get_data_from_db(base_query, tuple(params))

        return [{"item_id": row[0], "count": row[1]} for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail="요청값 에러입니다.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
