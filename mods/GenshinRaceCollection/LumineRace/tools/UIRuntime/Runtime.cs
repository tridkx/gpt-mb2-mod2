using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Web.Script.Serialization;
using TaleWorlds.Core;
using TaleWorlds.Engine;
using TaleWorlds.DotNet;
using TaleWorlds.Engine.GauntletUI;
using TaleWorlds.GauntletUI.BaseTypes;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;
using TaleWorlds.MountAndBlade.View;
using TaleWorlds.ScreenSystem;
using Path = System.IO.Path;

namespace LumineRace.UIRuntime {
    // Scope corrections to this race's UI previews; preserve all character data.
    public sealed class SubModule : MBSubModuleBase {
        private const string LeaderKey="gpt-mb2-mod2/GenshinRaceCollection/UILeader";
        private const string RegistryKey="gpt-mb2-mod2/GenshinRaceCollection/UIRepairs";
        internal sealed class ReferenceComparer : IEqualityComparer<object> {
            internal static readonly ReferenceComparer Instance=new ReferenceComparer();
            public new bool Equals(object a,object b) { return ReferenceEquals(a,b); }
            public int GetHashCode(object obj) { return RuntimeHelpers.GetHashCode(obj); }
        }
        private float elapsed;
        private float logElapsed;
        private static readonly bool RepairEnabled = typeof(SubModule).Assembly.GetName().Name == "LumineRace.UIRuntime";
        private int samples;
        private readonly Dictionary<string,int> screenSamples = new Dictionary<string,int>();
        private readonly string session = DateTime.Now.ToString("yyyyMMdd_HHmmss");
        private readonly Dictionary<Type, FieldInfo[]> fields = new Dictionary<Type, FieldInfo[]>();
        private readonly JavaScriptSerializer serializer = new JavaScriptSerializer();

        protected override void OnSubModuleLoad() {
            base.OnSubModuleLoad();
            var registry=AppDomain.CurrentDomain.GetData(RegistryKey) as Dictionary<string,Action<AgentVisuals,string,string>>;
            if(registry==null) {
                registry=new Dictionary<string,Action<AgentVisuals,string,string>>(StringComparer.Ordinal);
                AppDomain.CurrentDomain.SetData(RegistryKey,registry);
            }
            registry["lumine"]=CorrectPreview;
            if(AppDomain.CurrentDomain.GetData(LeaderKey)==null)AppDomain.CurrentDomain.SetData(LeaderKey,this);
            Write(new { kind="loaded", probe="ui-v3-creation-rebuild", changes_preview_skeleton=RepairEnabled });
        }

        protected override void OnApplicationTick(float dt) {
            base.OnApplicationTick(dt);
            if(!ReferenceEquals(AppDomain.CurrentDomain.GetData(LeaderKey),this))return;
            elapsed += dt;
            logElapsed += dt;
            if (elapsed < (RepairEnabled ? .25f : 3f) || (!RepairEnabled && samples >= 120)) return;
            elapsed = 0;
            bool logNow=logElapsed>=3f && (RepairEnabled || samples<120);
            if (logNow) logElapsed=0;
            try {
                var screen = ScreenManager.TopScreen;
                if (screen == null || screen.GetType().FullName.Contains("MissionScreen")) return;
                if (screen.GetType().FullName=="SandBox.View.Map.MapScreen") return;
                var visuals = new HashSet<AgentVisuals>();
                var owners = new Dictionary<AgentVisuals,string>();
                var seen = new HashSet<object>(ReferenceComparer.Instance);
                // Character creation's scene is not a tableau texture provider.
                // Read its exact stage -> BodyGeneratorView path before graph scanning.
                var bodyGenerator=FindBodyGenerator(screen);
                if (bodyGenerator!=null) CollectTableauVisuals(bodyGenerator,visuals,owners);
                int widgets=0;
                foreach (var layer in screen.Layers) {
                    var gauntlet=layer as GauntletLayer;
                    if (gauntlet == null || gauntlet.UIContext == null) continue;
                    var queue = new Queue<Widget>();
                    queue.Enqueue(gauntlet.UIContext.Root);
                    while (queue.Count > 0 && widgets++ < 5000) {
                        var widget=queue.Dequeue();
                        if (widget == null) continue;
                        // Inventory has thousands of item widgets. Read its explicit
                        // preview provider before traversing any screen object graph.
                        var texture=widget as TextureWidget;
                        var tableau=FindCharacterTableau(texture?.TextureProvider);
                        if (tableau!=null) CollectTableauVisuals(tableau,visuals,owners);
                        foreach (var child in widget.Children) queue.Enqueue(child);
                    }
                }
                // A separate discovery failure must not discard previews already found.
                try { Inspect(screen, 0, seen, visuals, owners, screen.GetType().FullName); }
                catch (Exception e) { if (logNow) Write(new {kind="discovery_error",error=e.ToString()}); }
                if (logNow) Write(new { kind="scan", screen=screen.GetType().FullName, widgets, visuals=visuals.Count });
                foreach (var visual in visuals) {
                    if (RepairEnabled) {
                        var registry=AppDomain.CurrentDomain.GetData(RegistryKey) as Dictionary<string,Action<AgentVisuals,string,string>>;
                        var data=visual.GetCopyAgentVisualsData();
                        var races=TaleWorlds.Core.FaceGen.GetRaceNames().ToArray();
                        Action<AgentVisuals,string,string> repair;
                        if(registry!=null && data.RaceData>=0 && data.RaceData<races.Length && registry.TryGetValue(races[data.RaceData],out repair))repair(visual,owners[visual],screen.GetType().FullName);
                    }
                    if (logNow) Capture(visual,screen.GetType().FullName);
                }
            } catch (Exception e) { Write(new { kind="error", error=e.ToString() }); }
        }

