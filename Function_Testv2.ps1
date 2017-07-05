#$global:basePath = ".\"
#$global:modulePath = $basePath + "Modules\"
#$ucsdAddr = "10.0.0.70"
#$cloupiaKey = "E7A4F16ACD934EC5A58BC0037EA7D96F"
#$ucsdAddr = "10.0.0.80"
#$cloupiaKey = "F81EC04E99E44D7E8D35017E36679835"

<# UCSD Object Class #>
class ucsdModule
{
    [string]$moduleName
    [string]$moduleDesc
    [string]$operationType
    [object]$modulePayload
    [string]$apiType
    [string]$apiCall

    ucsdModule([string]$name, [string]$desc, [string]$operType, [object]$payload, [string]$apiType, [string]$apiCall) {
        $this.moduleName = $name
        $this.moduleDesc = $desc
        $this.operationType = $operType
        $this.modulePayload = $payload
        $this.apiType = $apiType
        $this.apiCall = $apiCall

        #$tVar = $payload.param3
        #Write-Host "Printing..." $tVar.PSobject.Properties.name
        #if ($tVar.PSobject.Properties.name -contains "bootPolicy") {
        #    Write-Host "Got it!"
        #    Write-Host ($tVar.bootPolicy.descr -eq $null)
        #}
    }

    [string]getModuleName() {
        return $this.moduleName
    }

    [string]getOperationType() {
        return $this.operationType
    }

    [string]getAPI() {
        return $this.apiCall
    }

    [string]getAPIType() {
        return $this.apiType
    }

    [string]toJSON() {
        return $this.modulePayload | ConvertTo-Json -Depth 4
    }

    [string]toXML() {
        #$header = "<?xml version='1.0' encoding='utf-8'?>"
        $xmlTemp = ""
        $xmlTemp += "<cuicOperationRequest>"

        if($this.operationType) {
            $xmlTemp += "<operationType>"
            $xmlTemp += $this.operationType
            $xmlTemp += "</operationType>"
        }

        $xmlTemp += "<payload>"
        $xmlTemp += "<![CDATA["
        $xmlTemp += "<" + $this.getModuleName() + ">"

        $xmlTemp += $this.generateXML($this.modulePayload.param0)

        $xmlTemp += "</" + $this.getModuleName() + ">"
        $xmlTemp += "]]>"
        $xmlTemp += "</payload>"
        $xmlTemp += "</cuicOperationRequest>"

        return $xmlTemp
    }

    [string]generateXML($xmlObj){
        $xmlText = ""
        #$xmlData = @{}

        foreach($xmlProp in $xmlObj.psobject.Properties) {
            if($xmlProp.Value.toString() -eq "System.Object") {
                $xmlText += "<$($xmlProp.Name)>"
                $xmlText += $this.generateXML($xmlProp.Value)
                $xmlText += "</$($xmlProp.Name)>"
            }
            elseif($xmlProp.Value.GetType().isArray) {
                $tempObj = New-Object -TypeName psobject
                $tempObj | Add-Member -MemberType NoteProperty -Name $xmlProp.Name -Value $xmlProp.Value
                
                for($i = 0; $i -lt $tempObj.($xmlProp.name).count; $i++) {
                    $xmlText += "<$($xmlProp.Name)>"
                    $xmlText += $this.generateXML($tempObj.($xmlProp.name)[$i])
                    $xmlText += "</$($xmlProp.Name)>"
                }
            }
            else {
                $xmlText += "<$($xmlProp.Name)>$($xmlProp.Value)</$($xmlProp.Name)>"
            }
        }

        return $xmlText
    }
}

<# Import Modules in Module Folder #>
function Create-UCSDModule($modulePath, $modKey) {
    $json = Get-Content -Raw -Path $modulePath\$modKey.json
    $modObj = $json | ConvertFrom-Json

    $loadModule = Create-SubModule($modObj)

    #$tVar = $loadModule.modulePayload.param3
    #Write-Host "Validating..." $tVar.PSobject.Properties.name
    #if ($tVar.PSobject.Properties.name -contains "bootPolicy") {
    #    Write-Host "Got it!"
    #    Write-Host ($tVar.bootPolicy.descr -eq $null)
    #}

    [ucsdModule] $newModule = [ucsdModule]::new($loadModule.moduleName, $loadModule.moduleDesc, $loadModule.operationType, $loadModule.modulePayload, $loadModule.apiType, $loadModule.apiCall)

    return $newModule
}

