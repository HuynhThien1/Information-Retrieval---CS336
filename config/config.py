from pydantic import BaseModel
# from pydantic_settings import BaseSettings, SettingsConfigDict

class QdrantSettings(BaseModel):
    host: str = 'localhost'
    port: int = 6333
    grpc_port: int = 6334 # src: qdrant docs
    coll: str = 'clip_coll'
    prefer_grpc: bool = False
    api_key: str = None

class ClipSetting(BaseModel):
    model: str = 'RN50x4'

class Config():
    qdrant: QdrantSettings = QdrantSettings()
    clip: ClipSetting = ClipSetting()


configure = Config()