using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
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

namespace REAdaWongRace.UIProbe {
    // Read-only UI observer: no patches, action setters or mesh mutation.
    public sealed class SubModule : MBSubModuleBase {
        private float elapsed;
        private int samples;
        private readonly string session = DateTime.Now.ToString("yyyyMMdd_HHmmss");
        private readonly Dictionary<Type, FieldInfo[]> fields = new Dictionary<Type, FieldInfo[]>();
        private readonly JavaScriptSerializer serializer = new JavaScriptSerializer();

        protected override void OnSubModuleLoad() {
            base.OnSubModuleLoad();
            Write(new { kind="loaded", probe="ui-v1", changes_game_state=false });
        }

        protected override void OnApplicationTick(float dt) {
            base.OnApplicationTick(dt);
            elapsed += dt;
            if (elapsed < 3 || samples >= 120) return;
            elapsed = 0;
            try {
                var screen = ScreenManager.TopScreen;
                if (screen == null) return;
                var visuals = new HashSet<AgentVisuals>();
                var seen = new HashSet<object>();
                Inspect(screen, 0, seen, visuals);
                int widgets=0;
                foreach (var layer in screen.Layers) {
                    var gauntlet=layer as GauntletLayer;
                    if (gauntlet == null || gauntlet.UIContext == null) continue;
                    var queue = new Queue<Widget>();
                    queue.Enqueue(gauntlet.UIContext.Root);
                    while (queue.Count > 0 && widgets++ < 5000) {
                        var widget=queue.Dequeue();
                        if (widget == null) continue;
                        Inspect(widget, 0, seen, visuals);
                        foreach (var child in widget.Children) queue.Enqueue(child);
                    }
                }
                Write(new { kind="scan", screen=screen.GetType().FullName, widgets, visuals=visuals.Count });
                foreach (var visual in visuals) Capture(visual, screen.GetType().FullName);
            } catch (Exception e) { Write(new { kind="error", error=e.ToString() }); }
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

        private void Inspect(object obj, int depth, HashSet<object> seen, HashSet<AgentVisuals> visuals) {
            if (obj == null || depth > 5 || seen.Count > 8000 || !seen.Add(obj)) return;
            var visual=obj as AgentVisuals;
            if (visual != null) { visuals.Add(visual); return; }
            var type=obj.GetType();
            if (type.IsValueType || obj is string || obj is Delegate || obj is NativeObject) return;
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
                        Inspect(pair.HasValue?pair.Value.Value:entry, depth+1, seen, visuals);
                    }
                } else Inspect(value,depth+1,seen,visuals);
            }
        }

        private static float[] Matrix(MatrixFrame f) {
            return new [] { f.rotation.s.x,f.rotation.s.y,f.rotation.s.z,0,
                            f.rotation.f.x,f.rotation.f.y,f.rotation.f.z,0,
                            f.rotation.u.x,f.rotation.u.y,f.rotation.u.z,0,
                            f.origin.x,f.origin.y,f.origin.z,1 };
        }

        private void Capture(AgentVisuals visual, string screen) {
            try {
                var data=visual.GetCopyAgentVisualsData();
                var races=TaleWorlds.Core.FaceGen.GetRaceNames().ToArray();
                var entity=visual.GetEntity();
                var skeleton=entity.Skeleton;
                if (skeleton == null) return;
                var meshes=new List<object>();
                GetMeshes(entity,0,meshes);
                bool adaRace=data.RaceData>=0 && data.RaceData<races.Length && races[data.RaceData]=="reada_wong";
                if (!adaRace && !serializer.Serialize(meshes).Contains("adar_")) return;
                var bones=new List<object>();
                for (sbyte i=0; i<skeleton.GetBoneCount(); i++) {
                    bones.Add(new { index=i, name=skeleton.GetBoneName(i),
                        rest_local_unmapped=Matrix(skeleton.GetBoneLocalRestFrame(i,false)),
                        rest_local_mapped=Matrix(skeleton.GetBoneLocalRestFrame(i,true)),
                        posed_entity=Matrix(skeleton.GetBoneEntitialFrame(i)) });
                }
                Write(new { kind="ada_pose", screen, race=data.RaceData, skeleton=skeleton.GetName(),
                    skeleton_type=data.SkeletonTypeData.ToString(), morph_anims=data.UseMorphAnimsData,
                    monster=data.MonsterData?.StringId, action_set=data.ActionSetData.GetName(),
                    action_set_skeleton=data.ActionSetData.GetSkeletonName(),
                    gloves=visual.GetEquipment()[EquipmentIndex.Gloves].Item?.StringId,
                    action0=MBSkeletonExtensions.GetActionAtChannel(skeleton,0).ToString(),
                    action1=MBSkeletonExtensions.GetActionAtChannel(skeleton,1).ToString(),
                    animation0=skeleton.GetAnimationAtChannel(0), animation1=skeleton.GetAnimationAtChannel(1),
                    progress0=skeleton.GetAnimationParameterAtChannel(0), progress1=skeleton.GetAnimationParameterAtChannel(1),
                    scale=visual.GetScale(), global_frame=Matrix(entity.GetGlobalFrame()), bones, meshes });
                samples++;
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
                    "Mount and Blade II Bannerlord","REAdaWongRace");
                Directory.CreateDirectory(dir);
                var envelope=new { session, time=DateTime.Now.ToString("s"), record };
                string path=Path.Combine(dir,"ui_probe_v1.jsonl");
                if (File.Exists(path) && new FileInfo(path).Length>12*1024*1024) return;
                File.AppendAllText(path,serializer.Serialize(envelope)+Environment.NewLine);
            } catch { /* Diagnostics must never interrupt UI/gameplay. */ }
        }
    }
}
