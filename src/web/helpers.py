from dataclasses import dataclass


@dataclass(frozen=True)
class Pagination:
    page: int
    per_page: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 1
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def pages(self) -> list[int]:
        start = max(1, self.page - 2)
        end = min(self.total_pages, self.page + 2)
        return list(range(start, end + 1))
