from datetime import date, timedelta
import calendar
from typing import List
from flight_deals_engine.domain.models import RefreshTarget


class RefreshPlanner:
    def build_monthly_targets(
        self,
        origin: str,
        destinations: List[str],
        start_date: date,
        months_ahead: int,
        currency: str,
        nights_min: int = 3,
        nights_max: int = 7,
    ) -> List[RefreshTarget]:
        """
        Expands search scope into concrete monthly refresh targets.
        For the current month, starts from `start_date`.
        For future months, covers the full month (1st to last day).
        """
        targets = []
        
        # Start iterating from the first day of the start_date's month
        # This helps in month arithmetic, but we'll clamp the start date for the first iteration.
        current_month_first_day = start_date.replace(day=1)
        
        for i in range(months_ahead):
            # Determine the window for this month
            # If it's the first iteration (current month), ensure we don't search in the past
            if i == 0:
                window_start = start_date
            else:
                window_start = current_month_first_day
            
            # Calculate the last day of the current iterating month
            _, last_day = calendar.monthrange(current_month_first_day.year, current_month_first_day.month)
            window_end = current_month_first_day.replace(day=last_day)
            
            # Generate targets for all destinations
            for destination in destinations:
                targets.append(
                    RefreshTarget(
                        origin=origin,
                        destination=destination,
                        date_from=window_start,
                        date_to=window_end,
                        currency=currency,
                        nights_min=nights_min,
                        nights_max=nights_max,
                        direct_only=False
                    )
                )
            
            # Advance to the first day of the next month
            # Logic: Add 32 days to the first of current month, then snap to first of that month
            next_month_date = current_month_first_day + timedelta(days=32)
            current_month_first_day = next_month_date.replace(day=1)
            
        return targets
