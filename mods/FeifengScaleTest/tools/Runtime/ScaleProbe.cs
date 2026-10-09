using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using TaleWorlds.Core;
using TaleWorlds.Engine;
using Path = System.IO.Path;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;

namespace FeifengScaleTest {
 public class SubModule : MBSubModuleBase {
  public override void OnMissionBehaviorInitialize(Mission mission) {
   if (!GameNetwork.IsMultiplayer) mission.AddMissionBehavior(new ScaleProbe());
  }
 }
 public sealed class ScaleProbe : MissionBehavior {
  public override MissionBehaviorType BehaviorType { get { return MissionBehaviorType.Other; } }
  private sealed class State { public string Profile; public UIntPtr Skeleton; public bool PendingSnapshot; }
  private readonly Dictionary<Agent,State> states=new Dictionary<Agent,State>();
  private float elapsed;
  public override void OnMissionTick(float dt) {
   elapsed+=dt;if(elapsed<0.5f)return;elapsed=0;
   foreach(var agent in Mission.Agents) {
    if(!agent.IsHuman || !agent.IsActive() || agent.AgentVisuals==null)continue;
    var equipment=agent.SpawnEquipment;
    var item=equipment==null?null:equipment[EquipmentIndex.Body].Item;
    var id=item==null?"":item.StringId;
    var profile=id=="ffs_A_body"?"A":id=="ffs_B_body"?"B":"";
    var skeleton=agent.AgentVisuals.GetSkeleton();if(skeleton==null)continue;
    State previous;states.TryGetValue(agent,out previous);
    if(previous!=null && previous.Profile==profile && previous.Skeleton==skeleton.Pointer) {
     if(previous.PendingSnapshot) { Snapshot(agent,profile,"after-next-tick-v0.1.1");previous.PendingSnapshot=false; }
     continue;
    }
    if(profile=="" && previous==null)continue;
    try {
     if(skeleton.GetBoneCount()!=28) { Write("skip: unexpected skeleton count "+skeleton.GetBoneCount());continue; }
     if(previous!=null && previous.Skeleton==skeleton.Pointer && previous.Profile!="") {
      Apply(agent,Profiles.Neutral);
      int deform=item!=null && item.ArmorComponent!=null?(int)item.ArmorComponent.BodyDeformType:0;
      agent.AgentVisuals.UpdateSkeletonScale(deform);
     }
     if(profile!="") {
      foreach(var slot in new [] {EquipmentIndex.Head,EquipmentIndex.Body,EquipmentIndex.Leg}) {
       var equipped=equipment[slot].Item;if(equipped==null)continue;
       var mesh=MetaMesh.GetCopy(equipped.MultiMeshName,false,true);
       Write("v0.1.1 mesh="+equipped.MultiMeshName+" loaded="+(mesh!=null)+" groups="+(mesh==null?0:mesh.MeshCount));
      }
      Snapshot(agent,profile,"before");
      Apply(agent,profile=="A"?Profiles.A:Profiles.B);
      Snapshot(agent,profile,"after");
      InformationManager.DisplayMessage(new InformationMessage("Feifeng scale probe "+profile+" applied; game validation required."));
     } else Write("restored agent "+agent.Index);
     states[agent]=new State {Profile=profile,Skeleton=skeleton.Pointer,PendingSnapshot=profile!=""};
    } catch(Exception exception) {
     Write("ERROR "+exception);
     states[agent]=new State {Profile=profile,Skeleton=skeleton.Pointer};
     InformationManager.DisplayMessage(new InformationMessage("Feifeng scale probe failed; see probe log."));
    }
   }
  }
  private static void Apply(Agent agent,Vec3[] scales) {
   var indices=new sbyte[28];for(sbyte i=0;i<28;i++)indices[i]=i;
   agent.AgentVisuals.ApplySkeletonScale(new Vec3(1,1,1),0,indices,scales);
   agent.AgentVisuals.GetSkeleton().ForceUpdateBoneFrames();
  }
  private static void Snapshot(Agent agent,string profile,string stage) {
   var text=new StringBuilder();text.AppendLine("agent="+agent.Index+" profile="+profile+" stage="+stage+" agentScale="+agent.AgentScale.ToString("R",CultureInfo.InvariantCulture));
   var skeleton=agent.AgentVisuals.GetSkeleton();
   for(sbyte i=0;i<28;i++) {
    var rest=skeleton.GetBoneEntitialRestFrame(i,false);var current=skeleton.GetBoneEntitialFrame(i);
    text.AppendLine(i+" "+skeleton.GetBoneName(i)+" rest="+Vector(rest.origin)+" current="+Vector(current.origin));
   }
   Write(text.ToString());
  }
  private static string Vector(Vec3 p) { return string.Join(",",p.x.ToString("R",CultureInfo.InvariantCulture),p.y.ToString("R",CultureInfo.InvariantCulture),p.z.ToString("R",CultureInfo.InvariantCulture)); }
  private static void Write(string text) {
   try {
    var directory=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"Mount and Blade II Bannerlord","FeifengScaleTest");
    Directory.CreateDirectory(directory);File.AppendAllText(Path.Combine(directory,"scale_probe.log"),DateTime.Now.ToString("s")+" "+text+Environment.NewLine);
   } catch { /* Diagnostic logging must not stop a mission. */ }
  }
 }
}
