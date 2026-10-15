using System;
using System.IO;
using TaleWorlds.CampaignSystem;
using TaleWorlds.Core;
using TaleWorlds.Library;
using TaleWorlds.MountAndBlade;

namespace WutheringUndeadRace
{
 public sealed class SubModule : MBSubModuleBase
 {
  public static bool Ready;
  public static string Root=>Path.GetDirectoryName(Path.GetDirectoryName(Path.GetDirectoryName(typeof(SubModule).Assembly.Location)));
  protected override void OnSubModuleLoad()
  {
   base.OnSubModuleLoad();
   try{Catalog.Load(Path.Combine(Root,"ModuleData","undead_catalog.xml"));Patches.Install();Ready=true;Log("Runtime hooks ready: "+Patches.Targets.Count);}
   catch(Exception e){Fail(e);}
  }
  protected override void OnGameStart(Game game,IGameStarter starter)
  {base.OnGameStart(game,starter);if(Ready && game.GameType is Campaign)((CampaignGameStarter)starter).AddBehavior(new UndeadBehavior());}
  public static void Log(string message)
  {try{File.AppendAllText(Path.Combine(Root,"ModuleData","runtime.log"),DateTime.Now.ToString("s")+" "+message+Environment.NewLine);}catch{}}
  public static void Fail(Exception e)
  {Ready=false;Log("DISABLED: "+e);InformationManager.DisplayMessage(new InformationMessage("鸣潮感染危机初始化失败，请检查 ModuleData/runtime.log。"));}
 }
}
