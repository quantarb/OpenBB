"""ThetaData provider module."""

from openbb_core.provider.abstract.provider import Provider

from openbb_thetadata.models.options_chains import ThetaDataOptionsChainsFetcher

thetadata_provider = Provider(
    name="thetadata",
    website="https://thetadata.net",
    description="""ThetaData provides historical and real-time options market data.""",
    credentials=["api_key"],
    fetcher_dict={
        "OptionsChains": ThetaDataOptionsChainsFetcher,
    },
    repr_name="ThetaData",
)
