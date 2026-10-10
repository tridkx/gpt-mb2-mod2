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
 // A/B assets remain available for comparison; only E/F activate this diagnostic.
 public sealed class ScaleProbe : MissionBehavior {
  public override MissionBehaviorType BehaviorType { get { return MissionBehaviorType.Other; } }
  private Agent target;
  private UIntPtr skeletonPointer;
  private string profile="";
  private float time, sampleTime;
  private int phase=-1, calls;
  private bool failed, observePending;
  private MatrixFrame referenceLocal;
  internal static int PhaseAt(float seconds) {
   if(seconds<6)return 0;if(seconds<18)return 1;if(seconds<24)return 2;if(seconds<36)return 3;return 4;
  }
  public override void OnPreDisplayMissionTick(float dt) {
   var agent=Mission.MainAgent;
   var id=agent==null || agent.SpawnEquipment==null?"":agent.SpawnEquipment[EquipmentIndex.Body].Item?.StringId ?? "";
   var requested=id=="ffs_E_body"?"E":id=="ffs_F_body"?"F":"";
   if(agent==null || !agent.IsHuman || !agent.IsActive() || agent.AgentVisuals==null)requested="";
   var skeleton=requested==""?null:agent.AgentVisuals.GetSkeleton();
   if(skeleton==null)requested="";
   try {
    if(agent!=target || requested!=profile || (skeleton!=null && skeleton.Pointer!=skeletonPointer)) {
     RestorePrevious();target=null;profile="";failed=false;phase=-1;time=0;sampleTime=0;calls=0;
     if(requested=="")return;
     if(skeleton.GetBoneCount()!=28 || skeleton.GetBoneName(13)!="head" || skeleton.GetParentBoneIndex(13)!=12) {Write("skip: unexpected human head bone");return;}
     target=agent;profile=requested;skeletonPointer=skeleton.Pointer;referenceLocal=skeleton.GetBoneLocalRestFrame(13,false);observePending=false;
     Write("BEGIN v0.1.3 profile="+profile+" agent="+agent.Index+" skeleton="+skeletonPointer+" method="+(profile=="E"?"once":"pre-display-every-frame")+" method=SetBoneLocalFrame+UpdateEntitialFramesFromLocalFrames");
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
     if(phase==0 || phase==2 || phase==4)RestoreHead();
     else {ApplyHead();}
     Snapshot("phase-entry-after");
     string label=phase==0?"BASELINE 6s":phase==2?"RESTORE 6s":phase==4?"DONE - restored":"HEAD x2 12s";
     InformationManager.DisplayMessage(new InformationMessage("Feifeng "+profile+" "+label));
    }
    if(profile=="F" && (phase==1 || phase==3) && !transition)ApplyHead();
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
  // Absolute basis lengths make repeated writes idempotent, not multiplicative.
  internal static MatrixFrame BuildHeadLocal(MatrixFrame parent, MatrixFrame current, MatrixFrame reference, float scale) {
   var local=parent.TransformToLocalNonOrthogonal(current);
   local.rotation.s=Axis(local.rotation.s,reference.rotation.s.Length*scale);
   local.rotation.f=Axis(local.rotation.f,reference.rotation.f.Length*scale);
   local.rotation.u=Axis(local.rotation.u,reference.rotation.u.Length*scale);
   return local;
  }
  private static Vec3 Axis(Vec3 axis,float length) {
   float n=axis.Length;
   if(float.IsNaN(n) || float.IsInfinity(n) || n<0.00001f || float.IsNaN(length) || float.IsInfinity(length))
    throw new InvalidOperationException("Invalid head axis");
   return axis*(length/n);
  }
  private void SetHeadScale(float scale) {
   var skeleton=target.AgentVisuals.GetSkeleton();
   var parent=skeleton.GetBoneEntitialFrame(12);
   var current=skeleton.GetBoneEntitialFrame(13);
   var local=BuildHeadLocal(parent,current,referenceLocal,scale);
   skeleton.SetBoneLocalFrame(13,local);
   skeleton.UpdateEntitialFramesFromLocalFrames();
  }
  private void ApplyHead() {SetHeadScale(2);calls++;}
  private void RestoreHead() {SetHeadScale(1);}
  private void RestorePrevious() {
   if(target!=null && target.IsActive() && target.AgentVisuals!=null) {
    var sk=target.AgentVisuals.GetSkeleton();
    if(sk!=null && sk.Pointer==skeletonPointer) {RestoreHead();Write("RESTORED profile="+profile);}
   }
  }
  private void Snapshot(string stage) {
   var sk=target.AgentVisuals.GetSkeleton();
   var b=new StringBuilder();
   b.AppendLine("v0.1.3 profile="+profile+" phase="+phase+" time="+Number(time)+" stage="+stage+" calls="+calls+" agentScale="+Number(target.AgentScale));
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
    File.AppendAllText(Path.Combine(directory,"local_frame_probe_v0.1.3.log"),DateTime.Now.ToString("s")+" "+text+Environment.NewLine);
   } catch { }
  }
 }
}
