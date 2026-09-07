import abc

class BaseNotificationProvider(abc.ABC):
    @abc.abstractmethod
    async def send_alert(self, title: str, message: str) -> bool:
        pass
