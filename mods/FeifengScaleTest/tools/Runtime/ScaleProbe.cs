using System;
using System.Globalization;
using System.IO;
using System.Text;
using TaleWorlds.Core;
using TaleWorlds.Engine;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;
using Path = System.IO.Path;

namespace FeifengScaleTest {
 public class SubModule : MBSubModuleBase {
  public override void OnMissionBehaviorInitialize(Mission mission) {
   if (!GameNetwork.IsMultiplayer) mission.AddMissionBehavior(new ScaleProbe());
  }
 }
 // A/B assets remain available for comparison; only C/D activate this diagnostic.
 public sealed class ScaleProbe : MissionBehavior {
  public override MissionBehaviorType BehaviorType { get { return MissionBehaviorType.Other; } }
  private Agent target;
  private UIntPtr skeletonPointer;
  private string profile="";
  private float time, sampleTime;
  private int phase=-1, calls;
  private bool failed, observePending;
  private static readonly sbyte[] Head = {13};
  private static readonly Vec3[] DoubleHead = {new Vec3(2,2,2)};
  private static readonly sbyte[] All = MakeIndices();
  private static sbyte[] MakeIndices() {var a=new sbyte[28];for(sbyte i=0;i<28;i++)a[i]=i;return a;}
  internal static int PhaseAt(float seconds) {
   if(seconds<6)return 0;if(seconds<18)return 1;if(seconds<24)return 2;if(seconds<36)return 3;return 4;
  }
  public override void OnPreDisplayMissionTick(float dt) {
   var agent=Mission.MainAgent;
   var id=agent==null || agent.SpawnEquipment==null?"":agent.SpawnEquipment[EquipmentIndex.Body].Item?.StringId ?? "";
   var requested=id=="ffs_C_body"?"C":id=="ffs_D_body"?"D":"";
   if(agent==null || !agent.IsHuman || !agent.IsActive() || agent.AgentVisuals==null)requested="";
   var skeleton=requested==""?null:agent.AgentVisuals.GetSkeleton();
   if(skeleton==null)requested="";
   try {
    if(agent!=target || requested!=profile || (skeleton!=null && skeleton.Pointer!=skeletonPointer)) {
     RestorePrevious();target=null;profile="";failed=false;phase=-1;time=0;sampleTime=0;calls=0;
     if(requested=="")return;
     if(skeleton.GetBoneCount()!=28 || skeleton.GetBoneName(13)!="head") {Write("skip: unexpected human head bone");return;}
     target=agent;profile=requested;skeletonPointer=skeleton.Pointer;
     Write("BEGIN v0.1.2 profile="+profile+" agent="+agent.Index+" skeleton="+skeletonPointer+" method="+(profile=="C"?"once":"pre-display-every-frame")+" forceUpdate=false");
     foreach(var slot in new[]{EquipmentIndex.Head,EquipmentIndex.Body,EquipmentIndex.Leg}) {
      var item=agent.SpawnEquipment[slot].Item;
      Write("equipment slot="+slot+" id="+item?.StringId+" mesh="+item?.MultiMeshName);
     }
    }
    if(profile=="" || failed)return;
    time+=Math.Max(0,dt);
    int next=PhaseAt(time);
    bool transition=next!=phase;
    if(transition) {
     phase=next;
     Snapshot("phase-entry-before");
     if(phase==0 || phase==2 || phase==4)Neutral(target);
     else {ApplyHead();}
     Snapshot("phase-entry-after");
     string label=phase==0?"BASELINE 6s":phase==2?"RESTORE 6s":phase==4?"DONE - restored":"HEAD x2 12s";
     InformationManager.DisplayMessage(new InformationMessage("Feifeng "+profile+" "+label));
    }
    if(profile=="D" && (phase==1 || phase==3) && !transition)ApplyHead();
    sampleTime+=Math.Max(0,dt);
    if(sampleTime>=1 && phase<4) {sampleTime=0;Snapshot("pre-display-sample");observePending=true;}
   } catch(Exception error) {
    Write("ERROR "+error);failed=true;
    try {RestorePrevious();}catch(Exception restoreError){Write("RESTORE ERROR "+restoreError);}
    InformationManager.DisplayMessage(new InformationMessage("Feifeng diagnostic failed; see log."));
   }
  }
  // Observe the next mission update before any pre-display reapplication.
  public override void OnMissionTick(float dt) {
   if(target!=null && !failed && phase<4 && observePending) {
    observePending=false;
    try {Snapshot("mission-tick-observation");}catch(Exception error){Write("OBSERVATION ERROR "+error);}
   }
  }
  protected override void OnEndMission() { try {RestorePrevious();}catch(Exception error){Write("END RESTORE ERROR "+error);} }
  private void ApplyHead() {
   target.AgentVisuals.ApplySkeletonScale(new Vec3(1,1,1),0,Head,DoubleHead);calls++;
   // Do not ForceUpdateBoneFrames: it may rebuild frames and obscure persistence.
  }
  private static void Neutral(Agent agent) {
   agent.AgentVisuals.ApplySkeletonScale(new Vec3(1,1,1),0,All,Profiles.Neutral);
   var item=agent.SpawnEquipment?[EquipmentIndex.Body].Item;
   agent.AgentVisuals.UpdateSkeletonScale(item?.ArmorComponent==null?0:(int)item.ArmorComponent.BodyDeformType);
  }
  private void RestorePrevious() {
   if(target!=null && target.IsActive() && target.AgentVisuals!=null) {
    var sk=target.AgentVisuals.GetSkeleton();
    if(sk!=null && sk.Pointer==skeletonPointer) {Neutral(target);Write("RESTORED profile="+profile);}
   }
  }
  private void Snapshot(string stage) {
   var sk=target.AgentVisuals.GetSkeleton();
   var b=new StringBuilder();
   b.AppendLine("v0.1.2 profile="+profile+" phase="+phase+" time="+Number(time)+" stage="+stage+" calls="+calls+" agentScale="+Number(target.AgentScale));
   for(sbyte i=0;i<28;i++) {
    var rest=sk.GetBoneEntitialRestFrame(i,false);var current=sk.GetBoneEntitialFrame(i);
    b.AppendLine(i+" "+sk.GetBoneName(i)+" mapped="+sk.GetSkeletonBoneMapping(i)+" rest="+Frame(rest)+" current="+Frame(current));
   }
   Write(b.ToString());
  }
  private static string Number(float value) {return value.ToString("R",CultureInfo.InvariantCulture);}
  private static string Vector(Vec3 v) {return Number(v.x)+","+Number(v.y)+","+Number(v.z);}
  private static string Frame(MatrixFrame f) {
   return "origin("+Vector(f.origin)+") side("+Vector(f.rotation.s)+") forward("+Vector(f.rotation.f)+") up("+Vector(f.rotation.u)+")";
  }
  private static void Write(string text) {
   try {
    var directory=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"Mount and Blade II Bannerlord","FeifengScaleTest");
    Directory.CreateDirectory(directory);
    File.AppendAllText(Path.Combine(directory,"single_bone_probe_v0.1.2.log"),DateTime.Now.ToString("s")+" "+text+Environment.NewLine);
   } catch { }
  }
 }
}
