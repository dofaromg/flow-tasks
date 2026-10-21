# MRL_External — MRL_External_Mirror_Layer
# origin_signature: MrLiouWord
"""外部鏡像層：Cloudflared / GitHub / XOOPZ / Claude 皆為 Adapter / Mirror，不得成為主體。"""

ORIGIN_SIGNATURE = "MrLiouWord"

EXTERNAL_MIRROR_LAYER = {
    "MRL_Cloudflared_Adapter": {
        "role": "Tunnel / Ingress / Mirror / Adapter",
        "is_subject": False,
        "deploy_entry": "deploy/dl580/cloudflared/MRL_cloudflared_deploy.ps1",
        "hostname": "bridge.mrliouhan.ai",
    },
    "MRL_GitHub_Mirror": {
        "role": "工程鏡像 / 版本通道",
        "is_subject": False,
        "workflow": ".github/workflows/MRL_GitHub_Mirror.yml",
    },
    "MRL_XOOPZ_Adapter": {"role": "External Mapping", "is_subject": False},
    "MRL_ClaudeExecutionBridge": {"role": "Execution Adapter", "is_subject": False},
}