function Create-SubModule($modObj) {
    $modData = @{}
    $module = New-Object System.Object

    $modObj.psObject.Properties | Foreach { $modData[$_.Name] = $_.Value }

    #Write-Host "Entering Loop..."
    #Write-Host $modData
    #Write-Host $modData.Keys

    foreach($valKey in @($modData.Keys)) {
        #Write-Host "KEY:" $modData[$valKey]
        if($modData[$valKey] -eq $null) {
            #Write-Host "NULL!"
            $module | Add-Member $valKey $modData[$valKey]
            #Write-Host ($module.$valKey -eq $null)
        }
        elseif($modData[$valKey].pstypenames -contains 'System.Management.Automation.PSCustomObject') {
            #Write-Host "OBJECT!"
            #Write-Host $modData[$valKey].pstypenames
            #Write-Host "`$module | Add-Member $valKey Create-SubModule($valKey)"
            $module | Add-Member $valKey (Create-SubModule($modData[$valKey]))
        }
        else {
            #Write-Host $modData[$valKey]
            #Write-Host $modData[$valKey].pstypenames
            #Write-Host "else `$module | Add-Member $valKey (" $modData[$valKey].toString() ")"
            if($modData[$valKey].pstypenames -contains 'System.Array') {
                #Write-Host "ARRAY!"
                $module | Add-Member $valKey $modData[$valKey]
            }
            else {
                #Write-Host "STRING!"
                $module | Add-Member $valKey $modData[$valKey].toString()
            }
        }
    }

    return $module
}


<# List Modules in Module Folder #>
function List-Modules($modulePath) {
    $modules = New-Object System.Collections.ArrayList

    $files = Get-ChildItem -LiteralPath $modulePath -File

    # > $null supresses returning the Index output, can also use " | Out-Null" instead
    foreach($file in $files) {
        Write-Host "File: $file"
        $nameSplit = $file.Name.Split("{.}")
        $modules.Add($nameSplit[0]) > $null
    }

    return $modules
}

<# UCSD API Request Call #>
function Call-UCSDAPI($module) {
    if($module.GetAPIType() -eq "xml") {
        $xmlURL = "https://$ucsdAddr" + $module.getAPI()
        $xmlHeader = "<?xml version=`"1.0`" encoding=`"utf-8`"?>"
        $request = $xmlHeader + $module.toXML()
        $method = ""

        if($module.GetOperationType() -eq "UPDATE") {
            $method = "Put"
        }
        else {
            $method = "Post"
        }

        Write-Host "`$xmlURL: " $xmlURL
        Write-Host "`$xmlHeader: " $xmlHeader
        Write-Host "`$request: " $request
        Write-Host "`$result = Invoke-WebRequest -Uri $xmlUrl -Method $method -Body $request -Headers @{`"X-Cloupia-Request-Key`"=`"$cloupiaKey`"} -ContentType 'application/xml'"
        $result = Invoke-WebRequest -Uri $xmlUrl -Method $method -Body $request -Headers @{"X-Cloupia-Request-Key"="$cloupiaKey"} -ContentType 'application/xml'
    }
    elseif($module.GetAPIType() -eq "json") {
        $request = "https://" + $ucsdAddr + $module.getAPI() + $module.toJSON()

        Write-Host "`$request: " $request
        Write-Host "`$result = Invoke-RestMethod $request -Headers @{`"X-Cloupia-Request-Key`"=`"$cloupiaKey`"}"
        $result = Invoke-RestMethod $request -Headers @{"X-Cloupia-Request-Key"="$cloupiaKey"}
    }
    else {
        Write-Host "ERROR!!!"
    }

    return $result
}