        private void CollectTableauVisuals(object tableau,HashSet<AgentVisuals> visuals,Dictionary<AgentVisuals,string> owners) {
            foreach (var field in Fields(tableau.GetType())) {
                if (!typeof(AgentVisuals).IsAssignableFrom(field.FieldType)) continue;
                string owner=field.DeclaringType.FullName+"."+field.Name;
                if (!IsPreviewOwner(owner)) continue;
                var visual=field.GetValue(tableau) as AgentVisuals;
                if (visual==null) continue;
                visuals.Add(visual);owners[visual]=owner;
            }
        }

        internal static object FindCharacterTableau(object provider) {
            if (provider==null || provider.GetType().FullName!="TaleWorlds.MountAndBlade.GauntletUI.TextureProviders.CharacterTableauTextureProvider") return null;
            var field=provider.GetType().GetField("_characterTableau",BindingFlags.Instance|BindingFlags.NonPublic);
            var tableau=field?.GetValue(provider);
            return tableau?.GetType().FullName=="TaleWorlds.MountAndBlade.View.Tableaus.CharacterTableau"?tableau:null;
        }

        internal static object FindBodyGenerator(object screen) {
            const string bodyType="TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView";
            if (screen==null || screen.GetType().FullName!="SandBox.View.CharacterCreation.CharacterCreationScreen") return null;
            var stageField=screen.GetType().GetField("_currentStageView",BindingFlags.Instance|BindingFlags.NonPublic);
            var stage=stageField?.GetValue(screen);
            if (stage==null || stage.GetType().FullName!="SandBox.GauntletUI.CharacterCreation.CharacterCreationFaceGeneratorView") return null;
            var viewField=stage.GetType().GetField("_faceGeneratorView",BindingFlags.Instance|BindingFlags.NonPublic);
            var view=viewField?.GetValue(stage);
            return view?.GetType().FullName==bodyType?view:null;
        }

        private FieldInfo[] Fields(Type type) {
            FieldInfo[] result;
            if (fields.TryGetValue(type, out result)) return result;
            var list = new List<FieldInfo>();
            for (var t=type; t!=null && t!=typeof(object); t=t.BaseType)
                list.AddRange(t.GetFields(BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.DeclaredOnly));
            fields[type]=result=list.ToArray();
            return result;
        }

        private void Inspect(object obj, int depth, HashSet<object> seen, HashSet<AgentVisuals> visuals,
                             Dictionary<AgentVisuals,string> owners, string owner) {
            if (obj == null || depth > 5 || seen.Count > 8000) return;
            var type=obj.GetType();
            // Boxed ActionIndexCache.Equals(object) casts without checking type.
            // Filter values first and use identity for graph cycle detection.
            if (type.IsValueType || obj is string || obj is Delegate) return;
            if (!seen.Add(obj)) return;
            if (type.FullName=="TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView") {
                CollectTableauVisuals(obj,visuals,owners);
                return;
            }
            var visual=obj as AgentVisuals;
            if (visual != null) {
                // MapScreen also owns live campaign AgentVisuals. Never refresh
                // those as UI previews: their weapons/native entities belong to
                // the map lifecycle, which differs from a tableau scene.
                if (IsPreviewOwner(owner)) { visuals.Add(visual); owners[visual]=owner; }
                return;
            }
            if (obj is NativeObject) return;
            // Traverse UI-owned fields only, never the campaign/world object graph.
            string ns=type.Namespace??"";
            if (!(obj is Widget) && !(ns.StartsWith("TaleWorlds.ScreenSystem") ||
                  ns.StartsWith("TaleWorlds.Engine.GauntletUI") ||
                  ns.StartsWith("TaleWorlds.MountAndBlade.View") ||
                  ns.StartsWith("TaleWorlds.MountAndBlade.GauntletUI") ||
                  ns.StartsWith("SandBox.GauntletUI") || ns.StartsWith("SandBox.View"))) return;
            foreach (var field in Fields(type)) {
                object value;
                try { value=field.GetValue(obj); } catch { continue; }
                // Widget children are handled by the bounded queue above.
                if (value is Widget) continue;
                var enumerable=value as IEnumerable;
                if (enumerable != null && !(value is string)) {
                    int n=0;
                    foreach (var entry in enumerable) {
                        if (++n > 128) break;
                        var pair=entry as DictionaryEntry?;
                        Inspect(pair.HasValue?pair.Value.Value:entry,depth+1,seen,visuals,owners,type.FullName+"."+field.Name);
                    }
                } else Inspect(value,depth+1,seen,visuals,owners,type.FullName+"."+field.Name);
            }
        }

