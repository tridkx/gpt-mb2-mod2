using MCM.Abstractions.Attributes;
using MCM.Abstractions.Attributes.v2;
using MCM.Abstractions.Base.PerSave;

namespace WutheringUndeadRace
{
 public sealed class Settings : AttributePerSaveSettings<Settings>
 {
  public override string Id => "WutheringUndeadRace_v1";
  public override string DisplayName => "鸣潮感染危机 / Wuthering Undead Race";
  public override string FolderName => "WutheringUndeadRace";
  public override int UIVersion => 2;
  public static Settings Current => Instance ?? Defaults;
  private static readonly Settings Defaults = new Settings();
  [SettingPropertyBool("允许生成与领主重生", RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public bool Spawning {get;set;}=true;
  [SettingPropertyInteger("开局宽限天数",0,365,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int GraceDays {get;set;}=3;
  [SettingPropertyInteger("生成间隔（小时）",1,168,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int SpawnHours {get;set;}=12;
  [SettingPropertyInteger("尸群队伍上限（含领主）",1,100,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int MaxParties {get;set;}=24;
  [SettingPropertyInteger("全局普通感染兵上限",10,20000,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int MaxTroops {get;set;}=3000;
  [SettingPropertyInteger("单队普通感染兵上限",5,2000,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int PartyCap {get;set;}=250;
  [SettingPropertyInteger("新队最少人数",1,500,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int SpawnMin {get;set;}=20;
  [SettingPropertyInteger("新队最多人数",1,1000,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int SpawnMax {get;set;}=45;
  [SettingPropertyInteger("新队最高兵阶",1,5,RequireRestart=false)]
  [SettingPropertyGroup("生成")]
  public int SpawnTier {get;set;}=3;
  [SettingPropertyFloatingInteger("领主重生冷却（天）",0.25f,30f,"0.00",RequireRestart=false)]
  [SettingPropertyGroup("领主与军团")]
  public float RespawnDays {get;set;}=3f;
  [SettingPropertyBool("允许尸群军团",RequireRestart=false)]
  [SettingPropertyGroup("领主与军团")]
  public bool Armies {get;set;}=true;
  [SettingPropertyFloatingInteger("军团集结半径",1f,200f,"0.0",RequireRestart=false)]
  [SettingPropertyGroup("领主与军团")]
  public float GatherRadius {get;set;}=35f;
  [SettingPropertyInteger("军团最多队伍",2,16,RequireRestart=false)]
  [SettingPropertyGroup("领主与军团")]
  public int ArmyParties {get;set;}=4;
  [SettingPropertyInteger("军团普通兵力上限",10,5000,RequireRestart=false)]
  [SettingPropertyGroup("领主与军团")]
  public int ArmyCap {get;set;}=600;
  [SettingPropertyInteger("军团持续时间（小时）",6,240,RequireRestart=false)]
  [SettingPropertyGroup("领主与军团")]
  public int ArmyHours {get;set;}=48;
  [SettingPropertyInteger("军团集结冷却（小时）",1,240,RequireRestart=false)]
  [SettingPropertyGroup("领主与军团")]
  public int ArmyCooldown {get;set;}=24;
  [SettingPropertyFloatingInteger("大地图速度倍率",0.5f,3f,"0.00",RequireRestart=false)]
  [SettingPropertyGroup("行为")]
  public float Speed {get;set;}=1.05f;
  [SettingPropertyFloatingInteger("最终地图速度上限（0不限制）",0f,15f,"0.00",RequireRestart=false)]
  [SettingPropertyGroup("行为")]
  public float SpeedCap {get;set;}=0f;
  [SettingPropertyFloatingInteger("追击搜索半径",1f,200f,"0.0",RequireRestart=false)]
  [SettingPropertyGroup("行为")]
  public float ChaseRadius {get;set;}=25f;
  [SettingPropertyInteger("转化率（%）",0,100,RequireRestart=false)]
  [SettingPropertyGroup("转化与成长")]
  public int Conversion {get;set;}=100;
  [SettingPropertyBool("阵亡普通兵参与转化",RequireRestart=false)]
  [SettingPropertyGroup("转化与成长")]
  public bool ConvertDead {get;set;}=true;
  [SettingPropertyBool("实际被俘普通兵参与转化",RequireRestart=false)]
  [SettingPropertyGroup("转化与成长")]
  public bool ConvertCaptured {get;set;}=true;
  [SettingPropertyBool("尸群经验自动升级",RequireRestart=false)]
  [SettingPropertyGroup("转化与成长")]
  public bool Upgrade {get;set;}=true;
  [SettingPropertyFloatingInteger("升级所需经验倍率",0.1f,5f,"0.00",RequireRestart=false)]
  [SettingPropertyGroup("转化与成长")]
  public float UpgradeXp {get;set;}=1f;
  [SettingPropertyInteger("每兵阶清剿金币",0,1000,RequireRestart=false)]
  [SettingPropertyGroup("清剿奖励")]
  public int GoldPerTier {get;set;}=10;
  [SettingPropertyFloatingInteger("每兵阶清剿影响力",0f,5f,"0.00",RequireRestart=false)]
  [SettingPropertyGroup("清剿奖励")]
  public float InfluencePerTier {get;set;}=.05f;
  [SettingPropertyInteger("奖励感染兵比例（%）",0,100,RequireRestart=false)]
  [SettingPropertyGroup("清剿奖励")]
  public int RewardPercent {get;set;}=10;
  [SettingPropertyFloatingInteger("感染者自动结算战力倍率",0.25f,5f,"0.00",RequireRestart=false)]
  [SettingPropertyGroup("战斗")]
  public float SimulationPower {get;set;}=1f;
 }
}
