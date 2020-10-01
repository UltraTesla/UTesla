import time
import inspect

MINUTE = 60
HOUR = 60 * MINUTE
DAY = HOUR * 24
WEEK = DAY * 7

class Counter:
    """
    Inicia un contador para determinar cuánto ha durado un usuario

    Attributes:
        current_time: El tiempo actual en segundos desde que se inció
    """

    def __init__(self):
        self.current_time = time.time()
        self.__namedtuple = inspect.namedtuple(
            "counter",
            ("seconds", "minutes", "hours", "days", "weeks")

        )

    def calc_seconds(self):
        """Calcula los segundos transcurridos"""

        return time.time() - self.current_time

    def calc_minutes(self):
        """Calcula los minutos transcurridos"""

        return int(self.calc_seconds() // MINUTE)

    def calc_hours(self):
        """Calcula las horas transcurridas"""

        return int(self.calc_seconds() // HOUR)

    def calc_days(self):
        """Calcula los días transcurridos"""

        return int(self.calc_seconds() // DAY)

    def calc_weeks(self):
        """Calcula los meses transcurridos"""

        return int(self.calc_seconds() // WEEK)

    def calc(self):
        """Calcula los segundos, los minutos, las horas, los días y los meses"""

        return self.__namedtuple(
            self.calc_seconds(),
            self.calc_minutes(),
            self.calc_hours(),
            self.calc_days(),
            self.calc_weeks()

        )
