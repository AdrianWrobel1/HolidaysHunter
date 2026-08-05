from app.models.enums import Provider
from app.providers.base import BaseNormalizer, BaseProvider
from app.providers.itaka.normalizer import ItakaNormalizer
from app.providers.itaka.provider import ItakaProvider
from app.providers.rainbow.normalizer import RainbowNormalizer
from app.providers.rainbow.provider import RainbowProvider
from app.providers.tui.normalizer import TuiNormalizer
from app.providers.tui.provider import TuiProvider
from app.providers.wakacje_pl.normalizer import WakacjePlNormalizer
from app.providers.wakacje_pl.provider import WakacjePlProvider


class ProviderEntry:
    """Holds a provider/normalizer pair with metadata."""

    def __init__(
        self,
        provider_cls: type[BaseProvider],
        normalizer_cls: type[BaseNormalizer],
    ) -> None:
        self.provider_cls = provider_cls
        self.normalizer_cls = normalizer_cls

    def create_provider(self) -> BaseProvider:
        return self.provider_cls()

    def create_normalizer(self) -> BaseNormalizer:
        return self.normalizer_cls()


PROVIDER_REGISTRY: dict[Provider, ProviderEntry] = {
    Provider.ITAKA: ProviderEntry(
        provider_cls=ItakaProvider,
        normalizer_cls=ItakaNormalizer,
    ),
    Provider.TUI: ProviderEntry(
        provider_cls=TuiProvider,
        normalizer_cls=TuiNormalizer,
    ),
    Provider.RAINBOW: ProviderEntry(
        provider_cls=RainbowProvider,
        normalizer_cls=RainbowNormalizer,
    ),
    Provider.WAKACJE_PL: ProviderEntry(
        provider_cls=WakacjePlProvider,
        normalizer_cls=WakacjePlNormalizer,
    ),
}


def get_provider_entry(provider: Provider) -> ProviderEntry:
    """Look up a registered provider by enum value.

    Raises KeyError if the provider is not registered.
    """
    return PROVIDER_REGISTRY[provider]


def get_all_providers() -> list[Provider]:
    """Return all registered provider enum values."""
    return list(PROVIDER_REGISTRY.keys())
