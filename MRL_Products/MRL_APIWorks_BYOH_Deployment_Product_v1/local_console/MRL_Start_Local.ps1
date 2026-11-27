param([int]$Port=8766,[string]$EvidenceRoot="",[string]$StateDir="",[string]$PythonPath="",[switch]$NoBrowser)
$ErrorActionPreference="Stop"
$MrlScript=Join-Path $PSScriptRoot "MRL_local_console_v1.py"
$MrlArgs=@($MrlScript,"--port",[string]$Port)
if($EvidenceRoot){$MrlArgs+=@("--evidence-root",$EvidenceRoot)}
if($StateDir){$MrlArgs+=@("--state-dir",$StateDir)}
if($NoBrowser){$MrlArgs+="--no-browser"}
if($PythonPath){& $PythonPath @MrlArgs;exit $LASTEXITCODE}
if(Get-Command py -ErrorAction SilentlyContinue){& py -3 @MrlArgs;exit $LASTEXITCODE}
if(Get-Command python -ErrorAction SilentlyContinue){& python @MrlArgs;exit $LASTEXITCODE}
throw "Python 3.10+ not found. Provide -PythonPath D:\path\python.exe"
