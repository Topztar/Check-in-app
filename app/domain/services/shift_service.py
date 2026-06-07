"""
app/domain/services/shift_service.py
班別領域服務 — 計算班別詳情，包含跨夜班處理與加班費計算。
P2-1：將 O(n) 逐分鐘迴圈改為 O(1) 數學計算。
"""
from datetime import datetime, timedelta, time


class ShiftService:
    @staticmethod
    def calculate_shift_details(clock_in: datetime, clock_out: datetime) -> dict:
        """
        計算班別詳情，包含：
        - 跨夜班處理（以上班日期為邏輯班別日期）
        - 夜班加給小時數（22:00 至 06:00 的工作時數）
        - 標準加班小時數（超過 8 小時的部分）

        P2-1 優化：使用 O(1) 時間複雜度的數學計算取代 O(n) 逐分鐘迴圈。
        原本: while 迴圈逐分鐘計數，長班別（如 10 小時）需迭代 600 次
        現在: 透過區間交集計算直接得出夜班工時，時間複雜度 O(1)
        """
        total_duration = clock_out - clock_in
        total_hours = total_duration.total_seconds() / 3600.0

        # 加班計算（超過 8 小時的部分）
        regular_hours = min(8.0, total_hours)
        overtime_hours = max(0.0, total_hours - 8.0)

        # ─── 夜班加給計算（O(1) 數學方法）────────────────────────────────
        # 夜班時段定義：每天 22:00 至隔日 06:00（共 8 小時）
        # 演算法：計算工作區間與夜班時段的交集總長度
        overnight_seconds = ShiftService._calculate_overnight_seconds(clock_in, clock_out)
        overnight_hours = overnight_seconds / 3600.0

        return {
            "logical_shift_date": clock_in.date(),  # 跨夜班以上班日期為邏輯班別日期
            "total_hours": round(total_hours, 2),
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "overnight_premium_hours": round(overnight_hours, 2),
        }

    @staticmethod
    def _calculate_overnight_seconds(clock_in: datetime, clock_out: datetime) -> float:
        """
        計算工作區間與夜班時段（22:00–06:00）的交集秒數。

        方法：
        - 以日期為單位，迭代工作期間跨越的每一天（通常僅 1-2 天）
        - 對每天計算兩個夜班時段的交集：
            時段 A：前一天 22:00 至當天 06:00
            時段 B：當天 22:00 至隔天 06:00
        - 時間複雜度：O(工作天數)，實務上永遠 ≤ 2，等同 O(1)
        """
        total_seconds = 0.0

        # 計算工作期間跨越的日期集合
        start_date = clock_in.date()
        end_date = clock_out.date()
        current_date = start_date

        while current_date <= end_date:
            # 夜班時段 A：昨天 22:00 → 今天 06:00
            night_start_a = datetime.combine(
                current_date - timedelta(days=1),
                time(22, 0),
                tzinfo=clock_in.tzinfo,
            )
            night_end_a = datetime.combine(
                current_date,
                time(6, 0),
                tzinfo=clock_in.tzinfo,
            )
            total_seconds += ShiftService._intersect_seconds(
                clock_in, clock_out, night_start_a, night_end_a
            )

            # 夜班時段 B：今天 22:00 → 明天 06:00
            night_start_b = datetime.combine(
                current_date,
                time(22, 0),
                tzinfo=clock_in.tzinfo,
            )
            night_end_b = datetime.combine(
                current_date + timedelta(days=1),
                time(6, 0),
                tzinfo=clock_in.tzinfo,
            )
            total_seconds += ShiftService._intersect_seconds(
                clock_in, clock_out, night_start_b, night_end_b
            )

            current_date += timedelta(days=1)

        return total_seconds

    @staticmethod
    def _intersect_seconds(
        work_start: datetime,
        work_end: datetime,
        period_start: datetime,
        period_end: datetime,
    ) -> float:
        """計算兩個時間區間的交集秒數，若無交集則回傳 0。"""
        overlap_start = max(work_start, period_start)
        overlap_end = min(work_end, period_end)
        if overlap_end > overlap_start:
            return (overlap_end - overlap_start).total_seconds()
        return 0.0
