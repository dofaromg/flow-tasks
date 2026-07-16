# MRL_DL580_DEPLOYMENT_v1

## Windows Server / DL580
```powershell
cd D:\MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0
node -v
npm install
$env:MRL_PORT="8788"
$env:MRL_AUTH_REQUIRED="false"
npm run acceptance
npm start
```

Smoke:
```powershell
Invoke-RestMethod http://127.0.0.1:8788/api/mrl/health
npm run smoke
```

## Linux / Ubuntu 22.04
```bash
cd /opt/MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0
npm install
npm run acceptance
MRL_PORT=8788 npm start
```

## Enterprise env
- `MRL_PORT`: default 8788
- `MRL_HOST`: default 0.0.0.0
- `MRL_AUTH_REQUIRED`: true / false
- `MRL_API_TOKEN`: required when auth is true
- `MRL_LOG_LEVEL`: info / debug
- `MRL_MAX_BODY_BYTES`: default 52428800
