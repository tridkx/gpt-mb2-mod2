"""Build a scoped reader that includes native-style flagless simulation drivers."""
import subprocess
from context import workspace_root
def prepare_driver_probe(root):
    w=workspace_root(root);b=root/'build';source=(w/'tools/cloth_compiler/NativeClothProbe.cs').read_text(encoding='utf8')
    old='mesh in mm.Meshes.Where(m=>m.Flags.Contains("uses_cloth_simulation"))'
    new='mesh in mm.Meshes.Where(m=>m.Flags.Contains("uses_cloth_simulation") || mm.TypelessDataSegments.Any(s=>s.OwnerGuid==m.Guid && s.TypeGuid==new Guid("b97e0f10-df49-4666-8f1d-ada6630d4b4e")))'
    assert source.count(old)==1
    target=b/'native_driver_probe.cs';target.write_text(source.replace(old,new),encoding='utf8')
    result=subprocess.run(['dotnet','build',str(w/'tools/pmx_race_pipeline/NativeDriverProbe.csproj'),'--ignore-failed-sources','-p:DriverProbeSource='+str(target),'-p:BaseIntermediateOutputPath='+str(b/'native_driver_probe_obj')+'/', '-o',str(b/'cloth_probe')],capture_output=True,text=True,encoding='utf8',errors='replace')
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
