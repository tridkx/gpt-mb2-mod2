"""Compile the exact runtime owner gate and exercise map/preview regression cases."""
import json,re,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=(R/'tools/UIRuntime/Runtime.cs').read_text()
method=re.search(r'internal static bool IsPreviewOwner\(string owner\) \{.*?\n        \}',s,re.S).group()
provider_method=re.search(r'internal static object FindCharacterTableau\(object provider\) \{.*?\n        \}',s,re.S).group()
body_method=re.search(r'internal static object FindBodyGenerator\(object screen\) \{.*?\n        \}',s,re.S).group()
assert s.index('FindBodyGenerator(screen)')<s.index('Inspect(screen, 0, seen')
assert s.index('FindCharacterTableau(texture?.TextureProvider)')<s.index('Inspect(screen, 0, seen')
assert 'CollectTableauVisuals(tableau,visuals,owners)' in s
inspect_method=re.search(r'private void Inspect\(object obj,.*?\n        \}',s,re.S).group()
fields_method=re.search(r'private FieldInfo\[\] Fields\(Type type\) \{.*?\n        \}',s,re.S).group()
collect_method=re.search(r'private void CollectTableauVisuals\(object tableau,.*?\n        \}',s,re.S).group()
comparer=re.search(r'internal sealed class ReferenceComparer.*?\n        \}',s,re.S).group()
assert inspect_method.index('type.IsValueType')<inspect_method.index('seen.Add(obj)')
assert s.index('if (IsPreviewOwner(owner))')<s.index('private void CorrectPreview')
assert s.index('if (!IsPreviewOwner(owner)) return;')<s.index('var data=visual.GetCopyAgentVisualsData();')
cases={
 'SandBox.View.Map.MapScreen._mainPartyVisual':False,
 'SandBox.View.Map.PartyVisual._humanAgentVisuals':False,
 'SandBox.View.Map.MapConversationTableau._agentVisuals':False,
 'TaleWorlds.MountAndBlade.View.Tableaus.CharacterTableau._agentVisuals':True,
 'TaleWorlds.MountAndBlade.View.Tableaus.BasicCharacterTableau._agentVisuals':True,
 'TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView._visualToShow':True,
 'TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView._nextVisualToShow':True,
 'Unknown.BodyGeneratorView._visualToShow':False,
 'Unknown.CharacterTableau._agentVisuals':False,
 'TaleWorlds.MountAndBlade.View.Tableaus.CharacterTableauFake._agentVisuals':False,
}
B=R/'build/ui_scope_test';B.mkdir(parents=True,exist_ok=True)
(B/'Test.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework><OutputType>Exe</OutputType></PropertyGroup></Project>')
tests='\n'.join('if(IsPreviewOwner('+json.dumps(owner)+')!='+str(expected).lower()+')throw new Exception('+json.dumps(owner)+');' for owner,expected in cases.items())
provider_tests='''
var tableau=new TaleWorlds.MountAndBlade.View.Tableaus.CharacterTableau();
var provider=new TaleWorlds.MountAndBlade.GauntletUI.TextureProviders.CharacterTableauTextureProvider(tableau);
if(!ReferenceEquals(FindCharacterTableau(provider),tableau))throw new Exception("direct provider missed");
if(FindCharacterTableau(null)!=null || FindCharacterTableau(new object())!=null)throw new Exception("unknown provider allowed");
if(FindCharacterTableau(new TaleWorlds.MountAndBlade.GauntletUI.TextureProviders.CharacterTableauTextureProvider(new object()))!=null)throw new Exception("unknown tableau allowed");
var oldSeen=new HashSet<object>();oldSeen.Add(new BadAction(1));
bool reproduced=false;
try {oldSeen.Add(tableau);}catch(InvalidCastException){reproduced=true;}
if(!reproduced)throw new Exception("boxed action failure not reproduced");
var seen=new HashSet<object>(ReferenceComparer.Instance);
var visuals=new HashSet<AgentVisuals>();var owners=new Dictionary<AgentVisuals,string>();
var check=new Check();
check.CollectTableauVisuals(tableau,visuals,owners);
if(visuals.Count!=2)throw new Exception("direct visual fields missed");
check.Inspect(tableau,0,seen,visuals,owners,tableau.GetType().FullName);
if(visuals.Count!=2 || seen.Count!=4)throw new Exception("runtime traversal failed");
if(owners.Values.Any(owner=>!IsPreviewOwner(owner)))throw new Exception("unknown owner collected");
var body=new TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView();
var stage=new SandBox.GauntletUI.CharacterCreation.CharacterCreationFaceGeneratorView(body);
var screen=new SandBox.View.CharacterCreation.CharacterCreationScreen(stage);
if(!ReferenceEquals(FindBodyGenerator(screen),body))throw new Exception("creation stage path missed");
if(FindBodyGenerator(null)!=null || FindBodyGenerator(new object())!=null)throw new Exception("unknown creation screen accepted");
if(FindBodyGenerator(new SandBox.View.CharacterCreation.CharacterCreationScreen(new object()))!=null)throw new Exception("unknown stage accepted");
if(FindBodyGenerator(new SandBox.View.CharacterCreation.CharacterCreationScreen(new SandBox.GauntletUI.CharacterCreation.CharacterCreationFaceGeneratorView(new object())))!=null)throw new Exception("unknown body view accepted");
seen.Clear();visuals.Clear();owners.Clear();
check.CollectTableauVisuals(body,visuals,owners);
if(visuals.Count!=2)throw new Exception("current and rebuilding body visuals missed");
body.Rebuild();visuals.Clear();owners.Clear();
check.Inspect(body,0,seen,visuals,owners,body.GetType().FullName);
if(visuals.Count!=2 || seen.Count!=1)throw new Exception("rebuilt body visuals not collected directly");
if(owners.Values.Any(owner=>!IsPreviewOwner(owner)))throw new Exception("unknown body owner collected");
Console.WriteLine("BOXED_ACTION_EXCEPTION_REPRODUCED_AND_REAL_TRAVERSAL_PASS");
'''
stubs='''
public struct BadAction { int index;public BadAction(int value){index=value;}public override int GetHashCode(){return 1;}public override bool Equals(object obj){return index==((BadAction)obj).index;} }
public class AgentVisuals {} public class Widget {} public class NativeObject {}
namespace TaleWorlds.MountAndBlade.View.Tableaus {
 public class BadReference { public override int GetHashCode(){return 1;}public override bool Equals(object obj){throw new InvalidCastException("custom reference equality called");} }
 public class CharacterTableau {
  private BadAction _idleAction=new BadAction(1);
  private AgentVisuals _agentVisuals=new AgentVisuals();
  private AgentVisuals _oldAgentVisuals=new AgentVisuals();
  private BadReference _other=new BadReference();
  public override int GetHashCode(){return 1;}public override bool Equals(object obj){throw new InvalidCastException("custom reference equality called");}
 }
}
namespace TaleWorlds.MountAndBlade.GauntletUI.TextureProviders { public class CharacterTableauTextureProvider { private object _characterTableau; public CharacterTableauTextureProvider(object value){_characterTableau=value;} } }
namespace TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator { public class BodyGeneratorView { private AgentVisuals _visualToShow=new AgentVisuals();private AgentVisuals _nextVisualToShow=new AgentVisuals();public void Rebuild(){_visualToShow=new AgentVisuals();_nextVisualToShow=new AgentVisuals();} } }
namespace SandBox.GauntletUI.CharacterCreation { public class CharacterCreationFaceGeneratorView { private object _faceGeneratorView;public CharacterCreationFaceGeneratorView(object value){_faceGeneratorView=value;} } }
namespace SandBox.View.CharacterCreation { public class CharacterCreationScreen { private object _currentStageView;public CharacterCreationScreen(object value){_currentStageView=value;} } }
'''
(B/'Program.cs').write_text('using System;using System.Reflection;using System.Collections;using System.Collections.Generic;using System.Linq;using System.Runtime.CompilerServices;class Check{private readonly Dictionary<Type,FieldInfo[]> fields=new Dictionary<Type,FieldInfo[]>();'+method+provider_method+body_method+fields_method+inspect_method+collect_method+comparer+'\nstatic void Main(){'+tests+provider_tests+'\nif(IsPreviewOwner(null))throw new Exception("null");Console.WriteLine("OWNER_SCOPE_AND_PROVIDER_PASS");}}'+stubs)
subprocess.run(['dotnet','run','--project',str(B/'Test.csproj')],check=True)
dll=R/'module/BoRuRace/bin/Win64_Shipping_Client/BoRuRace.UIRuntime.dll'
report=dict(status='pass',cases=cases,null_owner_allowed=False,direct_provider_cases='actual runtime methods compiled with matching provider/tableau stubs; valid/null/unknown provider/unknown tableau',actual_field_collection_and_inspect_executed=True,boxed_action_invalid_cast_reproduced=True,reference_and_value_custom_equals_never_called=True,inventory_discovery_independent_of_screen_seen_budget=True,source_sha256=hashlib.sha256(s.encode()).hexdigest(),assembly_sha256=hashlib.sha256(dll.read_bytes()).hexdigest(),game_verified=False)
report.update(creation_current_and_next_visuals_collected=True,creation_stage_path_executed=True,creation_rebuilding_visuals_collected=True,unknown_creation_types_excluded=True)
(R/'reports/ui_scope_validation.json').write_text(json.dumps(report,indent=2))
