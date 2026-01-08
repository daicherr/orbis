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
    
    def get_time_of_day(self) -> str:
        """Retorna o período do dia baseado na hora"""
        hour = self.current_time.hour
        if 5 <= hour < 7:
            return "dawn"
        elif 7 <= hour < 12:
            return "morning"
        elif 12 <= hour < 14:
            return "noon"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 20:
            return "dusk"
        elif 20 <= hour < 22:
            return "evening"
        elif 22 <= hour < 24 or 0 <= hour < 2:
            return "night"
        else:
            return "midnight"
    
    def get_season(self) -> str:
        """Retorna a estação baseada no mês"""
        month = self.current_time.month
        if 3 <= month <= 5:
            return "Spring"
        elif 6 <= month <= 8:
            return "Summer"
        elif 9 <= month <= 11:
            return "Autumn"
        else:
            return "Winter"
    
    def get_current_turn(self) -> int:
        """Retorna o turno atual global (usado para deadlines de quests)."""
        # Calcula turnos totais desde o início (1000 turnos por dia)
        days_since_start = (self.current_time - datetime.strptime("01-01-1000", "%d-%m-%Y")).days
        return (days_since_start * 1000) + self.turn
    
    def get_current_date(self) -> str:
        """Retorna a data atual formatada."""
        return self.current_time.strftime("%d-%m-%Y")

# Instância global para ser usada em todo o jogo
world_clock = Chronos()
