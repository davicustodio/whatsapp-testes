from app.core.config import get_settings
from app.providers.base import WhatsAppProvider
from app.providers.evolution import EvolutionProvider
from app.providers.meta import MetaCloudProvider


def get_provider() -> WhatsAppProvider:
    settings = get_settings()
    provider_name = settings.whatsapp_provider.lower().strip()

    if provider_name == "evolution":
        return EvolutionProvider(
            base_url=settings.evolution_api_url,
            api_key=settings.evolution_api_key,
        )

    if provider_name == "meta":
        return MetaCloudProvider()

    raise ValueError(f"Provider desconhecido: {settings.whatsapp_provider}")
