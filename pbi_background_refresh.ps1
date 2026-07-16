$ErrorActionPreference = "Stop"

function Refresh-PowerBI {
    try {
        # Hardcoded Port for current Power BI session
        $port = "52476"
        
        # 2. Load ADOMD Client
        $adomdPath = 'C:\Program Files\Microsoft Office\root\Office16\ADDINS\Microsoft Power Query for Excel Integrated\bin\Microsoft.PowerBI.AdomdClient.dll'
        if (-not (Test-Path $adomdPath)) {
            Write-Host "ADOMD Client DLL not found. Cannot refresh."
            return
        }
        Add-Type -Path $adomdPath -ErrorAction SilentlyContinue
        
        # 3. Connect and get Database ID
        $conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection "Data Source=localhost:$port"
        $conn.Open()
        
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = 'SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS'
        $reader = $cmd.ExecuteReader()
        $reader.Read() | Out-Null
        $dbId = $reader.GetString(0)
        $reader.Close()
        
        # 4. Execute TMSL Refresh for the fact table
        $tmsl = @"
{
  "refresh": {
    "type": "dataOnly",
    "objects": [
      {
        "database": "$dbId",
        "table": "fact_sensor_live"
      }
    ]
  }
}
"@
        $cmd.CommandText = $tmsl
        $cmd.ExecuteNonQuery() | Out-Null
        
        $conn.Close()
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Successfully refreshed fact_sensor_live in Power BI (Port: $port)"
        
    } catch {
        Write-Host "Error during refresh: $_"
    }
}

Write-Host "Starting Invisible Power BI Auto-Refresh..."
Write-Host "Press Ctrl+C to stop."
while ($true) {
    Refresh-PowerBI
    Start-Sleep -Seconds 5
}
