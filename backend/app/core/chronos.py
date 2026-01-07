from datetime import datetime, timedelta

class Chronos:
    def __init__(self, start_date: str = "01-01-1000"):
        self.current_time = datetime.strptime(start_date, "%d-%m-%Y")
        self.turn = 0

    def advance_turn(self):
        """Avança o tempo em uma unidade (por exemplo, uma hora ou uma ação)."""
        self.current_time += timedelta(hours=1)
        self.turn += 1

    def advance_day(self):
        """Avança o tempo em um dia."""
        self.current_time += timedelta(days=1)
        self.turn = 0 # Reinicia os turnos do dia

    def get_current_time_str(self) -> str:
        """Retorna a data e hora atual como string."""
        return self.current_time.strftime("%d-%m-%Y %H:%M")

    def get_current_datetime(self) -> datetime:
        """Retorna o objeto datetime atual."""
        return self.current_time

# Instância global para ser usada em todo o jogo
world_clock = Chronos()
