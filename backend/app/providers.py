from datetime import datetime, timedelta

class MatchProvider:
    def matches(self):
        raise NotImplementedError

class MockMatchProvider(MatchProvider):
    """Betman-like fixture provider without login, payment, purchase, or crawling automation."""
    def matches(self):
        base = datetime.utcnow() + timedelta(hours=8)
        return [
            {"competition":"K League 1","home":"서울 졸라FC","away":"부산 스틱맨즈","cutoff_time":base,"odds":(2.05,3.25,3.45)},
            {"competition":"Premier Mock League","home":"레드 라인즈","away":"블루 서클스","cutoff_time":base+timedelta(hours=2),"odds":(1.82,3.55,4.1)},
            {"competition":"La Liga Mock","home":"마드리드 막대","away":"카탈루냐 드리블","cutoff_time":base+timedelta(days=1),"odds":(2.55,3.05,2.8)},
        ]