        internal static bool IsPreviewOwner(string owner) {
            return owner != null && (owner.StartsWith("TaleWorlds.MountAndBlade.View.Tableaus.CharacterTableau.",StringComparison.Ordinal) ||
                owner.StartsWith("TaleWorlds.MountAndBlade.View.Tableaus.BasicCharacterTableau.",StringComparison.Ordinal) ||
                owner.StartsWith("TaleWorlds.MountAndBlade.GauntletUI.BodyGenerator.BodyGeneratorView.",StringComparison.Ordinal));
        }

        internal static bool NeedsPreviewRepair(string skeleton, string actionSet, string expectedSet) {
            return skeleton!="lumine_skeleton" || actionSet!=expectedSet;
        }

        private void CorrectPreview(AgentVisuals visual, string owner, string screen) {
            if (!IsPreviewOwner(owner)) return;
            try {
                var data=visual.GetCopyAgentVisualsData();
                var races=TaleWorlds.Core.FaceGen.GetRaceNames().ToArray();
                if (data.RaceData<0 || data.RaceData>=races.Length || races[data.RaceData]!="lumine") return;
                var entity=visual.GetEntity();
                var oldSkeleton=entity.Skeleton;
                if (oldSkeleton==null) return;
                string previousSkeleton=oldSkeleton.GetName();
                string previousSet=data.ActionSetData.GetName();
                bool facegen=owner.Contains("BodyGenerator") || previousSet.EndsWith("_facegen");
                string setName="as_lumine"+(data.SkeletonTypeData==SkeletonType.Female?"_female":"")+
                               (facegen?"_facegen":"_warrior");
                if (!NeedsPreviewRepair(previousSkeleton,previousSet,setName)) return;
                var ownSet=MBActionSet.GetActionSet(setName);
                if (!ownSet.IsValid || ownSet.GetSkeletonName()!="lumine_skeleton") {
                    Write(new { kind="repair_unavailable", screen, set=setName });
                    return;
                }
                var actions=new [] { MBSkeletonExtensions.GetActionAtChannel(oldSkeleton,0),
                                     MBSkeletonExtensions.GetActionAtChannel(oldSkeleton,1) };
                var progress=new [] { oldSkeleton.GetAnimationParameterAtChannel(0),oldSkeleton.GetAnimationParameterAtChannel(1) };
                float scale=visual.GetScale();
                if (scale<=0) return;
                var frame=entity.GetFrame();
                var unscaledFrame=frame;
                unscaledFrame.rotation.ApplyScaleLocal(1f/scale);
                // Refresh with null oldEquipment forces skeleton recreation, including
                // inventory views where unchanged weapon slots would skip recreation.
                var refresh=typeof(AgentVisuals).GetMethod("Refresh",BindingFlags.Instance|BindingFlags.NonPublic,
                    null,new [] { typeof(bool),typeof(bool),typeof(Equipment),typeof(bool),typeof(bool) },null);
                var dataField=typeof(AgentVisuals).GetField("_data",BindingFlags.Instance|BindingFlags.NonPublic);
                if (refresh==null || dataField==null) return;
                data.ActionSet(ownSet).Frame(unscaledFrame).Scale(scale);
                dataField.SetValue(visual,data);
                refresh.Invoke(visual,new object[] { false,true,null,false,false });
                var skeleton=visual.GetEntity().Skeleton;
                for (int channel=0;channel<2;channel++) {
                    var action=actions[channel];
                    if (action!=ActionIndexCache.act_none)
                        MBSkeletonExtensions.SetAgentActionChannel(skeleton,channel,in action,progress[channel],-.2f,true,0);
                }
                skeleton.TickAnimationsAndForceUpdate(.001f,frame,true);
                Write(new { kind="preview_repair", screen, owner, previous_skeleton=previousSkeleton,
                    previous_action_set=previousSet, skeleton=skeleton.GetName(), action_set=ownSet.GetName(),
                    position_scale_and_channel_progress_preserved=true });
            } catch (Exception e) { Write(new { kind="repair_error", error=e.ToString() }); }
        }

