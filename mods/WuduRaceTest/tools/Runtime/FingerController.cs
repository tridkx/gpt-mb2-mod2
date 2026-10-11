using System;
using System.Collections.Generic;
using TaleWorlds.Core;
using TaleWorlds.Engine;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;

namespace WuduRaceTest {
    // The first 28 bones and their weapon/IK semantics remain native-compatible.
    // Added joints are driven after animation evaluation, only on this race.
    public sealed class FingerController : MissionBehavior {
        public override MissionBehaviorType BehaviorType => MissionBehaviorType.Other;
        private sealed class State {
            public Skeleton Skeleton;
            public readonly MatrixFrame[] Rest = new MatrixFrame[30];
            public float Left, Right;
            public int LastLeft=-1, LastRight=-1;
        }
        private readonly Dictionary<Agent,State> agents = new Dictionary<Agent,State>();
        private readonly HashSet<Agent> rejected = new HashSet<Agent>();
        private static readonly string[] Fingers={"thumb","index","middle","ring","little"};
        private static readonly float[] Angles={48f,62f,42f};
        public override void OnAgentBuild(Agent agent, Banner banner) {
            if(agent.Character==null || !agent.IsHuman || TaleWorlds.Core.FaceGen.GetRaceNames()[agent.Character.Race]!="wdr_canglan")return;
            agents[agent]=new State();
        }
        public override void OnAgentDeleted(Agent agent) {agents.Remove(agent);rejected.Remove(agent);}
        public override void OnRemoveBehavior() {agents.Clear();rejected.Clear();}
        private static bool Grip(Agent agent, bool left) {
            EquipmentIndex index=left?agent.GetOffhandWieldedItemIndex():agent.GetPrimaryWieldedItemIndex();
            if(index>=EquipmentIndex.WeaponItemBeginSlot && index<EquipmentIndex.ExtraWeaponSlot && !agent.Equipment[index].IsEmpty)return true;
            var weapon=agent.WieldedWeapon.CurrentUsageItem;
            // Bow support and a two-handed grip use both hands.
            return left && weapon!=null && (weapon.WeaponClass==WeaponClass.Bow ||
                weapon.WeaponFlags.HasFlag(WeaponFlags.NotUsableWithOneHand));
        }
        public override void OnPreDisplayMissionTick(float dt) {
            foreach(var pair in agents) {
                var agent=pair.Key;var state=pair.Value;
                if(rejected.Contains(agent) || !agent.IsActive() || agent.AgentVisuals==null)continue;
                try {
                    var sk=agent.AgentVisuals.GetSkeleton();
                    if(sk==null || !sk.IsValid)continue;
                    if(state.Skeleton==null || state.Skeleton.Pointer!=sk.Pointer) {
                        if(sk.GetName()!="wdr_skeleton" || sk.GetBoneCount()!=58) {rejected.Add(agent);SubModule.Log("FINGER_REJECT agent="+agent.Index+" skeleton="+sk.GetName()+" bones="+sk.GetBoneCount());continue;}
                        for(int j=0;j<30;j++) {
                            string expected=(j<15?"l_":"r_")+Fingers[(j%15)/3]+"_"+(j%3+1);
                            if(sk.GetBoneName((sbyte)(28+j))!=expected)throw new InvalidOperationException("Finger index mismatch: "+expected);
                            state.Rest[j]=sk.GetBoneLocalRestFrame((sbyte)(28+j),false);
                        }
                        state.Skeleton=sk;
                        SubModule.Log("FINGER_READY agent="+agent.Index+" joints=30");
                    }
                    int left=Grip(agent,true)?1:0, right=Grip(agent,false)?1:0;
                    float blend=1f-(float)Math.Exp(-12f*Math.Max(0,Math.Min(dt,.1f)));
                    state.Left+=(left-state.Left)*blend;state.Right+=(right-state.Right)*blend;
                    for(int j=0;j<30;j++) {
                        var frame=state.Rest[j];
                        frame.rotation.RotateAboutSide(Angles[j%3]*(float)Math.PI/180f*(j<15?state.Left:state.Right));
                        sk.SetBoneLocalFrame((sbyte)(28+j),frame);
                    }
                    sk.UpdateEntitialFramesFromLocalFrames();
                    if(left!=state.LastLeft || right!=state.LastRight) {
                        SubModule.Log("FINGER_GRIP agent="+agent.Index+" left="+left+" right="+right);
                        state.LastLeft=left;state.LastRight=right;
                    }
                } catch(Exception e) {rejected.Add(agent);SubModule.Log("FINGER_ERROR agent="+agent.Index+" "+e);}
            }
        }
    }
}
