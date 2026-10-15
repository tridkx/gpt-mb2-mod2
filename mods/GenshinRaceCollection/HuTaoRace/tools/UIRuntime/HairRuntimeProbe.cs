using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using TaleWorlds.Engine;
using TaleWorlds.MountAndBlade.View;

namespace HuTaoRace.UIRuntime {
    public sealed partial class SubModule {
        private sealed class HairProbeState { public HairProbeState(){} public DateTime Next; public int Count; }
        private readonly System.Runtime.CompilerServices.ConditionalWeakTable<AgentVisuals,HairProbeState> hairProbeStates =
            new System.Runtime.CompilerServices.ConditionalWeakTable<AgentVisuals,HairProbeState>();
        private readonly HashSet<string> hairProbeParts = new HashSet<string> { "hutao_part_10" };

        partial void SampleRuntimeHair(AgentVisuals visual,string owner,string screen) {
            var state=hairProbeStates.GetOrCreateValue(visual);
            var now=DateTime.UtcNow;
            if(state.Count>=6 || now<state.Next)return;
            state.Next=now.AddSeconds(2);state.Count++;
            try {
                var entity=visual.GetEntity();
                if(entity==null)return;
                var rows=new List<object>();
                if(entity.Skeleton!=null)
                    foreach(var mesh in entity.Skeleton.GetAllMeshes()) {
                        if(rows.Count>=160)break;
                        HairProbeMesh(mesh,"skeleton",rows);
                    }
                HairProbeEntity(entity,0,rows);
                Write(new {kind="runtime_hair_materials",screen,owner,sample=state.Count,
                    skeleton=entity.Skeleton==null?null:entity.Skeleton.GetName(),meshes=rows,
                    changes_rendering=false});
            } catch(Exception error) {Write(new {kind="runtime_hair_probe_error",error=error.ToString()});}
        }
        private void HairProbeEntity(GameEntity entity,int depth,List<object> rows) {
            if(depth>4||rows.Count>=160)return;
            for(int i=0;i<entity.MultiMeshComponentCount && rows.Count<160;i++) {
                var mm=entity.GetMetaMesh(i);
                for(int j=0;j<mm.MeshCount && rows.Count<160;j++)HairProbeMesh(mm.GetMeshAtIndex(j),"entity/"+mm.GetName(),rows);
            }
            for(int i=0;i<entity.ChildCount && rows.Count<160;i++)HairProbeEntity(entity.GetChild(i),depth+1,rows);
        }
        private void HairProbeMesh(Mesh mesh,string source,List<object> rows) {
            if(mesh==null)return;
            try {
                var name=mesh.Name;var material=mesh.GetMaterial();
                var texture=material==null?null:material.GetTextureWithSlot(0);
                var normalized=Regex.Replace(Regex.Replace(name,@"\.b\d+$",""),@"\.lod\d+$","");
                rows.Add(new {source,name,expected_hair=hairProbeParts.Contains(normalized),
                    named_proxy=name.StartsWith("hutao_cloth_proxy",StringComparison.Ordinal),
                    visibility_mask=(uint)mesh.VisibilityMask,has_cloth=mesh.HasCloth(),
                    material=material==null?null:material.Name,
                    diffuse=texture==null?null:texture.Name,
                    shader_flags=material==null?0UL:material.GetShaderFlags(),
                    alpha_test=material==null?0:material.GetAlphaTestValue()});
            } catch(Exception error) {rows.Add(new {source,error=error.Message});}
        }
    }
}
