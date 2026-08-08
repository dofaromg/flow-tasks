
FROM python:3.10

WORKDIR /mrliouai

COPY . /mrliouai

# 解壓封包
RUN apt-get update && apt-get install -y unzip && \
    unzip RestorePack.zip -d ./restorepack && \
    unzip RecoveryPack.zip -d ./recoverypack && \
    unzip FusionSync.zip -d ./systemfusion && \
    unzip RuntimeModules.zip -d ./modules

# 啟動 CLI 流程
CMD ["bash", "start.sh"]
