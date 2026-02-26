import asyncio
from viam.module.module import Module
try:
    from models.smart_plug import SmartPlug
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.smart_plug import SmartPlug


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
