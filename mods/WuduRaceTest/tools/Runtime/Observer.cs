using System;
using System.IO;
using System.Globalization;
using TaleWorlds.Core;
using TaleWorlds.CampaignSystem;
using TaleWorlds.MountAndBlade;

namespace WuduRaceTest {
    public class SubModule : MBSubModuleBase {
        internal static void Log(string message) {
            try {
                string dir=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),"Mount and Blade II Bannerlord","WuduRaceTest");
                Directory.CreateDirectory(dir);
                File.AppendAllText(Path.Combine(dir,"probe_v0.1.2.log"),DateTime.Now.ToString("s")+" "+message+Environment.NewLine);
            } catch(Exception) { /* Diagnostics must not interrupt the game. */ }
        }
        public override void OnGameInitializationFinished(Game game) {
            try {
                Log("BEGIN v0.1.2 races="+string.Join(",",TaleWorlds.Core.FaceGen.GetRaceNames()));
                var troop=game.ObjectManager.GetObject<CharacterObject>("imperial_recruit");
                if(troop!=null)Log("troop=imperial_recruit race="+troop.Race+" female="+troop.IsFemale+" level="+troop.Level+" monster="+TaleWorlds.Core.FaceGen.GetBaseMonsterNameFromRace(troop.Race)+" power="+(Campaign.Current==null?"n/a":Campaign.Current.Models.MilitaryPowerModel.GetDefaultTroopPower(troop).ToString(CultureInfo.InvariantCulture)));
            } catch(Exception e) { Log("INIT_ERROR "+e); }
        }
        public override void OnMissionBehaviorInitialize(Mission mission) {
            if(!GameNetwork.IsMultiplayer)mission.AddMissionBehavior(new Observer());
        }
    }
    public sealed class Observer : MissionBehavior {
        public override MissionBehaviorType BehaviorType { get { return MissionBehaviorType.Other; } }
        private int count;
        public override void OnAgentBuild(Agent agent, Banner banner) {
            if(agent.Character==null || agent.Character.StringId!="imperial_recruit" || count++>=10)return;
            try {
                var sk=agent.AgentVisuals.GetSkeleton();
                SubModule.Log("SPAWN agent="+agent.Index+" race="+agent.Character.Race+" scale="+agent.AgentScale.ToString(CultureInfo.InvariantCulture)+" bones="+sk.GetBoneCount());
                foreach(sbyte i in new sbyte[]{0,2,9,10,12,13,15,17,19})SubModule.Log("rest bone="+i+" name="+sk.GetBoneName(i)+" frame="+sk.GetBoneLocalRestFrame(i,false));
                foreach(var slot in new[]{EquipmentIndex.Head,EquipmentIndex.Body,EquipmentIndex.Gloves,EquipmentIndex.Leg,EquipmentIndex.Cape})SubModule.Log("equipment "+slot+"="+(agent.SpawnEquipment[slot].Item?.StringId??"empty"));
            } catch(Exception e) { SubModule.Log("SPAWN_ERROR "+e); }
        }
    }
}
