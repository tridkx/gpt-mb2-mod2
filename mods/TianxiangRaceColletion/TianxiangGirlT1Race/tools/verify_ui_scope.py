"""Compile the exact runtime owner gate and exercise map/preview regression cases."""
import json,re,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=(R/'tools/UIRuntime/Runtime.cs').read_text()
method=re.search(r'internal static bool IsPreviewOwner\(string owner\) \{.*?\n        \}',s,re.S).group()
assert s.index('if (IsPreviewOwner(owner))')<s.index('private void CorrectPreview')
assert s.index('if (!IsPreviewOwner(owner)) return;')<s.index('var data=visual.GetCopyAgentVisualsData();')
cases={
 'SandBox.View.Map.MapScreen._mainPartyVisual':False,
 'SandBox.View.Map.PartyVisual._humanAgentVisuals':False,
 'SandBox.View.Map.MapConversationTableau._agentVisuals':False,
 'TaleWorlds.MountAndBlade.View.Tableaus.CharacterTableau._agentVisuals':True,
 'TaleWorlds.MountAndBlade.View.Tableaus.BasicCharacterTableau._agentVisuals':True,
 'TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView._visualToShow':True,
 'Unknown.CharacterTableau._agentVisuals':False,
 'TaleWorlds.MountAndBlade.View.Tableaus.CharacterTableauFake._agentVisuals':False,
}
B=R/'build/ui_scope_test';B.mkdir(parents=True,exist_ok=True)
(B/'Test.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType></PropertyGroup></Project>')
tests='\n'.join('if(IsPreviewOwner('+json.dumps(owner)+')!='+str(expected).lower()+')throw new Exception('+json.dumps(owner)+');' for owner,expected in cases.items())
(B/'Program.cs').write_text('using System;class Check{'+method+'\nstatic void Main(){'+tests+'\nif(IsPreviewOwner(null))throw new Exception("null");Console.WriteLine("OWNER_SCOPE_PASS");}}')
subprocess.run(['dotnet','run','--project',str(B/'Test.csproj')],check=True)
dll=R/'module/TianxiangGirlT1Race/bin/Win64_Shipping_Client/TianxiangGirlT1Race.UIRuntime.dll'
report=dict(status='pass',cases=cases,null_owner_allowed=False,source_sha256=hashlib.sha256(s.encode()).hexdigest(),assembly_sha256=hashlib.sha256(dll.read_bytes()).hexdigest(),game_verified=False)
(R/'reports/ui_scope_validation.json').write_text(json.dumps(report,indent=2))