        private static float[] Matrix(MatrixFrame f) {
            return new [] { f.rotation.s.x,f.rotation.s.y,f.rotation.s.z,0,
                            f.rotation.f.x,f.rotation.f.y,f.rotation.f.z,0,
                            f.rotation.u.x,f.rotation.u.y,f.rotation.u.z,0,
                            f.origin.x,f.origin.y,f.origin.z,1 };
        }

        private void Capture(AgentVisuals visual, string screen) {
            try {
                int count;
                screenSamples.TryGetValue(screen,out count);
                if (count>=60) return;
                var data=visual.GetCopyAgentVisualsData();
                var races=TaleWorlds.Core.FaceGen.GetRaceNames().ToArray();
                var entity=visual.GetEntity();
                var skeleton=entity.Skeleton;
                if (skeleton == null) return;
                var meshes=new List<object>();
                GetMeshes(entity,0,meshes);
                bool adaRace=data.RaceData>=0 && data.RaceData<races.Length && races[data.RaceData]=="lumine";
                if (!adaRace && !serializer.Serialize(meshes).Contains("lumine_")) return;
                var bones=new List<object>();
                for (sbyte i=0; i<skeleton.GetBoneCount(); i++) {
                    bones.Add(new { index=i, name=skeleton.GetBoneName(i),
                        rest_local_unmapped=Matrix(skeleton.GetBoneLocalRestFrame(i,false)),
                        rest_local_mapped=Matrix(skeleton.GetBoneLocalRestFrame(i,true)),
                        posed_entity=Matrix(skeleton.GetBoneEntitialFrame(i)) });
                }
                var equipment=visual.GetEquipment();
                Write(new { kind="lumine_pose", screen, race=data.RaceData, skeleton=skeleton.GetName(),
                    skeleton_type=data.SkeletonTypeData.ToString(), morph_anims=data.UseMorphAnimsData,
                    monster=data.MonsterData?.StringId, action_set=data.ActionSetData.GetName(),
                    action_set_skeleton=data.ActionSetData.GetSkeletonName(),
                    gloves=equipment==null?null:equipment[EquipmentIndex.Gloves].Item?.StringId,
                    action0=MBSkeletonExtensions.GetActionAtChannel(skeleton,0).GetName(),
                    action1=MBSkeletonExtensions.GetActionAtChannel(skeleton,1).GetName(),
                    animation0=skeleton.GetAnimationAtChannel(0), animation1=skeleton.GetAnimationAtChannel(1),
                    progress0=skeleton.GetAnimationParameterAtChannel(0), progress1=skeleton.GetAnimationParameterAtChannel(1),
                    scale=visual.GetScale(), global_frame=Matrix(entity.GetGlobalFrame()), bones, meshes });
                samples++;
                screenSamples[screen]=count+1;
            } catch (Exception e) { Write(new { kind="capture_error", error=e.ToString() }); }
        }

        private static void GetMeshes(GameEntity entity, int depth, List<object> rows) {
            if (depth>4 || rows.Count>100) return;
            for (int i=0; i<entity.MultiMeshComponentCount; i++) {
                var mesh=entity.GetMetaMesh(i);
                var groups=new List<string>();
                for (int j=0;j<mesh.MeshCount;j++) groups.Add(mesh.GetMeshAtIndex(j).Name);
                rows.Add(new { meta_mesh=mesh.GetName(), groups });
            }
            for (int i=0; i<entity.ChildCount; i++) GetMeshes(entity.GetChild(i),depth+1,rows);
        }

        private void Write(object record) {
            try {
                string dir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                    "Mount and Blade II Bannerlord","LumineRace");
                Directory.CreateDirectory(dir);
                var envelope=new { session, time=DateTime.Now.ToString("s"), record };
                string path=Path.Combine(dir,RepairEnabled?"ui_runtime.jsonl":"ui_probe_v1.jsonl");
                if (File.Exists(path) && new FileInfo(path).Length>12*1024*1024) return;
                File.AppendAllText(path,serializer.Serialize(envelope)+Environment.NewLine);
            } catch { /* Diagnostics must never interrupt UI/gameplay. */ }
        }
    }
}
